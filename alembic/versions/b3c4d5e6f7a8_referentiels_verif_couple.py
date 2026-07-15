# -*- coding: utf-8 -*-
"""referentiels : colonne verif_couple (verdict IA du couple, fige a la validation)

Le verdict de l'IA sur le couple, rendu au depot (verifier_couple) et affiche a l'admin, etait
JETE apres l'ecran. On le CONSERVE : nouvelle colonne verif_couple sur referentiels, JSON
{correspond, niveau_lu, raison}, ecrite a la validation (le front transmet le verdict qu'il a deja).
Donnee NEUVE (n'existe nulle part ailleurs) -> pas une copie. NULL = non renseigne.

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("verif_couple", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("referentiels", "verif_couple")
