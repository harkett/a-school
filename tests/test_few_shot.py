"""Le few-shot « aSchool vous reconnaît » — livré, plus différé.

L'application l'affirmait au prof à trois endroits (jauge de Mes stats, astuce de l'Accueil,
deux mentions de l'aide) alors que la génération n'en tenait aucun compte. Vérifié ici :
  - sous le seuil, AUCUNE couche n'est ajoutée (deux exemples ne font pas un style) ;
  - au seuil, les activités précédentes du prof partent en exemple dans le prompt ;
  - le cloisonnement du style : même type mais autre couple, autre type, autre prof → rien ;
  - les extraits sont bornés (`few_shot_extrait_max`) pour que le prompt reste sain ;
  - les réglages viennent de la BASE : ligne absente = erreur claire, jamais un défaut caché ;
  - la jauge de Mes stats suit EXACTEMENT ce qui déclenche le few-shot (groupe type × couple).

Lancer : docker compose exec backend python -m pytest tests/test_few_shot.py -q
"""

import pytest


import backend.core.database as dbmod  # noqa: E402  (redirigé vers aschool_test par conftest)

from fastapi import HTTPException  # noqa: E402

from backend.contenu.activites import few_shot_du_prof  # noqa: E402
from backend.core.llm_prompts import PROMPTS  # noqa: E402
from backend.core.models_db import Activite, ActiviteType, Setting, User  # noqa: E402

EMAIL = "fewshot@local.test"

REGLAGES = {
    "few_shot_seuil": "3",
    "few_shot_extrait_max": "3000",
    "prompt_few_shot": PROMPTS["few_shot"]["default"],
}


def _seed_reglages(db, **surcharges):
    """Les réglages tels que la migration les sème (les tests peuvent en ajuster un)."""
    for cle, valeur in {**REGLAGES, **surcharges}.items():
        row = db.query(Setting).filter(Setting.key == cle).first()
        if row:
            row.value = valeur
        else:
            db.add(Setting(key=cle, value=valeur))
    db.commit()


def _user(db, email=EMAIL):
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(email=email, password_hash="x", is_verified=True)
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


def _type(db, label):
    t = db.query(ActiviteType).filter(ActiviteType.label == label).first()
    if not t:
        t = ActiviteType(label=label)
        db.add(t)
        db.commit()
        db.refresh(t)
    return t


def _activite(db, user, type_id, resultat, matiere="Français", niveau="6e", label="Compréhension"):
    db.add(Activite(user_id=user.id, activite_type_id=type_id, activite_label=label,
                    matiere=matiere, niveau=niveau, texte_source="src", resultat=resultat))
    db.commit()


def test_sous_le_seuil_aucune_couche():
    with dbmod.SessionLocal() as db:
        _seed_reglages(db)
        u = _user(db)
        t = _type(db, "Compréhension")
        db.query(Activite).filter(Activite.user_id == u.id).delete()
        db.commit()
        _activite(db, u, t.id, "# Activité A")
        _activite(db, u, t.id, "# Activité B")
        assert few_shot_du_prof(db, u, t.id, "Français", "6e") == ""


def test_au_seuil_les_precedentes_partent_en_exemple():
    with dbmod.SessionLocal() as db:
        _seed_reglages(db)
        u = _user(db)
        t = _type(db, "Compréhension")
        db.query(Activite).filter(Activite.user_id == u.id).delete()
        db.commit()
        for texte in ("# Activité A", "# Activité B", "# Activité C"):
            _activite(db, u, t.id, texte)

        couche = few_shot_du_prof(db, u, t.id, "Français", "6e")
        assert couche, "au seuil, la couche doit être ajoutée"
        for texte in ("# Activité A", "# Activité B", "# Activité C"):
            assert texte in couche
        assert "--- Exemple 1 (Compréhension) ---" in couche
        # La consigne qui empêche le style de déteindre sur le contenu doit rester.
        assert "jamais pour le CONTENU" in couche


def test_style_cloisonne_par_type_couple_et_prof():
    """Ses résumés n'influencent pas ses analyses, sa 6e n'influence pas sa 3e, et le style
    d'un autre prof ne l'atteint jamais."""
    with dbmod.SessionLocal() as db:
        _seed_reglages(db)
        u = _user(db)
        autre = _user(db, "fewshot-autre@local.test")
        compr = _type(db, "Compréhension")
        resume = _type(db, "Résumé")
        db.query(Activite).filter(Activite.user_id.in_([u.id, autre.id])).delete(synchronize_session=False)
        db.commit()

        for texte in ("# A", "# B", "# C"):
            _activite(db, u, compr.id, texte, niveau="6e")

        # Le seuil est atteint en 6e / Compréhension seulement.
        assert few_shot_du_prof(db, u, compr.id, "Français", "6e") != ""
        assert few_shot_du_prof(db, u, compr.id, "Français", "3e") == ""      # autre niveau
        assert few_shot_du_prof(db, u, compr.id, "Maths", "6e") == ""         # autre matière
        assert few_shot_du_prof(db, u, resume.id, "Français", "6e") == ""     # autre type
        assert few_shot_du_prof(db, autre, compr.id, "Français", "6e") == ""  # autre prof


def test_extraits_bornes_par_le_reglage_en_base():
    with dbmod.SessionLocal() as db:
        _seed_reglages(db, few_shot_extrait_max="250")
        u = _user(db)
        t = _type(db, "Compréhension")
        db.query(Activite).filter(Activite.user_id == u.id).delete()
        db.commit()
        for i in range(3):
            _activite(db, u, t.id, f"DEBUT{i}" + ("x" * 5000) + "FIN")

        couche = few_shot_du_prof(db, u, t.id, "Français", "6e")
        assert "FIN" not in couche          # la queue est coupée
        assert "DEBUT0" in couche
        assert len(couche) < 2000           # trois extraits de 250, pas trois pavés


def test_reglage_absent_dit_l_erreur_au_lieu_de_retomber_sur_du_dur():
    """Règle maison : base vide = erreur claire, jamais un défaut code silencieux."""
    with dbmod.SessionLocal() as db:
        _seed_reglages(db)
        u = _user(db)
        t = _type(db, "Compréhension")
        db.query(Setting).filter(Setting.key == "few_shot_seuil").delete()
        db.commit()
        try:
            with pytest.raises(HTTPException) as err:
                few_shot_du_prof(db, u, t.id, "Français", "6e")
            assert err.value.status_code == 500
            assert "few_shot_seuil" in err.value.detail
        finally:
            _seed_reglages(db)


def test_jauge_mes_stats_suit_le_declenchement_reel():
    """« aSchool vous connaît à X% » ne doit pas annoncer 100% quand rien ne s'applique :
    la jauge compte le meilleur groupe type × couple, comme le few-shot."""
    from backend.securite.comptes import create_access_token
    from backend.main import app
    from fastapi.testclient import TestClient

    with dbmod.SessionLocal() as db:
        _seed_reglages(db)
        u = _user(db)
        t = _type(db, "Compréhension")
        db.query(Activite).filter(Activite.user_id == u.id).delete()
        db.commit()
        # 2 en 6e + 1 en 3e = 3 activités du même TYPE, mais aucun couple au seuil.
        _activite(db, u, t.id, "# A", niveau="6e")
        _activite(db, u, t.id, "# B", niveau="6e")
        _activite(db, u, t.id, "# C", niveau="3e")

    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(EMAIL))
    d = c.get("/api/stats/perso").json()
    assert d["few_shot_seuil"] == 3
    assert d["score_adaptation"] == 66      # 2/3 du meilleur groupe, pas 100

    with dbmod.SessionLocal() as db:
        u = _user(db)
        t = _type(db, "Compréhension")
        _activite(db, u, t.id, "# D", niveau="6e")   # 3e activité en 6e → le few-shot s'applique
    assert c.get("/api/stats/perso").json()["score_adaptation"] == 100
