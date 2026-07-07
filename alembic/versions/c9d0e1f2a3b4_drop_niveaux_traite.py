"""drop colonne niveaux.traite (dérivée depuis les référentiels, plus stockée)

Le fait « ce niveau a reçu son vrai référentiel » n'est plus un drapeau stocké : il
est DÉRIVÉ à la lecture (un niveau est traité s'il a un référentiel réellement ingéré,
au moins 1 chunk — cf. backend/pedagogie/programmes.py). Source unique de vérité = les
référentiels eux-mêmes. On retire donc la colonne, qui dupliquait un fait dérivable et
devait être maintenue à la main.

downgrade : recree 'traite' avec server_default '0' NOT NULL (les lignes existantes
sont remplies par le default) — retour arriere sans casse.

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("niveaux", "traite")


def downgrade() -> None:
    op.add_column("niveaux", sa.Column("traite", sa.Boolean(), server_default="0", nullable=False))
