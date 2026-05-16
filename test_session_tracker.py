"""
Test du compteur STTSessionTracker.

Phase 1.4 — race condition strict (41 acquires sur max=40)
Phase 2.2 — max lu live à chaque acquire (refactor γ) + compteur R4 par catégorie

Standalone script — lance avec :
    python test_session_tracker.py

7 tests :
1. test_max_concurrent_strict        : 41 acquires concurrents sur max=40
                                       → 40 succès + 1 STTRateLimitError exactement
2. test_slot_released_after_use      : acquire → release → acquire à nouveau → OK
3. test_release_on_exception         : exception dans le with → slot libéré quand même
4. test_max_dynamic_bump             : bump env entre acquires → prise en compte sans restart
5. test_record_pre_accept_concurrent : 50+30+20 incréments parallèles 3 catégories → exact
6. test_snapshot_structure           : snapshot() retourne le TypedDict attendu + max live
7. test_record_pre_accept_unknown    : reason hors whitelist ignorée sans crash
"""

import asyncio
import contextlib
import os
import sys
from collections.abc import Iterator

from backend.stt.base import STTRateLimitError
from backend.stt.session_tracker import STTSessionTracker


@contextlib.contextmanager
def _override_env(key: str, value: str) -> Iterator[None]:
    """Set os.environ[key]=value le temps du with, restore l'ancienne valeur."""
    old = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old


async def test_max_concurrent_strict() -> None:
    """41 acquires concurrents sur max=40 → exactement 1 raise STTRateLimitError.

    C'est le test qui prouve l'absence de race condition. Si get_active_count()
    était utilisé comme gate AVANT acquire() (au lieu d'être atomique dans acquire),
    plusieurs tâches pourraient passer le check simultanément et le compteur
    dépasserait 40.
    """
    with _override_env("STT_MAX_CONCURRENT_SESSIONS", "40"):
        tracker = STTSessionTracker()

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

    print("  OK test_max_concurrent_strict : 40 succes + 1 rate-limited, compteur revenu a 0")


async def test_slot_released_after_use() -> None:
    """Après release, on peut acquire à nouveau (le slot est bien libéré)."""
    with _override_env("STT_MAX_CONCURRENT_SESSIONS", "1"):
        tracker = STTSessionTracker()

        # Premier acquire
        async with tracker.acquire():
            assert tracker.get_active_count() == 1
        assert tracker.get_active_count() == 0, "Slot doit etre libere apres with"

        # Deuxième acquire — doit fonctionner puisque le slot est dispo
        async with tracker.acquire():
            assert tracker.get_active_count() == 1
        assert tracker.get_active_count() == 0

    print("  OK test_slot_released_after_use : 2 acquires successifs, slot bien libere")


async def test_release_on_exception() -> None:
    """Une exception levée dans le with doit quand même libérer le slot."""
    with _override_env("STT_MAX_CONCURRENT_SESSIONS", "1"):
        tracker = STTSessionTracker()

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

    print("  OK test_release_on_exception : slot libere apres exception")


async def test_max_dynamic_bump() -> None:
    """Le max est relu live à chaque acquire — bump env prend effet sans restart.

    C'est le test qui prouve la décision D5γ (Phase 2.2) : le tracker ne fige
    plus max_concurrent à l'instanciation. Utile pour scénarios de test
    saturation + future Phase 4.1 admin qui pourra bumper sans restart serveur.
    """
    with _override_env("STT_MAX_CONCURRENT_SESSIONS", "2"):
        tracker = STTSessionTracker()

        # Tient 2 slots ouverts pendant le test
        stop = asyncio.Event()

        async def hold() -> None:
            async with tracker.acquire():
                await stop.wait()

        slot1 = asyncio.create_task(hold())
        slot2 = asyncio.create_task(hold())
        await asyncio.sleep(0.05)  # laisse le temps aux deux acquires
        assert tracker.get_active_count() == 2, "Devrait avoir 2 slots actifs"

        # 3e acquire doit fail avec max=2
        try:
            async with tracker.acquire():
                raise AssertionError("3e acquire devrait fail avec max=2")
        except STTRateLimitError:
            pass

        # Bump max à 3 via env (sans restart serveur, sans toucher tracker)
        os.environ["STT_MAX_CONCURRENT_SESSIONS"] = "3"

        # 3e acquire doit maintenant passer puisque _read_max() relit l'env
        async with tracker.acquire():
            assert tracker.get_active_count() == 3, "Devrait avoir 3 slots actifs apres bump"
        assert tracker.get_active_count() == 2, "Retour a 2 apres release du 3e"

        stop.set()
        await asyncio.gather(slot1, slot2)
        assert tracker.get_active_count() == 0

    print("  OK test_max_dynamic_bump : bump env de 2 a 3 pris en compte sans restart")


async def test_record_pre_accept_concurrent() -> None:
    """50+30+20 incréments parallèles sur 3 catégories → compteurs exacts.

    Prouve que record_pre_accept_reject est thread-safe sous Lock partagé avec
    acquire(). Si le Lock n'était pas partagé, on aurait des pertes
    d'incréments en parallèle.
    """
    with _override_env("STT_MAX_CONCURRENT_SESSIONS", "40"):
        tracker = STTSessionTracker()

        async def record(reason: str) -> None:
            await tracker.record_pre_accept_reject(reason)  # type: ignore[arg-type]

        # 50 anonymous + 30 bad_token + 20 saturated, parallèles
        tasks = (
            [record("anonymous") for _ in range(50)]
            + [record("bad_token") for _ in range(30)]
            + [record("saturated") for _ in range(20)]
        )
        await asyncio.gather(*tasks)

        snap = tracker.snapshot()
        assert snap["rejects_pre_accept"]["anonymous"] == 50, snap
        assert snap["rejects_pre_accept"]["bad_token"] == 30, snap
        assert snap["rejects_pre_accept"]["saturated"] == 20, snap
        assert snap["active"] == 0
        assert snap["max"] == 40

    print("  OK test_record_pre_accept_concurrent : 50+30+20 incrementes exactement sous Lock")


async def test_snapshot_structure() -> None:
    """snapshot() retourne le TypedDict attendu, max lu live à chaque appel."""
    with _override_env("STT_MAX_CONCURRENT_SESSIONS", "7"):
        tracker = STTSessionTracker()

        snap = tracker.snapshot()
        assert snap == {
            "active": 0,
            "max": 7,
            "rejects_pre_accept": {
                "anonymous": 0,
                "bad_token": 0,
                "saturated": 0,
            },
        }, f"Snapshot initial inattendu : {snap}"

        # Vérif que max est live : bump env, snapshot doit refléter immédiatement
        os.environ["STT_MAX_CONCURRENT_SESSIONS"] = "12"
        snap2 = tracker.snapshot()
        assert snap2["max"] == 12, f"max doit etre live, got {snap2['max']}"

    print("  OK test_snapshot_structure : structure TypedDict + max relu a chaque snapshot")


async def test_record_pre_accept_unknown() -> None:
    """Une reason hors whitelist est ignorée sans crasher (defense-in-depth runtime)."""
    with _override_env("STT_MAX_CONCURRENT_SESSIONS", "40"):
        tracker = STTSessionTracker()

        # Cast type ignore — on teste explicitement le runtime safety,
        # le Literal mypy refuserait normalement ce call.
        await tracker.record_pre_accept_reject("invalid_reason")  # type: ignore[arg-type]
        await tracker.record_pre_accept_reject("ok")  # type: ignore[arg-type]

        snap = tracker.snapshot()
        total = sum(snap["rejects_pre_accept"].values())
        assert total == 0, f"Aucun compteur ne doit etre incremente sur reason inconnue, got {total}"

    print("  OK test_record_pre_accept_unknown : reason invalide ignoree sans crash ni incrementation")


async def main() -> int:
    print("=" * 60)
    print("Test STTSessionTracker (Phases 1.4 + 2.2)")
    print("=" * 60)

    tests = [
        test_max_concurrent_strict,
        test_slot_released_after_use,
        test_release_on_exception,
        test_max_dynamic_bump,
        test_record_pre_accept_concurrent,
        test_snapshot_structure,
        test_record_pre_accept_unknown,
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
