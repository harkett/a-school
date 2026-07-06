r"""Preuve de raccordement — Phase 4.1 (prompts) : prompts d'outils administrables en base.

Ce que le test PROUVE (la chaine reelle remonte le bon texte, pas « le code existe ») :
  1. get_prompt() : pas de surcharge -> defaut code ; surcharge non vide -> surcharge ;
     surcharge vide -> repli sur defaut ; changement A CHAUD (meme process, sans redemarrage).
  2. valider_prompt() : les 5 defauts passent (.format sans casse) ; repere obligatoire manquant,
     repere inconnu, accolade cassee, cle inconnue -> message humain (jamais d'exception).
  3. Chaine complete /api/detect-ambiguites : la surcharge en base ressort DANS le prompt
     envoye au LLM, repères substitues ; sans surcharge -> le defaut ressort.
  4. GET/PUT/DELETE /admin/prompts : liste, ecriture validee (400 rien ecrit si invalide),
     vrai retour au defaut (DELETE), idempotence, 401 sans cookie admin, isolation vs temperature.

Lancer : .\.venv\Scripts\python.exe -m pytest test_settings_prompts.py -q
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
from backend.systeme.admin import get_prompt, valider_prompt, _make_admin_token
from backend.llm_prompts import PROMPTS
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


def _fake_groq_post(capture, content):
    def _post(url, headers=None, json=None, timeout=None):
        capture["body"] = json
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"choices": [{"message": {"content": content}}]}
        return resp
    return _post


# ===================== get_prompt : resolution =====================

def test_pas_de_surcharge_renvoie_defaut():
    db = _fresh_db()
    assert get_prompt(db, "ambiguites") == PROMPTS["ambiguites"]["default"]
    db.close()


def test_surcharge_non_vide_prioritaire():
    db = _fresh_db()
    db.add(Setting(key="prompt_consigne", value="MON PROMPT {matiere} {niveau} {consigne}"))
    db.commit()
    assert get_prompt(db, "consigne") == "MON PROMPT {matiere} {niveau} {consigne}"
    db.close()


def test_surcharge_vide_repli_sur_defaut():
    db = _fresh_db()
    db.add(Setting(key="prompt_consigne", value="   "))  # vide/espaces -> ignore
    db.commit()
    assert get_prompt(db, "consigne") == PROMPTS["consigne"]["default"]
    db.close()


def test_a_chaud_sans_redemarrage():
    db = _fresh_db()
    db.add(Setting(key="prompt_ambiguites", value="V1 {matiere} {niveau} {texte}"))
    db.commit()
    assert get_prompt(db, "ambiguites") == "V1 {matiere} {niveau} {texte}"
    db.query(Setting).filter(Setting.key == "prompt_ambiguites").update({"value": "V2 {matiere} {niveau} {texte}"})
    db.commit()
    assert get_prompt(db, "ambiguites") == "V2 {matiere} {niveau} {texte}"  # pris direct, meme process
    db.close()


# ===================== valider_prompt : garde-fou d'ecriture =====================

def test_les_5_defauts_sont_valides():
    # Re-prouve aussi que les 5 prompts par defaut .format() sans casser (fidelite + sûreté).
    for key in PROMPTS:
        assert valider_prompt(key, PROMPTS[key]["default"]) is None, key


def test_repere_obligatoire_manquant_refuse():
    msg = valider_prompt("ambiguites", "Texte sans le repere attendu {matiere} {niveau}")  # {texte} manquant
    assert msg and "{texte}" in msg


def test_repere_inconnu_refuse():
    msg = valider_prompt("consigne", "{matiere} {niveau} {consigne} {inconnu}")
    assert msg and "inconnu" in msg.lower()


def test_accolade_cassee_refuse():
    msg = valider_prompt("consigne", "{matiere} {niveau} {consigne} {")  # accolade ouvrante seule
    assert msg is not None


def test_cle_inconnue_refuse():
    assert valider_prompt("nexiste_pas", "peu importe") == "Prompt inconnu."


# ============ Chaine complete via /api/detect-ambiguites (cablage routeur prouve) ============

def _call_ambiguites(cap):
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    contenu_llm = '{"ambiguites": [], "verdict": "ok"}'
    with patch.object(gen, "AI_PROVIDER", "groq"), \
         patch("requests.post", side_effect=_fake_groq_post(cap, contenu_llm)):
        return c.post("/api/detect-ambiguites", json={
            "texte": "Un enonce.", "matiere": "Mathematiques", "niveau": "4e",
        })


def test_chaine_utilise_la_surcharge():
    _reset_settings()
    db = dbmod.SessionLocal()
    db.add(Setting(key="prompt_ambiguites", value="MARQUEUR_OVERRIDE {matiere} {niveau} {texte}"))
    db.commit()
    db.close()
    cap = {}
    r = _call_ambiguites(cap)
    assert r.status_code == 200, r.text
    envoye = cap["body"]["messages"][0]["content"]
    assert "MARQUEUR_OVERRIDE" in envoye               # la surcharge en base ressort
    assert "Mathematiques" in envoye and "Un enonce." in envoye  # repères substitues


def test_chaine_defaut_quand_pas_de_surcharge():
    _reset_settings()
    cap = {}
    r = _call_ambiguites(cap)
    assert r.status_code == 200, r.text
    envoye = cap["body"]["messages"][0]["content"]
    assert '"ambiguites":' in envoye  # fragment ASCII unique du prompt PAR DEFAUT (cle JSON attendue)


# ============ GET / PUT / DELETE /admin/prompts ============

def test_get_liste_tous_les_prompts():
    _reset_settings()
    r = _admin().get("/api/admin/prompts")
    assert r.status_code == 200, r.text
    out = r.json()["prompts"]
    assert {p["key"] for p in out} == set(PROMPTS.keys())
    amb = next(p for p in out if p["key"] == "ambiguites")
    assert amb["is_default"] is True                       # aucune surcharge
    assert amb["current"] == PROMPTS["ambiguites"]["default"]
    assert amb["placeholders"] == PROMPTS["ambiguites"]["placeholders"]


def test_put_valide_ecrit_et_get_reflete():
    _reset_settings()
    texte = "PERSO {matiere} {niveau} {consigne}"
    r = _admin().put("/api/admin/prompts", json={"key": "consigne", "text": texte})
    assert r.status_code == 200, r.text
    assert _row("prompt_consigne") == texte
    out = _admin().get("/api/admin/prompts").json()["prompts"]
    cons = next(p for p in out if p["key"] == "consigne")
    assert cons["is_default"] is False
    assert cons["current"] == texte


def test_put_repere_manquant_refuse_400_rien_ecrit():
    _reset_settings()
    r = _admin().put("/api/admin/prompts", json={"key": "consigne", "text": "{matiere} {niveau}"})  # {consigne} manquant
    assert r.status_code == 400, r.text
    assert "{consigne}" in r.json()["detail"]
    assert _row("prompt_consigne") is None  # rien ecrit


def test_put_cle_inconnue_refuse_400():
    _reset_settings()
    r = _admin().put("/api/admin/prompts", json={"key": "nexiste_pas", "text": "x"})
    assert r.status_code == 400, r.text


def test_delete_remet_vraiment_au_defaut():
    _reset_settings()
    _admin().put("/api/admin/prompts", json={"key": "consigne", "text": "PERSO {matiere} {niveau} {consigne}"})
    assert _row("prompt_consigne") is not None
    r = _admin().delete("/api/admin/prompts/consigne")
    assert r.status_code == 200, r.text
    assert _row("prompt_consigne") is None  # surcharge supprimee = vrai retour au defaut
    out = _admin().get("/api/admin/prompts").json()["prompts"]
    cons = next(p for p in out if p["key"] == "consigne")
    assert cons["is_default"] is True
    assert cons["current"] == PROMPTS["consigne"]["default"]


def test_delete_idempotent():
    _reset_settings()
    r = _admin().delete("/api/admin/prompts/consigne")  # rien en base -> deja au defaut
    assert r.status_code == 200, r.text


def test_delete_cle_inconnue_400():
    assert _admin().delete("/api/admin/prompts/nexiste_pas").status_code == 400


def test_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/prompts").status_code == 401
    assert TestClient(app).put("/api/admin/prompts", json={"key": "consigne", "text": "x"}).status_code == 401
    assert TestClient(app).delete("/api/admin/prompts/consigne").status_code == 401


def test_isolation_prompt_n_altere_pas_la_temperature():
    _reset_settings()
    _admin().put("/api/admin/temperature", json={"temperature": 0.6})
    r = _admin().put("/api/admin/prompts", json={"key": "consigne", "text": "PERSO {matiere} {niveau} {consigne}"})
    assert r.status_code == 200, r.text
    assert _row("ai_temperature") == "0.6"  # intact
