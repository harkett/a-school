r"""Preuve de raccordement — Phase 4.1.d : température administrable (GLOBALE).

Ce que le test PROUVE (la chaine reelle remonte la bonne valeur, pas « le code existe ») :
  1. get_temperature() : non reglee (cle vide/absente) -> None = defaut du fournisseur
     (comportement historique, zero regression).
  2. Valeur valide en base -> float ; valeur hors bornes ou corrompue -> None (jamais d'exception).
  3. La valeur change A CHAUD (meme process, sans redemarrage) — comme 4.1.a/4.1.c.
  4. Chaine complete /api/generate : la temperature en base ressort dans le corps HTTP LLM ;
     NON reglee -> la cle `temperature` n'est PAS envoyee (le fournisseur applique son defaut).
  5. GET/PUT /admin/temperature : lecture, ecriture validee, mise a vide (= defaut fournisseur),
     400 hors bornes (rien ecrit), 401 sans cookie admin, isolation vis-a-vis de max_tokens/email.

Lancer : .\.venv\Scripts\python.exe -m pytest test_settings_temperature.py -q
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
import backend.database as dbmod

from backend.main import app
from backend.auth import create_access_token
from backend.models_db import Setting
from backend.systeme.admin import (
    get_temperature, TEMPERATURE_MIN, TEMPERATURE_MAX, _make_admin_token,
)
import src.generator as gen
from fastapi.testclient import TestClient

TOKEN = create_access_token("prof.test@aschool.fr")


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


def _fake_groq_post(capture):
    def _post(url, headers=None, json=None, timeout=None):
        capture["body"] = json
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"choices": [{"message": {"content": "OK"}}]}
        return resp
    return _post


# ===================== get_temperature : resolution =====================

def test_non_reglee_renvoie_none():
    # Defaut historique : aucune ligne -> None -> generate() n'envoie rien -> defaut fournisseur.
    db = _fresh_db()
    assert get_temperature(db) is None
    db.close()


def test_valeur_valide_en_base():
    db = _fresh_db()
    db.add(Setting(key="ai_temperature", value="0.5"))
    db.commit()
    assert get_temperature(db) == 0.5
    db.close()


def test_hors_bornes_repli_sur_none():
    db = _fresh_db()
    db.add(Setting(key="ai_temperature", value="9"))  # > MAX
    db.commit()
    assert get_temperature(db) is None
    db.close()


def test_corrompue_repli_sur_none():
    db = _fresh_db()
    db.add(Setting(key="ai_temperature", value="pas-un-nombre"))
    db.commit()
    assert get_temperature(db) is None  # jamais d'exception
    db.close()


def test_a_chaud_sans_redemarrage():
    db = _fresh_db()
    db.add(Setting(key="ai_temperature", value="0.3"))
    db.commit()
    assert get_temperature(db) == 0.3
    db.query(Setting).filter(Setting.key == "ai_temperature").update({"value": "0.8"})
    db.commit()
    assert get_temperature(db) == 0.8  # pris en compte direct, meme process
    db.close()


# ============ Chaine complete via /api/generate (cablage routeur prouve) ============

def _call_generate(cap):
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    with patch("backend.activite.generate.build_prompt", return_value="PROMPT"), \
         patch.object(gen, "AI_PROVIDER", "groq"), \
         patch("requests.post", side_effect=_fake_groq_post(cap)):
        return c.post("/api/generate", json={
            "activite_key": "comprehension", "texte": "Un texte.", "niveau": "4e",
        })


def test_generate_envoie_la_temperature_en_base():
    _reset_settings()
    db = dbmod.SessionLocal()
    db.add(Setting(key="ai_temperature", value="0.4"))
    db.commit()
    db.close()
    cap = {}
    r = _call_generate(cap)
    assert r.status_code == 200, r.text
    assert cap["body"]["temperature"] == 0.4  # la valeur en base ressort dans l'appel LLM


def test_generate_non_reglee_n_envoie_pas_de_temperature():
    _reset_settings()  # aucune ligne -> None -> rien envoye -> defaut fournisseur (zero regression)
    cap = {}
    r = _call_generate(cap)
    assert r.status_code == 200, r.text
    assert "temperature" not in cap["body"]


# ============ GET / PUT /admin/temperature ============

def test_get_defaut_none_et_bornes():
    _reset_settings()
    r = _admin().get("/api/admin/temperature")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["temperature"] is None  # non reglee = defaut fournisseur
    assert data["bounds"] == {"min": TEMPERATURE_MIN, "max": TEMPERATURE_MAX}


def test_put_valide_ecrit_et_get_reflete():
    _reset_settings()
    r = _admin().put("/api/admin/temperature", json={"temperature": 0.7})
    assert r.status_code == 200, r.text
    assert _row("ai_temperature") == "0.7"
    assert _admin().get("/api/admin/temperature").json()["temperature"] == 0.7


def test_put_none_revient_au_defaut_fournisseur():
    _reset_settings()
    _admin().put("/api/admin/temperature", json={"temperature": 0.7})
    r = _admin().put("/api/admin/temperature", json={"temperature": None})
    assert r.status_code == 200, r.text
    assert _row("ai_temperature") == ""  # cle videe = defaut fournisseur
    assert _admin().get("/api/admin/temperature").json()["temperature"] is None


def test_put_hors_bornes_refuse_400_rien_ecrit():
    _reset_settings()
    r = _admin().put("/api/admin/temperature", json={"temperature": 5})
    assert r.status_code == 400, r.text
    assert "hors limites" in r.json()["detail"]
    assert _row("ai_temperature") is None  # rien ecrit


def test_put_negatif_refuse_400():
    _reset_settings()
    r = _admin().put("/api/admin/temperature", json={"temperature": -0.5})
    assert r.status_code == 400, r.text


def test_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/temperature").status_code == 401
    assert TestClient(app).put("/api/admin/temperature", json={"temperature": 0.5}).status_code == 401


def test_isolation_endpoint_email_n_altere_pas_la_temperature():
    _reset_settings()
    _admin().put("/api/admin/temperature", json={"temperature": 0.6})
    r = _admin().put("/api/admin/settings", json={
        "welcome_email_subject": "Sujet X", "welcome_email_body": "Corps Y",
    })
    assert r.status_code == 200, r.text
    assert _row("ai_temperature") == "0.6"  # intact
