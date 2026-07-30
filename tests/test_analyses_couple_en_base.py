"""Preuve — les DEUX analyses (Ambiguïtés, Consigne) lisent le couple EN BASE.

Ce que ces tests PROUVENT (base aschool_test via conftest.py, LLM MOQUÉ — aucun appel réel) :
  1. Le prompt part avec le couple RÉSOLU EN BASE (couple_de_travail — décision 25/07) ;
     un couple encore envoyé par un écran (corps forgé) est IGNORÉ, les champs ont quitté
     le modèle de requête — le serveur ne fait plus confiance à l'écran (trou du check-up).
  2. Profil sans couple → 400 humain, AUCUN appel LLM.
"""
import os
import sys
from unittest.mock import patch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import backend.core.database as dbmod
from backend.auth import create_access_token
from backend.main import app
from fastapi.testclient import TestClient
from _profil import user_couple

EMAIL = "prof.analyses@aschool.fr"

AMB_JSON = '{"ambiguites": [], "verdict": "RAS"}'
CONS_JSON = '{"analyses": [], "verdict": "RAS", "version_optimisee": "ok"}'


def _client():
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(EMAIL))
    return c


def _prof(subject=None, niveau=None):
    with dbmod.SessionLocal() as db:
        db.add(user_couple(db, email=EMAIL, password_hash="x", is_verified=True,
                           subject=subject, niveau=niveau))
        db.commit()


def test_ambiguites_prompt_porte_le_couple_de_la_base():
    _prof(subject="AC-Fr", niveau="AC-6e")
    with patch("backend.analyse.ambiguites.generate", return_value=AMB_JSON) as gen, \
         patch("backend.analyse.ambiguites.get_cle_texte", return_value="cle-test"):
        r = _client().post("/api/detect-ambiguites", json={
            "texte": "Consigne à analyser.",
            "matiere": "MAT-FORGEE", "niveau": "NIV-FORGE",   # ignorés : hors modèle de requête
        })
    assert r.status_code == 200, r.text
    prompt = gen.call_args.args[0]
    assert "AC-Fr" in prompt and "AC-6e" in prompt
    assert "MAT-FORGEE" not in prompt and "NIV-FORGE" not in prompt


def test_ambiguites_sans_couple_400_humain_zero_llm():
    _prof()   # profil sans matière ni niveau
    with patch("backend.analyse.ambiguites.generate") as gen:
        r = _client().post("/api/detect-ambiguites", json={"texte": "Un énoncé."})
    assert r.status_code == 400, r.text
    assert "Mon profil" in r.json()["detail"]
    gen.assert_not_called()


def test_consigne_prompt_porte_le_couple_de_la_base():
    _prof(subject="AC-Fr", niveau="AC-6e")
    with patch("backend.analyse.consigne.generate", return_value=CONS_JSON) as gen, \
         patch("backend.analyse.consigne.get_cle_texte", return_value="cle-test"):
        r = _client().post("/api/analyser-consigne", json={
            "consigne": "Recopie la phrase.",
            "matiere": "MAT-FORGEE", "niveau": "NIV-FORGE",   # ignorés : hors modèle de requête
        })
    assert r.status_code == 200, r.text
    prompt = gen.call_args.args[0]
    assert "AC-Fr" in prompt and "AC-6e" in prompt
    assert "MAT-FORGEE" not in prompt and "NIV-FORGE" not in prompt


def test_consigne_sans_couple_400_humain_zero_llm():
    _prof()
    with patch("backend.analyse.consigne.generate") as gen:
        r = _client().post("/api/analyser-consigne", json={"consigne": "Recopie."})
    assert r.status_code == 400, r.text
    assert "Mon profil" in r.json()["detail"]
    gen.assert_not_called()
