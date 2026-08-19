# -*- coding: utf-8 -*-
"""L'ÉPREUVE PROPRE À CHAQUE TÂCHE — une colonne, un texte.

Cocher une note lançait une suite de scénarios FIXE, identique pour toutes : cocher « Une seule
connexion par prof » rejouait l'administration, le menu et les grilles. La case tombait sans que
la fonctionnalité demandée ait été regardée. Chaque note porte désormais SON épreuve.

Revision ID: b7f2c4e91a08
Revises: e4a8c1d7f395
Create Date: 2026-08-18
"""
from alembic import op
import sqlalchemy as sa

revision = "b7f2c4e91a08"
down_revision = "e4a8c1d7f395"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("taches_a_faire", sa.Column("recette", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("taches_a_faire", "recette")
