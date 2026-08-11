# -*- coding: utf-8 -*-
"""Colonne `actif` sur ambiguite_exemples : desactiver un exemple sans le perdre

Retirer un exemple faux de la vue du professeur imposait jusqu'ici de le SUPPRIMER — donc de
perdre le texte qu'il fallait justement corriger, et de tout regenerer. Le bouton « Desactiver »
le retire de la vue en une seconde et garde le texte sous la main.

Ce n'est PAS une suppression deguisee (regle maison : supprimer veut dire supprimer). C'est un
etat a part entiere, dit par le mot du bouton, et qui se rallume : « Desactiver » / « Reactiver ».
Le DELETE existe toujours cote serveur, il n'a simplement plus sa place a cet ecran.

Les exemples deja en base sont ACTIFS : c'est ce qu'ils etaient avant cette colonne.

Revision ID: e6d2b9a4c318
Revises: d3b7c1f8e5a4
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e6d2b9a4c318"
down_revision: Union[str, Sequence[str], None] = "d3b7c1f8e5a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ambiguite_exemples",
                  sa.Column("actif", sa.Boolean(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("ambiguite_exemples", "actif")
