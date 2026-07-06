"""
Endpoint de transcription audio — dictée vocale (Groq Whisper batch).

`POST /api/transcribe` : reçoit un fichier audio (UploadFile), le transcrit via
Groq Whisper et renvoie `{"text": "..."}`.

Historique : la dictée a d'abord été ce POST batch (Groq Whisper), puis migrée
vers un streaming WebSocket Deepgram (Phases 1→3.1), puis ramenée au batch Groq
le 31/05/2026 (décision : besoin de base fiable, aligné « Groq par défaut » ;
le streaming temps réel Deepgram = amélioration future, isolée sur la branche
`wip/deepgram-streaming`).

Fix 400 (cause confirmée par repro le 31/05/2026, cf. backend/groq_client.transcribe_audio) :
Groq détermine le format audio par l'EXTENSION du nom de fichier. On force donc un
nom à extension valide AVANT de transmettre à Groq, et le paramètre `model` (requis).
"""

from fastapi import APIRouter, HTTPException, UploadFile

from backend.core.groq_client import transcribe_audio

router = APIRouter()

# Extensions acceptées par l'endpoint Groq Whisper (doc officielle Speech-to-Text).
_ALLOWED_EXT = {"flac", "mp3", "mp4", "mpeg", "mpga", "m4a", "ogg", "opus", "wav", "webm"}
_MAX_BYTES = 25 * 1024 * 1024  # 25 Mo — limite free tier Groq


def _safe_ext(filename: str | None, content_type: str | None) -> str:
    """Renvoie une extension acceptée par Groq, dérivée du nom de fichier puis,
    en repli, du content-type. Défaut : webm (MediaRecorder navigateur)."""
    name = filename or ""
    if "." in name:
        ext = name.rsplit(".", 1)[-1].lower()
        if ext in _ALLOWED_EXT:
            return ext
    ct = (content_type or "").lower()
    if "ogg" in ct:
        return "ogg"
    if "mp4" in ct or "m4a" in ct:
        return "mp4"
    if "wav" in ct:
        return "wav"
    return "webm"


@router.post("/transcribe")
async def transcribe(file: UploadFile):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Fichier audio vide.")
    if len(data) > _MAX_BYTES:
        raise HTTPException(413, "Fichier audio trop volumineux (max 25 Mo).")

    ext = _safe_ext(file.filename, file.content_type)
    # Fix 400 : nom de fichier À EXTENSION VALIDE transmis à Groq.
    texte = transcribe_audio(data, filename=f"audio.{ext}", content_type=file.content_type)
    return {"text": texte}
