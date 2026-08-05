r"""Preuve de raccordement — max_tokens administrable, TOUS LES OUTILS.

L'ecran ne reglait que 3 outils sur 17 : `default`, `ambiguites`, `sequence`, ecrits a la main
dans le backend ET dans le front. Les 14 autres prenaient le defaut global en silence, sans que
l'admin puisse le savoir. La liste des outils est descendue EN BASE (`outils_llm`) : l'ecran la
lit et n'en connait plus aucun par son nom.

Ce que le test PROUVE (la chaine reelle remonte la bonne valeur, pas « le code existe ») :
  1. get_max_tokens() resout HYBRIDE : surcharge `max_tokens_<outil>` si presente, sinon defaut
     global. Il ne CHANGE PAS : sa lecture etait deja generique, c'etaient les endpoints qui
     bloquaient.
  2. Sans aucune ligne en base, TOUS les outils tombent sur le defaut global — aucun n'est traite
     a part par le code.
  3. La valeur change A CHAUD (meme process, sans redemarrage).
  4. Surcharge corrompue en base -> repli sur le defaut (jamais d'exception).
  5. GET /admin/max-tokens renvoie les 17 outils LUS EN BASE, avec pour chacun sa surcharge
     (None s'il n'en a pas) et la valeur qui s'applique reellement.
  6. PUT ecrit le defaut et les surcharges, SUPPRIME celle qu'on vide (null), refuse un outil
     inconnu de la table et une valeur sous le plancher — sans rien ecrire.
  7. Aucun plafond : 99 999 passe. Le plafond a ete supprime et ne doit pas revenir.
  8. 401 sans cookie admin, isolation vis-a-vis de l'endpoint email.

Lancer : docker compose exec backend python -m pytest tests/test_settings_max_tokens.py -q
"""
# Windows : torch + chromadb -> deux runtimes OpenMP. Garde-fous AVANT tout import torch.


# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.main import app
from backend.securite.comptes import create_access_token
from backend.core.models_db import Setting
from backend.systeme.admin import (
    get_max_tokens, SETTING_DEFAULTS, MAX_TOKENS_MIN,
    _make_admin_token,
)
from fastapi.testclient import TestClient

TOKEN = create_access_token("prof.test@aschool.fr")

DEFAUT = int(SETTING_DEFAULTS["max_tokens_default"])


def _fresh_db():
    """Session avec la table settings vidée (isolation entre tests)."""
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


# ===================== get_max_tokens : resolution HYBRIDE =====================

def test_sans_aucune_ligne_tous_les_outils_suivent_le_defaut():
    """Aucun outil n'est traite a part par le code : plus aucune surcharge n'y est semee. Une
    surcharge n'existe que si l'admin l'a posee depuis l'ecran."""
    db = _fresh_db()
    for outil in ("ambiguites", "sequence", "activite", "exemple", "consigne", "decoupe_amont"):
        assert get_max_tokens(db, outil) == DEFAUT, outil
    assert "max_tokens_ambiguites" not in SETTING_DEFAULTS
    assert "max_tokens_sequence" not in SETTING_DEFAULTS
    db.close()


def test_surcharge_en_base_prioritaire():
    db = _fresh_db()
    db.add(Setting(key="max_tokens_ambiguites", value="5000"))
    db.commit()
    assert get_max_tokens(db, "ambiguites") == 5000
    assert get_max_tokens(db, "activite") == DEFAUT  # les autres ne bougent pas
    db.close()


def test_changer_le_defaut_change_tous_les_outils_sans_surcharge():
    db = _fresh_db()
    db.add(Setting(key="max_tokens_default", value="1500"))
    db.add(Setting(key="max_tokens_sequence", value="4000"))
    db.commit()
    assert get_max_tokens(db, "activite") == 1500
    assert get_max_tokens(db, "consigne") == 1500
    assert get_max_tokens(db, "sequence") == 4000  # celui-la a une surcharge : intact
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
    assert get_max_tokens(db, "ambiguites") == DEFAUT  # repli, jamais d'exception
    db.close()


# ============ GET /admin/max-tokens : TOUS les outils, lus en base ============

def test_get_renvoie_tous_les_outils_de_la_base():
    _reset_settings()
    data = _admin().get("/api/admin/max-tokens").json()
    assert data["default"] == DEFAUT
    assert data["bounds"] == {"min": MAX_TOKENS_MIN, "max": None}   # aucun plafond imposé

    outils = {o["outil"]: o for o in data["outils"]}
    # C'ETAIT LE BUG : l'ecran n'en montrait que 3. Les 14 muets sont la, avec la decoupe et la
    # fusion — les deux qui avaient un besoin reel et aucun champ.
    assert len(outils) >= 17, f"seulement {len(outils)} outils remontes"
    for attendu in ("activite", "sequence", "ambiguites", "decoupe_amont",
                    "referentiel_fusion", "detecter_types_activite", "ocr"):
        assert attendu in outils, attendu
    assert all(o["libelle"] and o["aide"] for o in data["outils"])


def test_get_distingue_la_surcharge_de_la_valeur_appliquee():
    _reset_settings()
    db = dbmod.SessionLocal()
    db.add(Setting(key="max_tokens_decoupe_amont", value="32000"))
    db.commit()
    db.close()

    outils = {o["outil"]: o for o in _admin().get("/api/admin/max-tokens").json()["outils"]}
    assert outils["decoupe_amont"]["valeur"] == 32000
    assert outils["decoupe_amont"]["effectif"] == 32000
    # Sans surcharge : `valeur` reste None (rien n'est pose), `effectif` dit ce qui s'applique.
    assert outils["activite"]["valeur"] is None
    assert outils["activite"]["effectif"] == DEFAUT


# ============ PUT /admin/max-tokens ============

def test_put_ecrit_le_defaut_et_les_surcharges():
    _reset_settings()
    r = _admin().put("/api/admin/max-tokens", json={
        "default": 9000,
        "outils": {"sequence": 12000, "decoupe_amont": 32000},
    })
    assert r.status_code == 200, r.text
    assert _row("max_tokens_default") == "9000"
    assert _row("max_tokens_sequence") == "12000"
    assert _row("max_tokens_decoupe_amont") == "32000"
    assert _admin().get("/api/admin/max-tokens").json()["default"] == 9000


def test_put_null_supprime_la_surcharge():
    """Vider un champ = un vrai DELETE, pas une valeur neutre gardee en base : l'outil repart sur
    le defaut global et le suivra de nouveau quand il changera."""
    _reset_settings()
    _admin().put("/api/admin/max-tokens", json={"default": 8000, "outils": {"sequence": 12000}})
    assert _row("max_tokens_sequence") == "12000"

    r = _admin().put("/api/admin/max-tokens", json={"default": 8000, "outils": {"sequence": None}})
    assert r.status_code == 200, r.text
    assert _row("max_tokens_sequence") is None            # ligne SUPPRIMEE
    db = dbmod.SessionLocal()
    assert get_max_tokens(db, "sequence") == 8000         # suit de nouveau le defaut
    db.close()


def test_put_outil_inconnu_refuse_400_rien_ecrit():
    """Sans ce refus on semerait des cles `max_tokens_<n'importe quoi>` que personne ne lit —
    exactement `max_tokens_optimiseur`, regle dans le vide pendant des jours."""
    _reset_settings()
    r = _admin().put("/api/admin/max-tokens", json={
        "default": 8000, "outils": {"outil_qui_n_existe_pas": 5000},
    })
    assert r.status_code == 400, r.text
    assert "inconnu" in r.json()["detail"]
    assert _row("max_tokens_outil_qui_n_existe_pas") is None
    assert _row("max_tokens_default") is None  # rien ecrit, pas meme le defaut


def test_put_trop_bas_refuse_400_rien_ecrit():
    _reset_settings()
    r = _admin().put("/api/admin/max-tokens", json={"default": 10, "outils": {}})
    assert r.status_code == 400, r.text
    assert "trop basse" in r.json()["detail"]
    assert _row("max_tokens_default") is None  # rien ecrit

    r = _admin().put("/api/admin/max-tokens", json={"default": 8000, "outils": {"sequence": 10}})
    assert r.status_code == 400, r.text
    assert _row("max_tokens_sequence") is None
    assert _row("max_tokens_default") is None  # la validation passe AVANT toute ecriture


def test_put_valeur_haute_acceptee_il_n_y_a_plus_de_plafond():
    """Le plafond a ete SUPPRIME le 05/08 et ne doit pas revenir. Il valait 8 000 « pour le
    cout » — c'est faux : on paie les tokens PRODUITS, jamais la valeur demandee. Ce chiffre a
    fini par empecher l'admin de saisir 32 000 pour la decoupe d'un referentiel, qui se faisait
    tronquer. La seule vraie limite est celle du modele, et c'est le fournisseur qui la fait
    respecter. Ce test tombe si quelqu'un remet un plafond dans le code."""
    _reset_settings()
    r = _admin().put("/api/admin/max-tokens", json={
        "default": 32000, "outils": {"sequence": 99999},
    })
    assert r.status_code == 200, r.text
    assert _row("max_tokens_default") == "32000"
    assert _row("max_tokens_sequence") == "99999"


def test_sans_cookie_admin_401():
    assert TestClient(app).get("/api/admin/max-tokens").status_code == 401
    assert TestClient(app).put(
        "/api/admin/max-tokens", json={"default": 8000, "outils": {}}
    ).status_code == 401


def test_isolation_endpoint_email_n_altere_pas_max_tokens():
    # Endpoints dedies : le PUT email ne doit jamais toucher les cles max_tokens.
    _reset_settings()
    _admin().put("/api/admin/max-tokens", json={"default": 2500, "outils": {}})
    r = _admin().put("/api/admin/settings", json={
        "welcome_email_subject": "Sujet X", "welcome_email_body": "Corps Y",
    })
    assert r.status_code == 200, r.text
    assert _row("max_tokens_default") == "2500"  # intact
