r"""Preuve de raccordement — Phase 4.1.e (e.4) : l'admin ecrit le fournisseur, avec validation.

Ce que le test PROUVE (chaine reelle, pas « le code existe ») :
  1. GET /admin/ai-providers renvoie la liste blanche + le fournisseur courant.
  2. PUT /admin/ai-provider avec une valeur de la liste blanche : 200, la cle `ai_provider`
     est ecrite en base (get_ai_provider la renvoie).
  3. PUT avec une valeur VIDE ou HORS liste : 400 (message humain pour la modale),
     RIEN n'est ecrit.
  4. Sans cookie admin : 401.
  5. Isolation : PUT /admin/settings (email) n'altere PAS `ai_provider` ; et PUT
     /admin/ai-provider n'altere PAS `ai_model` (endpoints dedies, jamais melanges).

Lancer : .\.venv\Scripts\python.exe -m pytest test_admin_ai_provider.py -q
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
import backend.core.database as dbmod

from backend.main import app
from backend.core.models_db import Setting
from backend.systeme.admin import (
    _make_admin_token, SUPPORTED_AI_PROVIDERS, SUPPORTED_AI_MODELS, get_ai_provider,
)
from fastapi.testclient import TestClient

VALID = SUPPORTED_AI_PROVIDERS[0]


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _reset_settings():
    db = dbmod.SessionLocal()
    db.query(Setting).delete()
    db.commit()
    db.close()


def _setting_row(key):
    db = dbmod.SessionLocal()
    row = db.query(Setting).filter(Setting.key == key).first()
    val = row.value if row else None
    db.close()
    return val


def test_get_ai_providers_liste_et_courant():
    _reset_settings()
    r = _admin().get("/api/admin/ai-providers")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["supported"] == SUPPORTED_AI_PROVIDERS
    assert data["current"] == VALID  # repli sur le defaut, aucune ligne en base


def test_put_fournisseur_valide_ecrit_en_base():
    _reset_settings()
    assert _setting_row("ai_provider") is None  # rien avant
    r = _admin().put("/api/admin/ai-provider", json={"provider": VALID})
    assert r.status_code == 200, r.text
    assert _setting_row("ai_provider") == VALID  # ligne ecrite
    assert _admin().get("/api/admin/ai-providers").json()["current"] == VALID


def test_put_fournisseur_vide_refuse_400_rien_ecrit():
    _reset_settings()
    r = _admin().put("/api/admin/ai-provider", json={"provider": "   "})
    assert r.status_code == 400, r.text
    assert "pris en charge" in r.json()["detail"]
    assert _setting_row("ai_provider") is None  # rien ecrit


def test_put_fournisseur_hors_liste_refuse_400_rien_ecrit():
    _reset_settings()
    r = _admin().put("/api/admin/ai-provider", json={"provider": "fournisseur-bidon"})
    assert r.status_code == 400, r.text
    assert _setting_row("ai_provider") is None


def test_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/ai-providers").status_code == 401
    assert TestClient(app).put("/api/admin/ai-provider", json={"provider": VALID}).status_code == 401


def test_put_settings_email_n_altere_pas_le_fournisseur():
    # Endpoint dedie : le PUT email ne doit jamais toucher ai_provider (isolation).
    _reset_settings()
    _admin().put("/api/admin/ai-provider", json={"provider": VALID})
    assert _setting_row("ai_provider") == VALID
    r = _admin().put("/api/admin/settings", json={
        "welcome_email_subject": "Sujet X", "welcome_email_body": "Corps Y",
    })
    assert r.status_code == 200, r.text
    assert _setting_row("ai_provider") == VALID  # intact


def test_put_fournisseur_n_altere_pas_le_modele():
    # Endpoints dedies, jamais melanges : ecrire le fournisseur ne touche pas ai_model.
    _reset_settings()
    _admin().put("/api/admin/ai-model", json={"model": SUPPORTED_AI_MODELS[0]})
    assert _setting_row("ai_model") == SUPPORTED_AI_MODELS[0]
    r = _admin().put("/api/admin/ai-provider", json={"provider": VALID})
    assert r.status_code == 200, r.text
    assert _setting_row("ai_model") == SUPPORTED_AI_MODELS[0]  # intact
    assert _setting_row("ai_provider") == VALID
