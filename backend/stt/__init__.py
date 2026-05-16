"""
Module STT — Speech-to-Text.

État actuel (Phase 1.6) : factory get_stt_provider() opérationnelle avec switch
sur STT_PROVIDER (env). Provider Deepgram Nova-3 actif par défaut. Multi-provider
prêt — ajouter un nouvel adapter = 1 ligne dans le dict _PROVIDERS.

Spec : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md
"""

import logging
import os

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
from backend.stt.deepgram_provider import DeepgramProvider

logger = logging.getLogger(__name__)

# Mapping provider key → classe provider.
# Ajouter ici une nouvelle implémentation (AzureProvider, SpeechmaticsProvider, etc.).
_PROVIDERS: dict[str, type[STTProvider]] = {
    "deepgram": DeepgramProvider,
}


def get_stt_provider() -> STTProvider:
    """Factory STT — retourne le provider configuré dans STT_PROVIDER (env).

    Lit STT_PROVIDER (.env, défaut 'deepgram'), normalise en lowercase, et
    instancie la classe correspondante. Lève STTServiceUnavailableError si la
    valeur pointe vers un provider inconnu — cohérent avec la philosophie
    fail-lazy en place (cf. DeepgramProvider.__init__ : warning + raise au
    premier create_session si DEEPGRAM_API_KEY manque).

    Raises:
        STTServiceUnavailableError: Si STT_PROVIDER pointe vers un provider
            inconnu. La liste des providers valides est dans le message d'erreur.
    """
    name = os.getenv("STT_PROVIDER", "deepgram").lower()
    provider_cls = _PROVIDERS.get(name)
    if provider_cls is None:
        known = ", ".join(sorted(_PROVIDERS.keys()))
        raise STTServiceUnavailableError(
            f"STT_PROVIDER='{name}' inconnu — providers disponibles : {known}"
        )
    logger.info("STT provider activé : %s", name)
    return provider_cls()


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
