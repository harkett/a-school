r"""Preuve de raccordement — Phase 4.1.e : le fournisseur LLM texte est lu au RUNTIME.

Ce que le test PROUVE (la chaine reelle remonte le bon fournisseur, pas « le code existe ») :
  1. get_ai_provider() lit la table Setting AU MOMENT de l'appel, avec repli sur le
     defaut code quand aucune ligne `ai_provider` n'existe.
  2. Le fournisseur change A CHAUD : modifier la ligne entre deux lectures, dans le MEME
     process, est pris en compte sans redemarrage (boot -> runtime, comme 4.1.a).
  3. generate() route selon le `provider` passe ; provider=None retombe sur AI_PROVIDER
     (config/.env) — retro-compatible.
  4. Chaine complete via l'endpoint /api/generate : le routeur resout get_ai_provider(db)
     et la valeur en base commande l'adaptateur appele (cablage routeur prouve).

Lancer : .\.venv\Scripts\python.exe -m pytest test_settings_provider.py -q
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
from backend.systeme.admin import get_ai_provider, SETTING_DEFAULTS
from backend.config import AI_PROVIDER
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
    """Remplace requests.post : capte l'URL appelee (l'adaptateur Groq tape l'API Groq)."""
    def _post(url, headers=None, json=None, timeout=None):
        capture["url"] = url
        capture["body"] = json
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"choices": [{"message": {"content": "OK"}}]}
        return resp
    return _post


# ===================== get_ai_provider : lecture DB avec repli =====================

def test_get_ai_provider_repli_sur_defaut_si_aucune_ligne():
    db = _fresh_db()
    assert get_ai_provider(db) == SETTING_DEFAULTS["ai_provider"]
    db.close()


def test_get_ai_provider_lit_la_valeur_en_base():
    db = _fresh_db()
    db.add(Setting(key="ai_provider", value="anthropic"))
    db.commit()
    assert get_ai_provider(db) == "anthropic"
    db.close()


def test_get_ai_provider_a_chaud_sans_redemarrage():
    # Changement en base entre deux lectures, MEME process -> pris en compte direct.
    db = _fresh_db()
    db.add(Setting(key="ai_provider", value="groq"))
    db.commit()
    assert get_ai_provider(db) == "groq"
    db.query(Setting).filter(Setting.key == "ai_provider").update({"value": "anthropic"})
    db.commit()
    assert get_ai_provider(db) == "anthropic"
    db.close()


# ============ generate() : le provider passe commande le routage ============

def test_generate_route_selon_le_provider_passe():
    # provider="groq" explicite -> adaptateur Groq (tape l'URL Groq), meme si AI_PROVIDER differe.
    cap = {}
    with patch.object(gen, "AI_PROVIDER", "anthropic"), patch.object(gen, "GROQ_API_KEY", "cle-test"), patch("requests.post", side_effect=_fake_groq_post(cap)):
        gen.generate("bonjour", provider="groq")
    assert "api.groq.com" in cap["url"]


def test_generate_repli_sur_AI_PROVIDER_si_provider_none():
    # provider=None -> retombe sur AI_PROVIDER (ici force a "groq") -> adaptateur Groq.
    cap = {}
    with patch.object(gen, "AI_PROVIDER", "groq"), patch.object(gen, "GROQ_API_KEY", "cle-test"), patch("requests.post", side_effect=_fake_groq_post(cap)):
        gen.generate("bonjour")
    assert "api.groq.com" in cap["url"]


def test_generate_provider_inconnu_leve():
    # Un provider non gere remonte une erreur claire (jamais un appel silencieux).
    import pytest
    with pytest.raises(ValueError):
        gen.generate("bonjour", provider="fournisseur-bidon")


# ============ Chaine complete via /api/generate (cablage routeur prouve) ============

def test_endpoint_generate_utilise_le_provider_en_base():
    # Le fournisseur ecrit en base ("groq") commande l'adaptateur appele par le routeur.
    db = _fresh_db()
    db.add(Setting(key="ai_provider", value="groq"))
    db.commit()
    db.close()

    cap = {}
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    # build_prompt mocke : ce test porte sur le provider, pas sur l'assemblage du prompt.
    with patch("backend.activite.generate.build_prompt", return_value="PROMPT"), \
         patch.object(gen, "AI_PROVIDER", "anthropic"), \
         patch.object(gen, "GROQ_API_KEY", "cle-test"), \
         patch("requests.post", side_effect=_fake_groq_post(cap)):
        r = c.post("/api/generate", json={
            "activite_key": "comprehension", "texte": "Un texte.", "niveau": "4e",
        })
    # AI_PROVIDER force a "anthropic" : si le routeur ignorait la base, l'adaptateur Anthropic
    # serait appele (pas d'URL Groq capturee). L'URL Groq prouve que la base ("groq") a gagne.
    assert r.status_code == 200, r.text
    assert "api.groq.com" in cap["url"]
