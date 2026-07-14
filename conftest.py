"""Plomberie + garde-fous des tests aSchool — PostgreSQL UNIQUEMENT, JAMAIS SQLite.

Tous les tests tournent sur la base de test dédiée `aschool_test` (instance 5433),
jamais sur SQLite, jamais sur la base dev `aschool`. Trois verrous :

  1. BARRIÈRE PHYSIQUE — `create_engine("sqlite...")` lève RuntimeError immédiatement.
     Le conftest étant importé AVANT la collecte des tests, tout test qui réintroduirait
     SQLite plante à la collecte au lieu de passer « en douce ».
  2. GARDE-FOU POSITIF — le moteur de test DOIT être PostgreSQL ET viser `aschool_test`,
     sinon on refuse de tourner (et donc de TRUNCATE).
  3. ISOLATION — `TRUNCATE` entre chaque test, exclusivement sur `aschool_test`.
"""
import os
from pathlib import Path

import pytest
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

# --- Verrou 1 : barrière physique anti-SQLite (posée avant toute collecte) ---
_real_create_engine = sqlalchemy.create_engine


def _no_sqlite_create_engine(url, *args, **kwargs):
    if str(url).startswith("sqlite"):
        raise RuntimeError(
            "SQLite INTERDIT dans les tests aSchool. Moteur unique = PostgreSQL "
            "(base de test 'aschool_test'). Tout create_engine('sqlite...') est banni "
            "— voir conftest.py. Les tests doivent passer par la redirection PostgreSQL."
        )
    return _real_create_engine(url, *args, **kwargs)


sqlalchemy.create_engine = _no_sqlite_create_engine

# --- URL de la base de test : obligatoire, PostgreSQL, base 'aschool_test' ---
from dotenv import load_dotenv  # noqa: E402

load_dotenv(dotenv_path=Path(__file__).resolve().parents[0] / ".env", override=True)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL absente du .env (postgresql .../aschool_test attendu).")
_u = make_url(TEST_DATABASE_URL)
if _u.get_backend_name() != "postgresql":
    raise RuntimeError(f"TEST_DATABASE_URL doit être PostgreSQL, reçu : {_u.get_backend_name()!r}")
if _u.database != "aschool_test":
    raise RuntimeError(f"TEST_DATABASE_URL doit viser 'aschool_test', reçu : {_u.database!r}")

# DATABASE_URL = test AVANT tout import de backend.core.database (sinon défaut SQLite de prod).
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

_test_engine = _real_create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

import backend.core.database as _dbmod  # noqa: E402

_dbmod.engine = _test_engine
_dbmod.SessionLocal = _TestSession


# --- Verrou 2 : garde-fou positif (refuse tout sauf postgresql/aschool_test) ---
def _assert_test_engine():
    eng = _dbmod.engine
    assert eng.dialect.name == "postgresql", \
        f"SÉCURITÉ: moteur de test non-PostgreSQL ({eng.dialect.name}) — on s'arrête."
    assert eng.url.database == "aschool_test", \
        f"SÉCURITÉ: base de test != 'aschool_test' (reçu {eng.url.database!r}) — TRUNCATE refusé."


_assert_test_engine()

# --- Schéma sur aschool_test (l'extension vector existe déjà ; create_all fait le reste) ---
from backend.core import models_db  # noqa: E402

with _test_engine.begin() as _conn:
    _conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
models_db.Base.metadata.create_all(bind=_test_engine)


# --- Verrou 3 : isolation par test = TRUNCATE, UNIQUEMENT sur aschool_test ---
@pytest.fixture(autouse=True)
def _clean_db():
    _assert_test_engine()      # garde-fou AVANT le test
    yield
    _assert_test_engine()      # garde-fou AVANT le TRUNCATE (re-vérifié à chaque fois)
    tables = [t.name for t in reversed(models_db.Base.metadata.sorted_tables)]
    if tables:
        with _test_engine.begin() as conn:
            conn.execute(text(
                "TRUNCATE TABLE "
                + ", ".join(f'"{t}"' for t in tables)
                + " RESTART IDENTITY CASCADE"
            ))
