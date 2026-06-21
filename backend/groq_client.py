import requests
from fastapi import HTTPException
from src.config import AI_API_KEY

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

    Note multipart : on ne force aucun Content-Type ici — requests pose lui-même
    le Content-Type multipart avec la boundary.
    """
    headers = {"Authorization": f"Bearer {AI_API_KEY}"}
    files = {"file": (filename, data, content_type or "application/octet-stream")}
    payload = {"model": TRANSCRIBE_MODEL, "language": "fr"}
    r = requests.post(GROQ_TRANSCRIBE_URL, headers=headers, files=files, data=payload, timeout=90)
    if not r.ok:
        raise HTTPException(status_code=502, detail=f"Erreur transcription Groq {r.status_code}: {r.text[:200]}")
    return (r.json().get("text") or "").strip()
