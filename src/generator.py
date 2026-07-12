import threading
from contextlib import contextmanager

from src.config import AI_PROVIDER, GROQ_API_KEY, CLAUDE_API_KEY_TEXTE, AI_MODEL, AI_MAX_CONCURRENCY, AI_SLOT_TIMEOUT


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


@contextmanager
def _llm_slot():
    """Réserve un créneau d'appel LLM. Attend au plus AI_SLOT_TIMEOUT secondes ; si aucun
    créneau ne se libère, lève une erreur honnête plutôt que de laisser la requête pendre."""
    if not _llm_semaphore.acquire(timeout=AI_SLOT_TIMEOUT):
        raise LLMRateLimitError("Trop de générations simultanées en ce moment. Réessayez dans un instant.")
    try:
        yield
    finally:
        _llm_semaphore.release()


def generate(
    prompt: str,
    *,
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    json_mode: bool = False,
    schema: dict | None = None,
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
    """
    fournisseur = provider or AI_PROVIDER
    if fournisseur not in ("groq", "anthropic"):
        raise ValueError(f"Fournisseur inconnu : {fournisseur}")  # validé AVANT de prendre un créneau
    with _llm_slot():
        if fournisseur == "groq":
            return _groq(prompt, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode, schema=schema)
        else:  # anthropic
            return _anthropic(prompt, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode, schema=schema)


def _groq(
    prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    json_mode: bool = False,
    schema: dict | None = None,
) -> str:
    import requests
    if not GROQ_API_KEY:
        raise RuntimeError(
            "Texte Groq non configuré (aucune clé Groq-texte dans le .env). "
            "Le texte passe par Anthropic — réglez le fournisseur sur « anthropic »."
        )
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
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
    response = requests.post(url, headers=headers, json=body, timeout=60)
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
    if not CLAUDE_API_KEY_TEXTE:
        raise RuntimeError("CLAUDE_API_KEY_TEXTE manquant dans le .env — requis pour le fournisseur Anthropic (texte).")
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY_TEXTE, timeout=60)
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
