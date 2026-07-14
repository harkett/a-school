# -*- coding: utf-8 -*-
"""famille_couples : pont famille <-> niveau (couples rattaches a une famille)

Table nouvelle. On ne stocke que famille_id + niveau_id ; le cycle se deduit du niveau
(niveaux.cycle_id) -> aucune redondance. UNIQUE (famille_id, niveau_id) : un niveau ne
s'inscrit qu'une fois dans une famille. Remplie par l'humain (admin/dev), jamais par l'IA.
Aucune donnee semee ici : la liste des couples viendra ensuite.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, Sequence[str], None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "famille_couples",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("famille_id", sa.Integer(), nullable=False),
        sa.Column("niveau_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["famille_id"], ["familles.id"]),
        sa.ForeignKeyConstraint(["niveau_id"], ["niveaux.id"]),
        sa.UniqueConstraint("famille_id", "niveau_id", name="uq_famille_couples_famille_niveau"),
    )
    op.create_index("ix_famille_couples_famille_id", "famille_couples", ["famille_id"])
    op.create_index("ix_famille_couples_niveau_id", "famille_couples", ["niveau_id"])


def downgrade() -> None:
    op.drop_index("ix_famille_couples_niveau_id", table_name="famille_couples")
    op.drop_index("ix_famille_couples_famille_id", table_name="famille_couples")
    op.drop_table("famille_couples")
