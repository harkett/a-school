"""Preuve — PATCH /user/profile porte le contrôle métier SERVEUR (paire au programme).

Ce que ces tests PROUVENT (base aschool_test via conftest.py — JAMAIS SQLite) :
  1. Une paire (matière, niveau) ABSENTE du programme officiel (matiere_niveaux) est refusée
     en 400 humain et RIEN n'est écrit — le front seul ne suffit plus (trou du check-up 30/07).
  2. Une paire au programme s'écrit par clés (subject_id / niveau_id), comme avant.
  3. Un profil encore incomplet (matière seule, niveau vide) reste enregistrable : l'état
     « profil incomplet » est légitime, c'est le flux profilIncomplet de l'écran qui le gère.

Même règle et même message que PUT /user/couple-travail (_couple_est_au_programme).
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import backend.core.database as dbmod
from backend.auth import create_access_token
from backend.core.models_db import Cycle, Matiere, MatiereNiveau, Niveau, User
from backend.main import app
from fastapi.testclient import TestClient

EMAIL = "prof.programme@aschool.fr"


def _client():
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(EMAIL))
    return c


def _semer():
    """Cycle + niveau PP-6e + PP-Fr AU programme (paire matiere_niveaux) et PP-HG HORS
    programme (matière existante mais aucune paire avec PP-6e) + le prof sans profil."""
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom="PP-College", ordre=90)
        db.add(cy); db.flush()
        n6 = Niveau(cycle_id=cy.id, nom="PP-6e", ordre=1)
        db.add(n6); db.flush()
        mfr = Matiere(nom="PP-Fr", ordre=901)
        mhg = Matiere(nom="PP-HG", ordre=902)
        db.add_all([mfr, mhg]); db.flush()
        db.add(MatiereNiveau(matiere_id=mfr.id, niveau_id=n6.id))
        db.add(User(email=EMAIL, password_hash="x", is_verified=True))
        db.commit()
        return mfr.id, n6.id


def test_paire_hors_programme_400_et_rien_ecrit():
    _semer()
    r = _client().patch("/api/user/profile", json={"prenom": "Ana", "subject": "PP-HG", "niveau": "PP-6e"})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Cette matière n'est pas enseignée à ce niveau dans les programmes. Choisissez une matière proposée pour ce niveau."
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        assert u.subject_id is None and u.niveau_id is None and u.prenom is None


def test_paire_au_programme_ecrite_par_cles():
    mfr_id, n6_id = _semer()
    r = _client().patch("/api/user/profile", json={"subject": "PP-Fr", "niveau": "PP-6e"})
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        assert u.subject_id == mfr_id and u.niveau_id == n6_id


def test_profil_incomplet_matiere_seule_acceptee():
    mfr_id, _n6_id = _semer()
    r = _client().patch("/api/user/profile", json={"subject": "PP-Fr", "niveau": ""})
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        assert u.subject_id == mfr_id and u.niveau_id is None
