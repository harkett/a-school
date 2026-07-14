"""ajoute referentiels.forcage_motif (motif de forçage d'une validation malgré alerte, EN BASE)

Quand l'admin valide un dépôt malgré une alerte des vérifications (couple lu par l'IA != couple
declare, ou famille absente de famille_couples), il saisit un motif OBLIGATOIRE. Ce motif est
trace EN BASE (regle « toute donnee metier en base ») + loggue. NULL = validation normale.

downgrade : supprime la colonne.

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-07-13
"""
from alembic import op
import sqlalchemy as sa


revision = "a6b7c8d9e0f1"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("forcage_motif", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("referentiels", "forcage_motif")
