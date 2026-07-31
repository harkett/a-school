"""Étape 9 lot B — les seuils métier sont EN BASE, et l'écran les lit au lieu de les connaître.

Cinq nombres décidaient du comportement depuis le code : taille et nombre de pièces jointes,
durée mini et maxi d'une séance, taille du cahier des charges. Trois d'entre eux étaient
recopiés dans l'écran — donc changer la valeur côté serveur n'aurait changé que la moitié de
l'application : le serveur aurait refusé à 4 Mo pendant que l'écran continuait d'annoncer 5.

Ce que ces tests garantissent :
  - changer la valeur EN BASE change ce que le serveur accepte, sans toucher au code ;
  - le serveur SERT ces valeurs aux écrans, et il sert exactement celles sur lesquelles il
    tranchera (c'est ce lien-là qui empêche l'écran de mentir) ;
  - le nombre de pièces jointes est désormais tenu par le SERVEUR aussi : une limite que seul
    le navigateur fait respecter n'est pas une limite ;
  - réglage absent = erreur claire, jamais un repli silencieux sur une valeur de code.

Lance avec : pytest (BDD jetable aschool_test via conftest.py — jamais la base dev).
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod  # noqa: E402  (redirigé vers aschool_test par conftest)

from fastapi import HTTPException  # noqa: E402

from backend.communication.feedback import (  # noqa: E402
    _controler_nombre_pieces, _limites_pieces_jointes, limites_pieces_jointes,
)
from backend.contenu.mes_contenus import (  # noqa: E402
    SeanceGeneration, _valider_generation, bornes_duree_seance,
)
from backend.core.models_db import Setting  # noqa: E402


def _regler(db, cle, valeur):
    row = db.query(Setting).filter(Setting.key == cle).first()
    if row:
        row.value = valeur
    else:
        db.add(Setting(key=cle, value=valeur))
    db.commit()


def _seance(duree):
    return SeanceGeneration(theme="Les fractions", duree=duree, mode="standard")


# ── Durée d'une séance ───────────────────────────────────────────────────────────────────

def test_les_bornes_de_duree_viennent_de_la_base():
    with dbmod.SessionLocal() as db:
        assert bornes_duree_seance(db) == (5, 300)
        _valider_generation(_seance(5), db)      # la borne basse est acceptée
        _valider_generation(_seance(300), db)    # la borne haute aussi
        with pytest.raises(HTTPException) as e:
            _valider_generation(_seance(4), db)
        assert e.value.status_code == 400
        assert "entre 5 et 300" in e.value.detail


def test_changer_la_borne_en_base_change_ce_que_le_serveur_accepte():
    """La preuve que le nombre n'est plus dans le code : 20 minutes était refusé, il passe —
    et le MESSAGE au prof suit la nouvelle valeur, il ne reste pas figé sur l'ancienne."""
    with dbmod.SessionLocal() as db:
        _regler(db, "seance_duree_min", "20")
        _valider_generation(_seance(20), db)
        with pytest.raises(HTTPException) as e:
            _valider_generation(_seance(19), db)
        assert "entre 20 et 300" in e.value.detail


def test_reglage_absent_erreur_claire_jamais_un_repli():
    with dbmod.SessionLocal() as db:
        db.query(Setting).filter(Setting.key == "seance_duree_max").delete()
        db.commit()
        with pytest.raises(HTTPException) as e:
            bornes_duree_seance(db)
        assert e.value.status_code == 500
        assert "seance_duree_max" in e.value.detail


# ── Pièces jointes ───────────────────────────────────────────────────────────────────────

def test_le_serveur_sert_a_l_ecran_les_valeurs_sur_lesquelles_il_tranchera():
    """Le piège de ce lot : passer la limite en base côté serveur SEUL remplace une copie par
    une autre. Ce test attache les deux bouts — ce que l'écran reçoit EST ce que le serveur
    applique, y compris après un changement en base."""
    with dbmod.SessionLocal() as db:
        _regler(db, "feedback_piece_jointe_max_mo", "8")
        _regler(db, "feedback_pieces_jointes_max", "2")
        servi = limites_pieces_jointes(db=db)
        assert (servi["taille_max_mo"], servi["nombre_max"]) == (8, 2)
        assert _limites_pieces_jointes(db) == (8, 2)
        # Et les formats annoncés sont ceux que le serveur accepte réellement.
        assert servi["formats_lisibles"] == ["PNG", "JPEG", "PDF", "TXT"]
        assert "image/png" in servi["mime_acceptes"]


def test_le_nombre_de_pieces_est_tenu_par_le_serveur():
    """Il ne l'était que par le navigateur. Aucun prof ne verra la différence — l'écran l'arrête
    avant — mais la limite existe maintenant vraiment."""
    with dbmod.SessionLocal() as db:
        _regler(db, "feedback_pieces_jointes_max", "5")
        _controler_nombre_pieces(db, "a.png,b.png,c.png,d.png,e.png")   # 5 : passe
        _controler_nombre_pieces(db, None)                              # aucune : passe
        with pytest.raises(HTTPException) as e:
            _controler_nombre_pieces(db, "a.png,b.png,c.png,d.png,e.png,f.png")
        assert e.value.status_code == 400
        assert "plus de 5 fichiers" in e.value.detail


def test_la_limite_de_nombre_suit_la_base():
    with dbmod.SessionLocal() as db:
        _regler(db, "feedback_pieces_jointes_max", "2")
        _controler_nombre_pieces(db, "a.png,b.png")
        with pytest.raises(HTTPException) as e:
            _controler_nombre_pieces(db, "a.png,b.png,c.png")
        assert "plus de 2 fichiers" in e.value.detail
