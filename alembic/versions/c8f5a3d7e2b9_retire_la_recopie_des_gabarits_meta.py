# -*- coding: utf-8 -*-
"""retire les 4 gabarits de meta-prompt et vide les colonnes qu'ils avaient remplies

CE QUE CETTE MIGRATION DEFAIT, ET POURQUOI. La veille (e3f7b1d5a8c2, puis b6e2c4a9f7d1) on a
seme quatre GABARITS de meta-prompt, recopies sur un referentiel neuf a sa validation. L'idee
etait de reparer un constat reel : College . 4e etait arrive avec ses quatre colonnes vides et
l'ecran repondait « aucun meta-prompt en base » aux quatre etapes.

C'ETAIT SE TROMPER DE PROBLEME. Une colonne vide sur un referentiel neuf n'est pas une panne,
c'est son etat normal — il n'a pas encore ete charge. Et les quatre gabarits ont ete ecrits a
partir des meta-prompts du BTS CIEL option A, les seuls qui existaient : sur les 5 494 caracteres
de celui de la decoupe, « option » revient 4 fois, « code » 4 fois, plus « diplome »,
« reglement d'examen », « grille horaire », « specialite », « pole », « fonction » — et pas une
seule mention de programme, de cycle, de theme ni d'annee. Recopie sur un programme de college,
ce texte fait chercher des codes d'unites et des options A/B dans un programme scolaire.

UN TEXTE FAUX QUI A L'AIR JUSTE EST PIRE QU'UNE COLONNE VIDE. Vide, l'ecran dit ce qu'il faut
charger et on le charge. Rempli, personne ne va compter les occurrences de « option » pour
s'apercevoir qu'il decrit un autre diplome.

C'est d'ailleurs la faute du 08/08/2026 refaite sous un autre nom : ce jour-la, le repli sur un
meta-prompt COMMUN avait ete retire — a raison, il faisait chercher une grille d'horaires dans
un programme de creche. La recopie a la validation produit exactement le meme effet ; seul le
mecanisme change.

CE QUE FAIT L'UPGRADE, dans cet ordre :
  1. vide toute colonne `prompt_meta_*` encore EGALE, mot pour mot, au gabarit correspondant :
     c'est une copie automatique, jamais un texte saisi par l'admin. Un meta-prompt retouche a
     la main, ou ecrit a la main, ne correspond plus et n'est pas touche ;
  2. supprime les quatre lignes de `settings`.
La comparaison lit `settings` AVANT le DELETE : l'ordre n'est pas indifferent.

downgrade : VOLONTAIREMENT VIDE. Ces quatre lignes sont une erreur reconnue le jour meme ; les
re-semer ne restaurerait rien d'utile et remettrait le mecanisme en marche sur toute base qui
redescendrait d'un cran. Le schema n'est pas touche, il n'y a donc rien a defaire.

Revision ID: c8f5a3d7e2b9
Revises: b6e2c4a9f7d1
Create Date: 2026-08-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8f5a3d7e2b9"
down_revision: Union[str, Sequence[str], None] = "b6e2c4a9f7d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Les cles du registre qui SORTENT. `tests/test_prompts_en_base.py` lit ce nom-la : sans lui,
# il signalerait eternellement quatre prompts « semes par une migration, absents du registre ».
PROMPTS_RETIRES = (
    "gabarit_meta_matieres",
    "gabarit_meta_decoupe",
    "gabarit_meta_types",
    "gabarit_meta_precisions",
)

# Colonne du referentiel -> cle du gabarit qui avait pu la remplir.
_COLONNES = {
    "prompt_meta_matieres": "gabarit_meta_matieres",
    "prompt_meta_decoupe": "gabarit_meta_decoupe",
    "prompt_meta_types": "gabarit_meta_types",
    "prompt_meta_precisions": "gabarit_meta_precisions",
}


def upgrade() -> None:
    for colonne, cle in _COLONNES.items():
        op.execute(sa.text(
            f"UPDATE referentiels SET {colonne} = NULL "
            f"WHERE {colonne} = (SELECT value FROM settings WHERE key = :k)"
        ).bindparams(k=f"prompt_{cle}"))
    for cle in PROMPTS_RETIRES:
        op.execute(sa.text("DELETE FROM settings WHERE key = :k").bindparams(k=f"prompt_{cle}"))


def downgrade() -> None:
    """Rien. Voir l'en-tete : re-semer une erreur reconnue n'a pas de sens, et le schema est intact."""
