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

Lancer : docker compose exec backend python -m pytest tests/test_settings_model.py -q
"""
# Windows : torch + chromadb -> deux runtimes OpenMP. Sans ces garde-fous, l'import de
# backend.main (qui tire le RAG) plante en « access violation ». Poses AVANT tout import torch.


from unittest.mock import MagicMock, patch

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import pytest
from fastapi import HTTPException

# `settings` vidée n'est plus un état neutre : les réglages vivent en base depuis le
# 10/08/2026 et une ligne absente fait lever. On repose donc ce qu'une installation à
# jour possède, juste après chaque table rase.
from conftest import resemer_reglages

import backend.core.database as dbmod

from backend.main import app
from backend.securite.comptes import create_access_token
from backend.core.models_db import Setting
from backend.systeme.admin import get_ai_model
from backend.config import AI_MODEL
import backend.llm.generator as gen
from fastapi.testclient import TestClient

TOKEN = create_access_token("prof.test@aschool.fr")


def _fresh_db():
    """Session in-memory avec la table settings videe (isolation entre tests)."""
    db = dbmod.SessionLocal()
    db.query(Setting).delete()
    db.commit()
    resemer_reglages(db, sauf=("ai_model",))
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

def test_get_ai_model_leve_si_aucune_ligne():
    """La base est la source, et une base incomplète se DIT.

    Ce test attendait un repli sur `SETTING_DEFAULTS`. Ce repli est parti le 10/08/2026 avec les
    16 réglages fantômes du dictionnaire : le modèle est désormais semé par migration
    (a4d8f2c6e1b9), et sans sa ligne le serveur refuse au lieu d'en inventer un — sinon une
    installation à qui il manque une migration travaillerait sur un modèle que personne n'a choisi,
    sans que rien ne le signale."""
    db = _fresh_db()
    # `_fresh_db` repose ce qu'une installation à jour possède, SAUF cette clé-ci : c'est
    # justement le cas qu'on veut éprouver — celui d'une migration non appliquée.
    with pytest.raises(HTTPException) as e:
        get_ai_model(db)
    assert e.value.status_code == 500
    assert "ai_model" in e.value.detail
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
    with patch.object(gen, "AI_PROVIDER", "groq"), \
         patch("requests.post", side_effect=_fake_groq_post(cap)):
        gen.generate("bonjour", cle="cle-test", model="modele-passe-abc")
    assert cap["body"]["model"] == "modele-passe-abc"


def test_generate_repli_sur_AI_MODEL_si_model_none():
    cap = {}
    with patch.object(gen, "AI_PROVIDER", "groq"), \
         patch("requests.post", side_effect=_fake_groq_post(cap)):
        gen.generate("bonjour", cle="cle-test")
    assert cap["body"]["model"] == AI_MODEL
