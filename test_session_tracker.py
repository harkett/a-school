"""
Test du compteur STTSessionTracker (Phase 1.4 — CHECKPOINT race condition).

Standalone script — lance avec :
    python test_session_tracker.py

3 tests :
1. test_max_concurrent_strict   : 41 acquires concurrents sur max=40
                                  → 40 succès + 1 STTRateLimitError exactement
2. test_slot_released_after_use : acquire → release → acquire à nouveau → OK
3. test_release_on_exception    : exception dans le with → slot libéré quand même
"""

import asyncio
import sys

from backend.stt.base import STTRateLimitError
from backend.stt.session_tracker import STTSessionTracker


async def test_max_concurrent_strict() -> None:
    """41 acquires concurrents sur max=40 → exactement 1 raise STTRateLimitError.

    C'est le test qui prouve l'absence de race condition. Si get_active_count()
    était utilisé comme gate AVANT acquire() (au lieu d'être atomique dans acquire),
    plusieurs tâches pourraient passer le check simultanément et le compteur
    dépasserait 40.
    """
    tracker = STTSessionTracker(max_concurrent=40)

    success_count = 0
    failure_count = 0

    async def try_acquire(hold_duration: float) -> None:
        nonlocal success_count, failure_count
        try:
            async with tracker.acquire():
                success_count += 1
                await asyncio.sleep(hold_duration)
        except STTRateLimitError:
            failure_count += 1

    # 41 tâches concurrentes, chacune tient son slot 100ms
    tasks = [try_acquire(0.1) for _ in range(41)]
    await asyncio.gather(*tasks)

    assert success_count == 40, f"Expected 40 successes, got {success_count}"
    assert failure_count == 1, f"Expected 1 failure, got {failure_count}"
    assert tracker.get_active_count() == 0, "Tracker should be back to 0 after gather"

    print(f"  OK test_max_concurrent_strict : 40 succes + 1 rate-limited, compteur revenu a 0")


async def test_slot_released_after_use() -> None:
    """Après release, on peut acquire à nouveau (le slot est bien libéré)."""
    tracker = STTSessionTracker(max_concurrent=1)

    # Premier acquire
    async with tracker.acquire():
        assert tracker.get_active_count() == 1
    assert tracker.get_active_count() == 0, "Slot doit etre libere apres with"

    # Deuxième acquire — doit fonctionner puisque le slot est dispo
    async with tracker.acquire():
        assert tracker.get_active_count() == 1
    assert tracker.get_active_count() == 0

    print(f"  OK test_slot_released_after_use : 2 acquires successifs, slot bien libere")


async def test_release_on_exception() -> None:
    """Une exception levée dans le with doit quand même libérer le slot."""
    tracker = STTSessionTracker(max_concurrent=1)

    class CustomError(Exception):
        pass

    # Acquire puis raise dans le bloc
    try:
        async with tracker.acquire():
            assert tracker.get_active_count() == 1
            raise CustomError("boom")
    except CustomError:
        pass

    # Le finally du context manager doit avoir décrémenté le compteur
    assert tracker.get_active_count() == 0, "Slot doit etre libere meme sur exception"

    # Confirmation : on peut acquire à nouveau (slot vraiment libéré, pas juste compteur)
    async with tracker.acquire():
        assert tracker.get_active_count() == 1
    assert tracker.get_active_count() == 0

    print(f"  OK test_release_on_exception : slot libere apres exception")


async def main() -> int:
    print("=" * 60)
    print("Test STTSessionTracker (Phase 1.4)")
    print("=" * 60)

    tests = [
        test_max_concurrent_strict,
        test_slot_released_after_use,
        test_release_on_exception,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            await test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {test_fn.__name__} : {e}")
            failed += 1
        except Exception as e:
            print(f"  ERR  {test_fn.__name__} : {type(e).__name__}: {e}")
            failed += 1

    print("=" * 60)
    print(f"Resultat : {passed}/{len(tests)} tests OK")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
