# Windows : torch (sentence-transformers, RAG) et chromadb embarquent chacun leur
# runtime OpenMP (libiomp5md.dll). Sans ces garde-fous, le 1er embedding dans le
# process serveur (retrieve() via uvicorn) plante en « access violation ». Posés
# AVANT tout import susceptible de charger torch.
import os as _omp
_omp.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
_omp.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
_omp.environ.setdefault("OMP_NUM_THREADS", "1")
# Modèle d'embeddings déjà en cache local → on coupe les allers-retours réseau HF Hub
# au chargement (petit gain, et pas de dépendance réseau au boot).
_omp.environ.setdefault("HF_HUB_OFFLINE", "1")
_omp.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from contextlib import asynccontextmanager
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s — %(message)s")

_pkg = json.loads((Path(__file__).resolve().parent.parent / "frontend" / "package.json").read_text())
APP_VERSION = _pkg.get("version", "0.0.0")

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
from backend.routers import generate, activites, auth, mes_activites, admin, feedback, profil, ocr, bibliotheque, maintenance, stats, fiches, optimiseur, votes, sequence, ambiguites, consigne, transcribe, programmes, exemple_referentiel

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
        "ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1",
        "ALTER TABLE activites_sauvegardees ADD COLUMN matiere VARCHAR(64)",
        "ALTER TABLE activites_sauvegardees ADD COLUMN objet VARCHAR(150)",
        "ALTER TABLE activites_sauvegardees ADD COLUMN partagee BOOLEAN NOT NULL DEFAULT 0",
        "CREATE TABLE IF NOT EXISTS fiches_matieres (id INTEGER PRIMARY KEY AUTOINCREMENT, matiere_key VARCHAR(64) NOT NULL UNIQUE, statut VARCHAR(16) NOT NULL DEFAULT 'brouillon', accroche TEXT, pour_qui TEXT, ameliorations TEXT, updated_at DATETIME, updated_by VARCHAR(255))",
        "CREATE TABLE IF NOT EXISTS feature_votes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id), feature_key VARCHAR(64) NOT NULL, created_at DATETIME, UNIQUE(user_id, feature_key))",
        "CREATE TABLE IF NOT EXISTS tool_usage_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id), tool VARCHAR(32) NOT NULL, score_label VARCHAR(32), created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)",
        "ALTER TABLE feedbacks ADD COLUMN updated_at DATETIME",
        "ALTER TABLE feedbacks ADD COLUMN attachment_path VARCHAR(500)",
        "ALTER TABLE activites_sauvegardees ADD COLUMN created_at DATETIME",
        "ALTER TABLE activites_sauvegardees ADD COLUMN anonyme BOOLEAN NOT NULL DEFAULT 0",
        "ALTER TABLE sequences_sauvegardees ADD COLUMN anonyme BOOLEAN NOT NULL DEFAULT 0",
        "ALTER TABLE sequences_sauvegardees ADD COLUMN partagee BOOLEAN NOT NULL DEFAULT 0",
        "ALTER TABLE niveaux ADD COLUMN traite BOOLEAN NOT NULL DEFAULT 0",
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

    # Préchauffe le modèle d'embeddings RAG en tâche de fond. Sans ça, le 1er clic
    # « Tester un exemple » paie ~30s de chargement à froid (torch + modèle). Ici le
    # serveur démarre tout de suite et le modèle se charge pendant que le prof navigue ;
    # le 1er clic tombe alors sur un modèle déjà chaud (~2-3s, juste la génération Groq).
    import threading

    def _warm_embeddings():
        try:
            from backend.rag.embeddings import get_embedding_function
            get_embedding_function()
            logging.getLogger("rag.warm").info("Modèle d'embeddings préchauffé.")
        except Exception as e:
            logging.getLogger("rag.warm").warning(f"Préchauffe embeddings échouée (non bloquant) : {e}")

    threading.Thread(target=_warm_embeddings, daemon=True, name="rag-warm").start()

    yield
    _scheduler.shutdown(wait=False)

app = FastAPI(title="aSchool API", version="2.0.0", lifespan=_lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(UserSessionMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://aschool.fr",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api")
app.include_router(exemple_referentiel.router, prefix="/api")
app.include_router(activites.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(mes_activites.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(profil.router, prefix="/api")
app.include_router(ocr.router, prefix="/api")
app.include_router(bibliotheque.router, prefix="/api")
app.include_router(maintenance.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(fiches.router)
app.include_router(optimiseur.router, prefix="/api")
app.include_router(votes.router, prefix="/api")
app.include_router(sequence.router, prefix="/api")
app.include_router(ambiguites.router, prefix="/api")
app.include_router(consigne.router, prefix="/api")
app.include_router(transcribe.router, prefix="/api")
app.include_router(programmes.router, prefix="/api")

# Seed exemples au démarrage (idempotent)
try:
    from backend.seed_exemples import run_seed
    from backend.database import SessionLocal as _SL
    _db = _SL()
    try:
        run_seed(_db)
    finally:
        _db.close()
except Exception as _e:
    print(f"⚠️  Seed exemples ignoré : {_e}")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "aSchool API"}

@app.get("/api/version")
def version():
    return {"version": APP_VERSION}
