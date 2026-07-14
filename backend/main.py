# Windows : torch (sentence-transformers, RAG) embarque son runtime OpenMP
# (libiomp5md.dll). Sans ces garde-fous, le 1er embedding dans le process serveur
# (retrieve_pg via uvicorn) plante en « access violation ». Posés AVANT tout import
# susceptible de charger torch.
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
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s — %(message)s")

_pkg = json.loads((Path(__file__).resolve().parent.parent / "frontend" / "package.json").read_text())
APP_VERSION = _pkg.get("version", "0.0.0")

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.core.limiter import limiter
from backend.core.middleware import UserSessionMiddleware
from backend.routers import auth
from backend.systeme import admin
from backend.activite import generate
from backend.pedagogie import programmes, exemple_referentiel, referentiels_admin
from backend.contenu import activites, mes_activites, fiches
from backend.prof import profil
from backend.communication import feedback, votes
from backend.analytique import stats
from backend.analyse import ambiguites, consigne
from backend.dictee import ocr, transcribe
from backend.reseau import bibliotheque
from backend.sequence import sequence, optimiseur
from backend.systeme import maintenance

# Schéma géré par Alembic (`alembic upgrade head`) — plus de create_all au démarrage (Pas 9).


import os as _os
if not _os.getenv("ADMIN_USERNAME") or not _os.getenv("ADMIN_PASSWORD"):
    print("\n⚠️  ATTENTION : ADMIN_USERNAME ou ADMIN_PASSWORD non chargés — connexion admin impossible.\n")

_scheduler = AsyncIOScheduler()

@asynccontextmanager
async def _lifespan(app: FastAPI):
    from backend.supervision.alerts import run_all_checks
    _scheduler.add_job(run_all_checks, "interval", minutes=5, id="alert_checks")
    _scheduler.start()

    # Préchauffe le modèle d'embeddings RAG en tâche de fond. Sans ça, le 1er clic
    # « Tester un exemple » paie ~30s de chargement à froid (torch + modèle). Ici le
    # serveur démarre tout de suite et le modèle se charge pendant que le prof navigue ;
    # le 1er clic tombe alors sur un modèle déjà chaud (~2-3s, juste la génération Groq).
    import threading

    def _warm_embeddings():
        try:
            from backend.rag.embeddings import get_st_model
            get_st_model()
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

# Origines CORS autorisées — externalisées en config de déploiement (D). La variable
# CORS_ALLOWED_ORIGINS est une liste séparée par des virgules ; VIDE ou absente = exactement
# les mêmes valeurs qu'avant (dev localhost + prod aschool.fr) → zéro changement de comportement.
_cors_defaut = ["http://localhost:5173", "http://localhost:3000", "https://aschool.fr"]
_cors_origins = [o.strip() for o in _os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()] or _cors_defaut

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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
app.include_router(fiches.router, prefix="/api")
app.include_router(optimiseur.router, prefix="/api")
app.include_router(votes.router, prefix="/api")
app.include_router(sequence.router, prefix="/api")
app.include_router(ambiguites.router, prefix="/api")
app.include_router(consigne.router, prefix="/api")
app.include_router(transcribe.router, prefix="/api")
app.include_router(programmes.router, prefix="/api")
app.include_router(referentiels_admin.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "aSchool API"}

@app.get("/api/version")
def version():
    return {"version": APP_VERSION}
