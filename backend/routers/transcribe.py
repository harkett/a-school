"""
Endpoints de transcription audio — Phase 2.1.

Route WebSocket /api/transcribe/stream : pont bidirectionnel entre le client
(audio Opus en MediaRecorder côté navigateur) et le provider STT
(Deepgram Nova-3 streaming en Phase 1).

Architecture :
- Auth JWT cookie httpOnly AVANT accept() (déni propre si non authentifié)
- Acquisition atomique d'un slot via STTSessionTracker (limite concurrence)
- Trois tasks concurrentes : audio_pump, transcript_pump, watchdog
- Cleanup centralisé : cancel des tasks pendantes + session.close() dans finally

Spec : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md §5
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend import auth as auth_lib
from backend.stt import (
    STTCreditExhaustedError,
    STTRateLimitError,
    STTServiceUnavailableError,
    STTSessionTimeoutError,
    get_stt_provider,
)
from backend.stt.session_tracker import tracker

logger = logging.getLogger(__name__)

router = APIRouter()


def _authenticate_ws(websocket: WebSocket) -> str | None:
    """Lit le cookie aschool_access et retourne l'email du prof, ou None.

    Pattern cas C (cf. backend/routers/auth.py:212) : on lit directement le
    cookie au lieu d'instancier un Depends() qui ne fonctionne pas pareil sur
    une route WebSocket. Pas de DB touchée — l'email suffit pour Phase 1.
    """
    token = websocket.cookies.get("aschool_access")
    if not token:
        return None
    try:
        return auth_lib.verify_access_token(token)
    except Exception as e:
        # jose.jwt raise normalement JWTError (catch interne → None) mais on se
        # protège contre les exceptions exotiques (cookie tordu, etc.) pour
        # éviter de logger une "unexpected STT error" pour ce qui n'est qu'une
        # auth qui échoue.
        logger.warning("WS auth token verification raised: %s", e)
        return None


@router.websocket("/transcribe/stream")
async def stt_stream(websocket: WebSocket) -> None:
    """Route WebSocket de transcription streaming.

    Sémantique des codes de fermeture (cf. spec §5.4) :

    Codes envoyés AVANT accept() — 4401 (auth) et 4429 (saturation) :
    Starlette ne peut pas transiter un code WebSocket sur un handshake non
    accepté — le client reçoit une réponse HTTP 403 au handshake et n'a pas
    de close frame. Le code 4401/4429 ici est déclaratif côté backend pour
    la lisibilité du code source. Le frontend (Phase 3.1) doit traiter
    "connection failed" comme "auth manquante / saturation" via fallback.

    Codes envoyés APRÈS accept() — 4402, 4502, 4408, 1011 : ils transitent
    correctement comme close frames WebSocket et sont lisibles côté client.
    """
    user = _authenticate_ws(websocket)
    if not user:
        await websocket.close(code=4401)
        return

    try:
        async with tracker.acquire():
            await websocket.accept()
            logger.info("STT WS opened — user=%s", user)
            await _run_stt_session(websocket, user)
            # Log AVANT close — si close() raise (WS déjà fermé côté Starlette),
            # on garde la trace d'audit. Close wrappé pour la même raison.
            logger.info("STT WS closed normally — user=%s", user)
            try:
                await websocket.close(code=1000)
            except Exception as e:
                logger.warning("WS close(1000) raised — user=%s, err=%s", user, e)

    except STTRateLimitError:
        logger.warning("STT saturated — user=%s", user)
        await websocket.close(code=4429, reason="HIGH_LOAD")

    except STTCreditExhaustedError as e:
        logger.error("STT credit exhausted — user=%s: %s", user, e)
        await websocket.close(code=4402, reason="CREDIT_EXHAUSTED")

    except STTServiceUnavailableError as e:
        logger.error("STT service unavailable — user=%s: %s", user, e)
        await websocket.close(code=4502, reason="SERVICE_DOWN")

    except STTSessionTimeoutError as e:
        logger.info("STT timeout — user=%s: %s", user, e)
        await websocket.close(code=4408, reason="SESSION_TIMEOUT")

    except WebSocketDisconnect:
        # Client a fermé proprement de son côté — pas de close à renvoyer
        logger.info("STT WS disconnected by client — user=%s", user)

    except Exception:
        logger.exception("STT WS unexpected error — user=%s", user)
        try:
            await websocket.close(code=1011)
        except Exception as e:
            logger.warning("WS close(1011) raised — user=%s, err=%s", user, e)


async def _run_stt_session(websocket: WebSocket, user: str) -> None:
    """Boucle de session : 3 tasks concurrentes + cleanup centralisé.

    Pattern create_task + cancel-in-finally (au lieu d'un gather pur) : c'est
    le point technique CRITIQUE de cette route. Comportement asyncio :
    quand une task de gather() raise, gather propage l'exception MAIS ne
    cancelle PAS ses sœurs. Sans cancel explicite ci-dessous, transcript_pump
    et/ou watchdog survivent à la mort d'audio_pump et gardent la session
    Deepgram en zombie (slot tracker libéré mais ressources provider non).

    Ordre du cleanup : cancel tasks → drain (return_exceptions=True) →
    session.close(). session.close() après le drain pour que transcript_pump
    ne lise plus la queue Deepgram pendant la fermeture.
    """
    idle_timeout = int(os.getenv("STT_SESSION_IDLE_TIMEOUT_SECONDS", "30"))
    max_duration = int(os.getenv("STT_SESSION_MAX_DURATION_SECONDS", "300"))

    provider = get_stt_provider()
    session = await provider.create_session()
    started_at = time.monotonic()
    logger.info(
        "STT provider session created — user=%s, provider=%s",
        user, session.provider_name,
    )

    async def audio_pump() -> None:
        """Reçoit l'audio binaire du client et le forwarde au provider.

        Timeout idle géré ici via asyncio.wait_for. WebSocketDisconnect
        remonte naturellement quand le client ferme proprement.
        """
        while True:
            try:
                chunk = await asyncio.wait_for(
                    websocket.receive_bytes(),
                    timeout=idle_timeout,
                )
            except asyncio.TimeoutError:
                raise STTSessionTimeoutError(
                    f"idle timeout reached ({idle_timeout}s)"
                )
            await session.send_audio(chunk)

    async def transcript_pump() -> None:
        """Reçoit les Transcript du provider et les pousse en JSON au client."""
        async for t in session.receive_transcripts():
            await websocket.send_json({
                "type": "transcript",
                "text": t.text,
                "is_final": t.is_final,
                "confidence": t.confidence,
                "start": t.start_seconds,
                "end": t.end_seconds,
            })

    async def watchdog() -> None:
        """Limite la durée totale de session, avec warning à T-60s.

        Si max_duration > 60 : sleep(max-60) → envoie session_warning →
        sleep(60) → raise timeout. Sinon (tests avec max court) : sleep direct
        puis raise, pas de warning (60s de marge n'a pas de sens sur 10s).
        """
        if max_duration > 60:
            await asyncio.sleep(max_duration - 60)
            try:
                await websocket.send_json({
                    "type": "session_warning",
                    "code": "EXPIRING_SOON",
                    "remaining_seconds": 60,
                })
            except Exception as e:
                # Client peut être déconnecté ; on log mais on continue
                logger.warning(
                    "STT session_warning send failed — user=%s: %s", user, e
                )
            await asyncio.sleep(60)
        else:
            await asyncio.sleep(max_duration)
        raise STTSessionTimeoutError(
            f"max session duration reached ({max_duration}s)"
        )

    tasks = [
        asyncio.create_task(audio_pump(), name="stt_audio_pump"),
        asyncio.create_task(transcript_pump(), name="stt_transcript_pump"),
        asyncio.create_task(watchdog(), name="stt_watchdog"),
    ]

    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        # Log AVANT close — trace d'audit garantie même si session.close() raise
        # (Deepgram unreachable au moment du teardown, etc.)
        duration_s = time.monotonic() - started_at
        logger.info(
            "STT provider session terminated — user=%s, duration_s=%.1f",
            user, duration_s,
        )
        try:
            await session.close()
        except Exception as e:
            logger.warning("session.close() raised — user=%s, err=%s", user, e)
