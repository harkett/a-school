r"""L'administration est un compte de `users`, plus un mot de passe posé à côté.

CE QUE CES TESTS PROUVENT (base aschool_test via conftest.py — JAMAIS SQLite) :

  1. Un compte `role = 'admin'` ouvre l'administration avec SON mot de passe, celui de sa ligne.
  2. Un compte `role = 'prof'` ne l'ouvre pas, même avec son mot de passe juste. C'est le rôle
     qui décide, pas la seule connaissance d'un mot de passe valide.
  3. Un administrateur DÉSACTIVÉ n'ouvre plus : couper un compte doit couper tous ses accès.
  4. LE FILET — tant qu'aucun compte `admin` n'existe en base, les variables d'environnement
     ouvrent comme avant. Sans lui, une base neuve mettrait dehors sans retour possible.
  5. Un compte `admin` en base FERME la porte du .env : deux mots de passe qui ouvrent, dont un
     qu'on croit retiré, c'est exactement ce qu'on venait de corriger côté `admin_password_hash`.
  6. Le journal des connexions nomme CELUI qui est entré, et non une adresse d'installation
     valable pour tout le monde.

Lancer : docker compose exec backend python -m pytest tests/test_admin_est_un_compte.py -q
"""
import os

import bcrypt
import pytest

from backend.core.database import SessionLocal
from backend.core.models_db import ConnexionLog, Setting, User
from backend.main import app
from fastapi.testclient import TestClient

MOT_DE_PASSE = "recette-Motdepasse-17"
ADMIN = "admin.test@aschool.fr"
PROF = "prof.test@aschool.fr"


def _empreinte(clair: str) -> str:
    return bcrypt.hashpw(clair.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")


def _poser(email: str, role: str, actif: bool = True) -> None:
    with SessionLocal() as db:
        db.query(User).filter(User.email == email).delete()
        db.add(User(email=email, password_hash=_empreinte(MOT_DE_PASSE), is_verified=True,
                    is_active=actif, role=role))
        db.commit()


@pytest.fixture(autouse=True)
def table_propre():
    """Aucun administrateur au départ : chaque test pose exactement ce qu'il veut prouver."""
    with SessionLocal() as db:
        db.query(User).filter(User.email.in_([ADMIN, PROF])).delete(synchronize_session=False)
        db.query(User).filter(User.role == "admin").update({"role": "prof"},
                                                           synchronize_session=False)
        db.commit()
    yield
    with SessionLocal() as db:
        db.query(User).filter(User.email.in_([ADMIN, PROF])).delete(synchronize_session=False)
        db.commit()


def _connexion(identifiant: str, mot_de_passe: str):
    return TestClient(app).post("/api/admin/login",
                                json={"username": identifiant, "password": mot_de_passe})


def test_un_compte_admin_ouvre_l_administration():
    _poser(ADMIN, "admin")
    r = _connexion(ADMIN, MOT_DE_PASSE)
    assert r.status_code == 200, r.text


def test_un_compte_prof_ne_l_ouvre_pas():
    """Le mot de passe est juste, le rôle ne l'est pas. C'est le rôle qui décide."""
    _poser(ADMIN, "admin")
    _poser(PROF, "prof")
    assert _connexion(PROF, MOT_DE_PASSE).status_code == 401


def test_un_administrateur_desactive_n_ouvre_plus():
    _poser(ADMIN, "admin", actif=False)
    assert _connexion(ADMIN, MOT_DE_PASSE).status_code == 401


def test_le_filet_ouvre_quand_la_base_n_a_aucun_admin():
    """Une base neuve n'a pas de compte d'administration : le .env doit encore ouvrir, sinon
    l'installation se verrouille elle-même dès la première migration."""
    with SessionLocal() as db:
        db.query(Setting).filter(Setting.key == "admin_password_hash").delete()
        db.commit()
    identifiant = os.getenv("ADMIN_USERNAME", "")
    clair = os.getenv("ADMIN_PASSWORD", "")
    if not identifiant or not clair:
        pytest.skip("ADMIN_USERNAME / ADMIN_PASSWORD absents de cet environnement")
    assert _connexion(identifiant, clair).status_code == 200


def test_un_compte_admin_ferme_la_porte_du_env():
    """Deux mots de passe qui ouvrent, dont un qu'on croit retiré : c'est le défaut qu'on venait
    de corriger sur `admin_password_hash`. Il ne revient pas par cette porte."""
    _poser(ADMIN, "admin")
    identifiant = os.getenv("ADMIN_USERNAME", "")
    clair = os.getenv("ADMIN_PASSWORD", "")
    if not identifiant or not clair:
        pytest.skip("ADMIN_USERNAME / ADMIN_PASSWORD absents de cet environnement")
    assert _connexion(identifiant, clair).status_code == 401


def test_le_journal_nomme_celui_qui_est_entre():
    _poser(ADMIN, "admin")
    with SessionLocal() as db:
        db.query(ConnexionLog).filter(ConnexionLog.email == ADMIN).delete()
        db.commit()

    assert _connexion(ADMIN, MOT_DE_PASSE).status_code == 200

    with SessionLocal() as db:
        trace = (db.query(ConnexionLog)
                   .filter(ConnexionLog.email == ADMIN, ConnexionLog.action == "admin_login")
                   .first())
    assert trace is not None, "la connexion n'a pas été tracée sous l'adresse de l'administrateur"
