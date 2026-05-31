import logging
import requests
from fastapi import HTTPException
from src.config import AI_API_KEY

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

FALLBACK_CHAIN = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
]

FALLBACK_STATUSES = {429, 413, 503}

_headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}

log = logging.getLogger(__name__)


def call_groq(body: dict) -> str:
    primary_model = body.get("model")
    models_to_try = [primary_model] + [m for m in FALLBACK_CHAIN if m != primary_model]

    for i, model in enumerate(models_to_try):
        attempt_body = {**body, "model": model}
        r = requests.post(GROQ_URL, headers=_headers, json=attempt_body, timeout=90)

        if r.ok:
            if i > 0:
                log.warning(f"Groq fallback réussi sur {model} (primaire={primary_model})")
            return r.json()["choices"][0]["message"]["content"]

        if r.status_code in FALLBACK_STATUSES:
            log.warning(f"Groq {r.status_code} sur {model} — passage au suivant")
            continue

        raise HTTPException(status_code=502, detail=f"Erreur Groq {r.status_code}: {r.text[:200]}")

    raise HTTPException(status_code=429, detail="Tous les modèles Groq sont indisponibles — réessayez dans quelques minutes.")


GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
TRANSCRIBE_MODEL = "whisper-large-v3"


def transcribe_audio(data: bytes, filename: str, content_type: str | None = None) -> str:
    """Transcrit un fichier audio via Groq Whisper (batch) et renvoie le texte.

    Fix 400 (cause confirmée par repro le 31/05/2026) : Groq détermine le format
    audio par l'EXTENSION DU NOM DE FICHIER — pas par le content-type ni les octets.
    Un blob sans extension → 400 "file must be one of the following types: [...]".
    On garantit donc les DEUX propriétés requises par l'API Groq :
      1. un `filename` à extension valide (responsabilité de l'appelant) ;
      2. le paramètre `model` (lui aussi Required → 400 sinon).

    Note multipart : on ne réutilise pas `_headers` (qui force Content-Type: json) —
    requests pose lui-même le Content-Type multipart avec la boundary.
    """
    headers = {"Authorization": f"Bearer {AI_API_KEY}"}
    files = {"file": (filename, data, content_type or "application/octet-stream")}
    payload = {"model": TRANSCRIBE_MODEL, "language": "fr"}
    r = requests.post(GROQ_TRANSCRIBE_URL, headers=headers, files=files, data=payload, timeout=90)
    if not r.ok:
        raise HTTPException(status_code=502, detail=f"Erreur transcription Groq {r.status_code}: {r.text[:200]}")
    return (r.json().get("text") or "").strip()
