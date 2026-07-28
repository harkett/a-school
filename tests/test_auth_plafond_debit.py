r"""Preuve de raccordement — Lot 0 : delai SMTP + plafond de debit des routes ouvertes.

Ce que les tests PROUVENT (la chaine reelle, pas « le code existe ») :
  1. _smtp_send passe bien un `timeout` a smtplib.SMTP — sans lui, un serveur de mail muet
     bloquait le fil d'execution indefiniment. Aucune vraie connexion n'est ouverte.
  2. smtp_check.py (diagnostic manuel) pose le meme delai.
  3. Les 3 routes OUVERTES (aucune authentification) qui declenchent un envoi repondent 429
     au-dela de leur plafond : /auth/request-reset, /auth/resend-verification, /auth/signup.
  4. Le corps du 429 porte un message HUMAIN sous la cle `detail` (RÈGLE 23) — et surtout PAS
     la cle `error` du gestionnaire slowapi, que les ecrans ne lisent pas (le prof y voyait
     « Erreur 429 » via Signup.jsx).
  5. NO-REGRESSION : resend-verification et request-reset, qui n'avaient PAS de parametre
     `request`, repondent toujours 200 sous le plafond — slowapi leve « No "request" argument »
     si la signature n'en porte pas, donc un 200 prouve que le raccordement est correct.

Les seuils ne sont JAMAIS recopies ici : ils sont lus depuis les constantes du limiteur.

Lancer : .\.venv\Scripts\python.exe -m pytest test_auth_plafond_debit.py -q
"""
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from email.mime.text import MIMEText

import pytest
from fastapi.testclient import TestClient

# engine / SessionLocal rediriges vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod  # noqa: F401
import backend.auth as auth_lib
from backend.core.limiter import (
    PLAFOND_DEMANDE_RESET,
    PLAFOND_RENVOI_VERIFICATION,
    PLAFOND_SIGNUP,
    limiter,
)
from backend.main import app


def _seuil(plafond: str) -> int:
    """Nombre d'appels autorises, lu depuis la constante (« 5/hour » -> 5). Zero seuil en dur."""
    return int(plafond.split("/")[0])


@pytest.fixture(autouse=True)
def _compteurs_a_zero():
    """Les compteurs slowapi vivent en memoire du process : sans remise a zero, un test
    hériterait du plafond deja consomme par le precedent."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def _smtp_muet(monkeypatch):
    """Aucun mail ne part pendant les tests : la porte SMTP unique est remplacee."""
    envoyes = []
    monkeypatch.setattr(auth_lib, "_smtp_send", lambda msg: envoyes.append(msg))
    return envoyes


# ── 1-2. Delai d'attente SMTP ──────────────────────────────────────────────

class _FauxSMTP:
    """Remplace smtplib.SMTP : capture les arguments d'appel, n'ouvre aucune connexion."""
    dernier_appel = {}

    def __init__(self, host, port, *args, **kwargs):
        type(self).dernier_appel = {"host": host, "port": port, **kwargs}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def ehlo(self):
        pass

    def starttls(self):
        pass

    def login(self, user, pwd):
        pass

    def send_message(self, msg):
        pass


def test_smtp_send_pose_un_delai_d_attente(monkeypatch):
    monkeypatch.setattr(auth_lib.smtplib, "SMTP", _FauxSMTP)
    auth_lib._smtp_send(MIMEText("corps de test"))
    assert "timeout" in _FauxSMTP.dernier_appel, "smtplib.SMTP appele SANS timeout — blocage infini possible"
    assert _FauxSMTP.dernier_appel["timeout"] == auth_lib._SMTP_TIMEOUT
    assert auth_lib._SMTP_TIMEOUT > 0


def test_diagnostic_smtp_pose_aussi_un_delai():
    """Le script de diagnostic manuel ouvre sa propre connexion : il doit borner l'attente
    lui aussi, sinon `python backend/mail/smtp_check.py` reste suspendu sans rien dire."""
    source = (
        open(os.path.join(os.path.dirname(ROOT), "backend", "mail", "smtp_check.py"),
             encoding="utf-8").read()
    )
    assert "timeout=" in source, "smtp_check.py ouvre une connexion SMTP sans timeout"


# ── 3-4. Plafond de debit des routes ouvertes ──────────────────────────────

def test_request_reset_plafonne_au_dela_du_seuil(_smtp_muet):
    client = TestClient(app)
    for i in range(_seuil(PLAFOND_DEMANDE_RESET)):
        r = client.post("/api/auth/request-reset", json={"email": "inconnu@exemple.fr"})
        assert r.status_code == 200, f"appel {i + 1} refuse avant le plafond : {r.text}"
    refuse = client.post("/api/auth/request-reset", json={"email": "inconnu@exemple.fr"})
    assert refuse.status_code == 429, "route ouverte NON plafonnee — envoi de masse possible"


def test_resend_verification_plafonne_au_dela_du_seuil(_smtp_muet):
    client = TestClient(app)
    for i in range(_seuil(PLAFOND_RENVOI_VERIFICATION)):
        r = client.post("/api/auth/resend-verification", json={"email": "inconnu@exemple.fr"})
        assert r.status_code == 200, f"appel {i + 1} refuse avant le plafond : {r.text}"
    refuse = client.post("/api/auth/resend-verification", json={"email": "inconnu@exemple.fr"})
    assert refuse.status_code == 429, "route ouverte NON plafonnee — envoi de masse possible"


def test_signup_plafonne_au_dela_du_seuil(_smtp_muet):
    client = TestClient(app)
    corps = {"password": "MotDePasse123", "password_confirm": "MotDePasse123"}
    for i in range(_seuil(PLAFOND_SIGNUP)):
        r = client.post("/api/auth/signup", json={"email": f"prof{i}@exemple.fr", **corps})
        assert r.status_code == 201, f"inscription {i + 1} refusee avant le plafond : {r.text}"
    refuse = client.post("/api/auth/signup", json={"email": "detrop@exemple.fr", **corps})
    assert refuse.status_code == 429, "inscription NON plafonnee — envoi de masse possible"


def test_message_du_plafond_est_humain_et_sous_la_cle_detail(_smtp_muet):
    client = TestClient(app)
    for _ in range(_seuil(PLAFOND_DEMANDE_RESET)):
        client.post("/api/auth/request-reset", json={"email": "inconnu@exemple.fr"})
    refuse = client.post("/api/auth/request-reset", json={"email": "inconnu@exemple.fr"})
    assert refuse.status_code == 429

    corps = refuse.json()
    # Les ecrans lisent TOUS `detail` (ex. Signup.jsx) — la cle `error` de slowapi y donnait
    # « Erreur 429 » a l'utilisateur.
    assert "detail" in corps, f"cle `detail` absente du 429 : {corps}"
    assert "error" not in corps, f"cle technique `error` encore presente : {corps}"
    # Message humain : francais, actionnable, aucune trace technique (RÈGLE 23).
    assert "Trop de demandes" in corps["detail"]
    assert "Rate limit" not in corps["detail"]
    assert "429" not in corps["detail"]


# ── 5. NO-REGRESSION : le parametre `request` ajoute aux deux routes ────────

def test_les_deux_routes_sans_request_repondent_toujours(_smtp_muet):
    """slowapi leve « No "request" or "websocket" argument on function » si la signature
    n'expose pas `request`. Ces deux routes ne l'avaient pas : un 200 prouve l'ajout."""
    client = TestClient(app)
    assert client.post("/api/auth/resend-verification",
                       json={"email": "inconnu@exemple.fr"}).status_code == 200
    assert client.post("/api/auth/request-reset",
                       json={"email": "inconnu@exemple.fr"}).status_code == 200
