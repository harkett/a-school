r"""Preuve — le clic du prof sur « Démonstration » redirige, il ne plante pas.

LE DÉFAUT CORRIGÉ (15/08/2026). `/demo/aller` appelait `/demo/pour-moi` comme une simple
fonction Python, en lui passant l'utilisateur et la session mais PAS la requête — que sa
signature exige en premier paramètre. Python levait « missing 1 required positional argument:
'request' » avant d'avoir rien fait, et le prof recevait « Internal Server Error » sur une page
blanche. Rien dans l'écran ne pouvait le prévenir : l'entrée du menu s'affichait active, car
c'est `/demo/pour-moi` qui décide de son grisé, et cette route-là, appelée normalement par
FastAPI, fonctionnait parfaitement. La panne n'apparaissait qu'AU CLIC.

POURQUOI CE PIÈGE EXISTE. FastAPI n'injecte les `Depends` et la `Request` qu'à l'entrée d'une
requête HTTP. Une route qui en appelle une autre en Python ordinaire n'obtient rien : elle doit
fournir elle-même TOUS les paramètres. Un appel qui en oublie un ne se voit ni à la lecture ni au
démarrage — seulement quand quelqu'un clique.

CE QUE LE TEST PROUVE :
  1. Le clic redirige (307) vers l'adresse de la démonstration, jeton accroché.
  2. Le jeton porte le prof et SON niveau.
  3. Une démonstration sans adresse refuse en 409 — un message, jamais une 500.
  4. Un prof sans niveau reçoit lui aussi un 409 lisible.
  5. `/demo/pour-moi` et `/demo/aller` sont d'accord : ce que la première déclare disponible,
     la seconde le sert. C'est cet accord que la panne avait rompu.

Base de test PostgreSQL dédiée (aschool_test via conftest.py) — JAMAIS SQLite.
Lancer : docker compose exec backend python -m pytest tests/test_demo_passage_du_prof.py -q
"""
import os

import pytest
from fastapi.testclient import TestClient
from jose import jwt

import backend.core.database as dbmod
from backend.core.models_db import Cycle, Demo, Matiere, Niveau, Referentiel, User
from backend.main import app
from backend.securite.comptes import create_access_token

SECRET = "secret-de-test-pour-le-passage-demo"
EMAIL = "prof.passage@aschool.fr"
NIVEAU = "Niveau de test du passage"
MATIERE = "Matière de test du passage"
URL = "http://demo-du-test.local"

_AVANT = {}


def setup_module(_module):
    for cle in ("DEMO_SECRET",):
        _AVANT[cle] = os.environ.get(cle)
    os.environ["DEMO_SECRET"] = SECRET


def teardown_module(_module):
    for cle, valeur in _AVANT.items():
        if valeur is None:
            os.environ.pop(cle, None)
        else:
            os.environ[cle] = valeur


def _semer(avec_url=True, avec_niveau=True):
    """Un prof, son niveau, son référentiel et la démonstration de ce référentiel."""
    db = dbmod.SessionLocal()
    db.query(User).filter(User.email == EMAIL).delete()
    db.query(Demo).delete()
    db.query(Matiere).delete()
    db.query(Referentiel).delete()
    db.query(Niveau).delete()
    db.query(Cycle).delete()
    db.commit()

    cycle = Cycle(nom="Cycle du passage", ordre=1); db.add(cycle); db.flush()
    niveau = Niveau(nom=NIVEAU, cycle_id=cycle.id, ordre=1); db.add(niveau); db.flush()
    ref = Referentiel(niveau_id=niveau.id, nom_fixe="ref_passage", collection="passage")
    db.add(ref); db.flush()
    mat = Matiere(nom=MATIERE, referentiel_id=ref.id, ordre=1, actif=True)
    db.add(mat); db.flush()
    db.add(Demo(referentiel_id=ref.id, nom_base="passage_demo", url=URL if avec_url else None))
    db.add(User(email=EMAIL, password_hash="x", is_verified=True,
                subject_id=mat.id if avec_niveau else None,
                niveau_id=niveau.id if avec_niveau else None))
    db.commit(); db.close()


@pytest.fixture
def client():
    c = TestClient(app, follow_redirects=False)
    c.cookies.set("aschool_access", create_access_token(EMAIL))
    return c


def test_le_clic_redirige_au_lieu_de_planter(client):
    """LE test de la panne : avant la correction, cette ligne rendait 500."""
    _semer()
    r = client.get("/api/demo/aller")
    assert r.status_code == 307, r.text
    assert r.headers["location"].startswith(f"{URL}/demo?jeton=")


def test_le_jeton_porte_le_prof_et_son_niveau(client):
    _semer()
    cible = client.get("/api/demo/aller").headers["location"]
    charge = jwt.decode(cible.split("jeton=", 1)[1], SECRET, algorithms=["HS256"])
    assert charge["email"] == EMAIL
    assert charge["niveau"] == NIVEAU
    assert charge["matiere"] == MATIERE


def test_une_demo_sans_adresse_refuse_avec_un_message(client):
    """409 et une phrase — jamais une 500, qui ne dit rien au prof.

    L'ADRESSE EST LE SEUL CONTRÔLE depuis le 16/08/2026. Ce test posait le statut « fait » pour
    fermer la porte ; les cinq statuts ont été supprimés — ils doublaient exactement ce que dit
    l'absence d'adresse : la démonstration n'est pas en ligne, personne n'y entre."""
    _semer(avec_url=False)
    r = client.get("/api/demo/aller")
    assert r.status_code == 409, r.text
    assert "en ligne" in r.json()["detail"].lower()


def test_un_prof_sans_niveau_recoit_un_refus_lisible(client):
    _semer(avec_niveau=False)
    r = client.get("/api/demo/aller")
    assert r.status_code == 409, r.text
    assert "niveau" in r.json()["detail"].lower()


def test_les_deux_routes_sont_d_accord(client):
    """Ce que le menu déclare disponible, le clic doit le servir. La panne rompait cet accord :
    `/demo/pour-moi` disait oui, `/demo/aller` rendait 500."""
    for avec_url, attendu in ((True, 307), (False, 409)):
        _semer(avec_url=avec_url)
        dispo = client.get("/api/demo/pour-moi").json()["disponible"]
        r = client.get("/api/demo/aller")
        assert r.status_code == attendu, r.text
        assert dispo is (attendu == 307)
