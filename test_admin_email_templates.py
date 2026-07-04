r"""Preuve de raccordement — modeles d'email (collection maitre-detail).

Ce que les tests PROUVENT (chaine reelle, pas « le code existe ») :
  1. GET /admin/email-templates : liste, le modele non supprimable ('welcome') en tete.
  2. POST : cree un modele 'manuel' avec slug derive du nom, supprimable.
  3. PUT : ecrit objet/corps en base.
  4. DELETE : refuse (400) un modele non supprimable ('welcome'), accepte un manuel.
  5. POST /{id}/send : envoie a l'adresse saisie via send_custom_email (SMTP patche) ;
     adresse invalide -> 400.
  6. NO-REGRESSION : la verification d'email (mail de bienvenue) lit le modele 'welcome'
     EN BASE et envoie son objet -> chaine /auth/verify-email prouvee.
  7. Sans cookie admin : 401.

Lancer : .\.venv\Scripts\python.exe -m pytest test_admin_email_templates.py -q
"""
import os
import sys
from datetime import datetime

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.database as dbmod  # engine/SessionLocal rediriges vers aschool_test par conftest
import backend.auth as auth_lib
from backend.main import app
from backend.models_db import EmailTemplate, User
from backend.routers.admin import _make_admin_token, get_welcome_template
from fastapi.testclient import TestClient


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _seed_welcome(objet="Bienvenue sur aSchool !", corps="Bonjour {prenom}, bienvenue."):
    db = dbmod.SessionLocal()
    db.add(EmailTemplate(slug="welcome", nom="Email de bienvenue", objet=objet,
                         corps=corps, mode_envoi="auto", supprimable=False))
    db.commit()
    db.close()


def test_liste_welcome_en_tete():
    _seed_welcome()
    c = _admin()
    c.post("/api/admin/email-templates", json={"nom": "Email UNICEF"})
    rows = c.get("/api/admin/email-templates").json()
    assert len(rows) == 2
    assert rows[0]["slug"] == "welcome"          # non supprimable -> en tete
    assert rows[0]["supprimable"] is False


def test_create_manuel_slug_derive():
    r = _admin().post("/api/admin/email-templates", json={"nom": "Email UNICEF"})
    assert r.status_code == 200, r.text
    t = r.json()
    assert t["slug"] == "email_unicef"
    assert t["mode_envoi"] == "manuel"
    assert t["supprimable"] is True


def test_create_slug_unique_suffixe():
    c = _admin()
    a = c.post("/api/admin/email-templates", json={"nom": "Relance"}).json()
    b = c.post("/api/admin/email-templates", json={"nom": "Relance"}).json()
    assert a["slug"] == "relance"
    assert b["slug"] == "relance_2"             # collision -> suffixe


def test_update_ecrit_objet_corps():
    c = _admin()
    t = c.post("/api/admin/email-templates", json={"nom": "Email UNICEF"}).json()
    r = c.put(f"/api/admin/email-templates/{t['id']}",
              json={"objet": "Demande d'autorisation", "corps": "Bonjour, ..."})
    assert r.status_code == 200, r.text
    rows = {x["slug"]: x for x in c.get("/api/admin/email-templates").json()}
    assert rows["email_unicef"]["objet"] == "Demande d'autorisation"
    assert rows["email_unicef"]["corps"] == "Bonjour, ..."


def test_description_editable_et_persistee():
    c = _admin()
    t = c.post("/api/admin/email-templates", json={"nom": "Email UNICEF"}).json()
    assert t["description"] == ""                       # vide a la creation
    c.put(f"/api/admin/email-templates/{t['id']}",
          json={"description": "Demande d'autorisation UNICEF", "objet": "O", "corps": "C"})
    rows = {x["slug"]: x for x in c.get("/api/admin/email-templates").json()}
    assert rows["email_unicef"]["description"] == "Demande d'autorisation UNICEF"


def test_delete_welcome_refuse_manuel_ok():
    _seed_welcome()
    c = _admin()
    welcome = next(x for x in c.get("/api/admin/email-templates").json() if x["slug"] == "welcome")
    r = c.delete(f"/api/admin/email-templates/{welcome['id']}")
    assert r.status_code == 400, r.text          # non supprimable

    t = c.post("/api/admin/email-templates", json={"nom": "Jetable"}).json()
    assert c.delete(f"/api/admin/email-templates/{t['id']}").status_code == 200
    assert all(x["slug"] != "jetable" for x in c.get("/api/admin/email-templates").json())


def test_send_manuel_passe_par_smtp(monkeypatch):
    sent = []
    monkeypatch.setattr(auth_lib, "_smtp_send", lambda msg: sent.append(msg))
    c = _admin()
    t = c.post("/api/admin/email-templates", json={"nom": "Email UNICEF"}).json()
    c.put(f"/api/admin/email-templates/{t['id']}",
          json={"objet": "Demande", "corps": "Bonjour l'UNICEF."})
    r = c.post(f"/api/admin/email-templates/{t['id']}/send", json={"to": "contact@unicef.org"})
    assert r.status_code == 200, r.text
    assert any(m["To"] == "contact@unicef.org" and m["Subject"] == "Demande" for m in sent)


def test_send_adresse_invalide_400(monkeypatch):
    sent = []
    monkeypatch.setattr(auth_lib, "_smtp_send", lambda msg: sent.append(msg))
    c = _admin()
    t = c.post("/api/admin/email-templates", json={"nom": "Email UNICEF"}).json()
    c.put(f"/api/admin/email-templates/{t['id']}", json={"objet": "O", "corps": "C"})
    r = c.post(f"/api/admin/email-templates/{t['id']}/send", json={"to": "pas-une-adresse"})
    assert r.status_code == 400, r.text
    assert sent == []                            # rien envoye


def test_send_refuse_si_objet_ou_corps_vide(monkeypatch):
    monkeypatch.setattr(auth_lib, "_smtp_send", lambda msg: None)
    c = _admin()
    t = c.post("/api/admin/email-templates", json={"nom": "Vide"}).json()  # objet/corps vides
    r = c.post(f"/api/admin/email-templates/{t['id']}/send", json={"to": "x@y.org"})
    assert r.status_code == 400, r.text


def test_welcome_autosend_lit_la_base(monkeypatch):
    """NO-REGRESSION : le mail de bienvenue (verify-email) lit le modele 'welcome'
    EN BASE et envoie son objet — chaine reelle."""
    sent = []
    monkeypatch.setattr(auth_lib, "_smtp_send", lambda msg: sent.append(msg))
    _seed_welcome(objet="OBJET-TEMOIN-BIENVENUE", corps="Bonjour {prenom} !")

    db = dbmod.SessionLocal()
    db.add(User(email="prof@college.fr", password_hash="x", is_verified=False, prenom="Marie"))
    db.commit()
    token = auth_lib.generate_email_token(db, "prof@college.fr", "verify_email")
    db.close()

    r = TestClient(app).get(f"/api/auth/verify-email?token={token}")
    assert r.status_code == 200, r.text
    # le mail adresse au prof porte l'objet du modele 'welcome' lu en base
    assert any(m["To"] == "prof@college.fr" and m["Subject"] == "OBJET-TEMOIN-BIENVENUE"
               for m in sent), [m["To"] for m in sent]


def test_welcome_fallback_si_table_vide():
    """Table vide -> get_welcome_template retombe sur le defaut code (jamais de plantage)."""
    db = dbmod.SessionLocal()
    tpl = get_welcome_template(db)
    db.close()
    assert tpl.objet and tpl.corps            # repli code, non vide


def test_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/email-templates").status_code == 401
    assert TestClient(app).post("/api/admin/email-templates", json={"nom": "X"}).status_code == 401
    assert TestClient(app).get("/api/admin/email-envois").status_code == 401


# ── Suivi des envois (onglet Suivi) ───────────────────────────────────────

def test_send_manuel_enregistre_suivi(monkeypatch):
    monkeypatch.setattr(auth_lib, "_smtp_send", lambda msg: None)
    c = _admin()
    assert c.get("/api/admin/email-envois").json() == []            # vide au depart
    t = c.post("/api/admin/email-templates", json={"nom": "Email UNICEF"}).json()
    c.put(f"/api/admin/email-templates/{t['id']}", json={"objet": "Demande", "corps": "Bonjour."})
    assert c.post(f"/api/admin/email-templates/{t['id']}/send", json={"to": "contact@unicef.org"}).status_code == 200
    envois = c.get("/api/admin/email-envois").json()
    assert len(envois) == 1
    e = envois[0]
    assert e["destinataire"] == "contact@unicef.org"
    assert e["statut"] == "envoye"
    assert e["modele_nom"] == "Email UNICEF"
    assert e["envoye_le"]                                           # date presente


def test_send_echec_trace_statut_echec(monkeypatch):
    def boom(msg):
        raise RuntimeError("SMTP down")
    monkeypatch.setattr(auth_lib, "_smtp_send", boom)
    c = _admin()
    t = c.post("/api/admin/email-templates", json={"nom": "Email UNICEF"}).json()
    c.put(f"/api/admin/email-templates/{t['id']}", json={"objet": "O", "corps": "C"})
    r = c.post(f"/api/admin/email-templates/{t['id']}/send", json={"to": "x@y.org"})
    assert r.status_code == 500                                     # l'echec remonte a l'admin
    envois = c.get("/api/admin/email-envois").json()
    assert len(envois) == 1 and envois[0]["statut"] == "echec"     # mais il est trace


def test_welcome_autosend_enregistre_suivi(monkeypatch):
    monkeypatch.setattr(auth_lib, "_smtp_send", lambda msg: None)
    _seed_welcome(objet="Bienvenue !", corps="Bonjour {prenom}")
    db = dbmod.SessionLocal()
    db.add(User(email="prof2@college.fr", password_hash="x", is_verified=False, prenom="Luc"))
    db.commit()
    token = auth_lib.generate_email_token(db, "prof2@college.fr", "verify_email")
    db.close()
    assert TestClient(app).get(f"/api/auth/verify-email?token={token}").status_code == 200
    envois = _admin().get("/api/admin/email-envois").json()
    assert any(e["destinataire"] == "prof2@college.fr" and e["modele_slug"] == "welcome"
               and e["statut"] == "envoye" for e in envois)
