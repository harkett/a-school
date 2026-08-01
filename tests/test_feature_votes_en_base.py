"""Preuve de raccordement — fonctionnalités votables EN BASE (table features_votables).

Ce que ces tests PROUVENT (base aschool_test via conftest.py — JAMAIS SQLite) :
  1. L'écran reçoit le catalogue DU SERVEUR, lu EN BASE (plus aucune liste en dur) :
     GET /feature-votes renvoie les cartes actives, dans l'ordre, avec compteurs.
  2. Une carte inactive quitte l'écran prof MAIS reste comptée côté admin.
  3. Voter un code inconnu ou retiré → 400 humain — fini le vote fantôme accepté à
     l'écran et refusé en silence par le serveur.
  4. Le vote est un bascule : premier POST = voté, second POST = retiré, compteur juste.
  5. La FK feature_votes.feature_key -> features_votables.code fait de la BASE l'autorité.
  6. Table vide = erreur claire (migration non appliquée), jamais un repli en dur.

Le catalogue est semé par conftest (_seed_catalogues) — en prod il l'est par migration.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import backend.core.database as dbmod
from backend.securite.comptes import create_access_token
from backend.core.models_db import FeatureVote, User
from backend.main import app
from fastapi.testclient import TestClient

EMAIL = "prof.votes@aschool.fr"
TOKEN = create_access_token(EMAIL)


def _client_prof():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def _make_user(db, email=EMAIL) -> int:
    u = User(email=email, password_hash="x")
    db.add(u); db.flush()
    uid = u.id
    db.commit()
    return uid


def test_ecran_recoit_le_catalogue_en_base_actives_seulement():
    with dbmod.SessionLocal() as db:
        _make_user(db)
    r = _client_prof().get("/api/feature-votes")
    assert r.status_code == 200, r.text
    data = r.json()
    # Les cartes actives, dans l'ordre du catalogue — la carte retirée n'apparaît pas.
    assert [f["key"] for f in data["features"]] == ["analyser-consigne", "quiz-interactif"]
    f = data["features"][0]
    assert f["label"] == "Analyser une consigne"
    assert f["categorie"] == "Outils pédagogiques"
    assert f["icone"] == "loupe"
    assert f["count"] == 0
    assert data["mes_votes"] == []


def test_vote_bascule_et_compteur_juste():
    with dbmod.SessionLocal() as db:
        _make_user(db)
    c = _client_prof()
    r1 = c.post("/api/feature-vote", json={"feature_key": "quiz-interactif"})
    assert r1.status_code == 200, r1.text
    assert r1.json() == {"voted": True, "count": 1}
    # L'écran relit le serveur : le vote est là.
    releve = c.get("/api/feature-votes").json()
    assert releve["mes_votes"] == ["quiz-interactif"]
    assert [f["count"] for f in releve["features"] if f["key"] == "quiz-interactif"] == [1]
    # Second clic = retrait.
    r2 = c.post("/api/feature-vote", json={"feature_key": "quiz-interactif"})
    assert r2.json() == {"voted": False, "count": 0}


def test_code_inconnu_ou_retire_400_humain():
    with dbmod.SessionLocal() as db:
        _make_user(db)
    c = _client_prof()
    for cle in ("ambiguites-cognitives", "outil-retire"):
        r = c.post("/api/feature-vote", json={"feature_key": cle})
        assert r.status_code == 400, r.text
        assert r.json()["detail"] == "Cette fonctionnalité n'est pas (ou plus) ouverte au vote."


def test_admin_voit_aussi_les_votes_d_une_carte_retiree():
    # Un vote posé du temps où la carte était active reste compté après son retrait.
    with dbmod.SessionLocal() as db:
        uid = _make_user(db)
        db.add(FeatureVote(user_id=uid, feature_key="outil-retire"))
        db.commit()
    from backend.communication.votes import catalogue_features
    with dbmod.SessionLocal() as db:
        assert [f.code for f in catalogue_features(db)] == ["analyser-consigne", "quiz-interactif"]
        tous = catalogue_features(db, actives_seulement=False)
        assert "outil-retire" in [f.code for f in tous]


def test_fk_refuse_un_code_inconnu():
    db = dbmod.SessionLocal()
    try:
        uid = _make_user(db)
        db.add(FeatureVote(user_id=uid, feature_key="zzz_inconnu"))
        with pytest.raises(IntegrityError):
            db.commit()   # la FK doit refuser : la base est l'autorité
    finally:
        db.rollback()
        db.close()


def test_catalogue_vide_erreur_claire_jamais_de_repli():
    with dbmod.SessionLocal() as db:
        _make_user(db)
        db.execute(text("DELETE FROM feature_votes"))
        db.execute(text("DELETE FROM features_votables"))
        db.commit()
    r = _client_prof().get("/api/feature-votes")
    assert r.status_code == 500, r.text
    assert r.json()["detail"] == "Fonctionnalités votables absentes en base (migration non appliquée ?)."
