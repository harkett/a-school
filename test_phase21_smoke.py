"""Smoke test Phase 2.1 — vérifie que /api/transcribe/stream rejette
correctement les tentatives non authentifiées.

Lance le backend (.venv\\Scripts\\python -m uvicorn backend.main:app)
puis exécute ce script.

Attendu :
- Test 1 : pas de cookie → rejet HTTP au handshake (code 4401 déclaratif backend)
- Test 2 : cookie bidon → idem (verify_access_token retourne None)

Côté Starlette, le close-before-accept se traduit par HTTP 403 au handshake,
donc côté client WS on voit InvalidStatus(403) plutôt que close frame avec
code 4401. C'est le point Q2 documenté dans la route.
"""

import asyncio

import websockets


async def try_connect(label: str, cookie_header: str | None) -> None:
    extra = {"Cookie": cookie_header} if cookie_header else {}
    try:
        async with websockets.connect(
            "ws://localhost:8000/api/transcribe/stream",
            additional_headers=extra,
        ) as ws:
            print(f"[{label}] FAIL: connection accepted")
    except websockets.exceptions.InvalidStatus as e:
        print(f"[{label}] OK denial @ handshake — HTTP {e.response.status_code}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"[{label}] OK closed — code={e.code} reason={e.reason!r}")
    except Exception as e:
        print(f"[{label}] other — {type(e).__name__}: {e}")


async def main() -> None:
    await try_connect("no-cookie", None)
    await try_connect("bad-cookie", "aschool_access=this.is.not.a.valid.jwt")


if __name__ == "__main__":
    asyncio.run(main())
