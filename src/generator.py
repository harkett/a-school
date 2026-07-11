import threading
from contextlib import contextmanager

from src.config import AI_PROVIDER, GROQ_API_KEY, CLAUDE_API_KEY, AI_MODEL, AI_MAX_CONCURRENCY, AI_SLOT_TIMEOUT


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
) -> str:
    """Point d'entrée UNIQUE pour tout appel LLM texte.

    Les paramètres sont des INTENTIONS métier neutres (« combien de tokens »,
    « du JSON », « déterministe »), jamais des formats fournisseur. Chaque
    adaptateur les traduit dans la langue de son fournisseur — ou les ignore
    quand le fournisseur ne les accepte pas (ex. temperature chez Anthropic).

    `provider` / `model` : résolvés par l'appelant (côté backend, lus en base à chaud).
    `None` ⇒ repli sur AI_PROVIDER / AI_MODEL (config/.env) — rétro-compatible. generate()
    reste pur : il ne lit aucune base, il reçoit les chaînes déjà résolues.
    """
    fournisseur = provider or AI_PROVIDER
    if fournisseur not in ("groq", "anthropic"):
        raise ValueError(f"Fournisseur inconnu : {fournisseur}")  # validé AVANT de prendre un créneau
    with _llm_slot():
        if fournisseur == "groq":
            return _groq(prompt, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode)
        else:  # anthropic
            return _anthropic(prompt, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode)


def _groq(
    prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    json_mode: bool = False,
) -> str:
    import requests
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
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    response = requests.post(url, headers=headers, json=body, timeout=60)
    if response.status_code == 429:
        raise LLMRateLimitError("Trop de demandes en ce moment. Réessayez dans un instant.")
    if not response.ok:
        raise RuntimeError(f"Erreur {response.status_code}: {response.text}")
    return response.json()["choices"][0]["message"]["content"]


# Note : la dictée (Whisper) passe par backend/groq_client.transcribe_audio, pas ici.
# (L'ancien transcribe_audio de ce module était du code mort — supprimé.)


def transcribe_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    import base64
    import requests
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    body = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
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
        "max_tokens": 2048,
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
    if json_mode:
        kwargs["system"] = "Réponds uniquement avec du JSON valide, sans aucun texte avant ni après."
    # timeout=60 s (secondes côté SDK Python) — voie propre du SDK, aligné sur les
    # autres branches LLM (requests timeout=60). Sans ça, le SDK attendrait 10 min.
    if not CLAUDE_API_KEY:
        raise RuntimeError("CLAUDE_API_KEY manquant dans le .env — requis pour le fournisseur Anthropic (texte).")
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY, timeout=60)
    try:
        message = client.messages.create(**kwargs)
    except anthropic.RateLimitError:
        raise LLMRateLimitError("Trop de demandes en ce moment. Réessayez dans un instant.")
    return message.content[0].text
