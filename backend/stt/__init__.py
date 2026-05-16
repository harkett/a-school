"""
Module STT — Speech-to-Text.

État actuel (Phase 1.3) : interfaces définies dans base.py, mais aucune
implémentation concrète disponible. La factory sera réimplémentée en
Phase 1.6 avec DeepgramProvider.

Spec : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md
"""

from backend.stt.base import (
    STTCreditExhaustedError,
    STTError,
    STTProvider,
    STTRateLimitError,
    STTServiceUnavailableError,
    STTSession,
    STTSessionConfig,
    STTSessionTimeoutError,
    Transcript,
)


# Factory réimplémentée en Phase 1.6 — ne pas appeler avant.
# Volontairement "fail loud" pour éviter un appel silencieux qui passerait inaperçu.
def get_stt_provider() -> STTProvider:
    raise NotImplementedError(
        "STT provider non disponible en Phase 1.3. "
        "Sera réimplémenté en Phase 1.6 (DeepgramProvider)."
    )


__all__ = [
    "STTCreditExhaustedError",
    "STTError",
    "STTProvider",
    "STTRateLimitError",
    "STTServiceUnavailableError",
    "STTSession",
    "STTSessionConfig",
    "STTSessionTimeoutError",
    "Transcript",
    "get_stt_provider",
]
