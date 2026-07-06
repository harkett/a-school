"""Alembic — environnement de migrations aSchool.

Câblé sur l'app : l'URL vient de DATABASE_URL (.env, même source que l'app), jamais
en dur dans alembic.ini ; les métadonnées cibles = le modèle ORM (backend.core.models_db).
Garde-fou : refuse de tourner si le moteur n'est pas PostgreSQL (SQLite jamais touché)."""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# env.py vit dans alembic/ : racine projet sur le path pour pouvoir importer backend.*
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

# .env pour DATABASE_URL. SANS override : un DATABASE_URL fourni dans le shell l'emporte
# (utile pour viser une base scratch vide lors de la génération de la baseline).
load_dotenv(_ROOT / ".env")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# URL pilotée par le .env (jamais en dur dans alembic.ini).
_db_url = os.getenv("DATABASE_URL")
if not _db_url:
    raise SystemExit("DATABASE_URL absente du .env — Alembic ne sait pas quelle base viser.")
# GARDE-FOU : jamais autre chose que PostgreSQL (SQLite, le filet, n'est jamais touché).
if not _db_url.startswith("postgresql"):
    raise SystemExit(f"ARRET : DATABASE_URL = '{_db_url.split('://')[0]}://…', Alembic exige postgresql.")
config.set_main_option("sqlalchemy.url", _db_url)

# Métadonnées cibles = le modèle ORM. Importer models_db enregistre les 22 tables sur Base.metadata.
from backend.core.database import Base
from backend.core import models_db  # noqa: F401  (effet de bord : enregistre les tables)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Mode 'offline' : génère le SQL sans connexion."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Mode 'online' : connexion réelle à la base."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
