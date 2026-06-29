import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Moteur UNIQUE = PostgreSQL. SQLite est BANNI (cap aSchool : tout en base relationnelle pro).
# DATABASE_URL doit être posée (.env) et pointer PostgreSQL, sinon on REFUSE de démarrer —
# même esprit que le garde-fou Alembic. load_dotenv() est appelé dans main.py AVANT cet import.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(
        "DATABASE_URL doit pointer PostgreSQL — SQLite est banni dans aSchool. "
        "Renseigne une URL 'postgresql+psycopg://…' dans le .env."
    )

# PostgreSQL (psycopg, synchrone) : pool robuste.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)
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
    """Taille de la base PostgreSQL en Mo (pg_database_size(current_database()))."""
    with engine.connect() as conn:
        size = conn.execute(text("SELECT pg_database_size(current_database())")).scalar()
    return round((size or 0) / 1024**2, 2)
