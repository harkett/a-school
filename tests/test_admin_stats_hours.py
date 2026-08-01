"""GET /admin/stats/hours — les connexions par heure, sur PostgreSQL.

POURQUOI CE TEST EXISTE. La route groupait par `func.strftime('%H', ...)`. `strftime` est une
fonction SQLITE ; PostgreSQL ne l'a pas. La route repondait donc 500 a CHAQUE appel de l'ecran
Serveur (AdminServeur.jsx:61), et aucun test ne la couvrait : le bug a survecu a toute la
bascule vers PostgreSQL. Il a fallu lire le fichier a la main pour le voir.

Ce que ce test PROUVE : la requete s'execute vraiment sur PostgreSQL (une fonction inconnue
leverait), les 24 heures sont toujours rendues, et une connexion enregistree tombe dans SA
tranche horaire.

Lancer : docker exec a-school-backend-1 python -m pytest tests/test_admin_stats_hours.py -q
"""
from datetime import datetime

from fastapi.testclient import TestClient

import backend.core.database as dbmod
from backend.main import app
from backend.core.models_db import ConnexionLog
from backend.systeme.admin import _make_admin_token


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def test_stats_hours_repond_et_rend_les_24_heures():
    r = _admin().get("/api/admin/stats/hours")
    assert r.status_code == 200, r.text          # 500 = la fonction SQL n'existe pas sur PostgreSQL
    data = r.json()
    assert len(data) == 24
    assert [d["hour"] for d in data] == [f"{h:02d}h" for h in range(24)]
    assert all(d["count"] == 0 for d in data)    # base vidée entre chaque test


def test_une_connexion_tombe_dans_sa_tranche_horaire():
    with dbmod.SessionLocal() as db:
        db.add(ConnexionLog(email="prof.stats@aschool.fr", action="login",
                            created_at=datetime(2026, 8, 1, 14, 30, 0)))
        db.add(ConnexionLog(email="prof.stats@aschool.fr", action="login",
                            created_at=datetime(2026, 8, 1, 14, 45, 0)))
        # `logout` ne compte pas : la route ne regarde que les connexions
        db.add(ConnexionLog(email="prof.stats@aschool.fr", action="logout",
                            created_at=datetime(2026, 8, 1, 14, 50, 0)))
        db.commit()

    data = _admin().get("/api/admin/stats/hours").json()
    par_heure = {d["hour"]: d["count"] for d in data}
    assert par_heure["14h"] == 2
    assert sum(par_heure.values()) == 2


def test_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/stats/hours").status_code == 401
