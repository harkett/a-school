r"""Preuve de raccordement — le catalogue de modèles LLM est LU EN BASE (table ai_modeles).

Ce que le test PROUVE (chaîne réelle, pas « le code existe ») :
  1. GET /admin/ai-models renvoie les modèles du FOURNISSEUR COURANT, lus en base,
     triés `recommande` puis `ordre`. Le modèle en base y apparaît (claude-opus-4-8).
  2. PUT /admin/ai-model avec un modèle EN BASE et actif : 200, la clé `ai_model` est écrite.
     -> le bug « claude-opus-4-8 en base mais inutilisable » est MORT.
  3. PUT avec une valeur VIDE, HORS base, ou d'un AUTRE fournisseur : 400, RIEN n'est écrit.
  4. Sans cookie admin : 401.
  5. Aucune liste en dur : ajouter un modèle = une ligne en base (aucun SUPPORTED_AI_MODELS).

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
import backend.core.database as dbmod

from backend.main import app
from backend.core.models_db import Setting, AiModele, AiFournisseur
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _reset():
    """Vide settings + catalogue, puis sème les fournisseurs (FK) PUIS les modèles (isolation).
    ai_modeles.fournisseur -> ai_fournisseurs.code : les fournisseurs doivent exister avant."""
    db = dbmod.SessionLocal()
    db.query(AiModele).delete()          # enfants d'abord (FK)
    db.query(AiFournisseur).delete()
    db.query(Setting).delete()
    db.add_all([
        AiFournisseur(code="anthropic", label="Anthropic (Claude)", actif=True, ordre=2,
                      cle_env="CLAUDE_API_KEY_TEXTE"),
        AiFournisseur(code="groq", label="Groq", actif=True, ordre=1, cle_env="GROQ_API_KEY"),
    ])
    db.flush()                           # fournisseurs visibles avant les modèles (FK)
    db.add_all([
        AiModele(fournisseur="anthropic", modele="claude-sonnet-5", label="Claude Sonnet 5",
                 recommande=True, actif=True, ordre=0),
        AiModele(fournisseur="anthropic", modele="claude-opus-4-8", label="Claude Opus 4.8",
                 recommande=False, actif=True, ordre=1),
        AiModele(fournisseur="groq", modele="llama-3.3-70b-versatile", label="Llama 3.3 70B",
                 recommande=True, actif=True, ordre=0),
    ])
    db.commit()
    db.close()


def _set_provider(nom):
    db = dbmod.SessionLocal()
    row = db.query(Setting).filter(Setting.key == "ai_provider").first()
    if row:
        row.value = nom
    else:
        db.add(Setting(key="ai_provider", value=nom))
    db.commit()
    db.close()


def _ai_model_row():
    db = dbmod.SessionLocal()
    row = db.query(Setting).filter(Setting.key == "ai_model").first()
    val = row.value if row else None
    db.close()
    return val


def test_get_ai_models_anthropic_liste_opus_en_base():
    _reset()
    _set_provider("anthropic")
    r = _admin().get("/api/admin/ai-models")
    assert r.status_code == 200, r.text
    # recommande d'abord (sonnet), puis ordre (opus) — les deux modèles anthropic actifs
    assert r.json()["supported"] == [
        {"modele": "claude-sonnet-5", "label": "Claude Sonnet 5"},
        {"modele": "claude-opus-4-8", "label": "Claude Opus 4.8"},
    ]
    # le modèle recommandé remonte dans le champ dédié -> l'admin affiche « (recommandé) »
    assert r.json()["recommande"] == "claude-sonnet-5"


def test_put_opus_accepte_le_bug_est_mort():
    _reset()
    _set_provider("anthropic")
    assert _ai_model_row() is None
    r = _admin().put("/api/admin/ai-model", json={"model": "claude-opus-4-8"})
    assert r.status_code == 200, r.text
    assert _ai_model_row() == "claude-opus-4-8"  # en base, actif -> ACCEPTÉ
    assert _admin().get("/api/admin/ai-models").json()["current"] == "claude-opus-4-8"


def test_get_ai_models_groq_liste_llama():
    _reset()
    _set_provider("groq")
    r = _admin().get("/api/admin/ai-models")
    assert r.status_code == 200, r.text
    assert r.json()["supported"] == [{"modele": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B"}]
    assert r.json()["recommande"] == "llama-3.3-70b-versatile"


def test_get_ai_models_param_fournisseur_prime_sur_le_courant():
    # Fournisseur COURANT = groq, mais la combo demande les modèles d'anthropic (sélection
    # pas encore enregistrée) -> ?fournisseur=anthropic prime, renvoie les modèles anthropic.
    _reset()
    _set_provider("groq")
    r = _admin().get("/api/admin/ai-models?fournisseur=anthropic")
    assert r.status_code == 200, r.text
    assert r.json()["supported"] == [
        {"modele": "claude-sonnet-5", "label": "Claude Sonnet 5"},
        {"modele": "claude-opus-4-8", "label": "Claude Opus 4.8"},
    ]
    assert r.json()["recommande"] == "claude-sonnet-5"


def test_put_modele_dun_autre_fournisseur_refuse_400():
    # provider=groq, mais on tente un modèle anthropic -> refusé (chaque modèle est lié à SON fournisseur)
    _reset()
    _set_provider("groq")
    r = _admin().put("/api/admin/ai-model", json={"model": "claude-opus-4-8"})
    assert r.status_code == 400, r.text
    assert _ai_model_row() is None


def test_put_modele_vide_refuse_400_rien_ecrit():
    _reset()
    _set_provider("anthropic")
    r = _admin().put("/api/admin/ai-model", json={"model": "   "})
    assert r.status_code == 400, r.text
    assert _ai_model_row() is None


def test_put_modele_hors_base_refuse_400_rien_ecrit():
    _reset()
    _set_provider("anthropic")
    r = _admin().put("/api/admin/ai-model", json={"model": "gpt-4o-inexistant"})
    assert r.status_code == 400, r.text
    assert _ai_model_row() is None


def test_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/ai-models").status_code == 401
    assert TestClient(app).put("/api/admin/ai-model", json={"model": "claude-opus-4-8"}).status_code == 401
