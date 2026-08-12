# Windows : torch (sentence-transformers, RAG) embarque son runtime OpenMP
# (libiomp5md.dll). Sans ces garde-fous, le 1er embedding dans le process serveur
# (retrieve_pg via uvicorn) plante en « access violation ». Posés AVANT tout import
# susceptible de charger torch.
import os as _omp
_omp.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
_omp.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
_omp.environ.setdefault("OMP_NUM_THREADS", "1")
# HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE vivaient ICI, et donc pour le serveur SEUL : tout ce
# qui charge le modèle sans passer par main.py (tests, script, `docker exec python -c`) partait
# sans garde-fou. Ils sont posés le 02/08 à la seule porte qu'on ne peut pas contourner —
# backend/rag/embeddings.py, qui explique le pourquoi — et dans docker-compose.yml. Rien à
# remettre ici : ce fichier n'est pas le chemin du modèle, il n'en est qu'un parmi d'autres.

from contextlib import asynccontextmanager
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=False)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s — %(message)s")

_pkg = json.loads((Path(__file__).resolve().parent.parent / "frontend" / "package.json").read_text())
APP_VERSION = _pkg.get("version", "0.0.0")

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from backend.core.limiter import limiter, plafond_depasse
from backend.llm.generator import (LLMIndisponibleError, LLMModeleIncompatibleError,
                                   LLMQuotaCompteError, LLMRateLimitError)
from backend.core.middleware import UserSessionMiddleware
from backend.core.schema_requete import SchemaRequeteMiddleware
from backend.securite import auth
from backend.systeme import admin
from backend.pedagogie import programmes, exemple_referentiel, referentiels_admin
from backend.contenu import activites, mes_contenus
from backend.prof import demo, profil
from backend.communication import feedback, votes
from backend.analytique import stats
from backend.analyse import ambiguites, consigne
from backend.dictee import ocr, transcribe
from backend.systeme import maintenance, mise_en_route

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

app = FastAPI(title="aSchool API", version=APP_VERSION, lifespan=_lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, plafond_depasse)


# ── Les refus du fournisseur d'IA arrivent à l'écran, en français ─────────────────────────────
#
# `generator.py` traduit chaque refus du fournisseur en une phrase écrite POUR LE PROF, qui dit
# ce qui se passe et quoi faire. Ces phrases n'arrivaient nulle part : seules les routes qui
# attrapaient l'exception à la main les rendaient, les autres laissaient remonter un 500 — et
# l'écran, devant un 500, affiche sa phrase passe-partout « le serveur n'a pas pu répondre ».
# Le prof recevait donc un message inutile à la place du seul qui l'aurait aidé (constaté le
# 07/08/2026 sur « Proposer une idée » : Groq refusait la taille de la demande, personne ne l'a su).
#
# Posé ICI et pas route par route : il y a une vingtaine d'appels à `generate()`, et chaque
# nouveau serait un oubli possible. Une seule règle, à l'entrée de l'application.
#
# Le code HTTP dit à QUI est le problème : 429 le service est bousculé (réessayer), 503 il est
# en panne (attendre), 409 le modèle choisi ne sait pas faire (changer de modèle), 413 le palier
# du compte refuse cette taille (changer de fournisseur ou d'abonnement).
_CODES_LLM = [
    (LLMRateLimitError, 429),
    (LLMIndisponibleError, 503),
    (LLMModeleIncompatibleError, 409),
    (LLMQuotaCompteError, 413),
]


async def _refus_du_fournisseur_ia(request, exc):
    """Rend le message de l'exception TEL QUEL dans `detail` : il est déjà écrit pour un humain,
    le réécrire ici le ferait diverger de sa source. Le détail technique, lui, reste au journal."""
    code = next((c for classe, c in _CODES_LLM if isinstance(exc, classe)), 503)
    logging.getLogger(__name__).warning("Refus du fournisseur d'IA (%s) : %s", code, exc)
    return JSONResponse(status_code=code, content={"detail": str(exc)})


for _classe, _ in _CODES_LLM:
    app.add_exception_handler(_classe, _refus_du_fournisseur_ia)

app.add_middleware(UserSessionMiddleware)

# AJOUTÉ APRÈS, DONC EXÉCUTÉ AVANT : Starlette empile les middlewares, le dernier ajouté est le
# plus externe. `UserSessionMiddleware` ouvre une session dès sa phase 1 pour vérifier la session
# du prof — il lui faut le schéma déjà résolu, sinon cette lecture-là partirait sur le réel même
# en démonstration. CORS reste ajouté après les deux : il doit envelopper jusqu'aux 404 de schéma
# inconnu, qui sans ses en-têtes arriveraient au navigateur comme une erreur réseau muette.
app.add_middleware(SchemaRequeteMiddleware)

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
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

app.include_router(exemple_referentiel.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(activites.router, prefix="/api")
app.include_router(mes_contenus.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(profil.router, prefix="/api")
app.include_router(demo.router, prefix="/api")
app.include_router(ocr.router, prefix="/api")
app.include_router(maintenance.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(votes.router, prefix="/api")
app.include_router(ambiguites.router, prefix="/api")
app.include_router(consigne.router, prefix="/api")
app.include_router(transcribe.router, prefix="/api")
app.include_router(programmes.router, prefix="/api")
app.include_router(referentiels_admin.router, prefix="/api")
app.include_router(mise_en_route.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "aSchool API"}

@app.get("/api/version")
def version():
    return {"version": APP_VERSION}
