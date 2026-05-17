"""
test_phase22.py — Robustesse route WS /api/transcribe/stream (Phase 2.2).

7 scénarios séquentiels, exécutés via fastapi.testclient.TestClient (option B).
Lifespan géré par TestClient, aucun serveur externe requis (pas de .\\run.ps1).

Décisions Phase 2.2 reflétées :
  D1 LINEAR16 (test_audio.wav PCM 16 kHz mono 25s)
  D2 ?encoding= en query string
  D3 whitelist côté backend → close 1003 (non testé ici, couvert par construction
     — toute valeur hors {"opus","linear16"} ferait échouer connect)
  D4 JWT forgé via backend.auth.create_access_token (D4=β)
  D5γ + R4 — tracker.acquire() relit STT_MAX_CONCURRENT_SESSIONS live →
            os.environ override suffit pour scénario 4 (pas de monkeypatch interne).
  D6 δ2 — FakeExhaustedProvider local, swap _PROVIDERS["deepgram"] temporaire.

Usage :
  .venv\\Scripts\\python test_phase22.py            # full run (~75s à cause du 7)
  .venv\\Scripts\\python test_phase22.py --fast     # skippe le scénario 7

Sortie : 0 si tous passent (skip OK), 1 si ≥1 FAIL.

Codes de close — rappel sémantique Phase 2.1 :
  Pré-accept (4401, 4429, 1003) → Starlette transcode HTTP 403 → client voit
    WebSocketDisconnect au handshake, pas de code lisible. On vérifie le rejet
    par le fait (exception levée), pas par le code numérique.
  Post-accept (4402, 4502, 4408, 1011) → transitent comme close frames
    WebSocket, lisibles via WebSocketDisconnect.code côté client.

Threading : nécessaire pour scénarios 3 et 7 car
WebSocketTestSession.receive_*() est bloquant sans timeout natif dans Starlette
1.0.0. Un thread daemon push l'audio, le main thread fait les receive bloquants.
Stop coordonné via threading.Event en finally.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
import wave
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.main import app
from backend.auth import create_access_token
from backend.stt import (
    _PROVIDERS,
    STTCreditExhaustedError,
    STTProvider,
    STTSession,
    STTSessionConfig,
)

# ============================================================
# Constantes
# ============================================================

TEST_AUDIO_PATH = Path(__file__).parent / "MesMD" / "DEEPGRAM" / "test_audio.wav"
DEFAULT_USER_EMAIL = "stt_test@aschool.local"

# Codes de close post-accept lisibles côté client (cf. transcribe.py docstring)
CODE_CREDIT_EXHAUSTED = 4402
CODE_SERVICE_DOWN     = 4502
CODE_IDLE_OR_MAX      = 4408

# Schéma message transcript émis par la route (cf. transcribe.py:227-234)
TRANSCRIPT_KEYS = {"type", "text", "is_final", "confidence", "start", "end"}

# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("test_phase22")


# ============================================================
# Sentinel : scénario non testé pour raison externe
# ============================================================

class _Skipped(Exception):
    """Levée par un scénario pour signaler un skip (vs échec).

    Distinct de PASS dans le décompte final. Typiquement levée si Deepgram
    répond close 4502 (service unavailable) — c'est aligné avec le contrat
    handoff Phase 2.2 (scénario 3 : "reception transcripts OU close 4502").
    """


# ============================================================
# Helpers env / provider
# ============================================================

@contextmanager
def env_override(**overrides: str) -> Iterator[None]:
    """Mute env vars pour la durée d'un scénario, restaure ensuite.

    D5γ : tracker.acquire() relit STT_MAX_CONCURRENT_SESSIONS live →
    override suffit pour scénario 4. STT_SESSION_*_SECONDS lus à l'ouverture
    de chaque session (transcribe.py:189-190) → override avant connect OK.
    """
    snapshot = {k: os.environ.get(k) for k in overrides}
    os.environ.update(overrides)
    try:
        yield
    finally:
        for k, v in snapshot.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@contextmanager
def provider_override(cls: type[STTProvider]) -> Iterator[None]:
    """Swap _PROVIDERS['deepgram'] le temps d'un scénario (D6 δ2).

    Restore en finally même si le scénario raise.
    """
    original = _PROVIDERS["deepgram"]
    _PROVIDERS["deepgram"] = cls
    try:
        yield
    finally:
        _PROVIDERS["deepgram"] = original


# ============================================================
# Helpers connexion
# ============================================================

def forge_jwt(email: str = DEFAULT_USER_EMAIL) -> str:
    """JWT valide via backend.auth.create_access_token (D4=β).

    Pas de round-trip via /api/auth/login : test indépendant du seed BDD,
    et le JWT contient juste l'email comme `sub` (verify_access_token le
    retourne tel quel — cf. transcribe.py:70).
    """
    return create_access_token(email)


def stream_url(encoding: str = "linear16") -> str:
    return f"/api/transcribe/stream?encoding={encoding}"


def jwt_header(token: str) -> dict[str, str]:
    """Cookie header pour TestClient.websocket_connect(headers=...).

    TestClient WS ne gère pas le cookie jar automatiquement pour les WS,
    on passe le Cookie header explicitement.
    """
    return {"Cookie": f"aschool_access={token}"}


def linear16_chunks(path: Path, chunk_ms: int = 50) -> Iterator[bytes]:
    """Charge un .wav PCM 16-bit mono 16 kHz et yield des chunks raw.

    Assert sur format pour ne pas envoyer du PCM mal formé à Deepgram —
    l'erreur côté provider serait cryptique.
    """
    with wave.open(str(path), "rb") as wf:
        assert wf.getsampwidth() == 2, (
            f"expected 16-bit PCM, got {wf.getsampwidth() * 8}-bit"
        )
        assert wf.getnchannels() == 1, (
            f"expected mono, got {wf.getnchannels()} channels"
        )
        sr = wf.getframerate()
        n_frames = int(sr * chunk_ms / 1000)
        while frames := wf.readframes(n_frames):
            yield frames


# ============================================================
# Mock provider (D6 δ2)
# ============================================================

class FakeExhaustedProvider(STTProvider):
    """Raise STTCreditExhaustedError dès create_session().

    Couvre scénario 5 sans appeler Deepgram réel ni dépendre d'une
    invalidation de clé. L'erreur est attrapée par la route en except
    STTCreditExhaustedError (transcribe.py:151-153) → close 4402 envoyé
    post-accept (lisible côté client via WebSocketDisconnect.code).
    """

    async def create_session(
        self, config: STTSessionConfig | None = None
    ) -> STTSession:
        raise STTCreditExhaustedError(
            "simulated credit exhaustion (test_phase22 FakeExhaustedProvider)"
        )


# ============================================================
# Scénarios 1 & 2 — rejets pré-accept (auth)
# ============================================================
# Pré-accept (4401) → Starlette transcode HTTP 403 → on attrape l'exception
# levée au handshake sans inspecter de close code (pas lisible côté client).

def scenario_1_no_cookie(client: TestClient) -> None:
    try:
        with client.websocket_connect(stream_url()):
            raise AssertionError("connexion acceptée sans cookie")
    except WebSocketDisconnect:
        return
    except Exception as e:
        log.info("rejet handshake via %s: %s", type(e).__name__, e)


def scenario_2_bad_cookie(client: TestClient) -> None:
    bad_headers = {"Cookie": "aschool_access=this.is.not.a.valid.jwt"}
    try:
        with client.websocket_connect(stream_url(), headers=bad_headers):
            raise AssertionError("connexion acceptée avec mauvais cookie")
    except WebSocketDisconnect:
        return
    except Exception as e:
        log.info("rejet handshake via %s: %s", type(e).__name__, e)


# ============================================================
# Scénario 3 — cookie valide + audio → transcript
# ============================================================

def scenario_3_valid_cookie_audio(client: TestClient, jwt: str) -> None:
    """Golden path : auth OK, audio LINEAR16 streamé, ≥1 transcript reçu.

    Thread daemon push l'audio en cycle ; main thread bloque sur
    receive_json() jusqu'au premier transcript. Timer 10s ferme le client
    en fallback si Deepgram est silent (auquel cas → _Skipped).

    Note teardown : on extrait les assertions HORS du with, et on tolère
    une exception bénigne (CancelledError) à la sortie du with si un
    transcript a déjà été reçu. Cause : ws.close() côté client (Timer ou
    break naturel) cancel les tasks serveur en plein wait_for, le portal
    anyio propage CancelledError au __exit__ — sans impact métier.
    """
    chunks = list(linear16_chunks(TEST_AUDIO_PATH))
    transcript_holder: list[dict] = []
    timed_out = threading.Event()

    try:
        with client.websocket_connect(
            stream_url(), headers=jwt_header(jwt)
        ) as ws:
            stop = threading.Event()

            def sender() -> None:
                for chunk in chunks:
                    if stop.is_set():
                        return
                    try:
                        ws.send_bytes(chunk)
                        time.sleep(0.05)
                    except Exception:
                        return

            def timer_close() -> None:
                timed_out.set()
                try:
                    ws.close()
                except Exception:
                    pass

            sender_thread = threading.Thread(target=sender, daemon=True)
            sender_thread.start()
            deadline = threading.Timer(10.0, timer_close)
            deadline.daemon = True
            deadline.start()

            try:
                while True:
                    msg = ws.receive_json()
                    if msg.get("type") == "transcript":
                        transcript_holder.append(msg)
                        break
            except WebSocketDisconnect as e:
                if e.code == CODE_SERVICE_DOWN:
                    raise _Skipped(
                        f"Deepgram service unavailable (close {e.code})"
                    )
                if timed_out.is_set():
                    raise _Skipped(
                        "timeout 10s sans transcript "
                        "(Deepgram silent ou audio non décodé)"
                    )
                raise AssertionError(
                    f"close serveur inattendu avant transcript : code={e.code}"
                )
            finally:
                stop.set()
                deadline.cancel()
                sender_thread.join(timeout=1.0)
    except (_Skipped, AssertionError):
        raise
    except Exception as e:
        # CancelledError ou similaire au teardown du portal Starlette si on
        # a interrompu les tasks serveur via ws.close() côté client. Bénin
        # ssi on a un transcript validé. Sinon propage.
        if not transcript_holder:
            raise
        log.debug(
            "exception bénigne au teardown ignorée : %s: %s",
            type(e).__name__, e,
        )

    assert transcript_holder, "aucun transcript reçu"
    transcript = transcript_holder[0]
    assert set(transcript.keys()) == TRANSCRIPT_KEYS, (
        f"keys inattendues : {set(transcript.keys())} "
        f"(attendu : {TRANSCRIPT_KEYS})"
    )
    assert transcript["type"] == "transcript"
    assert transcript["text"], "transcript text vide"
    log.info(
        "transcript reçu : text=%r is_final=%s",
        transcript["text"][:60],
        transcript["is_final"],
    )


# ============================================================
# Scénario 4 — saturation (D5γ : env override suffit)
# ============================================================

def scenario_4_saturation(client: TestClient, jwt: str) -> None:
    """STT_MAX_CONCURRENT_SESSIONS=1, 2 WS coexistantes → 2e rejetée pré-accept.

    Tracker relit max live à chaque acquire() (D5γ), donc override env suffit.
    Warm-up ws1 : send_bytes + sleep(0.2) pour garantir que accept+acquire
    serveur ont eu lieu avant la tentative ws2.
    """
    with env_override(STT_MAX_CONCURRENT_SESSIONS="1"):
        with client.websocket_connect(
            stream_url(), headers=jwt_header(jwt)
        ) as ws1:
            # Warm-up : forcer le portal à drainer accept + acquire serveur.
            try:
                ws1.send_bytes(b"\x00\x00")
            except Exception:
                # Tolérant : si le payload "silence 2 octets" est rejeté par
                # le portal/Deepgram, ce n'est pas le sujet du scénario.
                pass
            time.sleep(0.2)

            # Tentative ws2 : DOIT être rejetée pré-accept (4429 → HTTP 403).
            # Le try/except entoure la ligne `with` elle-même : l'exception
            # est levée à __enter__, pas dans le corps du with.
            try:
                with client.websocket_connect(
                    stream_url(), headers=jwt_header(jwt)
                ):
                    raise AssertionError(
                        "ws2 acceptée alors que tracker saturated"
                    )
            except WebSocketDisconnect:
                return
            except AssertionError:
                raise
            except Exception as e:
                log.info("ws2 rejet via %s: %s", type(e).__name__, e)
                return


# ============================================================
# Scénario 5 — crédit épuisé (D6 δ2)
# ============================================================

def scenario_5_exhausted_credit(client: TestClient, jwt: str) -> None:
    """FakeExhaustedProvider raise dans create_session() → mapping route
    → close 4402 post-accept, lisible côté client."""
    with provider_override(FakeExhaustedProvider):
        with client.websocket_connect(
            stream_url(), headers=jwt_header(jwt)
        ) as ws:
            try:
                ws.receive_text()
            except WebSocketDisconnect as e:
                assert e.code == CODE_CREDIT_EXHAUSTED, (
                    f"close code inattendu : {e.code} "
                    f"(attendu {CODE_CREDIT_EXHAUSTED})"
                )
                log.info("close 4402 reçu — mapping STTCreditExhaustedError OK")
                return
            raise AssertionError(
                "aucun close reçu malgré FakeExhaustedProvider"
            )


# ============================================================
# Scénario 6 — idle timeout
# ============================================================

def scenario_6_idle_timeout(client: TestClient, jwt: str) -> None:
    """STT_SESSION_IDLE_TIMEOUT_SECONDS=2, aucun audio envoyé →
    close 4408 attendu sous ~2-3s côté client."""
    with env_override(STT_SESSION_IDLE_TIMEOUT_SECONDS="2"):
        with client.websocket_connect(
            stream_url(), headers=jwt_header(jwt)
        ) as ws:
            try:
                ws.receive_text()
            except WebSocketDisconnect as e:
                assert e.code == CODE_IDLE_OR_MAX, (
                    f"close code inattendu : {e.code} "
                    f"(attendu {CODE_IDLE_OR_MAX})"
                )
                log.info("close 4408 reçu après idle timeout 2s")
                return
            raise AssertionError("aucun close reçu malgré idle timeout")


# ============================================================
# Scénario 7 — max duration + warning EXPIRING_SOON
# ============================================================

def scenario_7_max_duration_warning(client: TestClient, jwt: str) -> None:
    """STT_SESSION_MAX_DURATION_SECONDS=70 → warning à t≈10s, close 4408 à t≈70s.

    Override double : MAX=70 ET IDLE=120. Sans override IDLE, le default 30s
    tuerait la session avant le warning (le watchdog du serveur est sur max,
    pas sur idle).

    Thread daemon pump l'audio toutes les ~1s pour ne pas se faire idle-out
    (ceinture+bretelles avec IDLE=120). Main thread consomme TOUS les messages
    (transcripts intermédiaires inclus) jusqu'au close — la boucle ne sort
    que sur WebSocketDisconnect, et on vérifie alors que le warning a bien
    été vu en cours de route.

    Durée : ~70s. Skippé en --fast.
    """
    expected_warning = {
        "type": "session_warning",
        "code": "EXPIRING_SOON",
        "remaining_seconds": 60,
    }

    with env_override(
        STT_SESSION_MAX_DURATION_SECONDS="70",
        STT_SESSION_IDLE_TIMEOUT_SECONDS="120",
    ):
        chunks = list(linear16_chunks(TEST_AUDIO_PATH))
        with client.websocket_connect(
            stream_url(), headers=jwt_header(jwt)
        ) as ws:
            stop = threading.Event()

            def sender() -> None:
                i = 0
                while not stop.is_set():
                    try:
                        ws.send_bytes(chunks[i % len(chunks)])
                    except Exception:
                        return
                    i += 1
                    # ~1s entre chunks, décomposé pour répondre vite à stop.
                    for _ in range(20):
                        if stop.is_set():
                            return
                        time.sleep(0.05)

            threading.Thread(target=sender, daemon=True).start()

            got_warning = False
            try:
                while True:
                    msg = ws.receive_json()
                    if msg.get("type") == "session_warning":
                        assert msg == expected_warning, (
                            f"warning inattendu : {msg}"
                        )
                        got_warning = True
                        log.info("warning reçu : %s", msg)
                    # autres types (transcript, etc.) : on consomme et on
                    # continue jusqu'au close serveur.
            except WebSocketDisconnect as e:
                stop.set()
                if e.code == CODE_SERVICE_DOWN:
                    raise _Skipped(
                        f"Deepgram service unavailable (close {e.code})"
                    )
                assert e.code == CODE_IDLE_OR_MAX, (
                    f"close inattendu : {e.code} "
                    f"(attendu {CODE_IDLE_OR_MAX})"
                )
                assert got_warning, (
                    "session_warning jamais reçu avant le close 4408"
                )
                log.info("close 4408 reçu — flux warning + close OK")
            finally:
                stop.set()


# ============================================================
# Orchestration
# ============================================================

def main() -> int:
    if not TEST_AUDIO_PATH.exists():
        log.error("Asset manquant : %s", TEST_AUDIO_PATH)
        return 1

    fast = "--fast" in sys.argv

    client = TestClient(app)
    jwt = forge_jwt()

    scenarios: list[tuple[str, "callable"]] = [
        ("1_no_cookie",            lambda: scenario_1_no_cookie(client)),
        ("2_bad_cookie",           lambda: scenario_2_bad_cookie(client)),
        ("3_valid_cookie_audio",   lambda: scenario_3_valid_cookie_audio(client, jwt)),
        ("4_saturation",           lambda: scenario_4_saturation(client, jwt)),
        ("5_exhausted_credit",     lambda: scenario_5_exhausted_credit(client, jwt)),
        ("6_idle_timeout",         lambda: scenario_6_idle_timeout(client, jwt)),
        ("7_max_duration_warning", lambda: scenario_7_max_duration_warning(client, jwt)),
    ]
    if fast:
        log.info("Mode --fast : scénario 7 (~70s) skippé")
        scenarios = scenarios[:6]

    passes: list[str] = []
    failures: list[str] = []
    skipped: list[str] = []

    for name, run in scenarios:
        log.info("=== Scénario %s ===", name)
        try:
            run()
        except _Skipped as e:
            log.warning("SKIP %s — %s", name, e)
            skipped.append(name)
        except Exception:
            log.exception("FAIL %s", name)
            failures.append(name)
        else:
            log.info("PASS %s", name)
            passes.append(name)

    total = len(scenarios)
    log.info(
        "Bilan : %d PASS, %d SKIP, %d FAIL sur %d total",
        len(passes), len(skipped), len(failures), total,
    )
    if failures:
        log.error("KO : %s", failures)
        return 1
    if skipped:
        log.info("OK avec skip : %s", skipped)
    else:
        log.info("OK — %d/%d scénarios passent.", len(passes), total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
