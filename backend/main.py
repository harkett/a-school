from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine
from backend import models_db
from backend.routers import generate, activites, auth, mes_activites, admin

models_db.Base.metadata.create_all(bind=engine)

app = FastAPI(title="A-SCHOOL API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://school.afia.fr",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api")
app.include_router(activites.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(mes_activites.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "A-SCHOOL API"}
