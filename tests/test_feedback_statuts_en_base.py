"""Preuve de raccordement — statuts de feedback EN BASE (table feedback_statuts).

Ce que le test PROUVE (base aschool_test via conftest.py — JAMAIS SQLite) :
  1. Les helpers lisent les codes EN BASE (plus aucune liste en dur).
     - assignables  = toutes les lignes du catalogue.
     - modifiables  = lignes modifiable=true (notion SOURCE, distincte des assignables).
  2. La FK feedbacks.statut -> feedback_statuts.code fait de la BASE l'autorité :
     un statut inconnu est refusé par la base, pas seulement par le code.
  3. Un feedback dans un statut non-modifiable ('traite') n'est pas éditable.
  4. L'ÉCRAN PROF reçoit le libellé (`statut_label`) et le droit de modifier (`modifiable`)
     DU SERVEUR, lus en base — la copie STATUTS/STATUTS_MODIFIABLES du front est supprimée.

Le catalogue est semé par conftest (_seed_catalogues) — en prod il l'est par migration.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import pytest
from sqlalchemy.exc import IntegrityError

import backend.core.database as dbmod
from backend.auth import create_access_token
from backend.core.models_db import Feedback, User
from backend.main import app
from backend.systeme.admin import codes_statuts_assignables, codes_statuts_modifiables, labels_statuts
from fastapi.testclient import TestClient


def _make_user(db) -> int:
    u = User(email="prof@test.fr", password_hash="x")
    db.add(u); db.flush()
    uid = u.id
    db.commit()
    return uid


def test_helpers_lisent_les_codes_en_base():
    db = dbmod.SessionLocal()
    try:
        assert codes_statuts_assignables(db) == {"nouveau", "en_cours", "traite", "archive"}
        assert codes_statuts_modifiables(db) == {"nouveau", "en_cours"}
    finally:
        db.close()


def test_fk_refuse_un_statut_inconnu():
    db = dbmod.SessionLocal()
    try:
        uid = _make_user(db)
        db.add(Feedback(user_id=uid, message="m", statut="zzz_inconnu"))
        with pytest.raises(IntegrityError):
            db.commit()   # la FK doit refuser : la base est l'autorité
    finally:
        db.rollback()
        db.close()


def test_feedback_traite_non_modifiable():
    db = dbmod.SessionLocal()
    try:
        assert "traite" not in codes_statuts_modifiables(db)
        assert "nouveau" in codes_statuts_modifiables(db)
    finally:
        db.close()


def test_ecran_prof_recoit_label_et_modifiable_du_serveur():
    email = "prof.statuts@aschool.fr"
    with dbmod.SessionLocal() as db:
        u = User(email=email, password_hash="x")
        db.add(u); db.flush()
        db.add(Feedback(user_id=u.id, message="ouvert", statut="nouveau"))
        db.add(Feedback(user_id=u.id, message="clos", statut="traite"))
        db.commit()
        assert labels_statuts(db)["traite"] == "Traité"

    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(email))
    r = c.get("/api/feedback/mes-feedbacks")
    assert r.status_code == 200, r.text
    par_message = {fb["message"]: fb for fb in r.json()}
    # Le libellé affiché et le droit de modifier viennent de la base, par retour.
    assert par_message["ouvert"]["statut_label"] == "Nouveau"
    assert par_message["ouvert"]["modifiable"] is True
    assert par_message["clos"]["statut_label"] == "Traité"
    assert par_message["clos"]["modifiable"] is False
