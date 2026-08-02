"""Contexte du feedback EN BASE (colonne feedbacks.contexte, chantier du 25/07).

Ce que ces tests PROUVENT :
  1. POST /api/feedback avec `contexte` (« Écran Créer une activité · … ») → la ligne
     enregistrée le porte, et /api/feedback/mes-feedbacks le renvoie.
  2. Le contexte est un fait d'ÉVÉNEMENT figé à l'envoi : la MODIFICATION du feedback
     (PATCH) ne l'efface ni ne le change.
  3. Sans contexte (anciens clients, autres appels) → NULL, rien ne casse.

BDD de test PostgreSQL dédiée (aschool_test via conftest.py), notification e-mail mockée.

Lancer : docker compose exec backend python -m pytest tests/test_feedback_contexte.py -q
"""
from unittest.mock import patch


import backend.core.database as dbmod
from backend.main import app
from backend.securite.comptes import create_access_token
from fastapi.testclient import TestClient

EMAIL = "prof.ctx@aschool.fr"
TOKEN = create_access_token(EMAIL)
CTX = "Écran Créer une activité · CT-Fr × CT-6e"


def _client_avec_prof():
    from backend.core.models_db import User
    with dbmod.SessionLocal() as db:
        db.add(User(email=EMAIL, password_hash="x", is_verified=True))
        db.commit()
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def test_contexte_stocke_renvoye_et_fige_a_l_edition():
    from backend.core.models_db import Feedback
    c = _client_avec_prof()
    with patch("backend.communication.feedback.comptes.send_feedback_notification"):
        r = c.post("/api/feedback", json={"type": "feedback", "message": "Le bouton ne répond pas.",
                                          "category": "bug", "contexte": CTX})
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:      # la vérité est EN BASE
        fb = db.query(Feedback).first()
        assert fb.contexte == CTX
        fid = fb.id
    rows = c.get("/api/feedback/mes-feedbacks").json()
    assert rows[0]["contexte"] == CTX     # renvoyé au prof (Mes feedbacks)
    # L'édition du message NE TOUCHE PAS le contexte (fait d'événement figé à l'envoi).
    with patch("backend.communication.feedback.comptes.send_feedback_update_notification"):
        r = c.patch(f"/api/feedback/{fid}", json={"message": "Précision : sur le bouton Générer."})
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        assert db.query(Feedback).filter(Feedback.id == fid).first().contexte == CTX


def test_sans_contexte_null_et_rien_ne_casse():
    from backend.core.models_db import Feedback
    c = _client_avec_prof()
    with patch("backend.communication.feedback.comptes.send_feedback_notification"):
        r = c.post("/api/feedback", json={"type": "feedback", "message": "Sans contexte.",
                                          "category": "question"})
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        assert db.query(Feedback).first().contexte is None
    assert c.get("/api/feedback/mes-feedbacks").json()[0]["contexte"] is None
