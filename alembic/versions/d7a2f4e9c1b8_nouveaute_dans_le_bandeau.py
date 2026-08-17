# -*- coding: utf-8 -*-
"""Une fonctionnalite livree quitte « Bientot disponible » et devient une nouveaute

Deux etats sur la ligne, et ils sont lies :

  · `livree`    — la fonctionnalite existe pour de bon. La carte quitte l'ecran prof
                  « Bientot disponible » : on ne fait plus voter pour ce qui est fait.
  · `nouveaute` — elle s'annonce dans le bandeau d'accueil du professeur. Cette case ne
                  se coche que si `livree` l'est deja (l'ecran grise l'autre cas), et elle
                  se REcoche des mois plus tard quand la fonctionnalite est amelioree :
                  c'est ce qui distingue « c'est fait » de « regardez ca ».

Les votes ne sont jamais perdus : une carte livree garde les siens, ils disent ce que les
professeurs attendaient.

Cette migration n'ajoute QUE les deux colonnes. Le contenu du catalogue (libelles, textes,
ordre d'affichage) appartient a la migration qui le tient, et se branche sur celle du chantier
prof : deux mains sur la meme table, c'est une main de trop.

Revision ID: d7a2f4e9c1b8
Revises: e2b6d8a4f1c7
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7a2f4e9c1b8"
down_revision: Union[str, Sequence[str], None] = "e2b6d8a4f1c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("features_votables",
                  sa.Column("livree", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("features_votables",
                  sa.Column("nouveaute", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("features_votables", "nouveaute")
    op.drop_column("features_votables", "livree")
