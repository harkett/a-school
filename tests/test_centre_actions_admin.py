"""Preuve de raccordement — le centre d'actions de l'administration.

Ce que ces tests PROUVENT (base aschool_test via conftest.py — JAMAIS SQLite) :
  1. Une fonctionnalité livrée mais pas encore annoncée remonte comme ACTION À FAIRE, avec la
     phrase du geste attendu et l'écran où le faire.
  2. L'action DISPARAÎT dès que le geste est fait (case « Nouveauté » cochée) : rien ne se
     marque à la main, donc rien ne reste allumé par oubli.
  3. Ce qui n'est pas livré ne produit aucune action : on n'annonce pas ce qui n'existe pas.
  4. La route sert UNE SEULE source à l'encart et à la pastille : `total` et `par_ecran`
     comptent les mêmes lignes que la liste.
  5. La route est fermée sans cookie admin.

Lancer : docker compose exec backend python -m pytest tests/test_centre_actions_admin.py -q
"""

from sqlalchemy import text

import backend.core.database as dbmod
from backend.systeme.admin import _make_admin_token
from backend.main import app
from fastapi.testclient import TestClient


def _client_admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _etat(code, livree, nouveaute):
    with dbmod.SessionLocal() as db:
        db.execute(text("UPDATE features_votables SET livree = :l, nouveaute = :n WHERE code = :c"),
                   {"l": livree, "n": nouveaute, "c": code})
        db.commit()


def _rien_d_annonce():
    with dbmod.SessionLocal() as db:
        db.execute(text("UPDATE features_votables SET livree = false, nouveaute = false"))
        db.commit()


def test_une_livraison_non_annoncee_remonte_comme_action():
    _rien_d_annonce()
    _etat("quiz-interactif", True, False)

    data = _client_admin().get("/api/admin/actions").json()
    actions = data["actions"]

    assert [a["code"] for a in actions] == ["annonce:quiz-interactif"]
    # La ligne dit le GESTE attendu, pas l'état constaté, et mène là où il se fait.
    assert "annoncer" in actions[0]["titre"]
    assert actions[0]["page"] == "/admin/bientot-disponible"
    assert actions[0]["ecran"] == "bientot-disponible"


def test_l_action_s_efface_quand_le_geste_est_fait():
    _rien_d_annonce()
    _etat("quiz-interactif", True, False)
    a = _client_admin()
    assert a.get("/api/admin/actions").json()["total"] == 1

    a.patch("/api/admin/feature-votes/quiz-interactif", json={"livree": True, "nouveaute": True})

    assert a.get("/api/admin/actions").json()["total"] == 0


def test_ce_qui_n_est_pas_livre_ne_demande_rien():
    _rien_d_annonce()
    assert _client_admin().get("/api/admin/actions").json() == {
        "total": 0, "actions": [], "par_ecran": {},
    }


def test_l_encart_et_la_pastille_comptent_la_meme_chose():
    _rien_d_annonce()
    _etat("quiz-interactif", True, False)
    _etat("analyser-consigne", True, False)

    data = _client_admin().get("/api/admin/actions").json()
    assert data["total"] == len(data["actions"]) == 2
    assert data["par_ecran"] == {"bientot-disponible": 2}


def test_route_fermee_sans_cookie_admin():
    assert TestClient(app).get("/api/admin/actions").status_code == 401
