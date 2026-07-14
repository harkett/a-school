r"""Preuve de raccordement — Phase 4.1.c : max_tokens administrable (HYBRIDE).

Ce que le test PROUVE (la chaine reelle remonte la bonne valeur, pas « le code existe ») :
  1. get_max_tokens() resout HYBRIDE : surcharge `max_tokens_<outil>` si presente, sinon
     defaut global `max_tokens_default`. Les 3 surcharges semees (3000/4000/6000) sont bien
     lues SANS aucune ligne en base (anti-regression : pas de retombee a 2048).
  2. Les outils SANS surcharge (activite, exemple, consigne) tombent sur le defaut global ;
     changer le defaut les change tous.
  3. La valeur change A CHAUD (meme process, sans redemarrage) — comme 4.1.a.
  4. Surcharge corrompue en base -> repli sur le defaut (jamais d'exception).
  5. Chaine complete /api/generate : la valeur en base ressort dans le corps HTTP LLM.
  6. GET/PUT /admin/max-tokens : lecture, ecriture validee, 400 hors bornes (rien ecrit),
     401 sans cookie admin, isolation vis-a-vis de ai_model et de l'email.

Lancer : .\.venv\Scripts\python.exe -m pytest test_settings_max_tokens.py -q
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

from unittest.mock import MagicMock, patch

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.main import app
from backend.auth import create_access_token
from backend.core.models_db import Setting
from backend.systeme.admin import (
    get_max_tokens, SETTING_DEFAULTS, MAX_TOKENS_MIN, MAX_TOKENS_MAX,
    _make_admin_token,
)
import backend.llm.generator as gen
from fastapi.testclient import TestClient

TOKEN = create_access_token("prof.test@aschool.fr")


def _fresh_db():
    """Session in-memory avec la table settings videe (isolation entre tests)."""
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


def _fake_groq_post(capture):
    """Remplace requests.post : capte le corps envoye, renvoie une reponse Groq factice."""
    def _post(url, headers=None, json=None, timeout=None):
        capture["body"] = json
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"choices": [{"message": {"content": "OK"}}]}
        return resp
    return _post


# ===================== get_max_tokens : resolution HYBRIDE =====================

def test_surcharges_semees_lues_sans_aucune_ligne_en_base():
    # Anti-regression : sans ligne en base, les 3 surcharges restent a 3000/4000/6000
    # (semees dans SETTING_DEFAULTS) — PAS de retombee a 2048.
    db = _fresh_db()
    assert get_max_tokens(db, "ambiguites") == 3000
    assert get_max_tokens(db, "sequence") == 4000
    assert get_max_tokens(db, "optimiseur") == 6000
    db.close()


def test_outils_sans_surcharge_tombent_sur_le_defaut():
    db = _fresh_db()
    assert get_max_tokens(db, "activite") == int(SETTING_DEFAULTS["max_tokens_default"])
    assert get_max_tokens(db, "exemple") == 2048
    assert get_max_tokens(db, "consigne") == 2048  # 2000 -> 2048, laisse sur le defaut (valide)
    db.close()


def test_surcharge_en_base_prioritaire():
    db = _fresh_db()
    db.add(Setting(key="max_tokens_ambiguites", value="5000"))
    db.commit()
    assert get_max_tokens(db, "ambiguites") == 5000
    db.close()


def test_changer_le_defaut_change_les_outils_sans_surcharge():
    db = _fresh_db()
    db.add(Setting(key="max_tokens_default", value="1500"))
    db.commit()
    assert get_max_tokens(db, "activite") == 1500
    assert get_max_tokens(db, "consigne") == 1500
    # un outil AVEC surcharge semee n'est pas affecte
    assert get_max_tokens(db, "optimiseur") == 6000
    db.close()


def test_a_chaud_sans_redemarrage():
    db = _fresh_db()
    db.add(Setting(key="max_tokens_default", value="1500"))
    db.commit()
    assert get_max_tokens(db, "activite") == 1500
    db.query(Setting).filter(Setting.key == "max_tokens_default").update({"value": "1800"})
    db.commit()
    assert get_max_tokens(db, "activite") == 1800  # pris en compte direct, meme process
    db.close()


def test_surcharge_corrompue_repli_sur_defaut():
    db = _fresh_db()
    db.add(Setting(key="max_tokens_ambiguites", value="pas-un-nombre"))
    db.commit()
    assert get_max_tokens(db, "ambiguites") == 2048  # repli, jamais d'exception
    db.close()


# ============ Chaine complete via /api/generate (cablage routeur prouve) ============

def test_endpoint_generate_utilise_le_defaut_en_base():
    _reset_settings()
    db = dbmod.SessionLocal()
    db.add(Setting(key="max_tokens_default", value="1234"))
    db.commit()
    db.close()

    cap = {}
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    with patch("backend.activite.generate.build_prompt", return_value="PROMPT"), \
         patch.object(gen, "AI_PROVIDER", "groq"), \
         patch("requests.post", side_effect=_fake_groq_post(cap)):
        r = c.post("/api/generate", json={
            "activite_key": "comprehension", "texte": "Un texte.", "niveau": "4e",
        })
    assert r.status_code == 200, r.text
    assert cap["body"]["max_tokens"] == 1234  # la valeur en base ressort dans l'appel LLM


# ============ GET / PUT /admin/max-tokens ============

def test_get_max_tokens_defauts_et_bornes():
    _reset_settings()
    r = _admin().get("/api/admin/max-tokens")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["default"] == 2048
    assert data["overrides"] == {"ambiguites": 3000, "sequence": 4000, "optimiseur": 6000}
    assert data["bounds"] == {"min": MAX_TOKENS_MIN, "max": MAX_TOKENS_MAX}


def test_put_valide_ecrit_les_4_cles():
    _reset_settings()
    r = _admin().put("/api/admin/max-tokens", json={
        "default": 2500, "ambiguites": 3200, "sequence": 4200, "optimiseur": 6500,
    })
    assert r.status_code == 200, r.text
    assert _row("max_tokens_default") == "2500"
    assert _row("max_tokens_ambiguites") == "3200"
    assert _row("max_tokens_sequence") == "4200"
    assert _row("max_tokens_optimiseur") == "6500"
    # GET reflete le courant
    assert _admin().get("/api/admin/max-tokens").json()["default"] == 2500


def test_put_trop_bas_refuse_400_rien_ecrit():
    _reset_settings()
    r = _admin().put("/api/admin/max-tokens", json={
        "default": 10, "ambiguites": 3000, "sequence": 4000, "optimiseur": 6000,
    })
    assert r.status_code == 400, r.text
    assert "hors limites" in r.json()["detail"]
    assert _row("max_tokens_default") is None  # rien ecrit


def test_put_trop_haut_refuse_400_rien_ecrit():
    _reset_settings()
    r = _admin().put("/api/admin/max-tokens", json={
        "default": 2048, "ambiguites": 3000, "sequence": 4000, "optimiseur": 99999,
    })
    assert r.status_code == 400, r.text
    assert _row("max_tokens_optimiseur") is None


def test_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/max-tokens").status_code == 401
    assert TestClient(app).put("/api/admin/max-tokens", json={
        "default": 2048, "ambiguites": 3000, "sequence": 4000, "optimiseur": 6000,
    }).status_code == 401


def test_isolation_endpoint_email_n_altere_pas_max_tokens():
    # Endpoints dedies : le PUT email ne doit jamais toucher les cles max_tokens.
    _reset_settings()
    _admin().put("/api/admin/max-tokens", json={
        "default": 2500, "ambiguites": 3000, "sequence": 4000, "optimiseur": 6000,
    })
    r = _admin().put("/api/admin/settings", json={
        "welcome_email_subject": "Sujet X", "welcome_email_body": "Corps Y",
    })
    assert r.status_code == 200, r.text
    assert _row("max_tokens_default") == "2500"  # intact
