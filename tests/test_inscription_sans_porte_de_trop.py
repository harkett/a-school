r"""Preuve du PARCOURS D'INSCRIPTION — une seule porte, et elle s'ouvre toute seule.

CE QUI A CHANGÉ. Le professeur créait son compte, recevait un lien d'activation, cliquait… et se
retrouvait devant un écran de connexion à remplir. Il venait pourtant de prouver qu'il possédait
l'adresse — c'est tout ce que ce lien démontre. Trois portes lui étaient présentées : le
« Retour à la connexion » de l'écran d'attente (qui menait à un refus, le compte n'étant pas
encore actif), le bouton « Se connecter » de la page d'activation, et le gros bouton du mail de
bienvenue. Désormais le lien ACTIVE ET CONNECTE.

MAIS PAS N'IMPORTE OÙ, et c'est le cœur de ces tests. Un lien d'activation traîne dans une boîte
mail : s'il ouvrait la session partout, celui qui lit la boîte deviendrait le professeur. Il faut
DEUX preuves — le lien, et le navigateur qui s'est inscrit. Ouvert sur le téléphone ou par
quelqu'un d'autre, le lien active le compte et rien de plus.

CE QUE CES TESTS PROTÈGENT :
  1. l'inscription marque le navigateur, et ce marqueur ne donne rien à lui seul ;
  2. même navigateur + lien valide = session ouverte, sans mot de passe ;
  3. autre navigateur (le téléphone) = compte activé, session refusée ;
  4. un marqueur volé et présenté pour UNE AUTRE adresse n'ouvre rien ;
  5. le marqueur ne survit pas à son usage — il ne resservira pas ;
  6. le mail de bienvenue part SANS bouton d'entrée : le professeur est déjà dans l'application.

Lancer : docker compose exec backend python -m pytest tests/test_inscription_sans_porte_de_trop.py -q
"""
import backend.securite.auth as auth
import backend.core.database as dbmod
from backend.core.models_db import EmailToken, User
from backend.main import app
from backend.securite import comptes
from fastapi.testclient import TestClient

MDP = "motdepasse-solide-8"


def _oublier(email: str):
    db = dbmod.SessionLocal()
    try:
        db.query(EmailToken).filter(EmailToken.email == email).delete()
        u = db.query(User).filter(User.email == email).first()
        if u:
            db.delete(u)
        db.commit()
    finally:
        db.close()


def _jeton_du_courriel(email: str) -> str:
    """Le jeton que le professeur reçoit — relu en base plutôt qu'intercepté à l'envoi."""
    db = dbmod.SessionLocal()
    try:
        t = (db.query(EmailToken)
             .filter(EmailToken.email == email, EmailToken.purpose == "verify_email",
                     EmailToken.used == False)  # noqa: E712
             .order_by(EmailToken.id.desc()).first())
        return t.token
    finally:
        db.close()


def _inscrire(client: TestClient, email: str, monkeypatch) -> str:
    monkeypatch.setattr(comptes, "send_verification_email", lambda *a, **k: None)
    r = client.post("/api/auth/signup", json={
        "email": email, "password": MDP, "password_confirm": MDP,
    })
    assert r.status_code == 201, r.text[:200]
    return _jeton_du_courriel(email)


def _muet(monkeypatch):
    """Aucun courriel ne part pendant les tests — ni bienvenue, ni notification d'admin."""
    monkeypatch.setattr(comptes, "send_custom_email", lambda *a, **k: None)
    monkeypatch.setattr(comptes, "send_admin_new_user_notification", lambda *a, **k: None)


def test_l_inscription_marque_le_navigateur(monkeypatch):
    """Sans ce marqueur, impossible de distinguer au retour le navigateur qui s'est inscrit d'un
    inconnu qui a mis la main sur le lien."""
    email = "marque@test.fr"
    _oublier(email)
    c = TestClient(app)
    _inscrire(c, email, monkeypatch)
    assert c.cookies.get(auth._INSCRIPTION), "le navigateur n'a pas été marqué"
    assert comptes.read_signup_device_token(c.cookies.get(auth._INSCRIPTION)) == email


def test_le_marqueur_seul_n_ouvre_aucune_session(monkeypatch):
    """LE POINT DE SÉCURITÉ. Le marqueur ne vaut RIEN sans le jeton du courriel : il ne prouve pas
    qu'on a lu la boîte mail, seulement qu'on a rempli un formulaire."""
    email = "marque-seul@test.fr"
    _oublier(email)
    c = TestClient(app)
    _inscrire(c, email, monkeypatch)
    _muet(monkeypatch)

    r = c.get("/api/auth/verify-email?token=jeton-invente-de-toutes-pieces")
    assert r.status_code == 400
    assert not c.cookies.get(auth._ACCESS), "aucune session ne doit s'ouvrir sans le lien"
    db = dbmod.SessionLocal()
    try:
        assert db.query(User).filter(User.email == email).first().is_verified is False
    finally:
        db.close()


def test_meme_navigateur_le_lien_ouvre_la_session(monkeypatch):
    """LE POINT QUI COMPTE. Le professeur vient de prouver qu'il possède l'adresse : lui
    redemander le mot de passe qu'il vient de choisir est une porte pour rien."""
    email = "meme-navigateur@test.fr"
    _oublier(email)
    c = TestClient(app)
    jeton = _inscrire(c, email, monkeypatch)
    _muet(monkeypatch)

    r = c.get(f"/api/auth/verify-email?token={jeton}")
    assert r.status_code == 200, r.text[:200]
    assert r.json()["connecte"] is True, "l'écran doit savoir qu'il peut ouvrir l'application"
    assert c.cookies.get(auth._ACCESS), "la session n'a pas été ouverte"
    assert c.cookies.get(auth._REFRESH)

    # Et la session vaut vraiment : elle donne accès à la fiche du professeur.
    assert c.get("/api/auth/me").status_code == 200


def test_le_lien_ouvert_sur_le_telephone_active_sans_connecter(monkeypatch):
    """Un lien d'activation traîne dans une boîte mail. Ouvert ailleurs, il active le compte et
    s'arrête là — sinon celui qui lit la boîte deviendrait le professeur."""
    email = "telephone@test.fr"
    _oublier(email)
    ordinateur = TestClient(app)
    jeton = _inscrire(ordinateur, email, monkeypatch)
    _muet(monkeypatch)

    telephone = TestClient(app)  # un autre appareil : aucun marqueur
    r = telephone.get(f"/api/auth/verify-email?token={jeton}")
    assert r.status_code == 200
    assert r.json()["connecte"] is False
    assert not telephone.cookies.get(auth._ACCESS), "aucune session hors du navigateur d'origine"

    # Le compte, lui, est bien activé : le professeur peut se connecter normalement.
    db = dbmod.SessionLocal()
    try:
        assert db.query(User).filter(User.email == email).first().is_verified is True
    finally:
        db.close()


def test_un_marqueur_d_une_autre_adresse_n_ouvre_rien(monkeypatch):
    """Deux inscriptions sur le même poste : le marqueur de l'une ne doit pas ouvrir la session
    de l'autre. Le marqueur porte une adresse, et elle doit correspondre."""
    premier, second = "premier@test.fr", "second@test.fr"
    _oublier(premier)
    _oublier(second)
    c = TestClient(app)
    _inscrire(c, premier, monkeypatch)          # le marqueur reste celui du premier
    marqueur_du_premier = c.cookies.get(auth._INSCRIPTION)
    jeton_du_second = _inscrire(TestClient(app), second, monkeypatch)
    _muet(monkeypatch)

    autre = TestClient(app)
    autre.cookies.set(auth._INSCRIPTION, marqueur_du_premier)
    r = autre.get(f"/api/auth/verify-email?token={jeton_du_second}")
    assert r.status_code == 200
    assert r.json()["connecte"] is False, "le marqueur ne vaut que pour SON adresse"
    assert not autre.cookies.get(auth._ACCESS)


def test_le_marqueur_ne_ressert_pas(monkeypatch):
    """Il est effacé au retour, quel que soit le résultat : ce qui ne sert qu'une fois ne doit pas
    rester à traîner dans un navigateur pendant une heure."""
    email = "usage-unique@test.fr"
    _oublier(email)
    c = TestClient(app)
    jeton = _inscrire(c, email, monkeypatch)
    _muet(monkeypatch)

    c.get(f"/api/auth/verify-email?token={jeton}")
    assert not c.cookies.get(auth._INSCRIPTION), "le marqueur devait être effacé"


def test_le_mail_de_bienvenue_part_sans_bouton_d_entree(monkeypatch):
    """Ce courriel arrive quand le professeur est DÉJÀ dans l'application. Un bouton
    « Accéder à aSchool » l'inviterait à y entrer une seconde fois — la porte de trop."""
    envoyes = []
    monkeypatch.setattr(comptes, "_smtp_send", lambda msg: envoyes.append(msg))
    comptes.send_custom_email("prof@test.fr", "Marie", "Bienvenue", "Bonjour {prenom},",
                              bouton=False)
    corps = envoyes[0].get_payload()[1].get_payload(decode=True).decode("utf-8")
    assert "Accéder à aSchool" not in corps

    # Un envoi groupé, lui, garde son bouton : il doit ramener le professeur vers l'application.
    envoyes.clear()
    comptes.send_custom_email("prof@test.fr", "Marie", "Nouveauté", "Bonjour {prenom},")
    corps = envoyes[0].get_payload()[1].get_payload(decode=True).decode("utf-8")
    assert "Accéder à aSchool" in corps
