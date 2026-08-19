# -*- coding: utf-8 -*-
"""« Développement en cours » — la note est partie chez une session.

Le carnet ne disait pas ce qui était confié : une note donnée à une session ressemblait à une
note jamais ouverte. Posé par « Copier », retiré par la coche.

Revision ID: c3d9a1e75b42
Revises: b7f2c4e91a08
Create Date: 2026-08-19
"""
from alembic import op
import sqlalchemy as sa

revision = "c3d9a1e75b42"
down_revision = "b7f2c4e91a08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "taches_a_faire",
        sa.Column("dev_en_cours", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("taches_a_faire", "dev_en_cours")
