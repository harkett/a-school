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
from backend.core.models_db import Setting, AiModele, AiFournisseur
from backend.systeme.admin import _make_admin_token, get_ai_provider
from fastapi.testclient import TestClient

VALID = "groq"                     # fournisseur actif seedé, aussi le défaut de get_ai_provider
SUPPORTED = ["groq", "anthropic"]  # attendus dans l'ordre `ordre` (groq=1, anthropic=2)


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _seed_fournisseurs():
    """Fournisseurs offerts, désormais lus EN BASE (table ai_fournisseurs). aschool_test est
    vidée entre tests → on sème groq + anthropic (actifs) avant chaque appel aux endpoints."""
    db = dbmod.SessionLocal()
    db.query(AiFournisseur).delete()
    db.add_all([
        AiFournisseur(code="groq", label="Groq", actif=True, ordre=1, cle_env="GROQ_API_KEY"),
        AiFournisseur(code="anthropic", label="Anthropic (Claude)", actif=True, ordre=2,
                      cle_env="CLAUDE_API_KEY_TEXTE"),
    ])
    db.commit()
    db.close()


def _reset():
    """Vide settings, puis re-sème les fournisseurs (isolation entre tests)."""
    db = dbmod.SessionLocal()
    db.query(Setting).delete()
    db.commit()
    db.close()
    _seed_fournisseurs()


def _setting_row(key):
    db = dbmod.SessionLocal()
    row = db.query(Setting).filter(Setting.key == key).first()
    val = row.value if row else None
    db.close()
    return val


def test_get_ai_providers_liste_et_courant():
    _reset()
    r = _admin().get("/api/admin/ai-providers")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["supported"] == SUPPORTED  # lus en base (table ai_fournisseurs), tri par `ordre`
    assert data["current"] == VALID  # repli sur le defaut, aucune ligne ai_provider en base


def test_put_fournisseur_valide_ecrit_en_base():
    _reset()
    assert _setting_row("ai_provider") is None  # rien avant
    r = _admin().put("/api/admin/ai-provider", json={"provider": VALID})
    assert r.status_code == 200, r.text
    assert _setting_row("ai_provider") == VALID  # ligne ecrite
    assert _admin().get("/api/admin/ai-providers").json()["current"] == VALID


def test_put_fournisseur_vide_refuse_400_rien_ecrit():
    _reset()
    r = _admin().put("/api/admin/ai-provider", json={"provider": "   "})
    assert r.status_code == 400, r.text
    assert "pris en charge" in r.json()["detail"]
    assert _setting_row("ai_provider") is None  # rien ecrit


def test_put_fournisseur_hors_liste_refuse_400_rien_ecrit():
    _reset()
    r = _admin().put("/api/admin/ai-provider", json={"provider": "fournisseur-bidon"})
    assert r.status_code == 400, r.text
    assert _setting_row("ai_provider") is None


def test_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/ai-providers").status_code == 401
    assert TestClient(app).put("/api/admin/ai-provider", json={"provider": VALID}).status_code == 401


def test_put_settings_email_n_altere_pas_le_fournisseur():
    # Endpoint dedie : le PUT email ne doit jamais toucher ai_provider (isolation).
    _reset()
    _admin().put("/api/admin/ai-provider", json={"provider": VALID})
    assert _setting_row("ai_provider") == VALID
    r = _admin().put("/api/admin/settings", json={
        "welcome_email_subject": "Sujet X", "welcome_email_body": "Corps Y",
    })
    assert r.status_code == 200, r.text
    assert _setting_row("ai_provider") == VALID  # intact


def _seed_modele_groq():
    # Un modèle groq actif en base : le PUT /ai-model valide désormais contre ai_modeles.
    db = dbmod.SessionLocal()
    db.query(AiModele).delete()
    db.add(AiModele(fournisseur="groq", modele="llama-3.3-70b-versatile", label="Llama 3.3 70B",
                    recommande=True, actif=True, ordre=0))
    db.commit()
    db.close()


def test_put_fournisseur_n_altere_pas_le_modele():
    # Endpoints dedies, jamais melanges : ecrire le fournisseur ne touche pas ai_model.
    _reset()
    _seed_modele_groq()
    MODELE = "llama-3.3-70b-versatile"  # fournisseur courant par defaut = groq
    _admin().put("/api/admin/ai-model", json={"model": MODELE})
    assert _setting_row("ai_model") == MODELE
    r = _admin().put("/api/admin/ai-provider", json={"provider": VALID})
    assert r.status_code == 200, r.text
    assert _setting_row("ai_model") == MODELE  # intact
    assert _setting_row("ai_provider") == VALID
