"""Drapeau « visite guidée de l'écran Créer déjà vue » EN BASE (chantier aide du 25/07).

Ce que ces tests PROUVENT :
  1. /auth/me expose guide_creer_vu — False pour un compte neuf (la visite se lancera),
     True après le PUT (plus jamais automatiquement, sur aucun appareil).
  2. PUT /api/user/guide-creer-vu écrit EN BASE, idempotent.
  3. Sans cookie d'auth : 401.

BDD de test PostgreSQL dédiée (aschool_test via conftest.py).
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod
from backend.main import app
from backend.auth import create_access_token
from fastapi.testclient import TestClient

EMAIL = "prof.guide@aschool.fr"
TOKEN = create_access_token(EMAIL)


def _client_avec_prof():
    from backend.core.models_db import User
    with dbmod.SessionLocal() as db:
        db.add(User(email=EMAIL, password_hash="x", is_verified=True,
                    subject="GU-Matiere", niveau="GU-Niv"))
        db.commit()
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def test_me_expose_le_drapeau_puis_put_le_pose_en_base():
    from backend.core.models_db import User
    c = _client_avec_prof()
    # Compte neuf : la visite doit pouvoir se lancer.
    assert c.get("/api/auth/me").json()["guide_creer_vu"] is False
    # Fin de visite (Terminer ou Passer) : le « vu » s'écrit en base.
    r = c.put("/api/user/guide-creer-vu")
    assert r.status_code == 200, r.text
    assert r.json()["guide_creer_vu"] is True
    assert c.get("/api/auth/me").json()["guide_creer_vu"] is True
    with dbmod.SessionLocal() as db:   # la vérité est bien EN BASE
        assert db.query(User).filter(User.email == EMAIL).first().guide_creer_vu is True
    # Idempotent : re-noter un guide déjà vu ne change rien.
    assert c.put("/api/user/guide-creer-vu").status_code == 200


def test_exige_authentification():
    assert TestClient(app).put("/api/user/guide-creer-vu").status_code == 401
