import threading
import time
from contextlib import contextmanager

from backend.config import AI_PROVIDER, AI_MODEL, AI_MAX_CONCURRENCY, AI_SLOT_TIMEOUT


class LLMRateLimitError(RuntimeError):
    """Saturation : soit trop d'appels LLM simultanés chez nous (créneau indisponible), soit
    le fournisseur qui nous limite (HTTP 429). C'est transitoire, PAS une panne -> les routeurs
    la traduisent en 429 « réessayez dans un instant », jamais en 500/502. Sous-classe de
    RuntimeError : si un routeur l'oublie, le filet générique l'attrape encore (au pire 500,
    jamais un crash)."""


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
    """
    fournisseur = provider or AI_PROVIDER
    if fournisseur not in ("groq", "anthropic"):
        raise ValueError(f"Fournisseur inconnu : {fournisseur}")  # validé AVANT de prendre un créneau
    with _llm_slot():
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
    if response.status_code == 429:
        raise LLMRateLimitError("Trop de demandes en ce moment. Réessayez dans un instant.")
    if not response.ok:
        raise RuntimeError(f"Erreur {response.status_code}: {response.text}")
    return response.json()["choices"][0]["message"]["content"]


# Note : la dictée (Whisper) passe par backend/groq_client.transcribe_audio, pas ici.
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
    # temperature : volontairement IGNORÉE — les modèles Claude Opus 4.x la
    # rejettent (400). Le déterminisme se pilote par le prompt, pas par ce param.
    # json_mode : Claude n'a pas de response_format. Sans schéma JSON (le métier
    # parse en tolérant), on force le JSON par instruction système — jamais en
    # recopiant le dict response_format de Groq.
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
        # Prime sur json_mode (contrainte forte vs simple instruction).
        kwargs["output_config"] = {"format": {"type": "json_schema", "schema": schema}}
    elif json_mode:
        kwargs["system"] = "Réponds uniquement avec du JSON valide, sans aucun texte avant ni après."
    # timeout=60 s (secondes côté SDK Python) — voie propre du SDK, aligné sur les
    # autres branches LLM (requests timeout=60). Sans ça, le SDK attendrait 10 min.
    if not cle:
        raise RuntimeError("Clé API texte manquante (non résolue en base).")
    client = anthropic.Anthropic(api_key=cle, timeout=60)
    try:
        message = client.messages.create(**kwargs)
    except anthropic.RateLimitError:
        raise LLMRateLimitError("Trop de demandes en ce moment. Réessayez dans un instant.")
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
        yield from _groq_stream(prompt, cle=cle, model=model, max_tokens=max_tokens, temperature=temperature, read_timeout=read_timeout, retry_max=retry_max, retry_wait_max=retry_wait_max)
    elif fournisseur == "anthropic":
        yield from _anthropic_stream(prompt, cle=cle, model=model, max_tokens=max_tokens, read_timeout=read_timeout)
    else:
        raise ValueError(f"Fournisseur inconnu : {fournisseur}")


def _anthropic_stream(prompt, *, cle, model=None, max_tokens=2048, read_timeout=30.0):
    import anthropic
    import httpx
    if not cle:
        raise RuntimeError("Clé API texte manquante (non résolue en base).")
    # temperature : volontairement IGNORÉE (les Claude Opus 4.x la rejettent), comme _anthropic.
    # timeout de LECTURE = coupure de silence (se réarme à chaque morceau) ; connect/write/pool =
    # petits garde-fous de connexion, indépendants de la durée de génération.
    client = anthropic.Anthropic(
        api_key=cle,
        timeout=httpx.Timeout(read_timeout, connect=10.0, write=10.0, pool=10.0),
    )
    kwargs = {
        "model": model or AI_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
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
    except anthropic.RateLimitError:
        raise LLMRateLimitError("Trop de demandes en ce moment. Réessayez dans un instant.")


def _groq_stream(prompt, *, cle, model=None, max_tokens=2048, temperature=None, read_timeout=30.0, retry_max=0, retry_wait_max=10):
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
        if response.status_code == 429:
            raise LLMRateLimitError("Trop de demandes en ce moment. Réessayez dans un instant.")
        if not response.ok:
            raise RuntimeError(f"Erreur {response.status_code}: {response.text}")
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
