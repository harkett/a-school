from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from backend.database import engine
from backend import models_db
from backend.limiter import limiter
from backend.middleware import UserSessionMiddleware
from backend.routers import generate, activites, auth, mes_activites, admin, feedback, profil, ocr

models_db.Base.metadata.create_all(bind=engine)

# Migrations colonnes ajoutées après création initiale
with engine.connect() as _conn:
    for _col in [
        "ALTER TABLE users ADD COLUMN subject VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN prenom VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN nom VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN niveau VARCHAR(16)",
        "ALTER TABLE feedbacks ADD COLUMN type VARCHAR(16) DEFAULT 'feedback'",
        "ALTER TABLE users ADD COLUMN langue_lv VARCHAR(32)",
        "ALTER TABLE users ADD COLUMN mobile VARCHAR(20)",
        "ALTER TABLE feedbacks ADD COLUMN statut VARCHAR(16) NOT NULL DEFAULT 'nouveau'",
    ]:
        try:
            _conn.execute(text(_col))
            _conn.commit()
        except Exception:
            pass

import os as _os
if not _os.getenv("ADMIN_USERNAME") or not _os.getenv("ADMIN_PASSWORD"):
    print("\n⚠️  ATTENTION : ADMIN_USERNAME ou ADMIN_PASSWORD non chargés — connexion admin impossible.\n")

_scheduler = AsyncIOScheduler()

@asynccontextmanager
async def _lifespan(app: FastAPI):
    from backend.alerts import run_all_checks
    _scheduler.add_job(run_all_checks, "interval", minutes=5, id="alert_checks")
    _scheduler.start()
    yield
    _scheduler.shutdown(wait=False)

app = FastAPI(title="A-SCHOOL API", version="2.0.0", lifespan=_lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(UserSessionMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://school.afia.fr",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api")
app.include_router(activites.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(mes_activites.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(profil.router, prefix="/api")
app.include_router(ocr.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "A-SCHOOL API"}
