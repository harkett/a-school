"""Brique 2 « Mes contenus » — la séance en base, sous son vrai nom.

Vérifié ici :
  - le parser de phases (backend/sequence/phases.py) : découpe « ## Phase N — Nom (X min) »,
    tolère un tiret simple et une durée absente, renumérote dans l'ordre du texte,
    et rend [] sur un texte sans phases (le resultat complet reste la source d'affichage) ;
  - la génération écrit la séance + ses phases dans les tables « Mes contenus » et n'écrit
    PLUS dans sequences_sauvegardees (fin du doublon) — mode remédiation compris ;
  - DELETE /api/seances/{id} : auth, cloisonnement entre profs, CASCADE sur les phases ;
  - /api/dashboard : la « dernière séquence » de l'Accueil vient de `seances`, avec les
    clés historiques du Recharger (theme, duree, mode, description_classe).

Lance avec : pytest (BDD jetable aschool_test via conftest.py — jamais la base dev).
"""
import os
import sys
from unittest.mock import patch

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod  # noqa: E402

from backend.main import app  # noqa: E402
from backend.auth import create_access_token  # noqa: E402
from backend.sequence.phases import decouper_phases  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

EMAIL = "seances@local.test"

SEQ_MD = (
    "# Séance : Photosynthèse\n"
    "**Matière :** SVT | **Niveau :** 3e | **Durée :** 55 min\n\n"
    "---\n\n"
    "## Phase 1 — Activation (10 min)\n"
    "**Objectif :** réveiller les acquis\n\n"
    "## Phase 2 - Exploration (45 min)\n"
    "**Objectif :** découvrir\n**Déroulement :** manipulation\n\n"
    "---\n\n"
    "> *Séance générée par aSchool*\n"
)


def _client(email=EMAIL):
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(email))
    return c


def _uid(email=EMAIL):
    from backend.core.models_db import User
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            u = User(email=email, password_hash="x", is_verified=True)
            db.add(u)
            db.commit()
            db.refresh(u)
        return u.id


# ===================== Parser de phases =====================

def test_parser_decoupe_les_phases():
    phases = decouper_phases(SEQ_MD)
    assert [p["titre"] for p in phases] == ["Activation", "Exploration"]
    assert [p["duree_minutes"] for p in phases] == [10, 45]
    assert phases[0]["position"] == 1 and phases[1]["position"] == 2
    assert "réveiller les acquis" in phases[0]["contenu"]
    assert "manipulation" in phases[1]["contenu"]


def test_parser_renumerote_dans_l_ordre_du_texte():
    texte = "## Phase 3 — Fin (5 min)\nx\n## Phase 1 — Début\ny\n"
    phases = decouper_phases(texte)
    assert [p["position"] for p in phases] == [1, 2]
    assert [p["titre"] for p in phases] == ["Fin", "Début"]
    assert phases[1]["duree_minutes"] is None   # durée absente tolérée


def test_parser_texte_sans_phases():
    assert decouper_phases("Un simple paragraphe.\nSans structure.") == []
    assert decouper_phases("") == []


# ===================== Génération → seances (fin du doublon) =====================

def test_generation_remediation_ecrit_la_seance_et_plus_l_ancienne_table():
    from backend.core.models_db import Seance, SeancePhase, SequenceSauvegardee
    _uid()
    with patch("backend.sequence.sequence.generate", return_value=SEQ_MD):
        r = _client().post("/api/generate-sequence", json={
            "theme": "Photosynthèse", "matiere": "SVT", "niveau": "3e", "duree": 55,
            "mode": "remediation", "description_classe": "Classe fatiguée, fans de jeux vidéo."})
    assert r.status_code == 200, r.text
    seance_id = r.json()["seance_id"]

    with dbmod.SessionLocal() as db:
        s = db.query(Seance).filter(Seance.id == seance_id).one()
        assert s.mode == "remediation"
        assert s.description == "Classe fatiguée, fans de jeux vidéo."
        assert s.duree_minutes == 55
        assert db.query(SeancePhase).filter(SeancePhase.seance_id == seance_id).count() == 2
        # Fin du doublon : plus AUCUNE écriture dans l'ancienne table à la génération.
        assert db.query(SequenceSauvegardee).count() == 0


# ===================== DELETE /api/seances/{id} =====================

def test_suppression_seance_auth_cloisonnement_et_cascade():
    from backend.core.models_db import Seance, SeancePhase
    uid = _uid()
    with dbmod.SessionLocal() as db:
        s = Seance(user_id=uid, titre="À supprimer")
        db.add(s)
        db.flush()
        db.add(SeancePhase(seance_id=s.id, position=1, titre="Unique"))
        db.commit()
        sid = s.id

    assert TestClient(app).delete(f"/api/seances/{sid}").status_code == 401       # sans cookie
    _uid("intrus@local.test")
    assert _client("intrus@local.test").delete(f"/api/seances/{sid}").status_code == 404  # pas à lui

    assert _client().delete(f"/api/seances/{sid}").status_code == 200
    with dbmod.SessionLocal() as db:
        assert db.query(Seance).filter(Seance.id == sid).count() == 0
        assert db.query(SeancePhase).filter(SeancePhase.seance_id == sid).count() == 0  # CASCADE


# ===================== Dashboard (Accueil → Recharger) =====================

def test_dashboard_derniere_sequence_vient_des_seances():
    from backend.core.models_db import Seance
    uid = _uid()
    with dbmod.SessionLocal() as db:
        db.add(Seance(user_id=uid, titre="La Révolution", matiere="Histoire", niveau="4e",
                      duree_minutes=45, mode="standard", description="", resultat="# Séance"))
        db.commit()
    d = _client().get("/api/dashboard").json()
    seq = d["derniere_sequence"]
    assert seq["theme"] == "La Révolution"      # clés historiques du « Recharger »
    assert seq["duree"] == 45
    assert seq["mode"] == "standard"
    assert seq["description_classe"] == ""
