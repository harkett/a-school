"""
Compteur de WebSockets STT concurrentes (Phase 1.4).

Pattern Lock + int. Choisi plutôt que asyncio.Semaphore car :
- asyncio.Semaphore n'a pas de non-blocking acquire natif
- Exposer get_active_count() nécessiterait soit un compteur dupliqué soit
  l'API privée Sem._value (fragile)

Spec : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md §6

Compteur en mémoire process-local : OK pour mono-instance backend.
Migration Redis nécessaire si passage en multi-worker (cf §13.6 spec).
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from backend.stt.base import STTRateLimitError


class STTSessionTracker:
    """Compteur in-memory de WebSockets STT actives.

    API publique du chemin critique : acquire() (context manager async).
    Lève STTRateLimitError si quota atteint AU MOMENT de l'acquisition,
    sous lock — pas de race condition possible.

    À utiliser AVANT websocket.accept() dans la route WS.
    """

    def __init__(self, max_concurrent: int) -> None:
        self._active: int = 0
        self._max: int = max_concurrent
        self._lock: asyncio.Lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        """Acquiert un slot ou raise STTRateLimitError. Libère en sortie de with."""
        async with self._lock:
            if self._active >= self._max:
                raise STTRateLimitError(
                    f"Max concurrent STT sessions reached ({self._max})"
                )
            self._active += 1
        try:
            yield
        finally:
            async with self._lock:
                self._active -= 1

    def get_active_count(self) -> int:
        """Lecture seule du compteur — pour l'admin dashboard.

        Synchrone : lire un int Python est atomique (GIL), pas besoin de lock.
        Ne JAMAIS utiliser comme gate avant acquire() — risque de race condition.
        """
        return self._active

    def get_max(self) -> int:
        """Capacité max configurée."""
        return self._max


# Instance module-level — pattern aligné avec limiter.py et database.py
tracker = STTSessionTracker(
    max_concurrent=int(os.getenv("STT_MAX_CONCURRENT_SESSIONS", "40"))
)
