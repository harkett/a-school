r"""Preuve — TEMPS 2 de l'arbitrage : l'admin demande l'avis d'un professionnel par mail sur un cas
flou. Le statut « en attente » vit EN BASE (table `arbitrage_demandes`, une ligne par référentiel +
libellé). Le mail part par la porte SMTP unique `send_custom_email` (MOCKÉE ici — jamais de vrai envoi).

Ce que ce test PROUVE (chaîne réelle, TestClient + base aschool_test) :
  1. POST /demander -> envoie le mail (objet = couple cycle · niveau) + crée la ligne « en attente ».
  2. GET /en-attente relit la ligne (label + destinataire).
  3. Redemander le MÊME cas met à jour l'adresse, jamais un doublon (upsert).
  4. L'objet du mail contient le COUPLE (cycle + niveau), composé en base.
  5. Trancher le cas (POST /arbitrage-flou, bandes non vides) FERME la demande (ligne supprimée).
  6. Envoi mail en échec -> 502 ET aucune ligne « en attente » créée (pas d'état fantôme).
  7. email / message / label vides -> 400 ; couple sans référentiel -> 404 ; sans cookie -> 401.

Isolation : la base est TRUNCATée entre tests (conftest) ; chaque test sème son couple.

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_arbitrage_demande_endpoints.py -q
"""
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
import backend.pedagogie.referentiels_admin as refadmin
from backend.core.models_db import ArbitrageDemande, Cycle, Niveau, Referentiel
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

CYCLE = "Crèche"
NIVEAU = "Bébés (0-1 an)"
COLLECTION = "bebes_0_1_an"        # collection réelle de la crèche -> get_fiche -> BANDES_VALIDES {0-1,1-3}
FLOU = "dès ~2 ans"                # un libellé flou réel du document
EMAIL = "pro@exemple.fr"
MESSAGE = "Bonjour, un mot d'avis ?"


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _couple(avec_referentiel=True, niveau=NIVEAU):
    """Crée le cycle + le niveau (+ le référentiel du couple, sauf si avec_referentiel=False)."""
    db = dbmod.SessionLocal()
    cy = Cycle(nom=CYCLE, ordre=1); db.add(cy); db.flush()
    niv = Niveau(cycle_id=cy.id, nom=niveau, ordre=1); db.add(niv); db.flush()
    if avec_referentiel:
        db.add(Referentiel(niveau_id=niv.id, matiere_id=None, nom_fixe=COLLECTION,
                           collection=COLLECTION, filtres=None, fichier="referentiel.pdf"))
    db.commit()
    cid = cy.id
    db.close()
    return cid


def _en_attente_en_base():
    """Lignes arbitrage_demandes du couple (liste de (label, destinataire))."""
    db = dbmod.SessionLocal()
    try:
        rows = (db.query(ArbitrageDemande)
                  .join(Referentiel, Referentiel.id == ArbitrageDemande.referentiel_id)
                  .filter(Referentiel.collection == COLLECTION).all())
        return [(r.label, r.destinataire) for r in rows]
    finally:
        db.close()


def _capter_mail(monkeypatch):
    """Remplace send_custom_email par un enregistreur (aucun vrai envoi). Renvoie la liste des appels."""
    appels = []
    monkeypatch.setattr(refadmin, "send_custom_email",
                        lambda email, prenom, subject, body: appels.append((email, prenom, subject, body)))
    return appels


# ── Envoi + « en attente » + relecture ────────────────────────────────────────

def test_demander_envoie_et_passe_en_attente(monkeypatch):
    appels = _capter_mail(monkeypatch)
    cid = _couple()
    r = _admin().post("/api/admin/referentiels/arbitrage-flou/demander",
                      json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "email": EMAIL, "message": MESSAGE})
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "en_attente": True, "destinataire": EMAIL}
    assert len(appels) == 1                        # un mail parti
    assert appels[0][0] == EMAIL and appels[0][3] == MESSAGE
    # base : la ligne « en attente » existe
    assert _en_attente_en_base() == [(FLOU, EMAIL)]
    # GET relit
    g = _admin().get(f"/api/admin/referentiels/arbitrage-flou/en-attente?cycle_id={cid}&niveau={quote(NIVEAU)}")
    assert g.status_code == 200, g.text
    assert g.json() == {"en_attente": [{"label": FLOU, "destinataire": EMAIL}]}


def test_objet_du_mail_contient_le_couple(monkeypatch):
    appels = _capter_mail(monkeypatch)
    cid = _couple()
    _admin().post("/api/admin/referentiels/arbitrage-flou/demander",
                  json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "email": EMAIL, "message": MESSAGE})
    objet = appels[0][2]
    assert CYCLE in objet and NIVEAU in objet       # cycle · niveau dans l'objet
    assert "aSchool" in objet


def test_redemander_met_a_jour_sans_doublon(monkeypatch):
    _capter_mail(monkeypatch)
    cid = _couple()
    cli = _admin()
    cli.post("/api/admin/referentiels/arbitrage-flou/demander",
             json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "email": EMAIL, "message": MESSAGE})
    r = cli.post("/api/admin/referentiels/arbitrage-flou/demander",
                 json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "email": "autre@exemple.fr", "message": MESSAGE})
    assert r.status_code == 200, r.text
    assert _en_attente_en_base() == [(FLOU, "autre@exemple.fr")]   # une seule ligne, adresse à jour


# ── Fermeture de la demande quand l'admin tranche ─────────────────────────────

def test_trancher_ferme_la_demande(monkeypatch):
    _capter_mail(monkeypatch)
    cid = _couple()
    cli = _admin()
    cli.post("/api/admin/referentiels/arbitrage-flou/demander",
             json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "email": EMAIL, "message": MESSAGE})
    assert _en_attente_en_base() == [(FLOU, EMAIL)]                # en attente
    # l'admin tranche le MÊME cas -> la demande se ferme
    t = cli.post("/api/admin/referentiels/arbitrage-flou",
                 json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "bandes": ["1-3"]})
    assert t.status_code == 200, t.text
    assert _en_attente_en_base() == []                            # ligne supprimée


# ── Garde-fous ────────────────────────────────────────────────────────────────

def test_envoi_mail_echoue_502_et_aucune_ligne(monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("SMTP down")
    monkeypatch.setattr(refadmin, "send_custom_email", _boom)
    cid = _couple()
    r = _admin().post("/api/admin/referentiels/arbitrage-flou/demander",
                      json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "email": EMAIL, "message": MESSAGE})
    assert r.status_code == 502, r.text
    assert _en_attente_en_base() == []                            # aucun état fantôme


def test_email_vide_400(monkeypatch):
    _capter_mail(monkeypatch)
    cid = _couple()
    r = _admin().post("/api/admin/referentiels/arbitrage-flou/demander",
                      json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "email": "  ", "message": MESSAGE})
    assert r.status_code == 400, r.text


def test_message_vide_400(monkeypatch):
    _capter_mail(monkeypatch)
    cid = _couple()
    r = _admin().post("/api/admin/referentiels/arbitrage-flou/demander",
                      json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "email": EMAIL, "message": "   "})
    assert r.status_code == 400, r.text


def test_label_vide_400(monkeypatch):
    _capter_mail(monkeypatch)
    cid = _couple()
    r = _admin().post("/api/admin/referentiels/arbitrage-flou/demander",
                      json={"cycle_id": cid, "niveau": NIVEAU, "label": "   ", "email": EMAIL, "message": MESSAGE})
    assert r.status_code == 400, r.text


def test_demander_sans_referentiel_404(monkeypatch):
    _capter_mail(monkeypatch)
    cid = _couple(avec_referentiel=False)
    r = _admin().post("/api/admin/referentiels/arbitrage-flou/demander",
                      json={"cycle_id": cid, "niveau": NIVEAU, "label": FLOU, "email": EMAIL, "message": MESSAGE})
    assert r.status_code == 404, r.text


def test_en_attente_sans_referentiel_liste_vide():
    cid = _couple(avec_referentiel=False)
    g = _admin().get(f"/api/admin/referentiels/arbitrage-flou/en-attente?cycle_id={cid}&niveau={quote(NIVEAU)}")
    assert g.status_code == 200, g.text
    assert g.json() == {"en_attente": []}


def test_sans_cookie_admin_401():
    anon = TestClient(app)
    assert anon.get(
        f"/api/admin/referentiels/arbitrage-flou/en-attente?cycle_id=1&niveau={quote(NIVEAU)}").status_code == 401
    assert anon.post("/api/admin/referentiels/arbitrage-flou/demander",
                     json={"cycle_id": 1, "niveau": NIVEAU, "label": FLOU, "email": EMAIL, "message": MESSAGE}).status_code == 401
