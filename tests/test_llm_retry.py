r"""Preuve de raccordement — Résilience 429 (retry automatique) : réglages en base + moteur + admin.

Ce que le test PROUVE (le comportement réel, pas « le code existe ») :
  1. get_retry_max / get_retry_wait_max : défauts (2 / 10) sans ligne en base ; valeur valide en base ->
     cette valeur ; hors bornes -> plafonnée aux bornes ; corrompue -> défaut (jamais d'exception) ;
     changement A CHAUD (même process, sans redémarrage).
  2. Moteur LLM (_groq_stream + _groq) : sur 429, RE-TENTE en respectant `Retry-After` plafonné ;
     429 en boucle -> LLMRateLimitError après épuisement ; retry_max=0 -> lève direct (aucun retry) ;
     attente plafonnée à retry_wait_max ; en-tête absent -> attente au plafond (hypothèse prudente).
  3. GET/PUT /admin/retry : lecture (défauts + bornes), écriture validée, 400 hors bornes (rien écrit),
     401 sans cookie admin.

Lancer : docker compose exec backend python -m pytest tests/test_llm_retry.py -q
"""
# Windows : torch + chromadb -> deux runtimes OpenMP. Garde-fous AVANT tout import torch.


from unittest.mock import MagicMock, patch

import pytest

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.main import app
from backend.core.models_db import Setting
from backend.systeme.admin import (
    get_retry_max, get_retry_wait_max,
    RETRY_MAX_MIN, RETRY_MAX_MAX, RETRY_WAIT_MIN, RETRY_WAIT_MAX,
    _make_admin_token,
)
import backend.llm.generator as gen
from fastapi.testclient import TestClient


def _fresh_db():
    db = dbmod.SessionLocal()
    db.query(Setting).delete()
    db.commit()
    return db


def _reset_settings():
    db = dbmod.SessionLocal()
    db.query(Setting).delete()
    db.commit()
    db.close()


def _row(key):
    db = dbmod.SessionLocal()
    row = db.query(Setting).filter(Setting.key == key).first()
    val = row.value if row else None
    db.close()
    return val


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


# --- Fausses réponses HTTP du fournisseur (Groq) ---

def _stream_resp(status, headers=None, lines=None):
    r = MagicMock()
    r.status_code = status
    r.ok = (status == 200)
    r.headers = headers or {}
    r.iter_lines.return_value = iter(lines or [])
    return r


def _json_resp(status, headers=None, content="OK"):
    r = MagicMock()
    r.status_code = status
    r.ok = (status == 200)
    r.headers = headers or {}
    r.json.return_value = {"choices": [{"message": {"content": content}}]}
    return r


_SSE_OK = [
    'data: {"choices":[{"delta":{"content":"Bonjour"}}]}',
    'data: {"choices":[{"delta":{"content":" monde"},"finish_reason":"stop"}]}',
    'data: [DONE]',
]


def _sleeps(mock_time):
    """Liste des durées passées à time.sleep (dans l'ordre)."""
    return [c.args[0] for c in mock_time.sleep.call_args_list]


# ===================== 1) get_retry_* : résolution en base =====================

def test_getters_defaut_sans_ligne():
    db = _fresh_db()
    assert get_retry_max(db) == 2
    assert get_retry_wait_max(db) == 10
    db.close()


def test_getters_valeurs_en_base():
    db = _fresh_db()
    db.add(Setting(key="ai_retry_max", value="4"))
    db.add(Setting(key="ai_retry_wait_max", value="25"))
    db.commit()
    assert get_retry_max(db) == 4
    assert get_retry_wait_max(db) == 25
    db.close()


def test_getters_hors_bornes_plafonnes():
    db = _fresh_db()
    db.add(Setting(key="ai_retry_max", value="99"))      # > MAX
    db.add(Setting(key="ai_retry_wait_max", value="0"))  # < MIN
    db.commit()
    assert get_retry_max(db) == RETRY_MAX_MAX
    assert get_retry_wait_max(db) == RETRY_WAIT_MIN
    db.close()


def test_getters_corrompus_repli_defaut():
    db = _fresh_db()
    db.add(Setting(key="ai_retry_max", value="abc"))
    db.add(Setting(key="ai_retry_wait_max", value="xyz"))
    db.commit()
    assert get_retry_max(db) == 2       # jamais d'exception
    assert get_retry_wait_max(db) == 10
    db.close()


def test_getter_a_chaud_sans_redemarrage():
    db = _fresh_db()
    db.add(Setting(key="ai_retry_max", value="1"))
    db.commit()
    assert get_retry_max(db) == 1
    db.query(Setting).filter(Setting.key == "ai_retry_max").update({"value": "3"})
    db.commit()
    assert get_retry_max(db) == 3  # pris en compte direct, même process
    db.close()


# ===================== 2) Moteur LLM : retry sur 429 =====================

def test_stream_429_puis_200_retente():
    seq = [_stream_resp(429, {"Retry-After": "3"}), _stream_resp(200, {}, _SSE_OK)]
    with patch.object(gen, "time", MagicMock()) as t, patch("requests.post", side_effect=seq) as p:
        out = "".join(gen._groq_stream("x", cle="k", retry_max=2, retry_wait_max=10))
    assert out == "Bonjour monde"   # le flux a bien abouti après la re-tentative
    assert p.call_count == 2
    assert _sleeps(t) == [3.0]       # a respecté Retry-After


def test_stream_429_en_boucle_leve_apres_essais():
    seq = [_stream_resp(429, {"Retry-After": "1"}) for _ in range(3)]  # 1 + 2 essais tous en 429
    with patch.object(gen, "time", MagicMock()), patch("requests.post", side_effect=seq):
        with pytest.raises(gen.LLMRateLimitError):
            list(gen._groq_stream("x", cle="k", retry_max=2, retry_wait_max=10))


def test_stream_retry_max_0_leve_direct():
    seq = [_stream_resp(429, {"Retry-After": "3"})]
    with patch.object(gen, "time", MagicMock()), patch("requests.post", side_effect=seq) as p:
        with pytest.raises(gen.LLMRateLimitError):
            list(gen._groq_stream("x", cle="k", retry_max=0, retry_wait_max=10))
    assert p.call_count == 1  # aucun retry : comportement historique


def test_stream_attente_plafonnee():
    seq = [_stream_resp(429, {"Retry-After": "30"}), _stream_resp(200, {}, _SSE_OK)]
    with patch.object(gen, "time", MagicMock()) as t, patch("requests.post", side_effect=seq):
        "".join(gen._groq_stream("x", cle="k", retry_max=1, retry_wait_max=10))
    assert _sleeps(t) == [10.0]  # Retry-After=30 mais plafond=10 -> on n'attend que 10


def test_stream_sans_retry_after_attend_le_plafond():
    seq = [_stream_resp(429, {}), _stream_resp(200, {}, _SSE_OK)]  # en-tête absent
    with patch.object(gen, "time", MagicMock()) as t, patch("requests.post", side_effect=seq):
        "".join(gen._groq_stream("x", cle="k", retry_max=1, retry_wait_max=7))
    assert _sleeps(t) == [7.0]  # absent -> hypothèse prudente = le plafond


def test_non_stream_429_puis_200_retente():
    seq = [_json_resp(429, {"Retry-After": "2"}), _json_resp(200, {}, "OK-TEXTE")]
    with patch.object(gen, "time", MagicMock()) as t, patch("requests.post", side_effect=seq) as p:
        out = gen._groq("x", cle="k", retry_max=2, retry_wait_max=10)
    assert out == "OK-TEXTE"
    assert p.call_count == 2
    assert _sleeps(t) == [2.0]


def test_non_stream_retry_max_0_leve_direct():
    seq = [_json_resp(429, {"Retry-After": "2"})]
    with patch.object(gen, "time", MagicMock()), patch("requests.post", side_effect=seq) as p:
        with pytest.raises(gen.LLMRateLimitError):
            gen._groq("x", cle="k", retry_max=0, retry_wait_max=10)
    assert p.call_count == 1


# ===================== 3) GET / PUT /admin/retry =====================

def test_endpoint_get_defaut_et_bornes():
    _reset_settings()
    r = _admin().get("/api/admin/retry")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["retry_max"] == 2
    assert data["retry_wait_max"] == 10
    assert data["bounds"] == {
        "retry_max": {"min": RETRY_MAX_MIN, "max": RETRY_MAX_MAX},
        "retry_wait_max": {"min": RETRY_WAIT_MIN, "max": RETRY_WAIT_MAX},
    }


def test_endpoint_put_valide_ecrit_et_get_reflete():
    _reset_settings()
    r = _admin().put("/api/admin/retry", json={"retry_max": 3, "retry_wait_max": 15})
    assert r.status_code == 200, r.text
    assert _row("ai_retry_max") == "3"
    assert _row("ai_retry_wait_max") == "15"
    data = _admin().get("/api/admin/retry").json()
    assert data["retry_max"] == 3 and data["retry_wait_max"] == 15


def test_endpoint_put_retry_max_hors_bornes_400_rien_ecrit():
    _reset_settings()
    r = _admin().put("/api/admin/retry", json={"retry_max": 9, "retry_wait_max": 10})
    assert r.status_code == 400, r.text
    assert "hors limites" in r.json()["detail"]
    assert _row("ai_retry_max") is None and _row("ai_retry_wait_max") is None  # rien écrit


def test_endpoint_put_wait_hors_bornes_400_rien_ecrit():
    _reset_settings()
    r = _admin().put("/api/admin/retry", json={"retry_max": 2, "retry_wait_max": 999})
    assert r.status_code == 400, r.text
    assert _row("ai_retry_wait_max") is None and _row("ai_retry_max") is None


def test_endpoint_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/retry").status_code == 401
    assert TestClient(app).put("/api/admin/retry", json={"retry_max": 2, "retry_wait_max": 10}).status_code == 401
