r"""Preuve de raccordement — l'admin peut visiter N'IMPORTE QUELLE démonstration.

POURQUOI CETTE PORTE EXISTE (07/08/2026). Le passage du prof (`/demo/aller`) l'envoie vers la
démonstration de SON niveau, et seulement si elle est « testée » ou « validée ». Conséquence
constatée : l'administrateur, dont le compte est BTS CIEL Option A, ne pouvait ouvrir ni la
démonstration de l'option B, ni celle de la crèche — ni aucune démonstration fraîchement
fabriquée, puisque c'est en la visitant qu'on décide de la déclarer testée. Il aurait fallu se
fabriquer un compte par niveau. La route `/admin/demos/{id}/aller` lève ces deux limites, pour
l'administrateur seulement.

Ce que le test PROUVE (chaîne réelle) :
  1. Sans cookie admin : 401 — la porte n'est pas ouverte à tout le monde.
  2. Avec cookie admin, sur une démonstration d'un AUTRE niveau que le sien :
     307 vers l'adresse de l'instance, jeton accroché.
  3. Le jeton est signé avec DEMO_SECRET et porte l'identité de l'admin, le NIVEAU DE LA
     DÉMONSTRATION VISÉE (et non celui de l'admin) et une matière de son référentiel.
  4. Une démonstration sans adresse : 409 avec un message lisible, pas une redirection cassée.
  5. Une démonstration inconnue : 404.
  6. Le niveau emporté est bien celui de la démo demandée, démo par démo — c'est le cœur du
     besoin : deux démos de niveaux différents, deux jetons différents.

Lancer : docker compose exec backend python -m pytest tests/test_demo_visite_admin.py -q
"""
import os

from fastapi.testclient import TestClient
from jose import jwt

import backend.core.database as dbmod
from backend.main import app
from backend.core.models_db import Cycle, Demo, Matiere, Niveau, Referentiel
from backend.systeme.admin import _make_admin_token

SECRET = "secret-de-test-pour-le-passage-demo"
ADMIN = "admin.test@aschool.fr"


def _admin():
    c = TestClient(app, follow_redirects=False)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _semer():
    """Deux démonstrations de NIVEAUX DIFFÉRENTS — c'est-à-dire
    invisibles pour un prof. Rend (id_demo_a, id_demo_b)."""
    db = dbmod.SessionLocal()
    db.query(Demo).delete()
    db.query(Matiere).delete()
    db.query(Referentiel).delete()
    db.query(Niveau).delete()
    db.query(Cycle).delete()
    db.commit()

    cycle = Cycle(nom="Cycle de test", ordre=1)
    db.add(cycle)
    db.flush()
    faits = []
    for nom_niveau, nom_base, url, matiere in (
        ("Niveau A de test", "atest_demo", "http://demo-a.test", "Mathématiques de test"),
        ("Niveau B de test", "btest_demo", "http://demo-b.test", "Physique de test"),
    ):
        niveau = Niveau(nom=nom_niveau, cycle_id=cycle.id, ordre=1)
        db.add(niveau)
        db.flush()
        ref = Referentiel(niveau_id=niveau.id, nom_fixe=f"Référentiel {nom_niveau}",
                          collection=nom_base)
        db.add(ref)
        db.flush()
        db.add(Matiere(nom=matiere, referentiel_id=ref.id, ordre=1, actif=True))
        d = Demo(referentiel_id=ref.id, nom_base=nom_base, url=url)
        db.add(d)
        db.flush()
        faits.append((d.id, nom_niveau, matiere))
    db.commit()
    db.close()
    return faits


def _charge(reponse):
    """La charge du jeton accroché à l'adresse de redirection."""
    cible = reponse.headers["location"]
    return jwt.decode(cible.split("jeton=", 1)[1], SECRET, algorithms=["HS256"])


# Les variables posées pour ce fichier sont RENDUES à la fin. Sans ça, elles fuient vers les
# tests suivants — et ceux qui vérifient qu'un secret absent fait bien lever se retrouvent avec
# un secret posé par quelqu'un d'autre. Une suite doit laisser l'environnement comme elle l'a
# trouvé, sinon son résultat dépend de l'ordre des fichiers.
_AVANT = {}


def setup_module(_module):
    for cle in ("DEMO_SECRET", "ADMIN_EMAIL", "MODE_DEMO"):
        _AVANT[cle] = os.environ.get(cle)
    os.environ["DEMO_SECRET"] = SECRET
    os.environ["ADMIN_EMAIL"] = ADMIN
    os.environ.pop("MODE_DEMO", None)


def teardown_module(_module):
    for cle, valeur in _AVANT.items():
        if valeur is None:
            os.environ.pop(cle, None)
        else:
            os.environ[cle] = valeur


def test_sans_cookie_admin_la_porte_est_fermee():
    faits = _semer()
    r = TestClient(app, follow_redirects=False).get(f"/api/admin/demos/{faits[0][0]}/aller")
    assert r.status_code == 401


def test_une_demo_en_preparation_reste_visitable_par_l_admin():
    """Statut « fait » : le prof est refusé, l'admin passe. C'est TOUT le sujet de la route."""
    (id_a, _niveau, _mat), _b = _semer()
    r = _admin().get(f"/api/admin/demos/{id_a}/aller")
    assert r.status_code == 307, r.text
    assert r.headers["location"].startswith("http://demo-a.test/demo?jeton=")


def test_le_jeton_porte_l_admin_et_le_niveau_de_la_demo_visee():
    (id_a, niveau_a, matiere_a), _b = _semer()
    charge = _charge(_admin().get(f"/api/admin/demos/{id_a}/aller"))
    assert charge["typ"] == "passage_demo"
    assert charge["email"] == ADMIN
    assert charge["niveau"] == niveau_a
    assert charge["matiere"] == matiere_a


def test_deux_demos_donnent_deux_niveaux_differents():
    """Le besoin d'origine : ouvrir la crèche le matin et le BTS l'après-midi, sans changer de
    compte. Si le niveau emporté était celui de l'admin, les deux jetons seraient identiques."""
    (id_a, niveau_a, _), (id_b, niveau_b, _) = _semer()
    c = _admin()
    assert _charge(c.get(f"/api/admin/demos/{id_a}/aller"))["niveau"] == niveau_a
    assert _charge(c.get(f"/api/admin/demos/{id_b}/aller"))["niveau"] == niveau_b
    assert niveau_a != niveau_b


def test_sans_adresse_le_refus_est_lisible():
    faits = _semer()
    db = dbmod.SessionLocal()
    d = db.get(Demo, faits[0][0])
    d.url = None
    db.commit()
    db.close()
    r = _admin().get(f"/api/admin/demos/{faits[0][0]}/aller")
    assert r.status_code == 409
    assert "adresse" in r.json()["detail"].lower()


def test_demo_inconnue():
    _semer()
    assert _admin().get("/api/admin/demos/999999/aller").status_code == 404


def test_sans_secret_partage_aucun_passage():
    """Pas de repli : sans DEMO_SECRET, la porte se ferme au lieu d'émettre un jeton non signé."""
    faits = _semer()
    ancien = os.environ.pop("DEMO_SECRET", None)
    try:
        r = _admin().get(f"/api/admin/demos/{faits[0][0]}/aller")
        assert r.status_code == 409
        assert "DEMO_SECRET" in r.json()["detail"]
    finally:
        if ancien:
            os.environ["DEMO_SECRET"] = ancien
