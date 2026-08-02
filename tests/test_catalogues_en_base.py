"""Étape 9 lot A — les catalogues vivent EN BASE, plus dans le code.

Quatre listes de référence étaient écrites en dur et recopiées d'un fichier à l'autre : les
modes de séance (3 copies), les styles de production (2), les langues vivantes (1, absente du
serveur) et l'explication des statuts de feedback (recopiée alors que la table existait).

Ce que ces tests garantissent :
  - le serveur ACCEPTE ou REFUSE un mode/style d'après la TABLE, pas d'après une liste de code :
    retirer une ligne de la base la retire vraiment des valeurs acceptées ;
  - catalogue vide = erreur claire et immédiate, jamais un repli silencieux (règle maison) ;
  - l'écran reçoit du serveur exactement les lignes que le serveur validera (une seule vérité) ;
  - la LANGUE de la matière se reconnaît à l'indicateur `matieres.demande_langue`, plus au
    libellé de la matière — c'est LE défaut réparé ici : la matière réelle s'appelle « Langue
    vivante » et la comparaison au libellé « Langues Vivantes (LV) » était déjà fausse, en
    silence. Un renommage de matière ne doit plus rien casser.

Lancer : docker compose exec backend python -m pytest tests/test_catalogues_en_base.py -q
"""

import pytest


import backend.core.database as dbmod  # noqa: E402  (redirigé vers aschool_test par conftest)

from fastapi import HTTPException  # noqa: E402

from backend.contenu.mes_contenus import (  # noqa: E402
    SeanceGeneration, _valider_generation, modes_seance, styles_seance,
)
from backend.core.models_db import (  # noqa: E402
    FeedbackStatut, LangueLv, Matiere, SeanceMode, SeanceStyle, User,
)
from backend.prof.profil import matiere_demande_langue  # noqa: E402

from _profil import matiere_id, niveau_id  # noqa: E402


def _formulaire(theme="Les fractions", duree=55, mode="standard", style=None):
    return SeanceGeneration(theme=theme, duree=duree, mode=mode, style=style)


# ── Modes et styles : la table fait autorité ─────────────────────────────────────────────

def test_le_serveur_accepte_ce_que_la_table_contient():
    """Les 4 modes et 4 styles semés sont acceptés — et ce sont EXACTEMENT ceux que
    l'écran reçoit (même fonction de lecture des deux côtés)."""
    with dbmod.SessionLocal() as db:
        codes_modes = [m.code for m in modes_seance(db)]
        assert codes_modes == ["standard", "remediation", "approfondissement", "autonomie"]
        assert [s.code for s in styles_seance(db)] == ["classique", "ludique", "structure", "concis"]
        for code in codes_modes:
            _valider_generation(_formulaire(mode=code), db)   # ne lève pas


def test_retirer_une_ligne_de_la_base_la_retire_des_valeurs_acceptees():
    """La preuve que la liste n'est plus dans le code : on désactive « autonomie » en base et
    le serveur le refuse aussitôt, sans qu'une ligne de Python ait changé."""
    with dbmod.SessionLocal() as db:
        ligne = db.query(SeanceMode).filter(SeanceMode.code == "autonomie").first()
        ligne.actif = False
        db.commit()
        with pytest.raises(HTTPException) as e:
            _valider_generation(_formulaire(mode="autonomie"), db)
        assert e.value.status_code == 400
        assert "mode" in e.value.detail.lower()
        assert [m.code for m in modes_seance(db)] == ["standard", "remediation", "approfondissement"]


def test_un_style_inconnu_est_refuse_et_aucun_style_reste_permis():
    with dbmod.SessionLocal() as db:
        with pytest.raises(HTTPException) as e:
            _valider_generation(_formulaire(style="poetique"), db)
        assert e.value.status_code == 400
        _valider_generation(_formulaire(style=None), db)      # « Aucun style » : toujours valide


def test_catalogue_vide_erreur_dite_jamais_un_repli_silencieux():
    """Règle maison : une base vide est une erreur qu'on DIT. Le jour où la migration n'est pas
    passée, le prof lit un message clair — il ne travaille pas sur une liste inventée par le code."""
    with dbmod.SessionLocal() as db:
        db.query(SeanceMode).delete()
        db.commit()
        with pytest.raises(HTTPException) as e:
            modes_seance(db)
        assert e.value.status_code == 500
        assert "migration" in e.value.detail.lower()


# ── La langue de la matière : un indicateur, pas un libellé ──────────────────────────────

def test_la_langue_se_reconnait_au_drapeau_et_survit_a_un_renommage():
    """LE défaut réparé. Avant : `matiere == "Langues Vivantes (LV)"`. La matière réelle
    s'appelle « Langue vivante » → l'injection de {langue} ne partait jamais. Maintenant le
    drapeau décide, et renommer la matière ne change rien."""
    with dbmod.SessionLocal() as db:
        mid = matiere_id(db, "Langue vivante", "3e")
        db.query(Matiere).filter(Matiere.id == mid).update({"demande_langue": True})
        u = User(email="lv@local.test", password_hash="x", is_verified=True,
                 subject_id=mid, niveau_id=niveau_id(db, "3e"), langue_lv="Anglais")
        db.add(u)
        db.commit()
        assert matiere_demande_langue(db, u) is True

        # Renommage complet de la matière : le lien tient (il passe par la clé, pas par le nom).
        db.query(Matiere).filter(Matiere.id == mid).update({"nom": "Langues et cultures étrangères"})
        db.commit()
        db.refresh(u)
        assert matiere_demande_langue(db, u) is True


def test_une_matiere_ordinaire_ne_demande_pas_de_langue():
    with dbmod.SessionLocal() as db:
        u = User(email="hg@local.test", password_hash="x", is_verified=True,
                 subject_id=matiere_id(db, "Histoire-Géographie", "3e"), niveau_id=niveau_id(db, "3e"))
        db.add(u)
        db.commit()
        assert matiere_demande_langue(db, u) is False


def test_le_couple_de_travail_prime_sur_le_profil():
    """Le prof travaille hors de son profil : c'est la matière DE TRAVAIL qui décide, comme
    partout ailleurs dans l'application."""
    with dbmod.SessionLocal() as db:
        lv = matiere_id(db, "Langue vivante", "3e")
        db.query(Matiere).filter(Matiere.id == lv).update({"demande_langue": True})
        niv = niveau_id(db, "3e")
        u = User(email="bascule@local.test", password_hash="x", is_verified=True,
                 subject_id=matiere_id(db, "Français", "3e"), niveau_id=niv,
                 travail_matiere_id=lv, travail_niveau_id=niv)
        db.add(u)
        db.commit()
        assert matiere_demande_langue(db, u) is True


# ── Les langues et les statuts : servis depuis la base ───────────────────────────────────

def test_les_langues_vivantes_sont_un_catalogue_de_base():
    with dbmod.SessionLocal() as db:
        labels = [l.label for l in db.query(LangueLv).filter(LangueLv.actif.is_(True))
                                     .order_by(LangueLv.ordre).all()]
        assert labels[0] == "Anglais" and "Autre" in labels and len(labels) == 8


def test_chaque_statut_porte_son_explication():
    """L'écran d'aide recopiait ces phrases. Elles appartiennent au statut : elles sont en base,
    et un statut sans explication trahirait une migration incomplète."""
    with dbmod.SessionLocal() as db:
        rows = db.query(FeedbackStatut).order_by(FeedbackStatut.ordre).all()
        assert len(rows) == 4
        assert all(r.description.strip() for r in rows)
        assert dict((r.code, r.description) for r in rows)["nouveau"] == "Reçu, pas encore traité."
