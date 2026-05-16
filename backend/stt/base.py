"""
Interfaces et types de base pour le module STT (Speech-to-Text).

Définit le contrat que toute implémentation de provider STT doit respecter
(actuellement Deepgram Nova-3, futurs : Azure France, Speechmatics, OVHcloud,
Whisper local).

Spec : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md §4
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field


# ============================================================
# Dataclasses — DTO internes
# ============================================================

@dataclass
class Transcript:
    """Un fragment de transcription reçu pendant le streaming."""
    text: str
    is_final: bool          # True = définitif, False = interim (peut changer)
    confidence: float       # 0.0 à 1.0
    start_seconds: float    # offset depuis début de la session
    end_seconds: float


@dataclass
class STTSessionConfig:
    """Configuration d'une session de transcription.

    Valeurs par défaut alignées sur spec §3.2 (Phase 1).
    """
    language: str = "fr"
    sample_rate: int = 16000
    encoding: str = "opus"
    interim_results: bool = True
    smart_format: bool = True
    endpointing_ms: int = 800
    dictation: bool = False
    punctuate: bool = True
    keyterms: list[str] = field(default_factory=list)


# ============================================================
# Interfaces ABC — contrats à implémenter par les providers
# ============================================================

class STTSession(ABC):
    """Une session de transcription streaming active.

    Une session représente un échange bidirectionnel avec le provider :
    le client pousse de l'audio en continu, le provider renvoie des
    transcripts au fil de l'eau.
    """

    @abstractmethod
    async def send_audio(self, chunk: bytes) -> None:
        """Envoie un chunk audio au provider."""
        ...

    @abstractmethod
    async def receive_transcripts(self) -> AsyncIterator[Transcript]:
        """Itère sur les transcripts reçus du provider.

        Yields des Transcript au fur et à mesure de leur réception.
        L'itération se termine quand la session est fermée.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Ferme proprement la session (envoie EOF, attend les derniers transcripts)."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifiant du provider, ex: 'deepgram-nova-3'."""
        ...


class STTProvider(ABC):
    """Factory de sessions STT.

    Une implémentation concrète (DeepgramProvider, etc.) crée des STTSession
    selon la config fournie.
    """

    @abstractmethod
    async def create_session(
        self,
        config: STTSessionConfig | None = None,
    ) -> STTSession:
        """Ouvre une nouvelle session de streaming.

        Args:
            config: Configuration de la session. Si None, utilise les valeurs
                par défaut de STTSessionConfig.

        Raises:
            STTServiceUnavailableError: Si le provider est indisponible
                (panne, crédit épuisé, auth invalide).
        """
        ...


# ============================================================
# Exceptions métier
# ============================================================

class STTError(Exception):
    """Classe de base pour toutes les exceptions STT."""


class STTRateLimitError(STTError):
    """Quota STT simultané atteint (max sessions concurrentes).

    Levée par STTSessionTracker.acquire() quand le compteur atteint
    STT_MAX_CONCURRENT_SESSIONS.
    """


class STTServiceUnavailableError(STTError):
    """Service STT indisponible (panne provider, auth, etc.)."""


class STTCreditExhaustedError(STTServiceUnavailableError):
    """Crédit Deepgram épuisé spécifiquement.

    Sous-classe de STTServiceUnavailableError : un appelant générique
    peut catcher la parente, un appelant qui veut différencier les cas
    catch celle-ci spécifiquement.
    """


class STTSessionTimeoutError(STTError):
    """Session timeout (idle ou durée max atteinte).

    Levée par la route WebSocket quand :
    - aucun audio reçu pendant STT_SESSION_IDLE_TIMEOUT_SECONDS
    - durée totale dépasse STT_SESSION_MAX_DURATION_SECONDS
    """
