r"""Preuve de raccordement — Phase 5 : code d'erreur 429 distinct (surcharge / rate limit).

Ce que le test PROUVE (le bon code HTTP ressort vraiment, pas « le code existe ») :
  1. Rate limit AMONT (le fournisseur répond 429) -> le routeur renvoie 429 (pas 500/502).
  2. Saturation LOCALE (aucun créneau libre) -> le routeur renvoie 429.
  3. Prouvé sur DEUX chemins au comportement différent avant : detect-ambiguites (500 avant)
     ET generate (502 avant) -> la distinction remplace bien les deux.
  4. Dictée (groq_client) : réponse 429 du fournisseur -> HTTPException 429 (pas 502).

Lancer : .\.venv\Scripts\python.exe -m pytest test_llm_429.py -q
"""
import os
import sys
import threading

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from unittest.mock import MagicMock, patch

import pytest

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.main import app
from backend.auth import create_access_token
import src.generator as gen
import backend.core.groq_client as gc
from fastapi import HTTPException
from fastapi.testclient import TestClient

TOKEN = create_access_token("prof.test@aschool.fr")


def _reset_sem():
    """Sémaphore large + délai normal : les tests « amont » prennent un créneau sans souci."""
    gen._llm_semaphore = threading.BoundedSemaphore(8)
    gen.AI_SLOT_TIMEOUT = 30


def _post_429(*args, **kwargs):
    """Faux fournisseur qui répond 429 (rate limit amont)."""
    resp = MagicMock()
    resp.status_code = 429
    resp.ok = False
    resp.text = "rate limit"
    return resp


def _client_prof():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


# ===================== 1. Rate limit amont -> 429 =====================

def test_ambiguites_429_amont():
    _reset_sem()
    with patch.object(gen, "AI_PROVIDER", "groq"), patch.object(gen, "GROQ_API_KEY", "cle-test"), \
         patch("requests.post", side_effect=_post_429):
        r = _client_prof().post("/api/detect-ambiguites", json={
            "texte": "Un enonce.", "matiere": "Mathematiques", "niveau": "4e",
        })
    assert r.status_code == 429, r.text                 # avant : 500
    assert "instant" in r.json()["detail"].lower()


def test_generate_429_amont():
    _reset_sem()
    with patch("backend.activite.generate.build_prompt", return_value="PROMPT"), \
         patch.object(gen, "AI_PROVIDER", "groq"), \
         patch.object(gen, "GROQ_API_KEY", "cle-test"), \
         patch("requests.post", side_effect=_post_429):
        r = _client_prof().post("/api/generate", json={
            "activite_key": "comprehension", "texte": "Un texte.", "niveau": "4e",
        })
    assert r.status_code == 429, r.text                 # avant : 502
    assert "instant" in r.json()["detail"].lower()


# ===================== 2. Saturation locale -> 429 =====================

def test_ambiguites_429_saturation():
    gen._llm_semaphore = threading.BoundedSemaphore(1)
    gen.AI_SLOT_TIMEOUT = 0.1
    gen._llm_semaphore.acquire()                        # on occupe le seul créneau
    try:
        with patch.object(gen, "AI_PROVIDER", "groq"), patch("requests.post") as post:
            r = _client_prof().post("/api/detect-ambiguites", json={
                "texte": "Un enonce.", "matiere": "Mathematiques", "niveau": "4e",
            })
            assert r.status_code == 429, r.text
            post.assert_not_called()                    # aucun appel réseau : pas de créneau
    finally:
        gen._llm_semaphore.release()
    _reset_sem()


# ===================== 3. Dictée (groq_client) -> 429 =====================

def test_dictee_429_amont():
    _reset_sem()
    with patch("requests.post", side_effect=_post_429):
        with pytest.raises(HTTPException) as exc:
            gc.transcribe_audio(b"xxxx", filename="audio.webm", content_type="audio/webm", api_key="cle-test")
    assert exc.value.status_code == 429                 # avant : 502
