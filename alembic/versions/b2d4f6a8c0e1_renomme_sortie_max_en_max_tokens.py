# -*- coding: utf-8 -*-
"""Renomme sortie_max en max_tokens sur ai_modeles et ai_fournisseurs

POURQUOI. `sortie_max` ne nommait rien : ni le parametre envoye a l'API, ni ce que l'admin lit
quand une generation echoue. Le message d'erreur d'une reponse coupee affiche `max_tokens=5000` ;
l'ecran affichait « Reponse maximale (tokens) » ; la base disait `sortie_max`. Trois mots pour une
seule valeur, et personne — ni l'administrateur, ni la session suivante — ne faisait le lien.

`max_tokens` est le nom du parametre reellement envoye au fournisseur. C'est celui qui apparait
dans les erreurs, dans la documentation des trois fournisseurs, et desormais dans la base et sur
l'ecran. Un champ, un mot, partout.

LES DEUX TABLES ENSEMBLE. `ai_fournisseurs.sortie_max` porte la valeur dont les modeles heritent
faute de valeur propre (les 5 000 d'Infomaniak sont ceux du produit, pas d'un modele). Renommer
l'une sans l'autre casserait la lecture de cet heritage, qui compare les deux colonnes.

RENAME, PAS DROP/ADD : les valeurs deja saisies sont conservees telles quelles.

downgrade : rend aux deux colonnes leur nom d'origine.

Revision ID: b2d4f6a8c0e1
Revises: a1c3e5f7b9d2
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op


revision: str = "b2d4f6a8c0e1"
down_revision: Union[str, Sequence[str], None] = "a1c3e5f7b9d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("ai_modeles", "sortie_max", new_column_name="max_tokens")
    op.alter_column("ai_fournisseurs", "sortie_max", new_column_name="max_tokens")


def downgrade() -> None:
    op.alter_column("ai_fournisseurs", "max_tokens", new_column_name="sortie_max")
    op.alter_column("ai_modeles", "max_tokens", new_column_name="sortie_max")
