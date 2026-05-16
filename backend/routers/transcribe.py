"""
Endpoints de transcription audio.

Phase 1.3 : route POST /api/transcribe (Groq batch) supprimée — provider
défaillant en production (erreur 400 sur les formats MediaRecorder).

Phase 2.1 (à venir) : route WS /api/transcribe/stream pour Deepgram Nova-3
streaming temps réel.

Spec : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md §5
"""

from fastapi import APIRouter

router = APIRouter()
