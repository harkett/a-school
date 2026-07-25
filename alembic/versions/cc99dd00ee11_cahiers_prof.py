# -*- coding: utf-8 -*-
"""cahiers_prof : cahier des charges interne depose par le prof (1 PDF par prof)

Nouvelle table pour le document propre au prof (cahier des charges de son ecole/structure),
depose depuis son profil. UN par prof (user_id unique) : re-deposer remplace. Le PDF vit sur
disque (data/uploads/cahiers/<user_id>/cahier.pdf) ; la table garde le NOM d'origine + la date.
Additif pur, reversible (downgrade = drop de la table).

Revision ID: cc99dd00ee11
Revises: bb88cc99dd00
Create Date: 2026-07-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cc99dd00ee11"
down_revision: Union[str, Sequence[str], None] = "bb88cc99dd00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cahiers_prof",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("fichier", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_cahiers_prof_user_id"),
    )
    op.create_index("ix_cahiers_prof_user_id", "cahiers_prof", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_cahiers_prof_user_id", table_name="cahiers_prof")
    op.drop_table("cahiers_prof")
