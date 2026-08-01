r"""Preuve de raccordement — ÉCHANGE sur un retour (la réponse de l'administration).

Le canal prof -> admin existait déjà. Ce qui manquait : l'admin n'avait aucun endroit où
écrire, et le prof ne voyait qu'une étiquette de statut avancer. Ces tests prouvent la
chaîne reelle du retour, pas « le code existe » :

  1. L'admin repond -> le message est en base et ressort dans GET /admin/feedbacks.
  2. Le prof lit la reponse dans /feedback/mes-feedbacks, signee « aSchool » (jamais « IA »,
     jamais « admin »), et ses propres messages signes « Vous ».
  3. Cote admin, la meme conversation est signee dans l'autre sens (« Vous » / e-mail du prof).
  4. Le prof repond sur SON retour ; 403 sur celui d'un autre, 404 si le retour n'existe pas.
  5. L'avis part par la porte SMTP unique et n'emporte PAS le contenu du message (il se lit
     dans aSchool) — dans les deux sens, prof et administration.
  6. Chaque avis est JOURNALISE dans email_envois (onglet Suivi).
  7. SMTP en panne -> la reponse est quand meme enregistree (jamais perdue), l'echec est trace
     et l'ecran est prevenu (avis_envoye = false).
  8. Modele d'email absent en base -> aucun texte de repli invente : echec trace, message garde.
  9. Le message d'OUVERTURE (feedbacks.message) n'est jamais touche par l'echange.
 10. Supprimer le retour emporte son echange (CASCADE).
 11. Corps vide -> 400. Sans cookie admin -> 401.

Lancer : .\.venv\Scripts\python.exe -m pytest test_feedback_echange.py -q
"""
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import pytest
from fastapi.testclient import TestClient

# engine / SessionLocal rediriges vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod
import backend.securite.comptes as comptes
from backend.core.models_db import EmailEnvoi, EmailTemplate, Feedback, FeedbackMessage, User
from backend.main import app
from backend.systeme.admin import _make_admin_token

EMAIL_PROF = "prof@college.fr"
OUVERTURE = "La generation plante sur les 6e en francais."


@pytest.fixture(autouse=True)
def _modeles_d_avis():
    """Les 2 modeles d'avis, semes par la migration f1e2d3c4b5a6 en production. Le schema de
    test est monte par create_all (sans migrations) et vide entre chaque test : on les re-seme
    ICI et non dans le conftest partage, pour ne pas fausser les tests qui COMPTENT les lignes
    de email_templates. `created_at` explicite : le modele n'a pas le server_default de la
    migration."""
    db = dbmod.SessionLocal()
    for slug, nom, objet, corps in [
        ("reponse_feedback", "Réponse à un retour (vers le prof)",
         "Vous avez une réponse à votre retour aSchool", "Bonjour {prenom}, …"),
        ("reponse_prof", "Réponse d'un prof (vers l'administration)",
         "[aSchool] Un prof a répondu sur un retour", "Un prof a répondu."),
    ]:
        db.add(EmailTemplate(slug=slug, nom=nom, description="", objet=objet, corps=corps,
                             mode_envoi="auto", supprimable=False))
    db.commit()
    db.close()


def _prof_et_retour(email=EMAIL_PROF, message=OUVERTURE):
    """Un prof verifie + un retour deja depose (le canal qui marche deja)."""
    db = dbmod.SessionLocal()
    user = User(email=email, password_hash="x", is_verified=True, prenom="Marie")
    db.add(user)
    db.commit()
    db.refresh(user)
    fb = Feedback(user_id=user.id, type="feedback", message=message,
                  rating=0, category="bug", statut="nouveau")
    db.add(fb)
    db.commit()
    fb_id = fb.id
    db.close()
    return fb_id


def _client_prof(email=EMAIL_PROF):
    c = TestClient(app)
    c.cookies.set("aschool_access", comptes.create_access_token(email))
    return c


def _client_admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


@pytest.fixture
def smtp(monkeypatch):
    """Capture les mails au lieu de les envoyer. La porte SMTP unique est la seule remplacee."""
    envoyes = []
    monkeypatch.setattr(comptes, "_smtp_send", lambda msg: envoyes.append(msg))
    return envoyes


def _corps_texte(msg):
    """Le texte brut d'un mail multipart (pour verifier ce qu'il contient... et ne contient pas)."""
    morceaux = []
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            morceaux.append(part.get_payload(decode=True).decode("utf-8", "replace"))
    return "\n".join(morceaux)


# ── 1-3. L'echange existe et se lit des deux cotes ─────────────────────────

def test_admin_repond_et_le_prof_lit_la_reponse(smtp):
    fb_id = _prof_et_retour()

    r = _client_admin().post(f"/api/admin/feedbacks/{fb_id}/messages",
                             json={"corps": "C'est corrige depuis ce matin, reessayez."})
    assert r.status_code == 200, r.text
    assert r.json()["avis_envoye"] is True

    # Cote prof : la reponse apparait, signee « aSchool ».
    retours = _client_prof().get("/api/feedback/mes-feedbacks").json()
    assert len(retours) == 1
    messages = retours[0]["messages"]
    assert len(messages) == 1
    assert messages[0]["corps"] == "C'est corrige depuis ce matin, reessayez."
    assert messages[0]["auteur"] == "aSchool"
    assert messages[0]["de_l_administration"] is True
    assert messages[0]["de_moi"] is False


def test_les_deux_cotes_voient_la_meme_conversation_signee_dans_leur_sens(smtp):
    fb_id = _prof_et_retour()
    _client_admin().post(f"/api/admin/feedbacks/{fb_id}/messages", json={"corps": "Bonjour, on regarde."})
    _client_prof().post(f"/api/feedback/{fb_id}/messages", json={"corps": "Merci, c'est urgent."})

    vus_par_prof = _client_prof().get("/api/feedback/mes-feedbacks").json()[0]["messages"]
    assert [(m["auteur"], m["de_moi"]) for m in vus_par_prof] == [("aSchool", False), ("Vous", True)]

    vus_par_admin = next(f for f in _client_admin().get("/api/admin/feedbacks").json()
                         if f["id"] == fb_id)["messages"]
    assert [(m["auteur"], m["de_moi"]) for m in vus_par_admin] == [("Vous", True), (EMAIL_PROF, False)]
    # Meme conversation, meme ordre : une seule place en base.
    assert [m["corps"] for m in vus_par_prof] == [m["corps"] for m in vus_par_admin]


# ── 4. Acces ───────────────────────────────────────────────────────────────

def test_prof_ne_peut_pas_repondre_sur_le_retour_d_un_autre(smtp):
    fb_id = _prof_et_retour()
    db = dbmod.SessionLocal()
    db.add(User(email="autre@college.fr", password_hash="x", is_verified=True))
    db.commit()
    db.close()
    r = _client_prof("autre@college.fr").post(f"/api/feedback/{fb_id}/messages", json={"corps": "coucou"})
    assert r.status_code == 403, r.text
    assert smtp == []


def test_retour_inexistant_404_et_sans_cookie_admin_401(smtp):
    assert _client_prof().post("/api/feedback/999999/messages",
                               json={"corps": "x"}).status_code == 404
    assert TestClient(app).post("/api/admin/feedbacks/1/messages",
                                json={"corps": "x"}).status_code == 401


# ── 5-6. L'avis par mail : il previent, il ne raconte pas ──────────────────

def test_avis_vers_le_prof_ne_porte_pas_le_contenu(smtp):
    fb_id = _prof_et_retour()
    secret = "Le correctif est en ligne depuis 9h32."
    _client_admin().post(f"/api/admin/feedbacks/{fb_id}/messages", json={"corps": secret})

    assert len(smtp) == 1
    mail = smtp[0]
    assert mail["To"] == EMAIL_PROF
    assert secret not in _corps_texte(mail), "le mail emporte le contenu : il doit rester dans aSchool"


def test_avis_vers_l_administration_quand_le_prof_repond(smtp, monkeypatch):
    monkeypatch.setenv("FEEDBACK_NOTIFY_EMAIL", "contact@aschool.fr")
    fb_id = _prof_et_retour()
    secret = "En fait le probleme revient le mardi."
    r = _client_prof().post(f"/api/feedback/{fb_id}/messages", json={"corps": secret})
    assert r.status_code == 200, r.text

    assert len(smtp) == 1
    assert smtp[0]["To"] == "contact@aschool.fr"
    assert secret not in _corps_texte(smtp[0])


def test_chaque_avis_est_journalise(smtp):
    fb_id = _prof_et_retour()
    _client_admin().post(f"/api/admin/feedbacks/{fb_id}/messages", json={"corps": "Reponse."})

    db = dbmod.SessionLocal()
    envois = db.query(EmailEnvoi).all()
    assert len(envois) == 1
    assert envois[0].modele_slug == "reponse_feedback"
    assert envois[0].destinataire == EMAIL_PROF
    assert envois[0].statut == "envoye"
    db.close()


# ── 7-8. Rien n'est perdu quand l'envoi echoue ─────────────────────────────

def test_smtp_en_panne_la_reponse_est_gardee_et_l_echec_trace(monkeypatch):
    def boom(msg):
        raise RuntimeError("SMTP down")
    monkeypatch.setattr(comptes, "_smtp_send", boom)
    fb_id = _prof_et_retour()

    r = _client_admin().post(f"/api/admin/feedbacks/{fb_id}/messages", json={"corps": "Reponse quand meme."})
    assert r.status_code == 200, r.text
    assert r.json()["avis_envoye"] is False          # l'ecran est prevenu, honnetement
    assert r.json()["avis_erreur"]

    db = dbmod.SessionLocal()
    assert db.query(FeedbackMessage).count() == 1     # la reponse existe
    echec = db.query(EmailEnvoi).one()
    assert echec.statut == "echec" and "SMTP down" in echec.erreur
    db.close()
    # et le prof la lit dans l'application
    assert len(_client_prof().get("/api/feedback/mes-feedbacks").json()[0]["messages"]) == 1


def test_modele_absent_aucun_texte_de_repli_invente(smtp):
    """Base = source unique : un modele manquant est une ERREUR tracee, pas un mail fantome."""
    db = dbmod.SessionLocal()
    db.query(EmailTemplate).filter(EmailTemplate.slug == "reponse_feedback").delete()
    db.commit()
    db.close()

    fb_id = _prof_et_retour()
    r = _client_admin().post(f"/api/admin/feedbacks/{fb_id}/messages", json={"corps": "Reponse."})
    assert r.status_code == 200, r.text
    assert r.json()["avis_envoye"] is False
    assert smtp == [], "aucun mail ne doit partir avec un texte invente"

    db = dbmod.SessionLocal()
    assert db.query(FeedbackMessage).count() == 1                 # la reponse est gardee
    assert "absent de la base" in db.query(EmailEnvoi).one().erreur
    db.close()


# ── 9-11. Non-regression et garde-fous ─────────────────────────────────────

def test_le_message_d_ouverture_n_est_jamais_touche(smtp):
    fb_id = _prof_et_retour()
    _client_admin().post(f"/api/admin/feedbacks/{fb_id}/messages", json={"corps": "Reponse."})
    _client_prof().post(f"/api/feedback/{fb_id}/messages", json={"corps": "Merci."})

    db = dbmod.SessionLocal()
    assert db.get(Feedback, fb_id).message == OUVERTURE
    db.close()
    # et il reste affiche a part, hors du fil
    retour = _client_prof().get("/api/feedback/mes-feedbacks").json()[0]
    assert retour["message"] == OUVERTURE
    assert all(m["corps"] != OUVERTURE for m in retour["messages"])


def test_supprimer_le_retour_emporte_son_echange(smtp):
    fb_id = _prof_et_retour()
    _client_admin().post(f"/api/admin/feedbacks/{fb_id}/messages", json={"corps": "Reponse."})
    assert _client_admin().delete(f"/api/admin/feedbacks/{fb_id}").status_code == 200

    db = dbmod.SessionLocal()
    assert db.query(FeedbackMessage).count() == 0
    db.close()


def test_corps_vide_refuse(smtp):
    fb_id = _prof_et_retour()
    assert _client_admin().post(f"/api/admin/feedbacks/{fb_id}/messages",
                                json={"corps": "   "}).status_code == 400
    assert _client_prof().post(f"/api/feedback/{fb_id}/messages",
                               json={"corps": ""}).status_code == 422   # borne Pydantic
    db = dbmod.SessionLocal()
    assert db.query(FeedbackMessage).count() == 0
    db.close()
