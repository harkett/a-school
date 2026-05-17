"""
Wrapper Deepgram Nova-3 streaming pour le module STT.

Implémente STTProvider/STTSession (cf. backend/stt/base.py) au-dessus du SDK
deepgram-sdk 3.11.0. Pattern : callbacks Deepgram → asyncio.Queue → async iterator.

Spec : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md §4-5
SDK pin : deepgram-sdk==3.11.0
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import AsyncIterator

from deepgram import (
    DeepgramClient,
    LiveOptions,
    LiveTranscriptionEvents,
)
from sqlalchemy.orm import Session as SQLASession

from backend.database import SessionLocal
from backend.models_db import STTKeytermGlobal
from backend.stt.base import (
    STTCreditExhaustedError,
    STTError,
    STTProvider,
    STTRateLimitError,
    STTServiceUnavailableError,
    STTSession,
    STTSessionConfig,
    Transcript,
)

logger = logging.getLogger(__name__)

# Sentinel posté dans la queue pour signaler la fin du flux (close / erreur)
_QUEUE_SENTINEL: Transcript | None = None


class DeepgramSession(STTSession):
    """Session de transcription streaming Deepgram active.

    Encapsule la WebSocket Deepgram + une queue async qui sert de pont
    entre les callbacks du SDK et l'itération async côté appelant.
    """

    def __init__(self, connection, model: str) -> None:
        self._connection = connection
        self._model = model
        self._queue: asyncio.Queue[Transcript | None] = asyncio.Queue()
        self._closed = False
        # Phase 3.2 instrumentation — anchors pour mesure latence (cf. PROTOCOLE_PHASE32.md)
        self._last_audio_ts: float | None = None
        self._last_interim_change_ts: float | None = None
        self._last_interim_text: str = ""

    @property
    def provider_name(self) -> str:
        return f"deepgram-{self._model}"

    # --- Callbacks Deepgram → push dans la queue ---

    async def _on_transcript(self, _self_unused, result, **kwargs) -> None:
        """Callback déclenché à chaque transcript reçu de Deepgram."""
        try:
            alt = result.channel.alternatives[0]
            sentence = alt.transcript
            is_final = bool(result.is_final)
            speech_final = bool(getattr(result, "speech_final", False))
            now = time.monotonic()

            # Phase 3.2 — anchor "dernier interim non-final" (exclut is_final/speech_final
            # pour ne pas polluer la mesure : smart_format modifie le texte au final,
            # un anchor sur exact-match sauterait à now et donnerait delta=0).
            if sentence and not is_final and not speech_final:
                self._last_interim_change_ts = now
                self._last_interim_text = sentence

            # Phase 3.2 — log des DEUX anchors + dernier interim observé (instrument diag)
            if sentence and (is_final or speech_final):
                delta_audio = int((now - self._last_audio_ts) * 1000) if self._last_audio_ts else None
                delta_interim = int((now - self._last_interim_change_ts) * 1000) if self._last_interim_change_ts else None
                logger.info(
                    "STT_MEASURE event=%s delta_audio_ms=%s delta_interim_ms=%s text=%r last_interim=%r",
                    "speech_final" if speech_final else "is_final",
                    delta_audio if delta_audio is not None else "n/a",
                    delta_interim if delta_interim is not None else "n/a",
                    sentence,
                    self._last_interim_text,
                )

            if not sentence:
                return  # Deepgram envoie parfois des transcripts vides

            transcript = Transcript(
                text=sentence,
                is_final=is_final,
                confidence=float(alt.confidence),
                start_seconds=float(result.start),
                end_seconds=float(result.start + result.duration),
            )
            await self._queue.put(transcript)
        except Exception as e:
            logger.exception("Erreur dans _on_transcript : %s", e)
            await self._queue.put(_QUEUE_SENTINEL)

    async def _on_error(self, _self_unused, error, **kwargs) -> None:
        """Callback erreur Deepgram → log + sentinel pour stopper l'itération."""
        logger.error("Deepgram session error : %s", error)
        await self._queue.put(_QUEUE_SENTINEL)

    async def _on_close(self, _self_unused, **kwargs) -> None:
        """Callback fermeture → sentinel."""
        logger.info("Deepgram session closed")
        await self._queue.put(_QUEUE_SENTINEL)

    # --- API STTSession ---

    async def send_audio(self, chunk: bytes) -> None:
        if self._closed:
            raise STTServiceUnavailableError("Session déjà fermée")
        self._last_audio_ts = time.monotonic()
        try:
            await self._connection.send(chunk)
        except Exception as e:
            logger.error("Erreur envoi audio Deepgram : %s", e)
            raise STTServiceUnavailableError(f"Envoi audio échoué : {e}") from e

    async def receive_transcripts(self) -> AsyncIterator[Transcript]:
        """Itère sur les transcripts reçus jusqu'à fermeture de la session."""
        while True:
            item = await self._queue.get()
            if item is _QUEUE_SENTINEL:
                return
            yield item

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self._connection.finish()
        except Exception as e:
            logger.warning("Erreur fermeture session Deepgram : %s", e)


class DeepgramProvider(STTProvider):
    """Provider Deepgram Nova-3 streaming.

    Fail-lazy : si DEEPGRAM_API_KEY absente, le constructeur log un warning
    mais ne lève pas. La première tentative de create_session() lèvera
    STTServiceUnavailableError.
    """

    def __init__(self) -> None:
        self._api_key: str | None = os.getenv("DEEPGRAM_API_KEY")
        self._model: str = os.getenv("DEEPGRAM_MODEL", "nova-3")

        if not self._api_key:
            logger.warning(
                "DEEPGRAM_API_KEY non configuré — STT indisponible jusqu'à activation"
            )
            self._client: DeepgramClient | None = None
        else:
            self._client = DeepgramClient(self._api_key)

    @property
    def provider_name(self) -> str:
        return f"deepgram-{self._model}"

    async def create_session(
        self,
        config: STTSessionConfig | None = None,
    ) -> STTSession:
        if self._client is None:
            raise STTServiceUnavailableError(
                "DEEPGRAM_API_KEY non configuré"
            )

        cfg = config or STTSessionConfig()

        # Keyterms : variable locale, pas de mutation de cfg
        keyterms: list[str] = cfg.keyterms or self._load_global_keyterms()

        # Construit LiveOptions Deepgram
        # Phase 3.1 (smoke test 17/05/2026) : pour flux WebM/Opus depuis MediaRecorder
        # navigateur, NE PAS spécifier encoding/sample_rate — Deepgram détecte le
        # container WebM via les magic bytes EBML et extrait l'Opus seul.
        # Pour PCM linear16 brut (test_phase22) : encoding + sample_rate explicites obligatoires.
        options_kwargs = dict(
            model=self._model,
            language=cfg.language,
            channels=1,
            interim_results=cfg.interim_results,
            smart_format=cfg.smart_format,
            endpointing=cfg.endpointing_ms,
            punctuate=cfg.punctuate,
        )
        if cfg.encoding == "linear16":
            options_kwargs["encoding"] = "linear16"
            options_kwargs["sample_rate"] = cfg.sample_rate
        # cfg.encoding == "opus" → on omet (Deepgram parse le container WebM)
        # Plan B dictation : on tente, si TypeError on retire et on continue
        try:
            options = LiveOptions(**options_kwargs, dictation=cfg.dictation)
        except TypeError as e:
            logger.warning(
                "LiveOptions ne supporte pas 'dictation' en SDK 3.11.0 (%s) — "
                "paramètre ignoré, dictée naturelle utilisée",
                e,
            )
            options = LiveOptions(**options_kwargs)

        # keyterms : injection conditionnelle (l'attribut peut ne pas exister
        # dans toutes les sous-versions 3.x)
        if keyterms:
            try:
                options.keyterm = keyterms
            except Exception as e:
                logger.warning(
                    "Impossible d'injecter keyterms dans LiveOptions : %s — "
                    "boost vocabulaire désactivé pour cette session",
                    e,
                )

        # Création de la connexion WebSocket Deepgram
        connection = self._client.listen.asyncwebsocket.v("1")
        session = DeepgramSession(connection, model=self._model)

        # Bind callbacks AVANT start
        connection.on(LiveTranscriptionEvents.Transcript, session._on_transcript)
        connection.on(LiveTranscriptionEvents.Error, session._on_error)
        connection.on(LiveTranscriptionEvents.Close, session._on_close)

        # Démarrage de la connexion
        try:
            started = await connection.start(options)
            if started is False:
                raise STTServiceUnavailableError(
                    "Deepgram a refusé d'ouvrir la session (start returned False)"
                )
        except STTError:
            raise
        except Exception as e:
            raise self._map_deepgram_error(e) from e

        logger.info(
            "Session Deepgram ouverte (model=%s, language=%s, keyterms=%d)",
            self._model,
            cfg.language,
            len(keyterms),
        )
        return session

    # --- Helpers internes ---

    def _load_global_keyterms(self) -> list[str]:
        """Charge les keyterms transversaux depuis BDD à chaque session.

        Phase 1 : liste unique transversale (~80 termes).
        Phase 2+ : injection adaptative par matière.
        """
        db: SQLASession = SessionLocal()
        try:
            rows = db.query(STTKeytermGlobal.term).all()
            return [row.term for row in rows]
        except Exception as e:
            logger.warning(
                "Lecture keyterms BDD échouée : %s — session sans boost vocabulaire",
                e,
            )
            return []
        finally:
            db.close()

    def _map_deepgram_error(self, error: Exception) -> STTError:
        """Mappe les erreurs Deepgram brutes vers nos exceptions métier."""
        msg = str(error).lower()
        if "401" in msg or "unauthorized" in msg or "invalid api key" in msg:
            return STTServiceUnavailableError(f"Deepgram auth échouée : {error}")
        if "402" in msg or "payment" in msg or "insufficient" in msg or "credit" in msg:
            return STTCreditExhaustedError(f"Crédit Deepgram épuisé : {error}")
        if "429" in msg or "rate limit" in msg:
            return STTRateLimitError(f"Deepgram rate limit : {error}")
        return STTServiceUnavailableError(f"Erreur Deepgram : {error}")
