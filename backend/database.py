import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Moteur piloté par l'environnement. Défaut = SQLite (comportement historique inchangé
# tant qu'aucune DATABASE_URL n'est posée). Le jour où DATABASE_URL pointe PostgreSQL
# (.env), l'app bascule sans toucher au code. load_dotenv() est appelé dans main.py
# AVANT l'import de ce module → la valeur du .env est bien prise en compte.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/aschool.db")

if DATABASE_URL.startswith("sqlite"):
    Path("data").mkdir(exist_ok=True)               # dossier du fichier .db (SQLite uniquement)
    _engine_kwargs = {"connect_args": {"check_same_thread": False}}  # option SQLite
else:
    # PostgreSQL (psycopg, synchrone) : pas de check_same_thread ; pool robuste.
    _engine_kwargs = {"pool_pre_ping": True, "pool_recycle": 1800}

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_size_mb() -> float:
    """Taille de la base en Mo, selon le moteur effectif.
    SQLite -> taille du fichier .db (comportement historique).
    PostgreSQL -> pg_database_size(current_database())."""
    if engine.dialect.name == "sqlite":
        path = engine.url.database
        if path and os.path.exists(path):
            return round(os.path.getsize(path) / 1024**2, 2)
        return 0.0
    with engine.connect() as conn:
        size = conn.execute(text("SELECT pg_database_size(current_database())")).scalar()
    return round((size or 0) / 1024**2, 2)
