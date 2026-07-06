"""Preuve de raccordement — Phase 4.1.b : l'admin ecrit le modele LLM, avec validation.

Ce que le test PROUVE (chaine reelle, pas « le code existe ») :
  1. GET /admin/ai-models renvoie la liste blanche + le modele courant.
  2. PUT /admin/ai-model avec une valeur de la liste blanche : 200, la cle `ai_model`
     est ecrite en base (get_ai_model la renvoie).
  3. PUT avec une valeur VIDE ou HORS liste : 400 (message humain pour la modale),
     RIEN n'est ecrit.
  4. Sans cookie admin : 401.
  5. Isolation : PUT /admin/settings (email) n'altere PAS `ai_model` (endpoint dedie).

Lancer : .\.venv\Scripts\python.exe -m pytest test_admin_ai_model.py -q
"""
import os
import sys

# Windows : torch + chromadb -> deux runtimes OpenMP. Garde-fous AVANT tout import torch.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.database as dbmod

from backend.main import app
from backend.models_db import Setting
from backend.systeme.admin import _make_admin_token, SUPPORTED_AI_MODELS, get_ai_model
from fastapi.testclient import TestClient

VALID = SUPPORTED_AI_MODELS[0]


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _reset_settings():
    db = dbmod.SessionLocal()
    db.query(Setting).delete()
    db.commit()
    db.close()


def _ai_model_row():
    db = dbmod.SessionLocal()
    row = db.query(Setting).filter(Setting.key == "ai_model").first()
    val = row.value if row else None
    db.close()
    return val


def test_get_ai_models_liste_et_courant():
    _reset_settings()
    r = _admin().get("/api/admin/ai-models")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["supported"] == SUPPORTED_AI_MODELS
    assert data["current"] == VALID  # repli sur le defaut, aucune ligne en base


def test_put_modele_valide_ecrit_en_base():
    _reset_settings()
    assert _ai_model_row() is None  # rien avant
    r = _admin().put("/api/admin/ai-model", json={"model": VALID})
    assert r.status_code == 200, r.text
    assert _ai_model_row() == VALID  # ligne ecrite
    # GET reflete le courant
    assert _admin().get("/api/admin/ai-models").json()["current"] == VALID


def test_put_modele_vide_refuse_400_rien_ecrit():
    _reset_settings()
    r = _admin().put("/api/admin/ai-model", json={"model": "   "})
    assert r.status_code == 400, r.text
    assert "pris en charge" in r.json()["detail"]
    assert _ai_model_row() is None  # rien ecrit


def test_put_modele_hors_liste_refuse_400_rien_ecrit():
    _reset_settings()
    r = _admin().put("/api/admin/ai-model", json={"model": "gpt-4o-inexistant"})
    assert r.status_code == 400, r.text
    assert _ai_model_row() is None


def test_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/ai-models").status_code == 401
    assert TestClient(app).put("/api/admin/ai-model", json={"model": VALID}).status_code == 401


def test_put_settings_email_n_altere_pas_le_modele():
    # Endpoint dedie : le PUT email ne doit jamais toucher ai_model (isolation).
    _reset_settings()
    _admin().put("/api/admin/ai-model", json={"model": VALID})
    assert _ai_model_row() == VALID
    r = _admin().put("/api/admin/settings", json={
        "welcome_email_subject": "Sujet X", "welcome_email_body": "Corps Y",
    })
    assert r.status_code == 200, r.text
    assert _ai_model_row() == VALID  # intact
