# -*- coding: utf-8 -*-
"""tool_usage_logs : chaque analyse dit sur quel couple elle a ete lancee

Un professeur peut enseigner deux couples matiere/niveau sans rapport (BTS technique et
Licence Ergotherapie, par exemple) : l'application le permet, c'est voulu. Tous les ecrans
filtrent donc sur le couple de travail — sauf les compteurs d'analyses de l'Accueil, qui ne
POUVAIENT pas : le journal d'usage ne retenait que l'utilisateur et l'outil.

Deux colonnes NULLABLES, remplies desormais a chaque analyse (ambiguites, consignes, equite).
Les lignes deja en base restent a NULL : elles ne remontent dans aucun compteur par couple, et
c'est le seul choix honnete — leur attribuer le couple d'aujourd'hui inventerait un passe.

Revision ID: b7d4e1a9c3f6
Revises: a8c4f2b6d9e3
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d4e1a9c3f6"
down_revision: Union[str, Sequence[str], None] = "a8c4f2b6d9e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tool_usage_logs", sa.Column("matiere", sa.String(length=80), nullable=True))
    op.add_column("tool_usage_logs", sa.Column("niveau", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("tool_usage_logs", "niveau")
    op.drop_column("tool_usage_logs", "matiere")
