# -*- coding: utf-8 -*-
"""Suppression du clone famille_couples_autorises (vide, plus lu par aucun code)

Fin du chantier « une seule table de couples » : apres le rapatriement (f1a2b3c4d5e6), le clone est
vide et plus personne ne le lit ni ne l'ecrit (l'endpoint /admin/fc-autorisees lit desormais
famille_couples). On supprime donc la table.

upgrade  : DROP TABLE famille_couples_autorises.
downgrade: recree la table (structure identique a c8d9e0f1a2b3, sans FK, unicite interne) et la
           re-remplit depuis famille_couples -> reversible.

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("famille_couples_autorises")


def downgrade() -> None:
    op.create_table(
        "famille_couples_autorises",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("famille_id", sa.Integer(), nullable=False),
        sa.Column("niveau_id", sa.Integer(), nullable=False),
        sa.UniqueConstraint("famille_id", "niveau_id", name="uq_famille_couples_autorises"),
    )
    op.execute(
        "INSERT INTO famille_couples_autorises (famille_id, niveau_id) "
        "SELECT famille_id, niveau_id FROM famille_couples "
        "ON CONFLICT (famille_id, niveau_id) DO NOTHING"
    )
