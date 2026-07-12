import requests
from fastapi import HTTPException
from src.generator import _llm_slot, LLMRateLimitError

GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
TRANSCRIBE_MODEL = "whisper-large-v3"


def transcribe_audio(data: bytes, filename: str, content_type: str | None = None, *, api_key: str) -> str:
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
    # api_key : clé dictée résolue par le backend (nom de variable lu EN BASE, cle_env_dictee).
    if not api_key:
        raise HTTPException(status_code=500, detail="Clé dictée absente : la transcription ne peut pas s'exécuter.")
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": (filename, data, content_type or "application/octet-stream")}
    payload = {"model": TRANSCRIBE_MODEL, "language": "fr"}
    # Même créneau partagé que la génération/OCR (même quota Groq) ; saturation -> 429 « réessayez ».
    try:
        with _llm_slot():
            r = requests.post(GROQ_TRANSCRIBE_URL, headers=headers, files=files, data=payload, timeout=90)
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    if r.status_code == 429:
        raise HTTPException(status_code=429, detail="Trop de demandes en ce moment. Réessayez dans un instant.")
    if not r.ok:
        raise HTTPException(status_code=502, detail=f"Erreur transcription Groq {r.status_code}: {r.text[:200]}")
    return (r.json().get("text") or "").strip()
