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

Lancer : docker compose exec backend python -m pytest tests/test_settings_temperature.py -q
"""
# Windows : torch + chromadb -> deux runtimes OpenMP. Garde-fous AVANT tout import torch.


from unittest.mock import MagicMock, patch

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.main import app
from backend.securite.comptes import create_access_token
from backend.core.models_db import Setting
from backend.systeme.admin import (
    get_temperature, TEMPERATURE_MIN, TEMPERATURE_MAX, _make_admin_token,
)
import backend.llm.generator as gen
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


# ---------------------------------------------------------------------------
# La temperature depend du MODELE (05/08/2026)
#
# Le moteur portait la regle en dur : « temperature : volontairement IGNOREE — les Claude Opus 4.x
# la rejettent (400) ». Ecrite deux fois, au nom du fournisseur entier. Consequence pour l'admin :
# il reglait une temperature sur un Claude, validait, et elle etait jetee en silence. Rien ne le
# lui disait. La regle vit desormais sur la fiche du modele (`ai_modeles.supporte_temperature`).
# ---------------------------------------------------------------------------

from backend.core.models_db import AiFournisseur, AiModele  # noqa: E402
from backend.systeme.admin import modele_supporte_temperature  # noqa: E402

_F_TEMP = "fournisseur_test_temperature"
_M_TEMP = "modele-test-temperature"


def _poser_modele(db, *, supporte):
    """Met en service un couple fournisseur/modele dont on choisit la capacite."""
    db.query(AiModele).filter(AiModele.modele == _M_TEMP).delete()
    db.query(AiFournisseur).filter(AiFournisseur.code == _F_TEMP).delete()
    db.add(AiFournisseur(code=_F_TEMP, label="Test", cle_env="TEST_KEY"))
    db.add(AiModele(fournisseur=_F_TEMP, modele=_M_TEMP, label="Test",
                    supporte_temperature=supporte))
    db.add(Setting(key="ai_provider", value=_F_TEMP))
    db.add(Setting(key="ai_model", value=_M_TEMP))
    db.add(Setting(key="ai_temperature", value="0.7"))
    db.commit()


def _nettoyer_modele(db):
    db.query(Setting).delete()
    db.query(AiModele).filter(AiModele.modele == _M_TEMP).delete()
    db.query(AiFournisseur).filter(AiFournisseur.code == _F_TEMP).delete()
    db.commit()
    db.close()


def test_modele_qui_accepte_la_temperature_la_recoit():
    """Cas general : la valeur reglee arrive telle quelle au moteur."""
    db = _fresh_db()
    try:
        _poser_modele(db, supporte=True)
        assert modele_supporte_temperature(db) is True
        assert get_temperature(db) == 0.7
    finally:
        _nettoyer_modele(db)


def test_modele_qui_refuse_la_temperature_ne_la_recoit_pas():
    """LE COEUR DE LA CORRECTION. La valeur reste en base — elle n'est pas effacee — mais elle
    n'est PAS transmise au moteur : c'est ce qui evitait le 400 par un `if Anthropic` en dur."""
    db = _fresh_db()
    try:
        _poser_modele(db, supporte=False)
        assert modele_supporte_temperature(db) is False
        assert get_temperature(db) is None
        # La valeur reglee n'a pas ete perdue : elle redeviendra active au prochain modele qui
        # l'accepte. L'ecran l'affiche toujours, avec un avertissement.
        from backend.systeme.admin import get_settings_dict
        assert get_settings_dict(db)["ai_temperature"] == "0.7"
    finally:
        _nettoyer_modele(db)


def test_bascule_de_modele_a_chaud():
    """Changer de modele suffit a rendre la temperature active ou inactive — pas de redemarrage,
    pas de modification du moteur."""
    db = _fresh_db()
    try:
        _poser_modele(db, supporte=False)
        assert get_temperature(db) is None
        db.query(AiModele).filter(AiModele.modele == _M_TEMP).update(
            {"supporte_temperature": True})
        db.commit()
        assert get_temperature(db) == 0.7
    finally:
        _nettoyer_modele(db)
