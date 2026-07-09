"""ajoute referentiels.score_min (seuil de pertinence RAG par referentiel, EN BASE)

Le seuil de pertinence (1 - distance cosinus) etait code EN DUR dans la fiche
(creche_0_3_ans.py SCORE_MIN = 0.30). Regle « toute donnee metier en base » : il devient
une colonne de `referentiels`. server_default 0.30 = la valeur actuelle, preservee sur les
lignes existantes ; plus aucune constante en dur.

downgrade : supprime la colonne (le seuil redevient introuvable en base).

Revision ID: e1a2b3c4d5e6
Revises: c9d0e1f2a3b4
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e1a2b3c4d5e6"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("score_min", sa.Float(), nullable=False, server_default="0.30"))


def downgrade() -> None:
    op.drop_column("referentiels", "score_min")
