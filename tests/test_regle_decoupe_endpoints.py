r"""Preuve de raccordement — points 1 a 4 : la regle de decoupe (fichier a deux faces) est
lue et son STATUT est valide/rejete par l'admin, via 3 endpoints. La regle vit dans le dossier
du COUPLE (REFERENTIELS/<CYCLE>/<NIVEAU>/regle-decoupe.json), a cote du PDF — resolue par
cycle + niveau, jamais partagee au niveau du cycle.

Ce que ce test PROUVE (chaine reelle, pas « le code existe ») :
  1. GET /admin/referentiels/regle-decoupe?cycle_id=&niveau= renvoie les deux faces + depose_par + valide.
  2. GET sur un couple sans fichier -> { existe: false } (l'ecran n'affiche pas la carte).
  3. POST .../valider met valide=true (fichier disque), en PRESERVANT les deux faces.
  4. POST .../rejeter remet valide=false.
  5. valider sur un couple sans fichier -> 404 (jamais de statut fantome).
  6. Cycle inconnu -> 404. Sans cookie admin -> 401.

Isolation : REFERENTIELS_DIR est monkeypatche vers un dossier temporaire — les vrais
regle-decoupe.json de la creche (committes, un par couple) ne sont JAMAIS touches.

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_regle_decoupe_endpoints.py -q
"""
import json
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
import backend.pedagogie.referentiels_admin as radmin
from backend.core.models_db import Cycle
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

MOTIF = r"^\s*-?\s*Âge\s*:\s*(.+)$"   # meme motif que la fiche creche
CLAIR = "Une unite = une activite. Elle commence a chaque ligne qui indique un age."
NIVEAU = "Bébés (0-1 an)"             # couple = cycle + niveau ; entre dans le chemin de la regle


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


def _poser_regle(tmp_path, monkeypatch, cycle_cle="CRECHE", niveau=NIVEAU, valide=False):
    """Monkeypatch REFERENTIELS_DIR -> tmp_path et depose un regle-decoupe.json sous
    <CYCLE>/<NIVEAU>/ (le dossier du couple, comme le PDF)."""
    monkeypatch.setattr(radmin, "REFERENTIELS_DIR", tmp_path)
    dossier = tmp_path / cycle_cle / radmin._dossier_cle(niveau)
    dossier.mkdir(parents=True, exist_ok=True)
    fichier = dossier / "regle-decoupe.json"
    fichier.write_text(json.dumps({
        "explication_clair": CLAIR,
        "critere_technique": MOTIF,
        "depose_par": "dev",
        "valide": valide,
    }, ensure_ascii=False), encoding="utf-8")
    return fichier


def test_lire_regle_existe(monkeypatch, tmp_path):
    _poser_regle(tmp_path, monkeypatch)          # cle "CRECHE" = _dossier_cle("Crèche")
    cid = _make_cycle("Crèche")
    r = _admin().get(f"/api/admin/referentiels/regle-decoupe?cycle_id={cid}&niveau={quote(NIVEAU)}")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["existe"] is True
    assert d["explication_clair"] == CLAIR
    assert d["critere_technique"] == MOTIF
    assert d["depose_par"] == "dev"
    assert d["valide"] is False


def test_lire_regle_absente(monkeypatch, tmp_path):
    monkeypatch.setattr(radmin, "REFERENTIELS_DIR", tmp_path)   # aucun fichier pose
    cid = _make_cycle("Crèche")
    r = _admin().get(f"/api/admin/referentiels/regle-decoupe?cycle_id={cid}&niveau={quote(NIVEAU)}")
    assert r.status_code == 200, r.text
    assert r.json() == {"existe": False}


def test_valider_met_valide_true_et_preserve_les_faces(monkeypatch, tmp_path):
    fichier = _poser_regle(tmp_path, monkeypatch, valide=False)
    cid = _make_cycle("Crèche")
    r = _admin().post("/api/admin/referentiels/regle-decoupe/valider",
                      json={"cycle_id": cid, "niveau": NIVEAU})
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "valide": True}
    # Disque : valide=true ET les deux faces intactes.
    disque = json.loads(fichier.read_text(encoding="utf-8"))
    assert disque["valide"] is True
    assert disque["explication_clair"] == CLAIR
    assert disque["critere_technique"] == MOTIF
    assert disque["depose_par"] == "dev"
    # GET confirme.
    g = _admin().get(f"/api/admin/referentiels/regle-decoupe?cycle_id={cid}&niveau={quote(NIVEAU)}")
    assert g.json()["valide"] is True


def test_rejeter_remet_valide_false(monkeypatch, tmp_path):
    fichier = _poser_regle(tmp_path, monkeypatch, valide=True)
    cid = _make_cycle("Crèche")
    r = _admin().post("/api/admin/referentiels/regle-decoupe/rejeter",
                      json={"cycle_id": cid, "niveau": NIVEAU})
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "valide": False}
    assert json.loads(fichier.read_text(encoding="utf-8"))["valide"] is False


def test_valider_sans_fichier_404(monkeypatch, tmp_path):
    monkeypatch.setattr(radmin, "REFERENTIELS_DIR", tmp_path)   # aucun fichier
    cid = _make_cycle("Crèche")
    r = _admin().post("/api/admin/referentiels/regle-decoupe/valider",
                      json={"cycle_id": cid, "niveau": NIVEAU})
    assert r.status_code == 404, r.text


def test_cycle_inconnu_404(monkeypatch, tmp_path):
    monkeypatch.setattr(radmin, "REFERENTIELS_DIR", tmp_path)
    r = _admin().get(f"/api/admin/referentiels/regle-decoupe?cycle_id=999999&niveau={quote(NIVEAU)}")
    assert r.status_code == 404, r.text


def test_sans_cookie_admin_401(monkeypatch, tmp_path):
    monkeypatch.setattr(radmin, "REFERENTIELS_DIR", tmp_path)
    anon = TestClient(app)
    assert anon.get(
        f"/api/admin/referentiels/regle-decoupe?cycle_id=1&niveau={quote(NIVEAU)}").status_code == 401
    assert anon.post("/api/admin/referentiels/regle-decoupe/valider",
                     json={"cycle_id": 1, "niveau": NIVEAU}).status_code == 401
    assert anon.post("/api/admin/referentiels/regle-decoupe/rejeter",
                     json={"cycle_id": 1, "niveau": NIVEAU}).status_code == 401
