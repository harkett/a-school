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

# `lock_timeout` : un test qui laisse sa session ouverte (une exception levée avant son
# `db.close()`, par exemple) garde une transaction en cours ; le TRUNCATE de nettoyage l'attend
# alors INDÉFINIMENT et la suite entière se fige sans afficher une seule ligne — impossible à
# diagnostiquer, et chaque relance se met en file derrière la première. Avec ce plafond, le
# blocage devient une erreur immédiate qui NOMME la table : on sait quoi réparer.
# `idle_in_transaction_session_timeout` coupe la session fautive elle-même, pour que la relance
# suivante reparte sur une base saine.
_test_engine = _real_create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"options": "-c lock_timeout=15s -c idle_in_transaction_session_timeout=60s"},
)
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
from backend.core.llm_prompts import PROMPTS as _PROMPTS  # noqa: E402

with _test_engine.begin() as _conn:
    _conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
# drop_all AVANT create_all : `create_all` crée les tables MANQUANTES mais n'ajoute jamais une
# colonne à une table déjà là. Sans ce nettoyage, une base de test montée hier reste figée sur
# le schéma d'hier et la suite entière tombe sur une colonne inconnue — un faux échec, qui ne
# dit rien du code. Le schéma de test est donc reconstruit à neuf à chaque session (les deux
# verrous ci-dessus garantissent qu'on ne peut viser que `aschool_test`).
models_db.Base.metadata.drop_all(bind=_test_engine)
models_db.Base.metadata.create_all(bind=_test_engine)


# --- Catalogues de référence : semés par MIGRATION en prod, mais le schéma de test est monté
# par create_all (sans migrations). Le TRUNCATE (verrou 3) les vide entre chaque test → on les
# re-sème avant chaque test, sinon les FK (ex. feedbacks.statut) et le no-fallback plantent.
# Une entrée par table-catalogue : les tâches suivantes (features, durées) l'étendront ici.
_CATALOGUES_SEED = {
    "feedback_statuts": [
        {"code": "nouveau", "label": "Nouveau", "modifiable": True, "ordre": 0, "description": "Reçu, pas encore traité."},
        {"code": "en_cours", "label": "En cours", "modifiable": True, "ordre": 1, "description": "Pris en charge par l'équipe."},
        {"code": "traite", "label": "Traité", "modifiable": False, "ordre": 2, "description": "Résolu ou intégré."},
        {"code": "archive", "label": "Archivé", "modifiable": False, "ordre": 3, "description": "Clôturé."},
    ],
    # Catalogues du formulaire de séance : le serveur valide le mode et le style CONTRE ces
    # tables (plus de liste en dur), donc sans elles toute génération de séance est refusée.
    "seance_modes": [
        {"code": "standard", "label": "Séance standard", "description": "Nouvelle séance sur le thème", "ordre": 0, "actif": True},
        {"code": "remediation", "label": "Remédiation", "description": "La classe n'a pas compris, on recommence autrement", "ordre": 1, "actif": True},
        {"code": "approfondissement", "label": "Approfondissement", "description": "Aller plus loin sur un thème déjà acquis", "ordre": 2, "actif": True},
        {"code": "autonomie", "label": "Autonomie guidée", "description": "Les élèves travaillent seuls, la séance les guide", "ordre": 3, "actif": True},
    ],
    "seance_styles": [
        {"code": "classique", "label": "Classique", "description": "Fiche de préparation traditionnelle.", "ordre": 0, "actif": True},
        {"code": "ludique", "label": "Ludique", "description": "La séance passe par le jeu.", "ordre": 1, "actif": True},
        {"code": "structure", "label": "Structuré", "description": "Un découpage très net.", "ordre": 2, "actif": True},
        {"code": "concis", "label": "Très concis", "description": "Le format télégraphique.", "ordre": 3, "actif": True},
    ],
    "langues_lv": [
        {"code": "anglais", "label": "Anglais", "ordre": 0, "actif": True},
        {"code": "espagnol", "label": "Espagnol", "ordre": 1, "actif": True},
        {"code": "allemand", "label": "Allemand", "ordre": 2, "actif": True},
        {"code": "italien", "label": "Italien", "ordre": 3, "actif": True},
        {"code": "portugais", "label": "Portugais", "ordre": 4, "actif": True},
        {"code": "arabe", "label": "Arabe", "ordre": 5, "actif": True},
        {"code": "chinois", "label": "Chinois", "ordre": 6, "actif": True},
        {"code": "autre", "label": "Autre", "ordre": 7, "actif": True},
    ],
    # Fournisseurs LLM : catalogue semé par MIGRATION en prod (ai_fournisseurs), donc à re-semer
    # ici (create_all ne seed pas). cle_env = NOM de la variable d'env de la clé texte, lu en base
    # par get_cle_texte ; la valeur du secret vient du .env chargé par ce conftest.
    "ai_fournisseurs": [
        {"code": "groq", "label": "Groq", "actif": True, "ordre": 1, "cle_env": "GROQ_API_KEY_TEXTE"},
        {"code": "anthropic", "label": "Anthropic (Claude)", "actif": True, "ordre": 2, "cle_env": "CLAUDE_API_KEY_TEXTE"},
    ],
    # Fonctionnalités votables (écran « Bientôt disponible ») : catalogue semé par MIGRATION
    # en prod (features_votables). Sous-ensemble représentatif : deux actives + une inactive
    # (les votes d'une carte retirée restent comptés côté admin, mais la carte quitte l'écran).
    "features_votables": [
        {"code": "analyser-consigne", "label": "Analyser une consigne", "description": "Analyse d'une consigne.",
         "categorie": "Outils pédagogiques", "icone": "loupe", "ordre": 0, "actif": True},
        {"code": "quiz-interactif", "label": "Quiz interactif élèves", "description": "Quiz partagé aux élèves.",
         "categorie": "Autre", "icone": "horloge", "ordre": 1, "actif": True},
        {"code": "outil-retire", "label": "Outil retiré", "description": "Carte retirée de l'écran.",
         "categorie": "Autre", "icone": "fusee", "ordre": 2, "actif": False},
    ],
    # Réglages de `settings` SEMÉS PAR MIGRATION, que le code lit SANS défaut (get_few_shot_seuil
    # lève une erreur claire si la ligne manque — règle maison : base vide = erreur, pas repli).
    # Sans eux ici, la génération et Mes stats répondraient 500 dans les tests, à juste titre.
    "settings": [
        {"key": "few_shot_seuil", "value": "3"},
        {"key": "few_shot_extrait_max", "value": "3000"},
        # TOUS les prompts du registre (étape 9 lot C) : `get_prompt` n'a plus de repli code,
        # donc une clé non semée fait tomber l'outil qui l'utilise — ici comme en production.
        # Semés depuis le registre : ce fichier monte le schéma par create_all, pas par
        # migrations. Ce n'est PAS ce qui prouve la cohérence — la preuve, c'est
        # tests/test_prompts_en_base.py, qui compare le registre à la liste GELÉE de la
        # migration, pas à ce seed.
        *({"key": f"prompt_{cle}", "value": meta["default"]} for cle, meta in _PROMPTS.items()),
        # Seuils métier sortis du code (étape 9 lot B) : sans eux, joindre un fichier, générer
        # une séance ou déposer un cahier répondraient 500 dans les tests — à juste titre.
        {"key": "feedback_piece_jointe_max_mo", "value": "5"},
        {"key": "feedback_pieces_jointes_max", "value": "5"},
        {"key": "seance_duree_min", "value": "5"},
        {"key": "seance_duree_max", "value": "300"},
        {"key": "cahier_max_mo", "value": "20"},
    ],
}


def _seed_catalogues():
    with _test_engine.begin() as conn:
        for row in _CATALOGUES_SEED["feedback_statuts"]:
            conn.execute(
                text(
                    "INSERT INTO feedback_statuts (code, label, modifiable, ordre, description) "
                    "VALUES (:code, :label, :modifiable, :ordre, :description) ON CONFLICT (code) DO NOTHING"
                ),
                row,
            )
        for table in ("seance_modes", "seance_styles"):
            for row in _CATALOGUES_SEED[table]:
                conn.execute(
                    text(
                        f"INSERT INTO {table} (code, label, description, ordre, actif) "
                        "VALUES (:code, :label, :description, :ordre, :actif) ON CONFLICT (code) DO NOTHING"
                    ),
                    row,
                )
        for row in _CATALOGUES_SEED["langues_lv"]:
            conn.execute(
                text(
                    "INSERT INTO langues_lv (code, label, ordre, actif) "
                    "VALUES (:code, :label, :ordre, :actif) ON CONFLICT (code) DO NOTHING"
                ),
                row,
            )
        for row in _CATALOGUES_SEED["ai_fournisseurs"]:
            conn.execute(
                text(
                    "INSERT INTO ai_fournisseurs (code, label, actif, ordre, cle_env) "
                    "VALUES (:code, :label, :actif, :ordre, :cle_env) ON CONFLICT (code) DO NOTHING"
                ),
                row,
            )
        for row in _CATALOGUES_SEED["settings"]:
            conn.execute(
                text("INSERT INTO settings (key, value) VALUES (:key, :value) "
                     "ON CONFLICT (key) DO NOTHING"),
                row,
            )
        for row in _CATALOGUES_SEED["features_votables"]:
            conn.execute(
                text(
                    "INSERT INTO features_votables (code, label, description, categorie, icone, ordre, actif) "
                    "VALUES (:code, :label, :description, :categorie, :icone, :ordre, :actif) "
                    "ON CONFLICT (code) DO NOTHING"
                ),
                row,
            )


# --- Verrou 3 : isolation par test = TRUNCATE, UNIQUEMENT sur aschool_test ---
@pytest.fixture(autouse=True)
def _clean_db():
    _assert_test_engine()      # garde-fou AVANT le test
    _seed_catalogues()         # catalogues de référence re-semés (create_all ne les seed pas)
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
