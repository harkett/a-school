# -*- coding: utf-8 -*-
"""familles : table des 5 familles de structure d'un referentiel (donnee de reference)

Cree la table `familles` et seme ses 5 lignes (ids figes 1..5). Une famille dit COMMENT
un PDF de referentiel est organise. Idempotent : ON CONFLICT DO NOTHING (rejouable sans
doublon). downgrade : drop_table (aucune table ne depend d'elle).

Revision ID: a0b1c2d3e4f5
Revises: f9a0b1c2d3e4
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a0b1c2d3e4f5"
down_revision: Union[str, Sequence[str], None] = "f9a0b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_FAMILLES = [
    "INSERT INTO familles (id, nom, description) VALUES (1, 'UNITÉS_OFFICIELLES', 'Référentiels structurés en unités officielles (BTS, Bac Pro, etc.)') ON CONFLICT DO NOTHING",
    "INSERT INTO familles (id, nom, description) VALUES (2, 'ACTIVITÉS_PRO', 'Référentiels organisés par activités professionnelles') ON CONFLICT DO NOTHING",
    "INSERT INTO familles (id, nom, description) VALUES (3, 'RNCP_BLOCS', 'Référentiels découpés en blocs de compétences RNCP') ON CONFLICT DO NOTHING",
    "INSERT INTO familles (id, nom, description) VALUES (4, 'GRILLES_TABLEAUX', 'Documents structurés en tableaux/grilles') ON CONFLICT DO NOTHING",
    "INSERT INTO familles (id, nom, description) VALUES (5, 'REFERENTIEL_LIBRE', 'Documents non structurés, format libre') ON CONFLICT DO NOTHING",
]


def upgrade() -> None:
    op.create_table(
        "familles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nom", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.UniqueConstraint("nom", name="uq_familles_nom"),
    )
    for stmt in _FAMILLES:
        op.execute(stmt)


def downgrade() -> None:
    op.drop_table("familles")
