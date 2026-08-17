"""Preuve de raccordement — une fonctionnalité livrée quitte « Bientôt disponible »
et s'annonce, si on le décide, dans le bandeau d'accueil du professeur.

Ce que ces tests PROUVENT (base aschool_test via conftest.py — JAMAIS SQLite) :
  1. Cocher « livrée » retire la carte de l'écran prof : on ne fait plus voter pour ce qui
     existe. L'administration, elle, continue de la voir avec ses votes.
  2. GET /api/nouveautes ne renvoie QUE les lignes livrées ET annoncées : les deux cases,
     jamais une seule.
  3. Le serveur tient la règle des deux cases, pas seulement l'écran : demander
     « nouveauté » sans « livrée » n'annonce rien.
  4. Décocher « livrée » éteint « nouveauté » du même geste.
  5. Une fonctionnalité livrée n'est plus votable : le vote est refusé par un 400 humain.

Lancer : docker compose exec backend python -m pytest tests/test_nouveaute_dans_le_bandeau.py -q
"""

from sqlalchemy import text

import backend.core.database as dbmod
from backend.securite.comptes import create_access_token
from backend.core.models_db import User
from backend.systeme.admin import _make_admin_token
from backend.main import app
from fastapi.testclient import TestClient

EMAIL = "prof.nouveautes@aschool.fr"
TOKEN = create_access_token(EMAIL)


def _client_prof():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def _client_admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _make_user(db, email=EMAIL):
    if db.query(User).filter(User.email == email).first():
        return
    db.add(User(email=email, password_hash="x"))
    db.commit()


def _etat(code, livree, nouveaute):
    """Écrit les deux cases directement en base — l'écran d'administration passe, lui, par
    PATCH ; les tests qui visent la règle serveur utilisent la route, pas ce raccourci."""
    with dbmod.SessionLocal() as db:
        db.execute(text("UPDATE features_votables SET livree = :l, nouveaute = :n WHERE code = :c"),
                   {"l": livree, "n": nouveaute, "c": code})
        db.commit()


def test_une_carte_livree_quitte_l_ecran_prof_mais_reste_a_l_admin():
    with dbmod.SessionLocal() as db:
        _make_user(db)
    avant = _client_prof().get("/api/feature-votes").json()
    assert "quiz-interactif" in [f["key"] for f in avant["features"]]

    _etat("quiz-interactif", True, False)

    apres = _client_prof().get("/api/feature-votes").json()
    assert "quiz-interactif" not in [f["key"] for f in apres["features"]]

    vu_admin = _client_admin().get("/api/admin/feature-votes").json()
    ligne = [f for f in vu_admin if f["key"] == "quiz-interactif"]
    assert ligne and ligne[0]["livree"] is True


def test_les_nouveautes_exigent_les_deux_cases():
    with dbmod.SessionLocal() as db:
        _make_user(db)
    c = _client_prof()

    _etat("quiz-interactif", False, False)
    assert c.get("/api/nouveautes").json() == []

    # Livrée seule : elle a quitté « Bientôt disponible », mais rien ne s'annonce.
    _etat("quiz-interactif", True, False)
    assert c.get("/api/nouveautes").json() == []

    _etat("quiz-interactif", True, True)
    annonces = c.get("/api/nouveautes").json()
    assert [n["key"] for n in annonces] == ["quiz-interactif"]
    assert annonces[0]["label"] and annonces[0]["description"]


def test_le_serveur_refuse_une_nouveaute_non_livree():
    a = _client_admin()
    r = a.patch("/api/admin/feature-votes/quiz-interactif",
                json={"livree": False, "nouveaute": True})
    assert r.status_code == 200, r.text
    # La case suit la règle, même demandée directement au serveur.
    assert r.json() == {"key": "quiz-interactif", "livree": False, "nouveaute": False}


def test_decocher_livree_eteint_la_nouveaute():
    a = _client_admin()
    a.patch("/api/admin/feature-votes/quiz-interactif", json={"livree": True, "nouveaute": True})
    r = a.patch("/api/admin/feature-votes/quiz-interactif", json={"livree": False, "nouveaute": True})
    assert r.json()["nouveaute"] is False


def test_on_ne_vote_plus_pour_ce_qui_est_livre():
    with dbmod.SessionLocal() as db:
        _make_user(db)
    _etat("quiz-interactif", True, False)
    r = _client_prof().post("/api/feature-vote", json={"feature_key": "quiz-interactif"})
    assert r.status_code == 400
    assert "plus" in r.json()["detail"]
