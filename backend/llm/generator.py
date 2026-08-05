import logging
import threading
import time
from contextlib import contextmanager

from backend.config import AI_PROVIDER, AI_MODEL, AI_MAX_CONCURRENCY, AI_SLOT_TIMEOUT, AITOOLS_PRODUCT_ID
from backend.core.horloge import maintenant_utc
from backend.llm import cache

# `cache` et `horloge` ne dérogent pas à la pureté de ce module : ni l'un ni l'autre ne connaît la
# base — le premier ne sait manipuler que des fichiers, le second ne fait que lire l'heure.

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


def _marquer(e: Exception, detail: str) -> Exception:
    """Accroche un détail technique à une exception, quelle qu'en soit l'origine.

    TOUTE erreur d'IA doit en porter un, pas seulement celles qui viennent d'une réponse HTTP :
    une réponse coupée, une clé absente, un document trop gros n'ont pas de code d'état, et c'est
    justement là que « le détail est dans les journaux » laissait l'administrateur sans rien."""
    e.technique = detail
    return e


def _avec_technique(e: Exception, fournisseur: str, modele: str, statut: int, corps: str) -> Exception:
    """Accroche à l'exception le détail BRUT de l'échec, sans jamais l'injecter dans son message.

    Deux publics, deux besoins : le prof lit la phrase d'humain et rien d'autre ; l'admin, lui,
    doit pouvoir corriger — et « le détail est dans les journaux du serveur » l'envoie chercher
    ailleurs ce que l'application sait déjà. Le détail voyage donc À CÔTÉ du message, et seuls les
    écrans d'administration le montrent (cf. `detail_admin`). Le fournisseur et le modèle en font
    partie : avec trois fournisseurs, savoir QUI a refusé est la moitié du diagnostic."""
    return _marquer(e, f"{fournisseur} · {modele} · HTTP {statut} — {(corps or '').strip()[:400]}")


def detail_admin(e: Exception) -> str:
    """Le complément technique à coller au message, RÉSERVÉ aux écrans d'administration.
    Chaîne vide si l'exception n'en porte pas : l'appelant concatène sans se poser de question."""
    technique = getattr(e, "technique", "")
    return f"\n\nDétail technique : {technique}" if technique else ""


def _traduire_echec_fournisseur(statut: int, corps: str, modele: str, fournisseur: str = "") -> None:
    """Traduit un échec HTTP du fournisseur en exception MÉTIER portant un message d'HUMAIN.

    Le message part d'ici, à la source, et pas de chaque écran : tous les appelants font déjà
    `f\"... impossible : {e}\"`, donc corriger le texte ici les corrige tous d'un coup — et un
    nouvel appelant hérite du bon message sans rien savoir de tout ça.

    On ne recopie JAMAIS le JSON du fournisseur dans le MESSAGE : `{'type': 'error', 'error':
    {'details': None, 'type': 'overloaded_error'...}}` ne dit rien à un prof, sinon que le
    logiciel lui parle une langue qui n'est pas la sienne. Il voyage à CÔTÉ, sur l'exception
    (`_avec_technique`), et seuls les écrans d'administration l'affichent (`detail_admin`)."""
    texte = (corps or "").lower()
    tech = lambda e: _avec_technique(e, fournisseur, modele, statut, corps)  # noqa: E731
    if statut == 429:
        raise tech(LLMRateLimitError("Trop de demandes en ce moment. Réessayez dans un instant."))
    # Fenêtre dépassée. Le filet DERRIÈRE `verifier_fenetre` : celui-ci refuse sur une ESTIMATION,
    # volontairement basse pour ne jamais bloquer à tort — quand elle est trop optimiste, c'est le
    # fournisseur qui trancne, et il le dit en clair (« inputs tokens + max_tokens = 46235 but must
    # be < 32000 »). Le geste attendu est le même : changer de modèle, pas réessayer.
    if statut == 400 and "must be <" in texte:
        raise tech(LLMModeleIncompatibleError(
            f"Le document est trop volumineux pour le modèle « {modele} » : sa fenêtre ne peut pas "
            f"le contenir en entier. Choisissez un modèle à plus grande fenêtre dans "
            f"Paramètres → Génération."
        ))
    # Format de sortie refusé : c'est le MODÈLE qui ne sait pas, pas le service qui flanche.
    if statut == 400 and ("json_schema" in texte or "response_format" in texte or "output_config" in texte):
        raise tech(LLMModeleIncompatibleError(
            f"Le modèle « {modele} » ne sait pas rendre une réponse au format exigé par cette "
            f"opération. Choisissez un autre modèle dans Paramètres → Génération : cette étape a "
            f"besoin d'un modèle capable de sortie contrainte."
        ))
    # 413 : la demande dépasse ce que le PALIER DU COMPTE accepte (Groq plafonne les tokens par
    # minute). Rien à voir avec une panne ni avec le modèle : ni attendre ni changer de modèle n'y
    # changera quoi que ce soit — c'est l'abonnement ou la taille du document qui doit bouger.
    if statut == 413:
        raise tech(LLMQuotaCompteError(
            "Le document est trop volumineux pour le palier de votre compte chez ce fournisseur "
            "d'IA : il refuse une demande de cette taille. Basculez sur un autre fournisseur dans "
            "Paramètres → Génération, ou relevez le palier de votre abonnement."
        ))
    if statut >= 500:   # 500/502/503 = panne, 529 = « overloaded » (saturation Anthropic)
        raise tech(LLMIndisponibleError(
            "Le service d'IA est saturé ou indisponible en ce moment. Ce n'est pas une panne de "
            "l'application : réessayez dans quelques minutes, ou basculez sur un autre fournisseur "
            "dans Paramètres → Génération."
        ))


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


# --- Fournisseurs qui parlent le dialecte OpenAI (chat/completions) -------------------------
# Groq et Infomaniak AI Tools servent la MÊME API : mêmes champs, même flux SSE, même
# `response_format` pour la sortie contrainte (vérifié en appelant les deux). Ils partagent donc
# l'adaptateur `_groq` / `_groq_stream` — seule l'URL les distingue, d'où ce résolveur plutôt
# qu'une deuxième copie du même code. (Anthropic, lui, a son SDK et ses propres fonctions.)
_URL_GROQ = "https://api.groq.com/openai/v1/chat/completions"


def _journal_appel(fournisseur: str, modele: str, motif, entree, sortie, debut: float,
                   outil: str | None = None, cache_ecriture=None, cache_lecture=None) -> None:
    """UNE ligne par appel LLM RÉUSSI : qui a répondu, avec quel modèle, pourquoi il s'est arrêté,
    ce qu'il a consommé, en combien de temps.

    Jusqu'ici seuls les ÉCHECS laissaient une trace. Devant une découpe qui ne rend que deux unités,
    la question est « le modèle a-t-il été coupé, ou a-t-il vraiment fini ? » — et personne ne
    pouvait y répondre, faute d'avoir noté `finish_reason`. Un appel qui réussit mal ne dit rien
    de lui-même : c'est précisément pour ça qu'il faut l'écrire.

    DEUX DESTINATIONS, DEUX BESOINS. Le log répond à la question du moment, en clair, devant un
    appel qu'on est en train de regarder. La table `usage_llm` répond aux questions qui
    s'additionnent (par modèle, par outil, par période) — un journal ne s'additionne pas. Écrire aux
    deux endroits n'est pas un doublon : c'est la même mesure pour deux usages qui ne se remplacent
    pas, et le log survit même si la base refuse.

    LE MOTEUR RESTE PUR. Il ne lit toujours AUCUN réglage en base : fournisseur, modèle et bornes
    lui arrivent résolus par l'appelant. Il pose seulement une trace APRÈS coup, dans une session
    à lui, sans jamais pouvoir faire échouer la génération (cf. `enregistrer_usage`).

    `cache_ecriture` / `cache_lecture` : tokens du CACHE DE PROMPT du fournisseur. Ils comptent
    séparément parce qu'ils ne se paient pas au même prix (écriture 1,25×, relecture 0,10×), et
    surtout parce qu'Anthropic les SORT de `input_tokens` : les ignorer ferait afficher un appel
    de 70 000 tokens comme un appel de 200, et une facture dix fois trop basse."""
    duree = time.time() - debut
    log.info(
        "LLM %s · %s · outil=%s · arrêt=%s · tokens entrée=%s sortie=%s "
        "cache(écrit=%s lu=%s) · %.1fs",
        fournisseur, modele, outil or "?", motif if motif is not None else "?",
        entree if entree is not None else "?", sortie if sortie is not None else "?",
        cache_ecriture if cache_ecriture is not None else "-",
        cache_lecture if cache_lecture is not None else "-",
        duree,
    )
    # Import LOCAL : `generator` est importé très tôt et ne doit pas traîner la couche base derrière
    # lui au chargement. Même précaution que partout ailleurs ici (requests, anthropic, httpx).
    try:
        from backend.analytique.usage import enregistrer_usage
        enregistrer_usage(
            fournisseur=fournisseur, modele=modele, outil=outil,
            tokens_entree=entree, tokens_sortie=sortie,
            duree_ms=int(duree * 1000), motif_arret=motif,
            tokens_cache_ecriture=cache_ecriture, tokens_cache_lecture=cache_lecture,
        )
    except Exception as e:  # y compris l'import lui-même : mesurer ne casse jamais générer
        log.error("Usage LLM non enregistré : %s: %s", type(e).__name__, e)


def _tokens_estimes(texte: str) -> int:
    """Estimation GROSSIÈRE du nombre de tokens d'un texte français : ~3,5 caractères par token.

    Aucun tokenizer n'est embarqué (il faudrait celui de chaque fournisseur, et il change avec le
    modèle). L'estimation ne sert qu'à un garde-fou : décider s'il est inutile d'envoyer."""
    return int(len(texte) / 3.5) + 1


# Marge de sécurité sur la fenêtre : l'estimation ci-dessus est approximative, et frôler la borne
# revient à se faire refuser quand même — après plusieurs minutes d'attente. On ne s'autorise donc
# que 90 % de la fenêtre annoncée. Le prix de la marge est un refus un peu plus tôt ; le prix de
# son absence est un appel long pour rien.
_MARGE_FENETRE = 0.90


def verifier_fenetre(prompt: str, *, max_tokens: int, contexte_max: int | None, modele: str) -> None:
    """Refuse AVANT l'appel un document qui ne tient manifestement pas dans la fenêtre du modèle.

    Sans ce contrôle, l'admin attend plusieurs minutes pour recevoir « le service a refusé la
    demande » : le fournisseur ne se prononce qu'après avoir tout reçu. Le message nomme le modèle
    ET sa borne, parce que le geste attendu est de CHANGER de modèle — pas de réessayer.
    `contexte_max` None (fenêtre inconnue) = aucun contrôle, comportement d'avant."""
    if not contexte_max:
        return
    # La fenêtre porte sur l'ENTRÉE **ET** la sortie : c'est leur somme que le fournisseur compare
    # à sa borne (« inputs tokens + max_tokens = 46235 but must be < 32000 »). Compter le seul
    # texte laisserait passer des appels qui échouent à coup sûr.
    besoin = _tokens_estimes(prompt) + max_tokens
    if besoin <= int(contexte_max * _MARGE_FENETRE):
        return
    raise LLMModeleIncompatibleError(
        f"Le document est trop volumineux pour le modèle « {modele} » : il faudrait environ "
        f"{besoin:,} tokens (texte + réponse) alors que ce modèle n'en tient que {contexte_max:,}. "
        f"Choisissez un modèle à plus grande fenêtre dans Paramètres → Génération.".replace(",", " ")
    )


def _url_chat(fournisseur: str) -> str:
    """URL de chat/completions du fournisseur OpenAI-compatible demandé.

    L'URL d'Infomaniak porte le NUMÉRO DU PRODUIT du compte (config, pas un secret). Sans lui
    l'adresse serait trouée (« /1/ai//openai/... ») et reviendrait en 404 illisible : on préfère
    le dire à la source, en une phrase qui nomme la variable à renseigner."""
    if fournisseur == "infomaniak":
        if not AITOOLS_PRODUCT_ID:
            raise RuntimeError(
                "Numéro de produit Infomaniak absent : la variable « AITOOLS_PRODUCT_ID » n'est "
                "pas définie dans le .env. Sans elle, l'appel ne sait pas à quelle adresse aller."
            )
        return f"https://api.infomaniak.com/1/ai/{AITOOLS_PRODUCT_ID}/openai/chat/completions"
    return _URL_GROQ


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
    contexte_max: int | None = None,
    outil: str | None = None,
    prefixe_cache: str | None = None,
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

    `outil` : QUI appelle (le même mot que `outils_llm.outil` / `get_max_tokens`). Sert uniquement à
    la mesure — l'écran « IA › Statistiques » range la consommation par outil. Facultatif et sans
    effet sur la requête : un appel qui ne se nomme pas se compte sous « non précisé », il n'est
    jamais perdu. On le passe explicitement de fonction en fonction plutôt que par une variable
    ambiante : le flux est consommé par l'appelant, bien après l'appel, et un contexte implicite
    n'y survivrait pas de façon fiable.

    `prefixe_cache` : le DÉBUT du prompt que le fournisseur peut garder d'un appel à l'autre — en
    pratique, le référentiel. Six outils envoient le même document (~70 000 tokens) pour rendre
    trois lignes ; Anthropic ne facture que 10 % d'un préfixe déjà vu, à condition qu'on lui dise
    où il s'arrête. On passe donc le TEXTE lui-même, et non un nombre de caractères : le moteur
    vérifie que le prompt commence bien par lui, sinon il n'y touche pas (cf. `_contenu_utilisateur`).
    Sans effet sur la réponse, sans effet chez Groq/Infomaniak, qui n'ont pas cette mécanique.
    """
    fournisseur = provider or AI_PROVIDER
    if fournisseur not in ("groq", "anthropic", "infomaniak"):
        raise ValueError(f"Fournisseur inconnu : {fournisseur}")  # validé AVANT de prendre un créneau
    # Fenêtre du modèle : contrôlée AVANT le créneau, comme le fournisseur. Un appel voué au refus
    # ne doit ni occuper une place ni faire attendre le temps d'un envoi complet.
    verifier_fenetre(prompt, max_tokens=max_tokens, contexte_max=contexte_max, modele=model or AI_MODEL)
    with _llm_slot():
        if appel_long:
            # Le créneau LLM est tenu par ce `with` pendant TOUTE la consommation du flux (le
            # générateur est vidé ici, pas rendu à l'appelant) — pas de créneau relâché en cours de
            # génération, contrairement à `generate_stream` où l'appelant en a la charge.
            if fournisseur == "anthropic":
                morceaux = _anthropic_stream(prompt, cle=cle, model=model, max_tokens=max_tokens, json_mode=json_mode, schema=schema, read_timeout=read_timeout, outil=outil, prefixe_cache=prefixe_cache)
            else:  # groq / infomaniak : même dialecte OpenAI, seule l'URL change
                morceaux = _groq_stream(prompt, cle=cle, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode, schema=schema, read_timeout=read_timeout, retry_max=retry_max, retry_wait_max=retry_wait_max, fournisseur=fournisseur, outil=outil)
            return "".join(morceaux)
        if fournisseur == "anthropic":
            return _anthropic(prompt, cle=cle, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode, schema=schema, outil=outil, prefixe_cache=prefixe_cache)
        return _groq(prompt, cle=cle, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode, schema=schema, retry_max=retry_max, retry_wait_max=retry_wait_max, fournisseur=fournisseur, outil=outil)


def generate_cached(
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
    contexte_max: int | None = None,
    outil: str | None = None,
    prefixe_cache: str | None = None,
) -> str:
    """`generate()` qui ne repaie pas deux fois la même question — EN DÉVELOPPEMENT SEULEMENT.

    POURQUOI. Le coût en dev ne vient pas du modèle, il vient de rappeler l'API à chaque essai. Une
    découpe de référentiel envoie ~210 000 tokens ; la relancer trois fois pour régler un détail
    d'affichage, c'est la payer trois fois pour une réponse strictement identique.

    ÉTEINT PAR DÉFAUT. Sans `LLM_CACHE=1`, cette fonction appelle `generate` et rend la main : le
    comportement est celui d'aujourd'hui, à la ligne près. C'est ce qui permet de la laisser branchée
    en production — un cache de développement ne doit JAMAIS servir une réponse à un prof.

    LU AVANT LE CRÉNEAU LLM. Le `_llm_slot()` est pris dans `generate`, pas ici : un appel servi par
    le cache n'occupe donc aucune place et ne fait attendre personne. C'était le seul intérêt à
    envelopper `generate` plutôt qu'à se brancher dedans.

    ÉCRITURE : SUCCÈS PLEIN UNIQUEMENT. Une réponse en cache est figée — relancer ne la fait plus
    disparaître. Deux protections, et elles suffisent :
      - une ERREUR ne revient pas d'ici, elle lève : l'écriture ci-dessous n'est jamais atteinte ;
      - une réponse COUPÉE lève aussi, sur les quatre voies (generator.py, `stop_reason`/
        `finish_reason` == max_tokens/length). C'est vérifié par un test, parce que la dernière de
        ces quatre voies ne levait pas encore quand ce cache a été écrit.
    Reste le cas d'une réponse vide : elle ne s'écrit pas non plus (`if not reponse`).

    STATISTIQUES. Un rejeu POSE SA LIGNE comme un vrai appel — vrai modèle, vrai outil — mais à
    0 token, 0 $, et marqué `depuis_cache`. Sans cette ligne, l'écran afficherait 3 appels quand on
    en a lancé 10 et le cache travaillerait invisible ; avec un faux fournisseur « cache », on
    perdrait le modèle et l'outil, c'est-à-dire ce qu'on veut justement lire.

    La signature RECOPIE celle de `generate` : un paramètre ajouté là-bas et oublié ici fait lever
    un TypeError bruyant au lieu d'être avalé en silence dans une empreinte incomplète. Un test
    compare les deux signatures pour que l'oubli se voie avant l'exécution."""
    if not cache.actif():
        return generate(prompt, cle=cle, provider=provider, model=model, max_tokens=max_tokens,
                        temperature=temperature, json_mode=json_mode, schema=schema,
                        appel_long=appel_long, read_timeout=read_timeout, retry_max=retry_max,
                        retry_wait_max=retry_wait_max, contexte_max=contexte_max, outil=outil,
                        prefixe_cache=prefixe_cache)

    # L'empreinte porte TOUT ce qui change la réponse, et RIEN de volatil (cf. cache.PARAMS_EMPREINTE
    # et le pourquoi de chaque absence). La clé API n'y est pas : c'est un secret.
    empreinte = cache.empreinte({
        "prompt": prompt, "provider": provider, "model": model, "max_tokens": max_tokens,
        "temperature": temperature, "json_mode": json_mode, "schema": schema,
    })

    debut = time.time()
    deja = cache.lire(empreinte)
    if deja is not None:
        log.info("LLM %s · %s · outil=%s · SERVI PAR LE CACHE (0 token)",
                 provider or AI_PROVIDER, model or AI_MODEL, outil or "?")
        try:
            from backend.analytique.usage import enregistrer_usage
            enregistrer_usage(
                fournisseur=provider or AI_PROVIDER, modele=model or AI_MODEL, outil=outil,
                tokens_entree=0, tokens_sortie=0,
                duree_ms=int((time.time() - debut) * 1000),
                motif_arret=None, depuis_cache=True,
            )
        except Exception as e:  # mesurer ne casse jamais servir
            log.error("Usage LLM (cache) non enregistré : %s: %s", type(e).__name__, e)
        return deja

    reponse = generate(prompt, cle=cle, provider=provider, model=model, max_tokens=max_tokens,
                       temperature=temperature, json_mode=json_mode, schema=schema,
                       appel_long=appel_long, read_timeout=read_timeout, retry_max=retry_max,
                       retry_wait_max=retry_wait_max, contexte_max=contexte_max, outil=outil,
                       prefixe_cache=prefixe_cache)
    if reponse:
        # Le fichier garde la DEMANDE à côté de la réponse : un cache qu'on ne peut pas relire est
        # un cache qu'on ne peut pas vérifier. `outil` et la date sont là pour l'œil humain — ils ne
        # sont PAS dans l'empreinte, sinon elle ne se répéterait jamais.
        cache.ecrire(empreinte, reponse, {
            "provider": provider or AI_PROVIDER, "model": model or AI_MODEL,
            "max_tokens": max_tokens, "temperature": temperature,
            "json_mode": json_mode, "schema": schema,
            "outil": outil, "ecrit_le": maintenant_utc().isoformat(),
            "prompt": prompt,
        })
    return reponse


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
    fournisseur: str = "groq",
    outil: str | None = None,
) -> str:
    """Client des fournisseurs à dialecte OpenAI. `fournisseur` ne sert qu'à choisir l'URL et à
    nommer le fournisseur dans le journal : le corps de requête, lui, est le même pour tous
    (défaut « groq » = comportement d'avant, les appelants historiques ne changent pas)."""
    import requests
    if not cle:
        raise _marquer(RuntimeError("Clé API texte manquante (non résolue en base)."),
                       f"{fournisseur} · clé vide reçue par l'adaptateur (voir ai_fournisseurs.cle_env)")
    url = _url_chat(fournisseur)
    debut = time.time()
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
        _traduire_echec_fournisseur(response.status_code, response.text, model or AI_MODEL, fournisseur)
        log.warning("%s %s : %s", fournisseur, response.status_code, response.text[:500])
        raise _avec_technique(
            RuntimeError("Le service d'IA a refusé la demande. Réessayez ; si cela persiste, "
                         "signalez-le : le détail technique est dans les journaux du serveur."),
            fournisseur, model or AI_MODEL, response.status_code, response.text,
        )
    recu = response.json()
    choix = (recu.get("choices") or [{}])[0]
    usage = recu.get("usage") or {}
    # Journal AVANT le contrôle de troncature : un appel coupé a quand même consommé, et c'est le
    # cas où l'on veut le plus savoir combien.
    _journal_appel(fournisseur, model or AI_MODEL, choix.get("finish_reason"),
                   usage.get("prompt_tokens"), usage.get("completion_tokens"), debut, outil)
    # Garde-fou troncature — IL MANQUAIT ICI, et nulle part ailleurs : les trois autres voies
    # (`_anthropic`, `_anthropic_stream`, `_groq_stream`) lèvent déjà sur une sortie coupée. Cette
    # voie-ci rendait le texte amputé comme s'il était complet, et l'appelant le prenait pour tel :
    # au mieux il plantait plus loin sur un faux motif « JSON non parsable », au pire il l'ENREGISTRAIT.
    # Le cache disque rend le trou définitif — une réponse coupée mise en cache y reste, et relancer
    # ne la fait plus disparaître. D'où la symétrie, posée avant de brancher le cache.
    if choix.get("finish_reason") == "length":
        raise _marquer(
            RuntimeError("Réponse coupée : le modèle a atteint sa limite de sortie."),
            f"{fournisseur} · {model or AI_MODEL} · finish_reason=length · max_tokens={max_tokens} "
            f"(relever max_tokens sur la fiche du modèle, ou choisir un modèle qui écrit plus long)",
        )
    return choix["message"]["content"]


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
    debut = time.time()
    with _llm_slot():
        response = requests.post(url, headers=headers, json=body, timeout=60)
    if response.status_code == 429:
        raise LLMRateLimitError("Trop de demandes en ce moment. Réessayez dans un instant.")
    if not response.ok:
        raise RuntimeError(f"Erreur OCR {response.status_code}: {response.text}")
    recu = response.json()
    choix = (recu.get("choices") or [{}])[0]
    usage = recu.get("usage") or {}
    # L'OCR n'emprunte pas `generate()` (corps multimodal, image en base64) : il posait donc ses
    # tokens NULLE PART. Une page scannée coûte pourtant autant qu'une génération, et un PDF de
    # 15 pages en coûte quinze. Le même journal que les autres, avec le même mot d'outil qu'à
    # `get_max_tokens(db, "ocr")` — sinon l'écran des statistiques présente une facture amputée.
    _journal_appel("groq", model, choix.get("finish_reason"),
                   usage.get("prompt_tokens"), usage.get("completion_tokens"), debut, "ocr")
    return choix["message"]["content"]


def _echec_anthropic(e, modele: str) -> None:
    """Traduit une erreur du SDK Anthropic en message d'humain — même règle que pour Groq, mais
    l'échec arrive ici sous forme d'exception plutôt que de réponse HTTP. Ne rend jamais la main :
    ou bien elle lève l'exception métier, ou bien elle relaie l'erreur d'origine."""
    statut = getattr(e, "status_code", 0) or 0
    corps = str(e)  # le SDK met déjà le corps de la réponse dans le texte de l'exception
    log.warning("Anthropic %s : %s", statut, corps[:500])
    _traduire_echec_fournisseur(statut, corps, modele, "anthropic")
    raise e  # statut non répertorié : on ne masque rien, l'erreur d'origine repart telle quelle


def _contenu_utilisateur(prompt: str, prefixe_cache: str | None):
    """Le message de l'utilisateur : une chaîne simple, ou DEUX BLOCS quand le début du prompt peut
    être mis en cache chez le fournisseur.

    POURQUOI DEUX BLOCS. Six outils envoient le MÊME référentiel (~70 000 tokens) pour rendre trois
    lignes. Anthropic sait ne facturer que 10 % d'un préfixe déjà vu, à condition qu'on lui dise
    où ce préfixe s'arrête : c'est le rôle de `cache_control`, posé sur le premier bloc.

    LE CONTRÔLE `startswith` N'EST PAS DÉCORATIF. Le prompt part de la base et l'admin peut le
    modifier : rien ne garantit qu'il commence encore par le document. S'il ne commence pas par
    lui, on n'invente rien — on envoie la chaîne d'un seul tenant, exactement comme avant. Le
    résultat est identique, seule l'économie est perdue, et le journal le dit pour qu'on le voie.

    Ne JAMAIS lever ici : perdre une réduction de facture ne doit pas coûter une génération."""
    if not prefixe_cache:
        return prompt
    if not prompt.startswith(prefixe_cache):
        log.warning("Cache de prompt inactif : le prompt ne commence pas par le document. "
                    "Vérifier que {texte} est bien en tête du prompt en base.")
        return prompt
    suite = prompt[len(prefixe_cache):]
    if not suite.strip():
        return prompt   # un bloc de texte vide est refusé par l'API : rien à découper ici
    # Sous ~1024 tokens, Anthropic ignore simplement `cache_control` (aucune erreur) : pas de
    # garde-fou à écrire, le cas se règle tout seul.
    return [
        {"type": "text", "text": prefixe_cache, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": suite},
    ]


def _anthropic_kwargs(prompt: str, *, model: str | None, max_tokens: int, json_mode: bool,
                      schema: dict | None, temperature: float | None = None,
                      prefixe_cache: str | None = None) -> dict:
    """Corps de requête Anthropic, construit à UN SEUL endroit pour les DEUX voies (non-streaming et
    flux). Toute évolution du contrat de sortie profite aux deux d'un coup : impossible qu'un
    `output_config` existe d'un côté et pas de l'autre.

    temperature : envoyée si elle arrive ici, sinon rien. Ce n'est plus le moteur qui décide de la
    jeter — il ne connaît plus « Anthropic la refuse ». C'est l'appelant qui ne la passe pas quand
    la fiche du modèle dit `supporte_temperature = false`. La règle a quitté le code pour la base.
    json_mode : Claude n'a pas de response_format. Sans schéma JSON (le métier parse en tolérant),
    on force le JSON par instruction système — jamais en recopiant le dict response_format de Groq."""
    kwargs = {
        "model": model or AI_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": _contenu_utilisateur(prompt, prefixe_cache)}],
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
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
    outil: str | None = None,
    prefixe_cache: str | None = None,
) -> str:
    import anthropic
    kwargs = _anthropic_kwargs(prompt, model=model, max_tokens=max_tokens, json_mode=json_mode,
                               schema=schema, temperature=temperature, prefixe_cache=prefixe_cache)
    # timeout=60 s = délai TOTAL de la requête, donc réservé aux APPELS COURTS (une consigne, une
    # réponse). Tout appel qui fait LIRE UN DOCUMENT ENTIER au modèle dure plusieurs minutes et
    # dépasserait cette barre : il doit passer par `generate(appel_long=True)`, qui emprunte le flux
    # et ne connaît qu'un délai de SILENCE réarmable. Ne PAS relever ce 60 s pour faire tenir un
    # appel long en non-streaming : l'API coupe elle-même les requêtes longues non streamées.
    if not cle:
        raise _marquer(RuntimeError("Clé API texte manquante (non résolue en base)."),
                       "anthropic · clé vide reçue par l'adaptateur (voir ai_fournisseurs.cle_env)")
    client = anthropic.Anthropic(api_key=cle, timeout=60)
    debut = time.time()
    try:
        message = client.messages.create(**kwargs)
    except anthropic.APIStatusError as e:
        _echec_anthropic(e, model or AI_MODEL)
    except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
        log.warning("Anthropic : connexion interrompue — %s", e)
        raise _marquer(LLMIndisponibleError(
            "La réponse de l'IA n'est pas arrivée jusqu'au bout (connexion interrompue). "
            "Réessayez dans un instant."
        ), f"anthropic · {model or AI_MODEL} · connexion coupée — {type(e).__name__}: {e}")
    # Troncature : si le modèle atteint sa limite de sortie, la réponse est COUPÉE. On le signale
    # honnêtement — le drapeau vient de l'API (`stop_reason`), rien n'est deviné — au lieu de rendre
    # un texte tronqué que l'appelant prendrait pour complet (et qui planterait plus loin sur un
    # faux motif « non parsable »). Mesuré le 12/07 : Sonnet 5 consomme une partie de max_tokens en
    # raisonnement, donc la sortie visible peut être coupée là où Groq aurait tout rendu.
    _usage = getattr(message, "usage", None)
    _journal_appel("anthropic", model or AI_MODEL, getattr(message, "stop_reason", None),
                   getattr(_usage, "input_tokens", None), getattr(_usage, "output_tokens", None), debut, outil,
                   getattr(_usage, "cache_creation_input_tokens", None),
                   getattr(_usage, "cache_read_input_tokens", None))
    if getattr(message, "stop_reason", None) == "max_tokens":
        raise _marquer(
            RuntimeError("Réponse coupée : le modèle a atteint sa limite de sortie."),
            f"anthropic · {model or AI_MODEL} · stop_reason=max_tokens · max_tokens={max_tokens}",
        )
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
    contexte_max: int | None = None,
    outil: str | None = None,
    prefixe_cache: str | None = None,
):
    """Itérateur de morceaux de texte (deltas), au fil de l'écriture par le modèle. Même résolution
    fournisseur/modèle que generate() (chaînes déjà résolues par l'appelant). NE prend PAS le créneau
    LLM (cf. en-tête). Lève LLMRateLimitError (429 fournisseur) ou RuntimeError (autre échec).

    `retry_max` / `retry_wait_max` : résilience 429 (réglages admin en base, passés par l'appelant).
    Le retry n'agit qu'à l'OUVERTURE du flux, avant le 1er mot. Anthropic re-tente déjà côté SDK."""
    fournisseur = provider or AI_PROVIDER
    if fournisseur not in ("groq", "anthropic", "infomaniak"):
        raise ValueError(f"Fournisseur inconnu : {fournisseur}")
    verifier_fenetre(prompt, max_tokens=max_tokens, contexte_max=contexte_max, modele=model or AI_MODEL)
    if fournisseur == "anthropic":
        yield from _anthropic_stream(prompt, cle=cle, model=model, max_tokens=max_tokens, json_mode=json_mode, schema=schema, read_timeout=read_timeout, outil=outil, prefixe_cache=prefixe_cache)
    else:  # groq / infomaniak : même dialecte OpenAI, seule l'URL change
        yield from _groq_stream(prompt, cle=cle, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode, schema=schema, read_timeout=read_timeout, retry_max=retry_max, retry_wait_max=retry_wait_max, fournisseur=fournisseur, outil=outil)


def _anthropic_stream(prompt, *, cle, model=None, max_tokens=2048, temperature=None, json_mode=False, schema=None, read_timeout=30.0, outil=None, prefixe_cache=None):
    import anthropic
    import httpx
    if not cle:
        raise RuntimeError("Clé API texte manquante (non résolue en base).")
    # temperature : transmise si l'appelant l'a passée, comme dans _anthropic — c'est la fiche du
    # modèle (`supporte_temperature`) qui décide, plus ce fichier.
    # timeout de LECTURE = coupure de silence (se réarme à chaque morceau) ; connect/write/pool =
    # petits garde-fous de connexion, indépendants de la durée de génération. Ce client est PROPRE au
    # flux : il ne reprend rien du client non-streaming, donc le 60 s total ne peut pas mordre ici.
    client = anthropic.Anthropic(
        api_key=cle,
        timeout=httpx.Timeout(read_timeout, connect=10.0, write=10.0, pool=10.0),
    )
    # Même construction que la voie non-streaming (schéma compris) : `_anthropic_kwargs` est le seul
    # endroit qui décide du contrat de sortie. Structured Outputs vaut en flux comme hors flux.
    kwargs = _anthropic_kwargs(prompt, model=model, max_tokens=max_tokens, json_mode=json_mode,
                               schema=schema, prefixe_cache=prefixe_cache)
    debut = time.time()
    try:
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
            # Garde-fou troncature (repris de la voie non-streaming) : si le modèle s'est arrêté sur
            # sa limite de sortie, le texte est COUPÉ. On le SIGNALE en fin de flux (le motif vient de
            # l'API, rien n'est deviné) → l'endpoint émet `error` au lieu de `done`, l'écran refuse un
            # texte amputé au lieu de l'enregistrer comme complet.
            final = stream.get_final_message()
            _usage = getattr(final, "usage", None)
            _journal_appel("anthropic", model or AI_MODEL, getattr(final, "stop_reason", None),
                           getattr(_usage, "input_tokens", None), getattr(_usage, "output_tokens", None), debut, outil,
                           getattr(_usage, "cache_creation_input_tokens", None),
                           getattr(_usage, "cache_read_input_tokens", None))
            if getattr(final, "stop_reason", None) == "max_tokens":
                raise _marquer(
                    RuntimeError("Réponse coupée : le modèle a atteint sa limite de sortie."),
                    f"anthropic (flux) · {model or AI_MODEL} · stop_reason=max_tokens · max_tokens={max_tokens}",
                )
    except anthropic.APIStatusError as e:
        _echec_anthropic(e, model or AI_MODEL)
    except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
        log.warning("Anthropic (flux) : silence trop long ou connexion perdue — %s", e)
        raise _marquer(LLMIndisponibleError(
            "La réponse de l'IA s'est interrompue en cours de route. Réessayez dans un instant."
        ), f"anthropic (flux) · {model or AI_MODEL} · silence > read_timeout — {type(e).__name__}: {e}")


def _groq_stream(prompt, *, cle, model=None, max_tokens=2048, temperature=None, json_mode=False, schema=None, read_timeout=30.0, retry_max=0, retry_wait_max=10, fournisseur="groq", outil=None):
    """Flux des fournisseurs à dialecte OpenAI (Groq, Infomaniak AI Tools). Comme `_groq` :
    `fournisseur` ne choisit QUE l'URL et le nom au journal, jamais le corps de la requête."""
    import json
    import requests
    if not cle:
        raise _marquer(RuntimeError("Clé API texte manquante (non résolue en base)."),
                       f"{fournisseur} · clé vide reçue par l'adaptateur (voir ai_fournisseurs.cle_env)")
    url = _url_chat(fournisseur)
    debut = time.time()
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
            _traduire_echec_fournisseur(response.status_code, response.text, model or AI_MODEL, fournisseur)
            log.warning("%s (flux) %s : %s", fournisseur, response.status_code, response.text[:500])
            raise _avec_technique(
                RuntimeError("Le service d'IA a refusé la demande. Réessayez ; si cela persiste, "
                             "signalez-le : le détail technique est dans les journaux du serveur."),
                fournisseur, model or AI_MODEL, response.status_code, response.text,
            )
        # Ces API n'annoncent pas de charset sur leur flux SSE -> requests retombe sur ISO-8859-1 et
        # decode_unicode=True rendrait les accents UTF-8 en mojibake (« é » -> « Ã© »). On force UTF-8.
        response.encoding = "utf-8"
        finish_reason = None
        usage = {}
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
            if data.get("usage"):
                usage = data["usage"]   # dernier morceau : la consommation réelle de l'appel
            choix = (data.get("choices") or [{}])[0]
            if choix.get("finish_reason"):
                finish_reason = choix["finish_reason"]
            delta = choix.get("delta", {}).get("content")
            if delta:
                yield delta
        # Garde-fou troncature symétrique de la voie Anthropic : « length » = sortie coupée sur la
        # limite de tokens → on lève, l'endpoint émet `error`, l'écran refuse un texte amputé.
        # Journal AVANT le contrôle de troncature : un appel coupé a quand même consommé, et
        # c'est le cas où l'on veut le plus savoir combien.
        _journal_appel(fournisseur, model or AI_MODEL, finish_reason,
                       usage.get("prompt_tokens"), usage.get("completion_tokens"), debut, outil)
        if finish_reason == "length":
            raise _marquer(
                RuntimeError("Réponse coupée : le modèle a atteint sa limite de sortie."),
                f"{fournisseur} · {model or AI_MODEL} · finish_reason=length · max_tokens={max_tokens} "
                f"(relever la longueur dans IA → Génération, ou choisir un modèle qui écrit plus long)",
            )
