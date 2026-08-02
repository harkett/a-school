"""Preuve — Mes stats (prof) comptées sur le monde NEUF + minutes gagnées EN BASE.

Ce que ces tests PROUVENT (base aschool_test via conftest.py — JAMAIS SQLite) :
  1. /stats/perso : activités / séances / séquences comptées sur les tables NEUVES
     (décision 30/07 : l'ancien monde a disparu, tables droppées).
  2. heures_gagnees : les minutes par activité sont lues EN BASE
     (`stats_minutes_par_activite`, surchargeable à chaud) — plus de « 15 » en dur.
  3. /stats/communaute : total d'activités = monde neuf ; `partages_total` a disparu
     (le partage n'existe pas encore dans le monde neuf — pas de faux zéro).

Lancer : docker compose exec backend python -m pytest tests/test_stats_prof_monde_neuf.py -q
"""


import backend.core.database as dbmod
from backend.securite.comptes import create_access_token
from backend.core.models_db import Activite, ActiviteType, Seance, Sequence, Setting, User
from backend.main import app
from fastapi.testclient import TestClient

EMAIL = "prof.stats@aschool.fr"


def _client():
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(EMAIL))
    return c


def _semer():
    """Le prof + 4 activités NEUVES (3 « Compréhension », 1 « Dictée »), 1 séance, 1 séquence."""
    with dbmod.SessionLocal() as db:
        u = User(email=EMAIL, password_hash="x", is_verified=True)
        db.add(u); db.flush()
        t = ActiviteType(label="SP-Compréhension")
        db.add(t); db.flush()
        for label in ("Compréhension", "Compréhension", "Compréhension", "Dictée"):
            db.add(Activite(user_id=u.id, activite_type_id=t.id, activite_label=label,
                            matiere="SVT", niveau="3e", texte_source="t", resultat="r"))
        db.add(Seance(user_id=u.id, titre="Séance neuve"))
        db.add(Sequence(user_id=u.id, titre="Séquence neuve"))
        db.commit()


def test_perso_compte_le_monde_neuf():
    _semer()
    d = _client().get("/api/stats/perso").json()
    assert d["activites_total"] == 4
    assert d["seances"] == 1
    assert d["sequences"] == 1
    assert d["type_favori"] == "Compréhension"
    assert d["score_adaptation"] == 100       # 3 exemples du même type
    assert d["heures_gagnees"] == 1           # 4 × 15 min (défaut en base) = 60 min


def test_minutes_par_activite_lues_en_base():
    _semer()
    with dbmod.SessionLocal() as db:
        db.add(Setting(key="stats_minutes_par_activite", value="30"))
        db.commit()
    d = _client().get("/api/stats/perso").json()
    assert d["heures_gagnees"] == 2           # 4 × 30 min = 120 min — la base a parlé


def test_communaute_monde_neuf_et_sans_partages():
    _semer()
    d = _client().get("/api/stats/communaute").json()
    assert d["activites_total"] == 4          # monde neuf uniquement
    assert "partages_total" not in d          # le partage neuf n'existe pas : pas de faux zéro
