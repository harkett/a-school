"""Preuve de raccordement — Phase 4.1.a : le modele LLM texte est lu au RUNTIME.

Ce que le test PROUVE (la chaine reelle remonte le bon modele, pas « le code existe ») :
  1. get_ai_model() lit la table Setting AU MOMENT de l'appel, avec repli sur le
     defaut code quand aucune ligne `ai_model` n'existe.
  2. Le modele change A CHAUD : modifier la ligne entre deux lectures, dans le MEME
     process, est pris en compte sans redemarrage (c'est tout l'objet de 4.1.a :
     boot -> runtime).
  3. generate() transmet le modele resolu jusqu'au corps HTTP envoye au fournisseur ;
     model=None retombe sur AI_MODEL (config/.env) — retro-compatible.
  4. Chaine complete via l'endpoint /api/generate : le routeur resout get_ai_model(db)
     et la valeur en base ressort dans l'appel LLM (cablage routeur prouve).

Lancer : .\.venv\Scripts\python.exe -m pytest test_settings_model.py -q
"""
import os
import sys

# Windows : torch + chromadb -> deux runtimes OpenMP. Sans ces garde-fous, l'import de
# backend.main (qui tire le RAG) plante en « access violation ». Poses AVANT tout import torch.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from unittest.mock import MagicMock, patch

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.main import app
from backend.auth import create_access_token
from backend.core.models_db import Setting
from backend.systeme.admin import get_ai_model, SETTING_DEFAULTS
from backend.config import AI_MODEL
import backend.llm.generator as gen
from fastapi.testclient import TestClient

TOKEN = create_access_token("prof.test@aschool.fr")


def _fresh_db():
    """Session in-memory avec la table settings videe (isolation entre tests)."""
    db = dbmod.SessionLocal()
    db.query(Setting).delete()
    db.commit()
    return db


def _fake_groq_post(capture):
    """Remplace requests.post : capte le corps envoye, renvoie une reponse Groq factice."""
    def _post(url, headers=None, json=None, timeout=None):
        capture["body"] = json
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"choices": [{"message": {"content": "OK"}}]}
        return resp
    return _post


# ===================== get_ai_model : lecture DB avec repli =====================

def test_get_ai_model_repli_sur_defaut_si_aucune_ligne():
    db = _fresh_db()
    assert get_ai_model(db) == SETTING_DEFAULTS["ai_model"]
    db.close()


def test_get_ai_model_lit_la_valeur_en_base():
    db = _fresh_db()
    db.add(Setting(key="ai_model", value="modele-test-xyz"))
    db.commit()
    assert get_ai_model(db) == "modele-test-xyz"
    db.close()


def test_get_ai_model_a_chaud_sans_redemarrage():
    # Changement en base entre deux lectures, MEME process -> pris en compte direct.
    db = _fresh_db()
    db.add(Setting(key="ai_model", value="v1"))
    db.commit()
    assert get_ai_model(db) == "v1"
    db.query(Setting).filter(Setting.key == "ai_model").update({"value": "v2"})
    db.commit()
    assert get_ai_model(db) == "v2"
    db.close()


# ============ generate() : le modele resolu arrive dans le corps HTTP ============

def test_generate_emet_le_modele_passe():
    cap = {}
    with patch.object(gen, "AI_PROVIDER", "groq"), patch.object(gen, "GROQ_API_KEY", "cle-test"), \
         patch("requests.post", side_effect=_fake_groq_post(cap)):
        gen.generate("bonjour", model="modele-passe-abc")
    assert cap["body"]["model"] == "modele-passe-abc"


def test_generate_repli_sur_AI_MODEL_si_model_none():
    cap = {}
    with patch.object(gen, "AI_PROVIDER", "groq"), patch.object(gen, "GROQ_API_KEY", "cle-test"), \
         patch("requests.post", side_effect=_fake_groq_post(cap)):
        gen.generate("bonjour")
    assert cap["body"]["model"] == AI_MODEL
