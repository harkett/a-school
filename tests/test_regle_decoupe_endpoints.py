r"""Preuve de raccordement — points 1 a 4 : la regle de decoupe (objet a deux faces) est lue et
son STATUT est valide/rejete par l'admin, via 3 endpoints. La regle vit EN BASE, portee par la
ligne `referentiels` du COUPLE (colonnes regle_explication / regle_motif / regle_depose_par /
regle_valide) — resolue par cycle + niveau, jamais partagee au niveau du cycle.

Ce que ce test PROUVE (chaine reelle, TestClient + base aschool_test) :
  1. GET /admin/referentiels/regle-decoupe?cycle_id=&niveau= renvoie les deux faces + depose_par + valide.
  2. GET sur un couple sans regle -> { existe: false } (l'ecran n'affiche pas la carte).
  3. POST .../valider met regle_valide=true EN BASE, en PRESERVANT les deux faces.
  4. POST .../rejeter remet regle_valide=false.
  5. valider sur un couple sans regle -> 404 (jamais de statut fantome).
  6. Cycle inconnu -> 404. Sans cookie admin -> 401.

Isolation : la base est TRUNCATee entre tests (conftest) ; chaque test seme sa ligne referentiels.

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_regle_decoupe_endpoints.py -q
"""
import os
import sys
from urllib.parse import quote

# Windows : garde-fous OpenMP AVANT tout import torch (via backend.main).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod              # redirige vers aschool_test (conftest)
from backend.core.models_db import Cycle, Niveau, Referentiel
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

MOTIF = r"^\s*-?\s*Âge\s*:\s*(.+)$"   # meme motif que la fiche creche
CLAIR = "Une unite = une activite. Elle commence a chaque ligne qui indique un age."
NIVEAU = "Bébés (0-1 an)"             # couple = cycle + niveau
COLLECTION = "bebes_0_1_an"


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _make_cycle(nom="Crèche"):
    db = dbmod.SessionLocal()
    cy = Cycle(nom=nom, ordre=1)
    db.add(cy); db.commit()
    cid = cy.id
    db.close()
    return cid


def _seed_regle(cycle_nom="Crèche", niveau=NIVEAU, valide=False):
    """Crée cycle + niveau + référentiel du couple, et pose la règle EN BASE (colonnes regle_*).
    Renvoie le cycle_id."""
    db = dbmod.SessionLocal()
    cy = Cycle(nom=cycle_nom, ordre=1); db.add(cy); db.flush()
    niv = Niveau(cycle_id=cy.id, nom=niveau, ordre=1); db.add(niv); db.flush()
    db.add(Referentiel(
        niveau_id=niv.id, matiere_id=None, nom_fixe=COLLECTION, collection=COLLECTION,
        filtres=None, fichier="referentiel.pdf",
        regle_explication=CLAIR, regle_motif=MOTIF, regle_depose_par="dev", regle_valide=valide,
    ))
    db.commit()
    cid = cy.id
    db.close()
    return cid


def _regle_en_base():
    """Relit la règle du référentiel crèche EN BASE (pour vérifier ce que le POST a écrit)."""
    db = dbmod.SessionLocal()
    try:
        r = db.query(Referentiel).filter(Referentiel.collection == COLLECTION).first()
        return None if r is None else {
            "valide": bool(r.regle_valide), "explication": r.regle_explication,
            "motif": r.regle_motif, "depose_par": r.regle_depose_par,
        }
    finally:
        db.close()


def test_lire_regle_existe():
    cid = _seed_regle(valide=False)
    r = _admin().get(f"/api/admin/referentiels/regle-decoupe?cycle_id={cid}&niveau={quote(NIVEAU)}")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["existe"] is True
    assert d["explication_clair"] == CLAIR
    assert d["critere_technique"] == MOTIF
    assert d["depose_par"] == "dev"
    assert d["valide"] is False


def test_lire_regle_absente():
    cid = _make_cycle("Crèche")   # cycle seul : aucun référentiel/règle pour ce couple
    r = _admin().get(f"/api/admin/referentiels/regle-decoupe?cycle_id={cid}&niveau={quote(NIVEAU)}")
    assert r.status_code == 200, r.text
    assert r.json() == {"existe": False}


def test_valider_met_valide_true_et_preserve_les_faces():
    cid = _seed_regle(valide=False)
    r = _admin().post("/api/admin/referentiels/regle-decoupe/valider",
                      json={"cycle_id": cid, "niveau": NIVEAU})
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "valide": True}
    # Base : valide=true ET les deux faces intactes.
    base = _regle_en_base()
    assert base["valide"] is True
    assert base["explication"] == CLAIR
    assert base["motif"] == MOTIF
    assert base["depose_par"] == "dev"
    # GET confirme.
    g = _admin().get(f"/api/admin/referentiels/regle-decoupe?cycle_id={cid}&niveau={quote(NIVEAU)}")
    assert g.json()["valide"] is True


def test_rejeter_remet_valide_false():
    cid = _seed_regle(valide=True)
    r = _admin().post("/api/admin/referentiels/regle-decoupe/rejeter",
                      json={"cycle_id": cid, "niveau": NIVEAU})
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "valide": False}
    assert _regle_en_base()["valide"] is False


def test_valider_sans_regle_404():
    cid = _make_cycle("Crèche")   # aucun référentiel/règle
    r = _admin().post("/api/admin/referentiels/regle-decoupe/valider",
                      json={"cycle_id": cid, "niveau": NIVEAU})
    assert r.status_code == 404, r.text


def test_cycle_inconnu_404():
    r = _admin().get(f"/api/admin/referentiels/regle-decoupe?cycle_id=999999&niveau={quote(NIVEAU)}")
    assert r.status_code == 404, r.text


def test_sans_cookie_admin_401():
    anon = TestClient(app)
    assert anon.get(
        f"/api/admin/referentiels/regle-decoupe?cycle_id=1&niveau={quote(NIVEAU)}").status_code == 401
    assert anon.post("/api/admin/referentiels/regle-decoupe/valider",
                     json={"cycle_id": 1, "niveau": NIVEAU}).status_code == 401
    assert anon.post("/api/admin/referentiels/regle-decoupe/rejeter",
                     json={"cycle_id": 1, "niveau": NIVEAU}).status_code == 401
