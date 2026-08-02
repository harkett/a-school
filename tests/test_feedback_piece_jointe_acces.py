r"""Preuve d'acces — QUI a le droit de telecharger une piece jointe de retour.

GET /feedback/attachment/{filename} ouvre deux portes : le prof PROPRIETAIRE du retour, et
l'admin. La porte admin verifiait le cookie aschool_admin avec le verificateur PROF
(comptes.verify_access_token). Or les deux jetons n'ont ni la meme cle de signature
(ADMIN_JWT_SECRET contre JWT_SECRET) ni la meme forme (role == "admin" contre type == "access").

Deux degats, et non un seul :

  1. L'admin n'entrait JAMAIS par sa porte — mauvaise cle, et aucun champ `type` dans son jeton.
     Il retombait sur la branche prof : 401 sans session prof, ou la recherche d'un retour
     appartenant a son propre compte prof s'il en avait une.

  2. Un prof qui recopiait la valeur de son cookie aschool_access dans un cookie NOMME
     aschool_admin passait, lui : bonne cle, bon `type`. Il devenait admin et sautait
     entierement le controle de propriete — il telechargeait n'importe quelle piece jointe
     dont il connaissait le nom.

Aucun test ne couvrait cette route : c'est ce qui a laisse passer le trou. Ces trois-la
tiennent les trois chemins reels, pas « le code existe ».

Lancer : docker compose exec backend python -m pytest tests/test_feedback_piece_jointe_acces.py -q
"""
from fastapi.testclient import TestClient

# engine / SessionLocal rediriges vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod
import backend.securite.comptes as comptes
from backend.communication.feedback import UPLOAD_DIR
from backend.core.models_db import Feedback, User
from backend.main import app
from backend.systeme.admin import _make_admin_token

EMAIL_PROPRIETAIRE = "marie@college.fr"
EMAIL_AUTRE_PROF = "paul@college.fr"


def _prof_avec_piece_jointe(email, nom_fichier, contenu=b"le contenu joint"):
    """Un prof verifie, son retour, et le fichier REELLEMENT pose sur le disque (dossier
    temporaire pose par conftest.py). Sans le fichier, la route repondrait 404 et le test
    ne prouverait plus rien du controle d'acces, qui se joue AVANT."""
    db = dbmod.SessionLocal()
    user = User(email=email, password_hash="x", is_verified=True, prenom="Marie")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(Feedback(user_id=user.id, type="feedback", message="La generation plante.",
                    rating=0, category="bug", statut="nouveau", attachment_path=nom_fichier))
    db.commit()
    db.close()
    (UPLOAD_DIR / nom_fichier).write_bytes(contenu)
    return nom_fichier


def _client_prof(email):
    c = TestClient(app)
    c.cookies.set("aschool_access", comptes.create_access_token(email))
    return c


def test_admin_telecharge_la_piece_jointe_d_un_prof():
    """Cas 1 : l'admin passe par SA porte. Il n'a aucun compte prof, aucun cookie
    aschool_access — avant, il tombait donc en 401 sur sa propre route."""
    nom = _prof_avec_piece_jointe(EMAIL_PROPRIETAIRE, "aaaa1111.png", b"image du prof")

    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    r = c.get(f"/api/feedback/attachment/{nom}")

    assert r.status_code == 200, r.text
    assert r.content == b"image du prof"


def test_un_prof_ne_devient_pas_admin_en_recopiant_son_jeton():
    """Cas 2 : le jeton PROF depose dans le cookie aschool_admin ne doit plus ouvrir la porte
    admin. La piece jointe visee n'appartient pas a ce prof : le controle de propriete doit
    donc s'appliquer et refuser."""
    nom = _prof_avec_piece_jointe(EMAIL_PROPRIETAIRE, "bbbb2222.png")

    jeton_prof = comptes.create_access_token(EMAIL_AUTRE_PROF)
    db = dbmod.SessionLocal()
    db.add(User(email=EMAIL_AUTRE_PROF, password_hash="x", is_verified=True, prenom="Paul"))
    db.commit()
    db.close()

    c = TestClient(app)
    c.cookies.set("aschool_access", jeton_prof)
    c.cookies.set("aschool_admin", jeton_prof)   # le geste exact de l'escalade
    r = c.get(f"/api/feedback/attachment/{nom}")

    assert r.status_code == 403, r.text


def test_le_prof_proprietaire_telecharge_toujours_la_sienne():
    """La correction ne devait rien retirer au prof legitime."""
    nom = _prof_avec_piece_jointe(EMAIL_PROPRIETAIRE, "cccc3333.png", b"ma propre image")

    r = _client_prof(EMAIL_PROPRIETAIRE).get(f"/api/feedback/attachment/{nom}")

    assert r.status_code == 200, r.text
    assert r.content == b"ma propre image"
