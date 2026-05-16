"""
Compteur de WebSockets STT concurrentes + observabilité denials pré-accept.

Phase 1.4 — Pattern Lock + int pour acquire concurrent atomique. Choisi plutôt
que asyncio.Semaphore car :
- asyncio.Semaphore n'a pas de non-blocking acquire natif
- Exposer get_active_count() nécessiterait soit un compteur dupliqué soit
  l'API privée Sem._value (fragile)

Phase 2.2 — max_concurrent lu live à chaque acquire() (mutation dynamique
possible sans restart serveur, utile en tests + future admin Phase 4.1) +
compteur agrégé R4 par catégorie (anonymous/bad_token/saturated) pour
observabilité des denials pré-accept tout en préservant l'anti-énumération
(pas de log par tentative, juste des compteurs incrémentés).

Spec : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md §6

Compteur en mémoire process-local : OK pour mono-instance backend.
Migration Redis nécessaire si passage en multi-worker (cf §13.6 spec).
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal, TypedDict

from backend.stt.base import STTRateLimitError

logger = logging.getLogger(__name__)

RejectReason = Literal["anonymous", "bad_token", "saturated"]


class STTRejectsPreAccept(TypedDict):
    anonymous: int
    bad_token: int
    saturated: int


class STTSessionSnapshot(TypedDict):
    active: int
    max: int
    rejects_pre_accept: STTRejectsPreAccept


def _read_max() -> int:
    """Lit STT_MAX_CONCURRENT_SESSIONS live (default 40).

    Lu à chaque acquire() pour permettre la mutation dynamique sans restart
    serveur — utile pour tests scénarios saturation + future Phase 4.1 admin.
    Le coût (un os.getenv par session ouverte) est négligeable hors hot path.
    """
    return int(os.getenv("STT_MAX_CONCURRENT_SESSIONS", "40"))


class STTSessionTracker:
    """Compteur in-memory de WebSockets STT actives + rejets pré-accept.

    API publique du chemin critique : acquire() (context manager async).
    Lève STTRateLimitError si quota atteint AU MOMENT de l'acquisition,
    sous lock — pas de race condition possible.

    À utiliser AVANT websocket.accept() dans la route WS.

    Observabilité R4 : record_pre_accept_reject(reason) pour chaque denial
    avant accept(). Catégories : anonymous (pas de cookie), bad_token
    (cookie présent mais JWT invalide/expiré), saturated (quota atteint).
    Compteurs exposés via snapshot() pour /admin/stt-status (Phase 4.1).
    """

    def __init__(self) -> None:
        self._active: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()
        self._rejects_pre_accept: STTRejectsPreAccept = {
            "anonymous": 0,
            "bad_token": 0,
            "saturated": 0,
        }

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        """Acquiert un slot ou raise STTRateLimitError. Libère en sortie de with."""
        async with self._lock:
            current_max = _read_max()
            if self._active >= current_max:
                raise STTRateLimitError(
                    f"Max concurrent STT sessions reached ({current_max})"
                )
            self._active += 1
        try:
            yield
        finally:
            async with self._lock:
                self._active -= 1

    async def record_pre_accept_reject(self, reason: RejectReason) -> None:
        """Incrémente le compteur agrégé d'un denial pré-accept.

        Whitelist runtime sur reason (defense-in-depth en plus du Literal mypy).
        Sous le même Lock que acquire() pour garantir une vue consistante via
        snapshot() — sinon un admin pourrait observer un état où active a été
        décrémenté mais rejects pas encore incrémenté.
        """
        if reason not in ("anonymous", "bad_token", "saturated"):
            logger.warning(
                "record_pre_accept_reject: reason inconnue '%s' — ignorée",
                reason,
            )
            return
        async with self._lock:
            self._rejects_pre_accept[reason] += 1

    def get_active_count(self) -> int:
        """Lecture seule du compteur — pour l'admin dashboard.

        Synchrone : lire un int Python est atomique (GIL), pas besoin de lock.
        Ne JAMAIS utiliser comme gate avant acquire() — risque de race condition.
        """
        return self._active

    def snapshot(self) -> STTSessionSnapshot:
        """Vue synchronisée pour /admin/stt-status (Phase 4.1).

        max lu live via _read_max() — reflète l'env actuelle, pas une valeur
        figée au boot. Copie défensive du dict rejects pour empêcher un caller
        de muter l'état interne. Pas de lock : lecture d'ints atomique en
        Python (GIL), micro-incohérence inter-clés acceptable pour observabilité.
        """
        return {
            "active": self._active,
            "max": _read_max(),
            "rejects_pre_accept": {
                "anonymous": self._rejects_pre_accept["anonymous"],
                "bad_token": self._rejects_pre_accept["bad_token"],
                "saturated": self._rejects_pre_accept["saturated"],
            },
        }


# Instance module-level — pattern aligné avec limiter.py et database.py
tracker = STTSessionTracker()
