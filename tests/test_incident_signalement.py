"""Signalement PRO — incident technique + rattachement au feedback du prof (Fix 2).

Ce que ces tests PROUVENT (comportement réel sur la base de test) :
  1. creer_incident écrit un incident EN BASE (erreur réelle + contexte technique) et renvoie sa
     référence courte « INC-… » ; feedback_id est NULL tant que le prof n'a pas signalé.
  2. POST /api/feedback avec `incident_ref` → l'incident est RELIÉ (incidents.feedback_id =
     feedbacks.id) : l'admin retrouve, sur ce feedback, ce qui a techniquement planté.
  3. Sans `incident_ref` → aucun incident touché ; le feedback s'enregistre normalement.
  4. `incident_ref` inconnue → le feedback s'enregistre QUAND MÊME (200), rien ne casse (best-effort).
  5. La réf d'incident part dans la notification e-mail de l'admin (`incident_ref=…`).
  6. L'admin VOIT l'incident sur le feedback : GET /api/admin/feedbacks renvoie le bloc `incident`
     (réf + erreur brute + contexte technique) sur le feedback relié.

BDD de test PostgreSQL dédiée (aschool_test via conftest.py), notification e-mail mockée.
"""
from unittest.mock import patch


import backend.core.database as dbmod
from backend.main import app
from backend.securite.comptes import create_access_token
from backend.core.models_db import User, Feedback, Incident
from backend.supervision.incidents import creer_incident
from fastapi.testclient import TestClient

EMAIL = "prof.incident@aschool.fr"
TOKEN = create_access_token(EMAIL)


def _client_avec_prof():
    with dbmod.SessionLocal() as db:
        db.add(User(email=EMAIL, password_hash="x", is_verified=True))
        db.commit()
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def _creer_incident_en_base(**over):
    params = dict(endpoint="/api/generate", error="LLMRateLimitError: Trop de demandes",
                  provider="groq", model="llama-3.3", matiere="Maths", niveau="6e",
                  type_activite="Exercice", consigne="additions", user_email=EMAIL)
    params.update(over)
    ref = creer_incident(**params)
    assert ref and ref.startswith("INC-")
    return ref


def test_creer_incident_ecrit_en_base_et_renvoie_ref():
    ref = _creer_incident_en_base()
    with dbmod.SessionLocal() as db:
        inc = db.query(Incident).filter(Incident.ref == ref).first()
        assert inc is not None
        assert inc.error.startswith("LLMRateLimitError")
        assert inc.endpoint == "/api/generate"
        assert inc.provider == "groq" and inc.matiere == "Maths" and inc.niveau == "6e"
        assert inc.type_activite == "Exercice" and inc.consigne == "additions"
        assert inc.user_email == EMAIL
        assert inc.feedback_id is None   # pas encore signalé par le prof


def test_feedback_avec_ref_relie_l_incident():
    c = _client_avec_prof()
    ref = _creer_incident_en_base()
    with patch("backend.communication.feedback.comptes.send_feedback_notification") as notif:
        r = c.post("/api/feedback", json={"type": "feedback", "message": "Ça a planté chez moi.",
                                          "category": "bug", "incident_ref": ref})
    assert r.status_code == 200, r.text
    # La réf voyage jusqu'à la notification e-mail de l'admin.
    assert notif.call_args.kwargs.get("incident_ref") == ref
    with dbmod.SessionLocal() as db:
        fb = db.query(Feedback).first()
        inc = db.query(Incident).filter(Incident.ref == ref).first()
        assert inc.feedback_id == fb.id   # incident RELIÉ au message du prof


def test_admin_voit_l_incident_sur_le_feedback():
    from backend.systeme.admin import _make_admin_token
    prof = _client_avec_prof()
    ref = _creer_incident_en_base()
    with patch("backend.communication.feedback.comptes.send_feedback_notification"):
        prof.post("/api/feedback", json={"type": "feedback", "message": "Ça a planté chez moi.",
                                         "category": "bug", "incident_ref": ref})
    admin = TestClient(app)
    admin.cookies.set("aschool_admin", _make_admin_token())
    r = admin.get("/api/admin/feedbacks")
    assert r.status_code == 200, r.text
    cible = [x for x in r.json() if x.get("incident") and x["incident"]["ref"] == ref]
    assert cible, "l'incident doit apparaître sur le feedback côté admin"
    inc = cible[0]["incident"]
    assert inc["error"].startswith("LLMRateLimitError")
    assert inc["provider"] == "groq" and inc["type_activite"] == "Exercice"


def test_feedback_sans_ref_n_altere_aucun_incident():
    c = _client_avec_prof()
    ref = _creer_incident_en_base()
    with patch("backend.communication.feedback.comptes.send_feedback_notification"):
        r = c.post("/api/feedback", json={"type": "feedback", "message": "Suggestion diverse.",
                                          "category": "suggestion"})
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        assert db.query(Incident).filter(Incident.ref == ref).first().feedback_id is None


def test_feedback_ref_inconnue_ne_casse_pas():
    c = _client_avec_prof()
    with patch("backend.communication.feedback.comptes.send_feedback_notification"):
        r = c.post("/api/feedback", json={"type": "feedback", "message": "Réf inexistante.",
                                          "category": "bug", "incident_ref": "INC-INEXISTANT"})
    assert r.status_code == 200, r.text   # feedback enregistré malgré la réf inconnue
    with dbmod.SessionLocal() as db:
        assert db.query(Feedback).count() == 1
