# -*- coding: utf-8 -*-
"""referentiels.famille_id : lien d'un referentiel vers sa famille de structure

Ajoute la colonne `famille_id` sur `referentiels` (FK -> familles.id), nullable :
les referentiels existants n'ont pas encore de famille. Ajout non destructif.

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("famille_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_referentiels_famille", "referentiels", "familles", ["famille_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_referentiels_famille", "referentiels", type_="foreignkey")
    op.drop_column("referentiels", "famille_id")
