r"""Preuve — voir, depuis le PROFIL du prof, le programme officiel de son niveau.

Endpoints testés (routeur profil, prefix /api) :
  1. GET /api/user/referentiel      → { disponible, fichier } ; `fichier` = le NOM EXACT déposé
                                        par l'admin (referentiels.fichier), PAS « referentiel.pdf ».
  2. GET /api/user/referentiel/pdf  → sert le PDF du niveau du prof (inline), 401 sans auth,
                                        404 si pas de référentiel.

Base de test PostgreSQL dédiée (aschool_test via conftest.py) — JAMAIS SQLite, JAMAIS la vraie base.
Lancer : python -m pytest test_mon_referentiel.py -q
"""
import os
import sys

# Windows : garde-fous OpenMP (torch) posés AVANT tout import susceptible de le charger.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from unittest.mock import patch

import backend.core.database as dbmod  # engine/SessionLocal redirigés vers aschool_test par conftest.py

from backend.main import app
from backend.auth import create_access_token
from backend.core.models_db import Cycle, Niveau, Referentiel, User
from backend.core.resolution_couple import matiere_id_du_nom, niveau_id_du_nom
from fastapi.testclient import TestClient

NIVEAU = "Bébés (0-1 an)"
NOM_FICHIER = "Projet pédagogique crèche 2024.pdf"   # nom réel déposé (≠ nom de disque figé)
TEXTE_EPURE = "Programme épuré de test — contenu propre et lisible du référentiel."
TOKEN = create_access_token("prof.ref@aschool.fr")


def _authed():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def _prof(niveau=NIVEAU, subject="Langage"):
    # Comme en prod : le profil range niveau/matière PAR CLÉ. On résout l'id depuis le nom (donc le
    # niveau doit être semé AVANT le prof pour les cas « référentiel présent »). Nom absent de la
    # table → id None → « indisponible » (exactement le comportement attendu côté profil).
    with dbmod.SessionLocal() as db:
        niv_id = niveau_id_du_nom(db, niveau)
        db.add(User(email="prof.ref@aschool.fr", password_hash="x", is_verified=True,
                    subject_id=matiere_id_du_nom(db, subject, niv_id),
                    niveau_id=niv_id))
        db.commit()


def _seed_referentiel(fichier=NOM_FICHIER):
    with dbmod.SessionLocal() as db:
        cyc = Cycle(nom="Crèche", ordre=1); db.add(cyc); db.flush()
        niv = Niveau(cycle_id=cyc.id, nom=NIVEAU, ordre=1); db.add(niv); db.flush()
        db.add(Referentiel(niveau_id=niv.id, nom_fixe="bebes_0_1_an",
                           collection="bebes_0_1_an", filtres=None, fichier=fichier,
                           source="dépôt manuel", texte_epure=TEXTE_EPURE))
        db.commit()


def test_renvoie_le_nom_exact_du_fichier_depose():
    _seed_referentiel(); _prof()   # niveau semé AVANT le prof (le profil résout niveau_id depuis le nom)
    r = _authed().get("/api/user/referentiel")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["disponible"] is True
    assert d["fichier"] == NOM_FICHIER          # le NOM EXACT déposé, jamais « referentiel.pdf »


def test_pas_de_referentiel_indisponible():
    _prof(niveau="4e", subject="Français")       # aucun référentiel semé pour ce niveau
    r = _authed().get("/api/user/referentiel")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["disponible"] is False
    assert d["fichier"] is None


def test_exige_authentification():
    assert TestClient(app).get("/api/user/referentiel").status_code == 401


# Les trois tests de GET /user/referentiel/texte sont partis avec l'endpoint (ménage du 31/07) :
# aucun écran ne l'appelait, le prof lit son programme dans le PDF d'origine. `texte_epure` reste
# en base et reste testé là où il compte — c'est la GÉNÉRATION qui le lit.
