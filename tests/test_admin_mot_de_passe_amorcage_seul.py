r"""Le mot de passe du .env AMORCE, il n'ouvre pas pour toujours.

CE QUE CE TEST PROUVE, et pourquoi il existe. Les deux routes du mot de passe admin ne
disaient PAS la même chose :

  - /admin/change-password (admin.py:938) refusait le mot de passe du .env comme « mot de
    passe actuel » dès qu'un mot de passe existait en base : `if pwd_setting: ... else: ...` ;
  - /admin/login (admin.py:506) faisait `password_ok = env_ok or db_ok` : le mot de passe du
    .env ouvrait TOUJOURS, y compris après un changement.

Conséquence concrète : le bouton « changer mon mot de passe » ne fermait rien. L'ancien mot
de passe — celui écrit en clair dans le .env, donc présent dans chaque copie du dossier et
dans chaque sauvegarde — continuait d'ouvrir la porte d'entrée.

La règle est désormais la même des deux côtés : tant qu'aucun mot de passe n'a été choisi,
celui du .env amorce ; dès qu'un existe en base, LUI SEUL ouvre.

SECOURS. Mot de passe oublié : supprimer la ligne `admin_password_hash` de la table
`settings` remet celui du .env en service. Le dernier test le prouve — ce n'est pas une
promesse de documentation, c'est un chemin vérifié.

Lancer : docker compose exec backend python -m pytest tests/test_admin_mot_de_passe_amorcage_seul.py -q
"""
import bcrypt

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.main import app
from backend.core.models_db import Setting, FailedLoginAttempt
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

USER = "admin-de-test"
ENV_PASS = "mot-de-passe-du-env"
CHOISI = "celui-que-j-ai-choisi"

# /admin/login est limité à 10 appels par heure (slowapi, mémoire du process). Ce fichier en
# fait quatre : garder de la marge si on en ajoute.


def _reset(avec_hash: bool):
    """Table settings et tentatives ratées remises à zéro ; hash posé ou non.

    `alerte_tentatives_1h` est semé par MIGRATION ; la base de test est bâtie par create_all,
    donc la ligne n'y est pas. Le chemin d'échec de /admin/login la lit (seuil de blocage) et
    rend un 500 explicite si elle manque — on la pose ici pour tester le mot de passe, pas ça.
    """
    db = dbmod.SessionLocal()
    db.query(Setting).filter(Setting.key == "admin_password_hash").delete()
    db.query(FailedLoginAttempt).delete()
    if not db.query(Setting).filter(Setting.key == "alerte_tentatives_1h").first():
        db.add(Setting(key="alerte_tentatives_1h", value="10"))
    if avec_hash:
        h = bcrypt.hashpw(CHOISI.encode("utf-8"), bcrypt.gensalt(4)).decode("utf-8")
        db.add(Setting(key="admin_password_hash", value=h))
    db.commit()
    db.close()


def _env(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", USER)
    monkeypatch.setenv("ADMIN_PASSWORD", ENV_PASS)


def _login(mot_de_passe):
    return TestClient(app).post("/api/admin/login",
                                json={"username": USER, "password": mot_de_passe})


def test_sans_mot_de_passe_en_base_le_env_amorce(monkeypatch):
    """Première installation : rien en base, le .env est la seule clé et il ouvre."""
    _env(monkeypatch)
    _reset(avec_hash=False)
    assert _login(ENV_PASS).status_code == 200


def test_un_mot_de_passe_en_base_ferme_la_porte_du_env(monkeypatch):
    """LA régression à empêcher : après un changement, l'ancien ne doit plus ouvrir."""
    _env(monkeypatch)
    _reset(avec_hash=True)
    r = _login(ENV_PASS)
    assert r.status_code == 401, (
        "Le mot de passe du .env ouvre encore alors qu'un mot de passe est posé en base : "
        "on est revenu au `env_ok or db_ok`, et le bouton « changer mon mot de passe » ment."
    )


def test_le_mot_de_passe_choisi_ouvre(monkeypatch):
    """L'autre moitié : fermer la porte du .env n'a de sens que si la nouvelle clé marche."""
    _env(monkeypatch)
    _reset(avec_hash=True)
    assert _login(CHOISI).status_code == 200


def test_supprimer_la_ligne_en_base_remet_le_env_en_service(monkeypatch):
    """La procédure de secours de PROJET.md, vérifiée : on ne peut pas rester enfermé dehors."""
    _env(monkeypatch)
    _reset(avec_hash=True)
    db = dbmod.SessionLocal()
    db.query(Setting).filter(Setting.key == "admin_password_hash").delete()
    db.commit()
    db.close()
    assert _login(ENV_PASS).status_code == 200


def test_le_changement_de_mot_de_passe_dit_la_meme_chose_que_la_connexion(monkeypatch):
    """Les deux routes s'accordent : le .env n'est pas non plus le « mot de passe actuel »."""
    _env(monkeypatch)
    _reset(avec_hash=True)
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    r = c.post("/api/admin/change-password", json={
        "old_password": ENV_PASS,
        "new_password": "un-tout-nouveau-mdp",
        "new_password_confirm": "un-tout-nouveau-mdp",
    })
    assert r.status_code == 400, r.text
    _reset(avec_hash=False)  # ne pas laisser de hash derrière soi
