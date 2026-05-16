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
from dataclasses import replace
from typing import Literal

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend import auth as auth_lib
from backend.stt import (
    STTCreditExhaustedError,
    STTRateLimitError,
    STTServiceUnavailableError,
    STTSessionConfig,
    STTSessionTimeoutError,
    get_stt_provider,
)
from backend.stt.session_tracker import tracker

logger = logging.getLogger(__name__)

router = APIRouter()

AuthStatus = Literal["ok", "anonymous", "bad_token"]

# Phase 2.2 (D3) : whitelist des encodings audio acceptés en query string
# `?encoding=`. Hors-whitelist → close 1003 (Unsupported Data, RFC 6455).
# Note : close pré-accept transcodé HTTP 403 par Starlette (comme 4401/4429
# Phase 2.1). Le code est déclaratif côté backend pour logs/audit lisibles.
_ALLOWED_ENCODINGS: tuple[str, ...] = ("opus", "linear16")


def _authenticate_ws(websocket: WebSocket) -> tuple[str | None, AuthStatus]:
    """Lit le cookie aschool_access et retourne (email, status).

    Pattern cas C (cf. backend/routers/auth.py:212) : on lit directement le
    cookie au lieu d'instancier un Depends() qui ne fonctionne pas pareil sur
    une route WebSocket. Pas de DB touchée — l'email suffit pour Phase 1.

    Status (Phase 2.2 — observabilité R4) :
    - "ok"        : email valide retourné, auth OK
    - "anonymous" : pas de cookie aschool_access (utilisateur non authentifié)
    - "bad_token" : cookie présent mais JWT invalide/expiré/tordu

    Invariant : status == "ok" ⟺ email is not None.
    """
    token = websocket.cookies.get("aschool_access")
    if not token:
        return None, "anonymous"
    try:
        email = auth_lib.verify_access_token(token)
        if not email:
            return None, "bad_token"
        return email, "ok"
    except Exception as e:
        # jose.jwt raise normalement JWTError (catch interne → None) mais on se
        # protège contre les exceptions exotiques (cookie tordu, etc.) pour
        # éviter de logger une "unexpected STT error" pour ce qui n'est qu'une
        # auth qui échoue.
        logger.warning("WS auth token verification raised: %s", e)
        return None, "bad_token"


@router.websocket("/transcribe/stream")
async def stt_stream(websocket: WebSocket) -> None:
    """Route WebSocket de transcription streaming.

    Paramètre URL (Phase 2.2 — D2/D3) :
        ?encoding=opus|linear16  (default : opus)

    Whitelist côté backend (cf. _ALLOWED_ENCODINGS) : hors-whitelist → close 1003.
    Tests Phase 2.2 utilisent ?encoding=linear16 avec test_audio.wav (PCM 16 kHz mono).
    Phase 3.2 : MediaRecorder Edge produit du 48 kHz — sample_rate à reconsidérer
    (cf. TRACKER section NON RETENU, note "STT Deepgram — sample_rate paramétrable").

    Sémantique des codes de fermeture (cf. spec §5.4) :

    Codes envoyés AVANT accept() — 4401 (auth), 4429 (saturation), 1003 (encoding
    rejeté) : Starlette ne peut pas transiter un code WebSocket sur un handshake non
    accepté — le client reçoit une réponse HTTP 403 au handshake et n'a pas
    de close frame. Le code 4401/4429/1003 ici est déclaratif côté backend pour
    la lisibilité du code source et l'audit log. Le frontend (Phase 3.1) doit traiter
    "connection failed" comme "auth manquante / saturation / encoding non supporté"
    via fallback.

    Codes envoyés APRÈS accept() — 4402, 4502, 4408, 1011 : ils transitent
    correctement comme close frames WebSocket et sont lisibles côté client.
    """
    user, auth_status = _authenticate_ws(websocket)
    if not user:
        # auth_status ∈ {"anonymous", "bad_token"} ici par invariant de
        # _authenticate_ws (user is None ⟹ status != "ok"). Narrowing
        # explicite pour mypy + safety runtime de record_pre_accept_reject.
        if auth_status in ("anonymous", "bad_token"):
            await tracker.record_pre_accept_reject(auth_status)
        await websocket.close(code=4401)
        return

    # Phase 2.2 (D2/D3) : query string encoding + whitelist côté backend.
    # Check AVANT tracker.acquire() pour ne pas consommer un slot inutile en
    # cas de rejet. close(1003) pré-accept est déclaratif (Starlette → HTTP 403).
    encoding = websocket.query_params.get("encoding", "opus")
    if encoding not in _ALLOWED_ENCODINGS:
        logger.warning(
            "STT encoding rejeté '%s' (whitelist=%s) — user=%s",
            encoding, _ALLOWED_ENCODINGS, user,
        )
        await websocket.close(code=1003, reason="UNSUPPORTED_ENCODING")
        return
    logger.info("STT encoding=%s — user=%s", encoding, user)

    try:
        async with tracker.acquire():
            await websocket.accept()
            logger.info("STT WS opened — user=%s", user)
            await _run_stt_session(websocket, user, encoding)
            # Log AVANT close — si close() raise (WS déjà fermé côté Starlette),
            # on garde la trace d'audit. Close wrappé pour la même raison.
            logger.info("STT WS closed normally — user=%s", user)
            try:
                await websocket.close(code=1000)
            except Exception as e:
                logger.warning("WS close(1000) raised — user=%s, err=%s", user, e)

    except STTRateLimitError:
        # Denial pré-accept par saturation — incrémenter le compteur R4 avant
        # close (cohérence avec anonymous/bad_token, qui sont aussi pré-accept).
        await tracker.record_pre_accept_reject("saturated")
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


async def _run_stt_session(websocket: WebSocket, user: str, encoding: str) -> None:
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
    # Phase 2.2 (D2) : seul `encoding` est paramétré. Les autres champs prennent
    # les defaults via STTSessionConfig() (language="fr", sample_rate=16000, etc.).
    # `replace()` future-proof : si STTSessionConfig acquiert un __post_init__ ou
    # des defaults env-based, les champs non-overridés restent fidèles aux
    # defaults dynamiques (vs kwargs explicites qui figeraient à des constantes).
    config = replace(STTSessionConfig(), encoding=encoding)
    session = await provider.create_session(config)
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
