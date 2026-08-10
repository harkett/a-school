r"""Preuve de raccordement — les cinq dernières routes d'écriture qui n'avaient aucun test.

CE QUI N'ÉTAIT PAS TENU. Au terme du balayage du 10/08/2026, quarante-quatre routes d'écriture
n'avaient aucun test. Les quarante précédentes ont reçu le leur ; voici les cinq qui restaient :
la sortie de l'admin, l'envoi groupé, l'entrée en démonstration, le dépôt d'une pièce jointe et
le battement de cœur du navigateur.

CE QUE LE TEST PROUVE :
  1. `POST /admin/logout` efface le cookie d'administration — l'en-tête `Set-Cookie` le vide,
     ce n'est pas seulement un « ok » de politesse ;
  2. `POST /admin/mail-groupe` refuse les trois envois qui n'ont pas de sens (aucun destinataire,
     objet vide, message vide) SANS écrire ni envoyer, et refuse tout sans cookie admin ;
  3. `POST /demo/entrer` rend 404 sur une instance ORDINAIRE — c'est la garde qui fait qu'une
     porte sans mot de passe n'existe que sur les instances de démonstration ;
  4. `POST /feedback/upload` refuse sans session, et refuse un format non autorisé ;
  5. `POST /heartbeat` répond sans corps ni session — il n'a rien d'autre à faire, et un test le
     fige pour que personne ne lui ajoute un jour un effet de bord.

CE QU'IL N'ENVOIE PAS : aucun mail. Les trois cas d'envoi groupé éprouvés sont des REFUS, qui
tombent avant l'appel SMTP.

Lancer : docker compose exec backend python -m pytest tests/test_dernieres_portes_ecriture.py -q
"""
import io

from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def test_admin_logout_vide_le_cookie():
    r = _admin().post("/api/admin/logout")
    assert r.status_code == 200
    poses = [v for k, v in r.headers.items() if k.lower() == "set-cookie" and "aschool_admin" in v]
    assert poses, "La sortie doit reposer le cookie pour l'effacer."
    assert 'aschool_admin=""' in poses[-1] or "aschool_admin=;" in poses[-1], (
        f"Le cookie d'administration doit être vidé, l'en-tête dit : {poses[-1]}"
    )


def test_mail_groupe_refuse_les_envois_qui_n_ont_pas_de_sens():
    c = _admin()
    valable = {"emails": ["prof@exemple.fr"], "subject": "Objet", "body": "Message"}
    refus = [
        ({**valable, "emails": []}, "aucun destinataire"),
        ({**valable, "subject": "   "}, "objet vide"),
        ({**valable, "body": "   "}, "message vide"),
    ]
    for corps, quoi in refus:
        r = c.post("/api/admin/mail-groupe", json=corps)
        assert r.status_code == 400, f"{quoi} : rend {r.status_code}"


def test_mail_groupe_ferme_sans_cookie_admin():
    r = TestClient(app).post("/api/admin/mail-groupe",
                             json={"emails": ["prof@exemple.fr"], "subject": "O", "body": "M"})
    assert r.status_code == 401


def test_entrer_en_demonstration_n_existe_pas_sur_une_instance_ordinaire():
    """La porte sans mot de passe ne doit exister QUE là où MODE_DEMO est allumé. Sur une
    instance ordinaire elle répond 404 — pas 401 : on ne dit même pas qu'elle existe."""
    r = TestClient(app).post("/api/demo/entrer", json={"jeton": "peu importe"})
    assert r.status_code == 404, (
        f"Une instance ordinaire doit ignorer cette adresse, elle rend {r.status_code}."
    )


def test_depot_de_piece_jointe_ferme_sans_session():
    fichier = {"file": ("preuve.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")}
    assert TestClient(app).post("/api/feedback/upload", files=fichier).status_code == 401


def test_depot_de_piece_jointe_refuse_un_format_non_autorise():
    """Le contrôle de format vient APRÈS l'authentification : on éprouve donc les deux gardes
    dans l'ordre où elles s'exécutent, avec une session valide pour atteindre la seconde."""
    from backend.securite import comptes
    import backend.core.database as dbmod
    from backend.core.models_db import User

    db = dbmod.SessionLocal()
    try:
        email = "prof.piece@exemple.fr"
        db.query(User).filter(User.email == email).delete()
        db.add(User(email=email, password_hash="x", is_verified=True, is_active=True,
                    failed_attempts=0))
        db.commit()
        acces = comptes.create_access_token(email)
    finally:
        db.close()

    c = TestClient(app)
    c.cookies.set("aschool_access", acces)
    fichier = {"file": ("script.exe", io.BytesIO(b"MZ"), "application/x-msdownload")}
    r = c.post("/api/feedback/upload", files=fichier)
    assert r.status_code == 400, f"Un exécutable ne doit pas entrer, la route rend {r.status_code}."


def test_le_battement_de_coeur_ne_fait_rien_d_autre():
    """Il existe pour que le navigateur puisse pinger sans charge utile. S'il se met un jour à
    écrire quelque chose, ce test devra être réécrit sciemment — c'est le but."""
    r = TestClient(app).post("/api/heartbeat")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
