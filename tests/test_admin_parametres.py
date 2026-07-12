r"""Preuve de raccordement — écran « Paramètres » : la table settings en LECTURE SEULE.

Ce que le test PROUVE (chaîne réelle, pas « le code existe ») :
  1. GET /admin/parametres renvoie les LIGNES RÉELLES de settings (JAMAIS le merge avec les
     défauts code) : table vide -> liste vide, malgré des défauts en dur côté code.
  2. Les clés à écran dédié sont marquées `ecran_dedie: true` (repère UI) ; la valeur remonte bien.
  3. Sans cookie admin -> 401.

L'écran ne modifie rien (plus de POST/PUT) : changer une valeur passe par un autre moyen
(un secret se change dans le .env, jamais dans l'UI).

Lancer : .\.venv\Scripts\python.exe -m pytest test_admin_parametres.py -q
"""
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.main import app
from backend.core.models_db import Setting, AiFournisseur
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _reset():
    db = dbmod.SessionLocal()
    db.query(Setting).delete()
    db.commit()
    db.close()


def _seed(key, value="v"):
    db = dbmod.SessionLocal()
    db.add(Setting(key=key, value=value))
    db.commit()
    db.close()


def test_get_lignes_reelles_jamais_les_defauts():
    # Table vide -> la liste doit être VIDE, même si SETTING_DEFAULTS contient des clés en dur.
    _reset()
    r = _admin().get("/api/admin/parametres")
    assert r.status_code == 200, r.text
    assert r.json() == []  # aucun merge avec les défauts code


def test_get_marque_ecran_dedie():
    _reset()
    _seed("ai_model", "claude-sonnet-5")     # clé à écran dédié
    _seed("cle_env_ocr", "GROQ_API_KEY_OCR")  # paramètre pur
    data = {p["key"]: p for p in _admin().get("/api/admin/parametres").json()}
    assert data["ai_model"]["ecran_dedie"] is True
    assert data["cle_env_ocr"]["ecran_dedie"] is False
    # la valeur remonte bien
    assert data["cle_env_ocr"]["value"] == "GROQ_API_KEY_OCR"
    # une clé NON pointeur n'a ni libellé ni ligne pointée
    assert data["cle_env_ocr"]["label"] is None
    assert data["cle_env_ocr"]["pointe_vers"] is None


def _reset_fournisseurs():
    db = dbmod.SessionLocal()
    db.query(AiFournisseur).delete()
    db.commit()
    db.close()


def test_pointeur_resout_label_et_ligne():
    # settings.ai_provider = 'anthropic' pointe vers la ligne ai_fournisseurs 'anthropic' :
    # l'endpoint doit renvoyer le LIBELLÉ (pas le code) + la ligne pointée complète.
    _reset()
    _reset_fournisseurs()
    db = dbmod.SessionLocal()
    db.add(AiFournisseur(code="anthropic", label="Anthropic (Claude)", actif=True, ordre=2,
                         cle_env="CLAUDE_API_KEY_TEXTE"))
    db.commit()
    db.close()
    _seed("ai_provider", "anthropic")
    data = {p["key"]: p for p in _admin().get("/api/admin/parametres").json()}
    row = data["ai_provider"]
    assert row["value"] == "anthropic"                 # le code brut reste disponible
    assert row["label"] == "Anthropic (Claude)"        # le LIBELLÉ, pas le code
    assert row["pointe_vers"]["table"] == "ai_fournisseurs"
    assert row["pointe_vers"]["code"] == "anthropic"
    assert row["pointe_vers"]["cle_env"] == "CLAUDE_API_KEY_TEXTE"
    assert row["pointe_vers"]["actif"] is True
    assert row["pointe_vers"]["ordre"] == 2


def test_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/parametres").status_code == 401
