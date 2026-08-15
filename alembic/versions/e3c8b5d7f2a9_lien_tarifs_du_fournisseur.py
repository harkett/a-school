# -*- coding: utf-8 -*-
"""Ajoute `lien_tarifs` sur ai_fournisseurs — l'adresse de sa grille, pour aller la lire

POURQUOI. Les tarifs se saisissaient à la main, en lisant la page du fournisseur dans un autre
onglet. C'est long, et surtout ça vieillit : un prix changé chez lui reste faux chez nous jusqu'à
ce que quelqu'un s'en aperçoive. Le fournisseur publie ses prix — il suffit d'aller les lire, donc
de savoir OÙ.

L'adresse est une donnée du fournisseur, au même titre que son `base_url` : elle n'est pas la même
pour deux fournisseurs, elle change quand il refait son site, et personne d'autre que
l'administrateur ne peut la corriger. Elle a donc sa colonne, et pas une constante dans le code.

CE QU'ELLE PERMET : le bouton « Relever les tarifs » de sa fiche, qui lit la page et remplit le
prix d'entrée et de sortie de chaque modèle (`backend/systeme/releve_tarifs.py`). Aucune IA, aucune
clé : une grille tarifaire est un tableau, et un tableau se lit.

CE QUE CETTE MIGRATION REMPLIT : Infomaniak seul, dont l'adresse est connue et vérifiée. Les
autres se saisissent depuis l'écran — affirmer une adresse qu'on n'a pas ouverte, c'est poser un
lien mort dans la base.

downgrade : retire la colonne.

Revision ID: e3c8b5d7f2a9
Revises: b9d4f6a1c3e7
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3c8b5d7f2a9"
down_revision: Union[str, Sequence[str], None] = "b9d4f6a1c3e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_fournisseurs", sa.Column("lien_tarifs", sa.String(500), nullable=True))
    op.execute("UPDATE ai_fournisseurs "
               "SET lien_tarifs = 'https://www.infomaniak.com/fr/hebergement/ai-services/tarifs' "
               "WHERE code = 'infomaniak'")


def downgrade() -> None:
    op.drop_column("ai_fournisseurs", "lien_tarifs")
