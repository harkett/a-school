r"""Preuve — BRIQUE 1b : l'admin tranche un cas flou via 2 endpoints. La décision vit dans le
dossier du COUPLE (REFERENTIELS/<CYCLE>/<NIVEAU>/arbitrage-flou.json), à côté du PDF — comme
regle-decoupe.json. Les bandes saisies sont validées contre celles de la FICHE (jamais une bande
inconnue = trou muet).

Ce que ce test PROUVE (chaîne réelle, TestClient + base aschool_test) :
  1. POST /admin/referentiels/arbitrage-flou écrit { label: [bandes] } ; GET le relit.
  2. Deux décisions cohabitent (les autres entrées sont préservées).
  3. POST bande invalide (« 9-9 ») -> 400 (garde-fou anti-trou-muet).
  4. POST bandes:[] -> retire la décision (dé-trancher).
  5. GET sans fichier -> { arbitrages: {} }.
  6. Couple sans référentiel -> 404 ; niveau inconnu -> 404 ; cycle inconnu -> 404 ; sans cookie -> 401.

Isolation : REFERENTIELS_DIR est monkeypatché vers un dossier temporaire — les vrais
arbitrage-flou.json committés ne sont JAMAIS touchés. La base est TRUNCATée entre tests (conftest).

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_arbitrage_flou_endpoints.py -q
"""
import json
import os
import sys
from urllib.parse import quote

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod
import backend.pedagogie.referentiels_admin as radmin
from backend.core.models_db import Cycle, Niveau, Referentiel
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

NIVEAU = "Bébés (0-1 an)"
COLLECTION = "bebes_0_1_an"        # collection réelle de la crèche -> get_fiche -> BANDES_VALIDES {0-1,1-3}
FLOU = "dès ~2 ans"               # un libellé flou réel du document


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _couple(tmp_path, monkeypatch, avec_referentiel=True, niveau=NIVEAU):
    """Monkeypatch REFERENTIELS_DIR -> tmp_path, crée le cycle + le niveau (+ le référentiel du
    couple, sauf si avec_referentiel=False). Renvoie le cycle_id."""
    monkeypatch.setattr(radmin, "REFERENTIELS_DIR", tmp_path)
    db = dbmod.SessionLocal()
    cy = Cycle(nom="Crèche", ordre=1); db.add(cy); db.flush()
    niv = Niveau(cycle_id=cy.id, nom=niveau, ordre=1); db.add(niv); db.flush()
    if avec_referentiel:
        db.add(Referentiel(niveau_id=niv.id, matiere_id=None, nom_fixe=COLLECTION,
                           collection=COLLECTION, filtres=None, fichier="referentiel.pdf"))
    db.commit()
    cid = cy.id
    db.close()
    return cid


def _fichier(tmp_path, niveau=NIVEAU):
    return tmp_path / "CRECHE" / radmin._dossier_cle(niveau) / "arbitrage-flou.json"


# ── POST écrit / GET relit ────────────────────────────────────────────────────

def test_post_ecrit_et_get_relit(tmp_path, monkeypatch):
    cid = _couple(tmp_path, monkeypatch)
    r = _admin().post("/api/admin/referentiels/arbitrage-flou",
                      json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "bandes": ["1-3"]})
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "arbitrages": {FLOU: ["1-3"]}}
    # disque
    assert json.loads(_fichier(tmp_path).read_text(encoding="utf-8"))["arbitrages"][FLOU] == ["1-3"]
    # GET relit
    g = _admin().get(f"/api/admin/referentiels/arbitrage-flou?cycle_id={cid}&niveau={quote(NIVEAU)}")
    assert g.status_code == 200, g.text
    assert g.json() == {"arbitrages": {FLOU: ["1-3"]}}


def test_post_deux_decisions_cohabitent(tmp_path, monkeypatch):
    cid = _couple(tmp_path, monkeypatch)
    cli = _admin()
    cli.post("/api/admin/referentiels/arbitrage-flou",
             json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "bandes": ["1-3"]})
    r = cli.post("/api/admin/referentiels/arbitrage-flou",
                 json={"cycle_id": cid, "niveau": NIVEAU, "label": "tout-petits", "bandes": ["0-1", "1-3"]})
    assert r.status_code == 200, r.text
    arb = r.json()["arbitrages"]
    assert arb == {FLOU: ["1-3"], "tout-petits": ["0-1", "1-3"]}   # la 1re décision préservée


def test_post_bande_invalide_400(tmp_path, monkeypatch):
    cid = _couple(tmp_path, monkeypatch)
    r = _admin().post("/api/admin/referentiels/arbitrage-flou",
                      json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "bandes": ["9-9"]})
    assert r.status_code == 400, r.text
    assert "inconnue" in r.json()["detail"].lower()
    assert not _fichier(tmp_path).exists()          # rien écrit


def test_post_bandes_vides_retire(tmp_path, monkeypatch):
    cid = _couple(tmp_path, monkeypatch)
    cli = _admin()
    cli.post("/api/admin/referentiels/arbitrage-flou",
             json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "bandes": ["1-3"]})
    r = cli.post("/api/admin/referentiels/arbitrage-flou",
                 json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "bandes": []})
    assert r.status_code == 200, r.text
    assert r.json()["arbitrages"] == {}             # décision retirée
    assert json.loads(_fichier(tmp_path).read_text(encoding="utf-8"))["arbitrages"] == {}


def test_post_label_vide_400(tmp_path, monkeypatch):
    cid = _couple(tmp_path, monkeypatch)
    r = _admin().post("/api/admin/referentiels/arbitrage-flou",
                      json={"cycle_id": cid, "niveau": NIVEAU, "label": "   ", "bandes": ["1-3"]})
    assert r.status_code == 400, r.text


# ── GET absent / erreurs ──────────────────────────────────────────────────────

def test_get_absent_arbitrages_vides(tmp_path, monkeypatch):
    cid = _couple(tmp_path, monkeypatch)
    g = _admin().get(f"/api/admin/referentiels/arbitrage-flou?cycle_id={cid}&niveau={quote(NIVEAU)}")
    assert g.status_code == 200, g.text
    assert g.json() == {"arbitrages": {}}


def test_post_sans_referentiel_404(tmp_path, monkeypatch):
    cid = _couple(tmp_path, monkeypatch, avec_referentiel=False)   # niveau existe, pas de référentiel
    r = _admin().post("/api/admin/referentiels/arbitrage-flou",
                      json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "bandes": ["1-3"]})
    assert r.status_code == 404, r.text
    assert "référentiel" in r.json()["detail"].lower()


def test_post_niveau_inconnu_404(tmp_path, monkeypatch):
    cid = _couple(tmp_path, monkeypatch)
    r = _admin().post("/api/admin/referentiels/arbitrage-flou",
                      json={"cycle_id": cid, "niveau": "Niveau qui n'existe pas", "label": FLOU, "bandes": ["1-3"]})
    assert r.status_code == 404, r.text


def test_get_cycle_inconnu_404(tmp_path, monkeypatch):
    monkeypatch.setattr(radmin, "REFERENTIELS_DIR", tmp_path)
    r = _admin().get(f"/api/admin/referentiels/arbitrage-flou?cycle_id=999999&niveau={quote(NIVEAU)}")
    assert r.status_code == 404, r.text


def test_sans_cookie_admin_401(tmp_path, monkeypatch):
    monkeypatch.setattr(radmin, "REFERENTIELS_DIR", tmp_path)
    anon = TestClient(app)
    assert anon.get(
        f"/api/admin/referentiels/arbitrage-flou?cycle_id=1&niveau={quote(NIVEAU)}").status_code == 401
    assert anon.post("/api/admin/referentiels/arbitrage-flou",
                     json={"cycle_id": 1, "niveau": NIVEAU, "label": FLOU, "bandes": ["1-3"]}).status_code == 401
