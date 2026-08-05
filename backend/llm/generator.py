import logging
import threading
import time
from contextlib import contextmanager

from backend.config import AI_PROVIDER, AI_MODEL, AI_MAX_CONCURRENCY, AI_SLOT_TIMEOUT

# Le détail technique d'un échec fournisseur (corps de réponse, identifiant de requête) va ICI,
# jamais à l'écran : l'admin lit une phrase, le journal garde de quoi diagnostiquer.
log = logging.getLogger(__name__)


class LLMRateLimitError(RuntimeError):
    """Saturation : soit trop d'appels LLM simultanés chez nous (créneau indisponible), soit
    le fournisseur qui nous limite (HTTP 429). C'est transitoire, PAS une panne -> les routeurs
    la traduisent en 429 « réessayez dans un instant », jamais en 500/502. Sous-classe de
    RuntimeError : si un routeur l'oublie, le filet générique l'attrape encore (au pire 500,
    jamais un crash)."""


class LLMIndisponibleError(RuntimeError):
    """Le service d'IA ne répond pas MAINTENANT : saturé (529 « overloaded »), en panne (5xx), ou
    la connexion a lâché. Transitoire et EXTÉRIEUR à l'application — il n'y a rien à corriger chez
    nous, il faut redemander plus tard ou changer de fournisseur."""


class LLMModeleIncompatibleError(RuntimeError):
    """Le MODÈLE choisi ne sait pas faire ce qu'on lui demande (ici : rendre une réponse au format
    imposé). Ce n'est ni une panne ni une saturation : c'est un RÉGLAGE à changer. Distinguer les
    deux compte — devant « réessayez plus tard », un admin attend en vain une panne qui n'existe
    pas, alors qu'il lui suffisait de choisir un autre modèle."""


class LLMQuotaCompteError(RuntimeError):
    """La demande dépasse ce que le PALIER DU COMPTE autorise (ex. Groq : 8 000 tokens par minute
    sur l'offre gratuite, alors qu'un référentiel entier en réclame ~49 000). Ni une panne, ni un
    mauvais modèle : réessayer ou changer de modèle ne sert à rien. Seuls l'abonnement ou la taille
    du document peuvent changer — d'où un message qui dit CE geste-là et pas un autre."""


def _traduire_echec_fournisseur(statut: int, corps: str, modele: str) -> None:
    """Traduit un échec HTTP du fournisseur en exception MÉTIER portant un message d'HUMAIN.

    Le message part d'ici, à la source, et pas de chaque écran : tous les appelants font déjà
    `f\"... impossible : {e}\"`, donc corriger le texte ici les corrige tous d'un coup — et un
    nouvel appelant hérite du bon message sans rien savoir de tout ça.

    On ne recopie JAMAIS le JSON du fournisseur dans le message : `{'type': 'error', 'error':
    {'details': None, 'type': 'overloaded_error'...}}` ne dit rien à un admin, sinon que le
    logiciel lui parle une langue qui n'est pas la sienne. Le détail technique reste dans les
    journaux, où il sert."""
    texte = (corps or "").lower()
    if statut == 429:
        raise LLMRateLimitError("Trop de demandes en ce moment. Réessayez dans un instant.")
    # Format de sortie refusé : c'est le MODÈLE qui ne sait pas, pas le service qui flanche.
    if statut == 400 and ("json_schema" in texte or "response_format" in texte or "output_config" in texte):
        raise LLMModeleIncompatibleError(
            f"Le modèle « {modele} » ne sait pas rendre une réponse au format exigé par cette "
            f"opération. Choisissez un autre modèle dans Paramètres → Génération : cette étape a "
            f"besoin d'un modèle capable de sortie contrainte."
        )
    # 413 : la demande dépasse ce que le PALIER DU COMPTE accepte (Groq plafonne les tokens par
    # minute). Rien à voir avec une panne ni avec le modèle : ni attendre ni changer de modèle n'y
    # changera quoi que ce soit — c'est l'abonnement ou la taille du document qui doit bouger.
    if statut == 413:
        raise LLMQuotaCompteError(
            "Le document est trop volumineux pour le palier de votre compte chez ce fournisseur "
            "d'IA : il refuse une demande de cette taille. Basculez sur l'autre fournisseur dans "
            "Paramètres → Génération, ou relevez le palier de votre abonnement."
        )
    if statut >= 500:   # 500/502/503 = panne, 529 = « overloaded » (saturation Anthropic)
        raise LLMIndisponibleError(
            "Le service d'IA est saturé ou indisponible en ce moment. Ce n'est pas une panne de "
            "l'application : réessayez dans quelques minutes, ou basculez sur l'autre fournisseur "
            "dans Paramètres → Génération."
        )


# Régulation de concurrence : UN seul sémaphore pour TOUS les appels sortants Groq
# (génération + OCR + dictée), car ils partagent le même quota de compte. Les endpoints
# sont synchrones -> exécutés dans le pool de threads de FastAPI : le primitif correct est
# threading, pas asyncio. Au-delà de la limite, les appels en trop attendent un créneau.
_llm_semaphore = threading.BoundedSemaphore(AI_MAX_CONCURRENCY)


def acquire_llm_slot() -> None:
    """Prend un créneau d'appel LLM (attend au plus AI_SLOT_TIMEOUT s). Lève LLMRateLimitError si
    aucun créneau ne se libère. Le CALLER est alors responsable d'appeler release_llm_slot() dans
    TOUS ses cas de sortie — voie utilisée par le streaming, où le créneau doit rester pris pendant
    TOUTE la durée du flux (un ticket jamais rendu = créneau perdu jusqu'au redémarrage)."""
    if not _llm_semaphore.acquire(timeout=AI_SLOT_TIMEOUT):
        raise LLMRateLimitError("Trop de générations simultanées en ce moment. Réessayez dans un instant.")


def release_llm_slot() -> None:
    """Rend un créneau pris par acquire_llm_slot(). À appeler UNE seule fois par acquisition."""
    _llm_semaphore.release()


@contextmanager
def _llm_slot():
    """Réserve un créneau d'appel LLM le temps d'un bloc (voie synchrone, non-streaming)."""
    acquire_llm_slot()
    try:
        yield
    finally:
        release_llm_slot()


def _retry_wait(retry_after_raw, wait_max: int) -> float:
    """Délai (secondes) avant une re-tentative sur 429 : on RESPECTE le `Retry-After` renvoyé par le
    fournisseur, mais PLAFONNÉ à `wait_max` (réglage admin en base) — un prof n'attend jamais plus.
    En-tête absent ou illisible -> on attend le plafond (l'hypothèse la plus prudente)."""
    try:
        wait = float(retry_after_raw)
    except (TypeError, ValueError):
        wait = float(wait_max)
    return max(0.0, min(wait, float(wait_max)))


def generate(
    prompt: str,
    *,
    cle: str,
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    json_mode: bool = False,
    schema: dict | None = None,
    appel_long: bool = False,
    read_timeout: float = 60.0,
    retry_max: int = 0,
    retry_wait_max: int = 10,
) -> str:
    """Point d'entrée UNIQUE pour tout appel LLM texte.

    Les paramètres sont des INTENTIONS métier neutres (« combien de tokens »,
    « du JSON », « déterministe »), jamais des formats fournisseur. Chaque
    adaptateur les traduit dans la langue de son fournisseur — ou les ignore
    quand le fournisseur ne les accepte pas (ex. temperature chez Anthropic).

    `schema` (Structured Outputs) : un schéma JSON qui CONTRAINT la sortie token par token
    (grammaire compilée côté API). Ce n'est PAS « demander du JSON » (ça, c'est `json_mode`) :
    un champ hors schéma devient PHYSIQUEMENT impossible à produire. Quand `schema` est fourni,
    il PRIME sur `json_mode`. Chaque adaptateur le traduit (`output_config` chez Anthropic,
    `response_format`/`json_schema` chez Groq) — norme des deux côtés.

    `provider` / `model` : résolvés par l'appelant (côté backend, lus en base à chaud).
    `None` ⇒ repli sur AI_PROVIDER / AI_MODEL (config/.env) — rétro-compatible. generate()
    reste pur : il ne lit aucune base, il reçoit les chaînes déjà résolues.

    `retry_max` / `retry_wait_max` : résilience 429 (réglages admin lus en base par l'appelant,
    passés ici — le moteur reste pur). Sur une limite de débit fournisseur, on re-tente au lieu
    d'abandonner. Défaut retry_max=0 ⇒ aucun retry (comportement historique). Anthropic re-tente
    déjà côté SDK ⇒ on ne branche le retry manuel que sur Groq.

    `appel_long` : à mettre à True dès que le modèle doit LIRE UN DOCUMENT ENTIER (découpe d'un
    référentiel, rédaction d'un prompt à partir d'un PDF complet). Ces appels durent plusieurs
    minutes ; en non-streaming, la requête est bornée par un délai TOTAL et se fait couper avant la
    fin (« Request timed out or interrupted »). Le mode long emprunte le MÊME transport que
    `generate_stream` — le flux — mais recolle les morceaux et rend la chaîne complète : l'appelant
    ne change pas d'une ligne, et le schéma (Structured Outputs) s'applique exactement pareil.
    `read_timeout` : délai de SILENCE (durée max sans nouveau morceau), pas un délai total — il se
    RÉARME à chaque morceau reçu, donc il ne borne jamais une génération qui progresse.
    """
    fournisseur = provider or AI_PROVIDER
    if fournisseur not in ("groq", "anthropic"):
        raise ValueError(f"Fournisseur inconnu : {fournisseur}")  # validé AVANT de prendre un créneau
    with _llm_slot():
        if appel_long:
            # Le créneau LLM est tenu par ce `with` pendant TOUTE la consommation du flux (le
            # générateur est vidé ici, pas rendu à l'appelant) — pas de créneau relâché en cours de
            # génération, contrairement à `generate_stream` où l'appelant en a la charge.
            if fournisseur == "groq":
                morceaux = _groq_stream(prompt, cle=cle, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode, schema=schema, read_timeout=read_timeout, retry_max=retry_max, retry_wait_max=retry_wait_max)
            else:  # anthropic
                morceaux = _anthropic_stream(prompt, cle=cle, model=model, max_tokens=max_tokens, json_mode=json_mode, schema=schema, read_timeout=read_timeout)
            return "".join(morceaux)
        if fournisseur == "groq":
            return _groq(prompt, cle=cle, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode, schema=schema, retry_max=retry_max, retry_wait_max=retry_wait_max)
        else:  # anthropic
            return _anthropic(prompt, cle=cle, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode, schema=schema)


def _groq(
    prompt: str,
    *,
    cle: str,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    json_mode: bool = False,
    schema: dict | None = None,
    retry_max: int = 0,
    retry_wait_max: int = 10,
) -> str:
    import requests
    if not cle:
        raise RuntimeError("Clé API texte manquante (non résolue en base).")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {cle}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model or AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        body["temperature"] = temperature
    if schema is not None:
        # Structured Outputs Groq : décodage contraint au schéma (équivalent de output_config
        # Anthropic). Prime sur json_mode : un champ hors schéma est impossible à produire.
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "reponse", "strict": True, "schema": schema},
        }
    elif json_mode:
        body["response_format"] = {"type": "json_object"}
    # Résilience 429 : sur une limite de débit fournisseur, on RE-TENTE (jusqu'à retry_max fois) en
    # respectant le délai `Retry-After` plafonné à retry_wait_max. retry_max=0 -> comportement d'avant.
    for tentative in range(retry_max + 1):
        response = requests.post(url, headers=headers, json=body, timeout=60)
        if response.status_code == 429 and tentative < retry_max:
            time.sleep(_retry_wait(response.headers.get("Retry-After"), retry_wait_max))
            continue
        break
    if not response.ok:
        # Traduction à la source : 429 / format refusé / service en panne repartent en message
        # d'humain. Le corps brut du fournisseur ne va JAMAIS à l'écran, seulement au journal.
        _traduire_echec_fournisseur(response.status_code, response.text, model or AI_MODEL)
        log.warning("Groq %s : %s", response.status_code, response.text[:500])
        raise RuntimeError("Le service d'IA a refusé la demande. Réessayez ; si cela persiste, "
                           "signalez-le : le détail technique est dans les journaux du serveur.")
    return response.json()["choices"][0]["message"]["content"]


# Note : la dictée (Whisper) passe par backend/core/groq_client.transcribe_audio, pas ici.
# (L'ancien transcribe_audio de ce module était du code mort — supprimé.)


def transcribe_image(image_bytes: bytes, mime_type: str = "image/jpeg", *, api_key: str, model: str, max_tokens: int = 2048) -> str:
    # api_key / model : résolus par le backend EN BASE (cle_env_ocr / ocr_model) et passés ici.
    # src reste pur : il reçoit la clé ET le modèle, il ne les cherche jamais (aucun modèle en dur).
    import base64
    import requests
    if not api_key:
        raise RuntimeError("Clé OCR absente : la génération OCR ne peut pas s'exécuter.")
    if not model:
        raise RuntimeError("Modèle OCR absent : la génération OCR ne peut pas s'exécuter.")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    body = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                },
                {
                    "type": "text",
                    "text": "Extrais tout le texte visible sur ce document de façon fidèle, sans reformuler ni résumer. Retourne uniquement le texte brut.",
                },
            ],
        }],
        "max_tokens": max_tokens,
    }
    with _llm_slot():
        response = requests.post(url, headers=headers, json=body, timeout=60)
    if response.status_code == 429:
        raise LLMRateLimitError("Trop de demandes en ce moment. Réessayez dans un instant.")
    if not response.ok:
        raise RuntimeError(f"Erreur OCR {response.status_code}: {response.text}")
    return response.json()["choices"][0]["message"]["content"]


def _echec_anthropic(e, modele: str) -> None:
    """Traduit une erreur du SDK Anthropic en message d'humain — même règle que pour Groq, mais
    l'échec arrive ici sous forme d'exception plutôt que de réponse HTTP. Ne rend jamais la main :
    ou bien elle lève l'exception métier, ou bien elle relaie l'erreur d'origine."""
    statut = getattr(e, "status_code", 0) or 0
    corps = str(e)  # le SDK met déjà le corps de la réponse dans le texte de l'exception
    log.warning("Anthropic %s : %s", statut, corps[:500])
    _traduire_echec_fournisseur(statut, corps, modele)
    raise e  # statut non répertorié : on ne masque rien, l'erreur d'origine repart telle quelle


def _anthropic_kwargs(prompt: str, *, model: str | None, max_tokens: int, json_mode: bool, schema: dict | None) -> dict:
    """Corps de requête Anthropic, construit à UN SEUL endroit pour les DEUX voies (non-streaming et
    flux). Toute évolution du contrat de sortie profite aux deux d'un coup : impossible qu'un
    `output_config` existe d'un côté et pas de l'autre.

    temperature : volontairement IGNORÉE — les modèles Claude Opus 4.x la rejettent (400). Le
    déterminisme se pilote par le prompt, pas par ce paramètre.
    json_mode : Claude n'a pas de response_format. Sans schéma JSON (le métier parse en tolérant),
    on force le JSON par instruction système — jamais en recopiant le dict response_format de Groq."""
    kwargs = {
        "model": model or AI_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if schema is not None:
        # Structured Outputs (GA) : la génération est CONTRAINTE token par token au schéma
        # (grammaire compilée par l'API), pas une simple consigne « réponds en JSON ». Un champ
        # hors schéma est PHYSIQUEMENT impossible — avec additionalProperties:false, le modèle ne
        # peut plus ajouter de « contenu » superflu, donc la réponse reste petite (ni troncature,
        # ni dépassement de délai). La contrainte porte sur la sortie finale, PAS sur le
        # raisonnement (thinking) : le modèle réfléchit librement, la réponse reste conforme.
        # Prime sur json_mode (contrainte forte vs simple instruction). Vaut aussi en flux.
        kwargs["output_config"] = {"format": {"type": "json_schema", "schema": schema}}
    elif json_mode:
        kwargs["system"] = "Réponds uniquement avec du JSON valide, sans aucun texte avant ni après."
    return kwargs


def _anthropic(
    prompt: str,
    *,
    cle: str,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    json_mode: bool = False,
    schema: dict | None = None,
) -> str:
    import anthropic
    kwargs = _anthropic_kwargs(prompt, model=model, max_tokens=max_tokens, json_mode=json_mode, schema=schema)
    # timeout=60 s = délai TOTAL de la requête, donc réservé aux APPELS COURTS (une consigne, une
    # réponse). Tout appel qui fait LIRE UN DOCUMENT ENTIER au modèle dure plusieurs minutes et
    # dépasserait cette barre : il doit passer par `generate(appel_long=True)`, qui emprunte le flux
    # et ne connaît qu'un délai de SILENCE réarmable. Ne PAS relever ce 60 s pour faire tenir un
    # appel long en non-streaming : l'API coupe elle-même les requêtes longues non streamées.
    if not cle:
        raise RuntimeError("Clé API texte manquante (non résolue en base).")
    client = anthropic.Anthropic(api_key=cle, timeout=60)
    try:
        message = client.messages.create(**kwargs)
    except anthropic.APIStatusError as e:
        _echec_anthropic(e, model or AI_MODEL)
    except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
        log.warning("Anthropic : connexion interrompue — %s", e)
        raise LLMIndisponibleError(
            "La réponse de l'IA n'est pas arrivée jusqu'au bout (connexion interrompue). "
            "Réessayez dans un instant."
        )
    # Troncature : si le modèle atteint sa limite de sortie, la réponse est COUPÉE. On le signale
    # honnêtement — le drapeau vient de l'API (`stop_reason`), rien n'est deviné — au lieu de rendre
    # un texte tronqué que l'appelant prendrait pour complet (et qui planterait plus loin sur un
    # faux motif « non parsable »). Mesuré le 12/07 : Sonnet 5 consomme une partie de max_tokens en
    # raisonnement, donc la sortie visible peut être coupée là où Groq aurait tout rendu.
    if getattr(message, "stop_reason", None) == "max_tokens":
        raise RuntimeError("Réponse coupée : le modèle a atteint sa limite de sortie.")
    # La réponse est une LISTE de blocs. Avec le raisonnement (thinking), le 1er bloc peut être un
    # ThinkingBlock (pas de .text) → on ne lit JAMAIS content[0] à l'aveugle : on garde les blocs de
    # type "text" et on les concatène. Aucun bloc de texte = on LÈVE (jamais une chaîne vide en douce).
    textes = [b.text for b in message.content if getattr(b, "type", None) == "text"]
    if not textes:
        types = [getattr(b, "type", "?") for b in message.content]
        raise RuntimeError(f"Réponse Anthropic sans bloc de texte (blocs reçus : {types}).")
    return "".join(textes)


# ---------------------------------------------------------------------------
# STREAMING — génération au fil de l'écriture (deltas de texte)
#
# Le créneau LLM (sémaphore) N'EST PAS pris ici : l'appelant le prend AVANT (acquire_llm_slot) et
# le rend dans TOUS ses cas de sortie (fin, erreur, déconnexion du client) — le flux doit tenir le
# créneau tout du long. `read_timeout` = coupure de SILENCE : durée max sans nouveau morceau. Elle
# se RÉARME à chaque morceau reçu (timeout de lecture HTTP), donc elle ne borne PAS une génération
# qui progresse — seulement les silences anormaux. Valeur lue en base (réglage admin), zéro dur.
# ---------------------------------------------------------------------------

def generate_stream(
    prompt: str,
    *,
    cle: str,
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    json_mode: bool = False,
    schema: dict | None = None,
    read_timeout: float = 30.0,
    retry_max: int = 0,
    retry_wait_max: int = 10,
):
    """Itérateur de morceaux de texte (deltas), au fil de l'écriture par le modèle. Même résolution
    fournisseur/modèle que generate() (chaînes déjà résolues par l'appelant). NE prend PAS le créneau
    LLM (cf. en-tête). Lève LLMRateLimitError (429 fournisseur) ou RuntimeError (autre échec).

    `retry_max` / `retry_wait_max` : résilience 429 (réglages admin en base, passés par l'appelant).
    Le retry n'agit qu'à l'OUVERTURE du flux, avant le 1er mot. Anthropic re-tente déjà côté SDK."""
    fournisseur = provider or AI_PROVIDER
    if fournisseur == "groq":
        yield from _groq_stream(prompt, cle=cle, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode, schema=schema, read_timeout=read_timeout, retry_max=retry_max, retry_wait_max=retry_wait_max)
    elif fournisseur == "anthropic":
        yield from _anthropic_stream(prompt, cle=cle, model=model, max_tokens=max_tokens, json_mode=json_mode, schema=schema, read_timeout=read_timeout)
    else:
        raise ValueError(f"Fournisseur inconnu : {fournisseur}")


def _anthropic_stream(prompt, *, cle, model=None, max_tokens=2048, json_mode=False, schema=None, read_timeout=30.0):
    import anthropic
    import httpx
    if not cle:
        raise RuntimeError("Clé API texte manquante (non résolue en base).")
    # temperature : volontairement IGNORÉE (les Claude Opus 4.x la rejettent), comme _anthropic.
    # timeout de LECTURE = coupure de silence (se réarme à chaque morceau) ; connect/write/pool =
    # petits garde-fous de connexion, indépendants de la durée de génération. Ce client est PROPRE au
    # flux : il ne reprend rien du client non-streaming, donc le 60 s total ne peut pas mordre ici.
    client = anthropic.Anthropic(
        api_key=cle,
        timeout=httpx.Timeout(read_timeout, connect=10.0, write=10.0, pool=10.0),
    )
    # Même construction que la voie non-streaming (schéma compris) : `_anthropic_kwargs` est le seul
    # endroit qui décide du contrat de sortie. Structured Outputs vaut en flux comme hors flux.
    kwargs = _anthropic_kwargs(prompt, model=model, max_tokens=max_tokens, json_mode=json_mode, schema=schema)
    try:
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
            # Garde-fou troncature (repris de la voie non-streaming) : si le modèle s'est arrêté sur
            # sa limite de sortie, le texte est COUPÉ. On le SIGNALE en fin de flux (le motif vient de
            # l'API, rien n'est deviné) → l'endpoint émet `error` au lieu de `done`, l'écran refuse un
            # texte amputé au lieu de l'enregistrer comme complet.
            final = stream.get_final_message()
            if getattr(final, "stop_reason", None) == "max_tokens":
                raise RuntimeError("Réponse coupée : le modèle a atteint sa limite de sortie.")
    except anthropic.APIStatusError as e:
        _echec_anthropic(e, model or AI_MODEL)
    except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
        log.warning("Anthropic (flux) : silence trop long ou connexion perdue — %s", e)
        raise LLMIndisponibleError(
            "La réponse de l'IA s'est interrompue en cours de route. Réessayez dans un instant."
        )


def _groq_stream(prompt, *, cle, model=None, max_tokens=2048, temperature=None, json_mode=False, schema=None, read_timeout=30.0, retry_max=0, retry_wait_max=10):
    import json
    import requests
    if not cle:
        raise RuntimeError("Clé API texte manquante (non résolue en base).")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {cle}", "Content-Type": "application/json"}
    body = {
        "model": model or AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "stream": True,
    }
    if temperature is not None:
        body["temperature"] = temperature
    if schema is not None:
        # Structured Outputs Groq, à l'identique de la voie non-streaming (`_groq`) : le contrat de
        # sortie ne doit pas dépendre du mode de transport. Prime sur json_mode.
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "reponse", "strict": True, "schema": schema},
        }
    elif json_mode:
        body["response_format"] = {"type": "json_object"}
    # (connect, read) : read = silence toléré entre deux morceaux (se réarme à chaque morceau reçu).
    # Résilience 429 : la limite de débit arrive dans les EN-TÊTES (avant le 1er mot) -> on peut
    # RE-TENTER proprement l'ouverture du flux (jusqu'à retry_max fois) tant qu'aucun texte n'est
    # encore parti à l'écran. Une fois le flux commencé, on ne re-tente JAMAIS. retry_max=0 -> avant.
    for tentative in range(retry_max + 1):
        response = requests.post(url, headers=headers, json=body, stream=True, timeout=(10, read_timeout))
        if response.status_code == 429 and tentative < retry_max:
            attente = _retry_wait(response.headers.get("Retry-After"), retry_wait_max)
            response.close()
            time.sleep(attente)
            continue
        break
    with response:
        if not response.ok:
            _traduire_echec_fournisseur(response.status_code, response.text, model or AI_MODEL)
            log.warning("Groq (flux) %s : %s", response.status_code, response.text[:500])
            raise RuntimeError("Le service d'IA a refusé la demande. Réessayez ; si cela persiste, "
                               "signalez-le : le détail technique est dans les journaux du serveur.")
        # Groq n'annonce pas de charset sur son flux SSE -> requests retombe sur ISO-8859-1 et
        # decode_unicode=True rendrait les accents UTF-8 en mojibake (« é » -> « Ã© »). On force UTF-8.
        response.encoding = "utf-8"
        finish_reason = None
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if payload == "[DONE]":
                break
            try:
                data = json.loads(payload)
            except ValueError:
                continue
            choix = (data.get("choices") or [{}])[0]
            if choix.get("finish_reason"):
                finish_reason = choix["finish_reason"]
            delta = choix.get("delta", {}).get("content")
            if delta:
                yield delta
        # Garde-fou troncature symétrique de la voie Anthropic : « length » = sortie coupée sur la
        # limite de tokens → on lève, l'endpoint émet `error`, l'écran refuse un texte amputé.
        if finish_reason == "length":
            raise RuntimeError("Réponse coupée : le modèle a atteint sa limite de sortie.")
