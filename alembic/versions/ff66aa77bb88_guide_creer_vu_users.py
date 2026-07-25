"""Drapeau `users.guide_creer_vu` (chantier aide du 25/07) : la visite guidée de l'écran
Créer se lance toute seule à la PREMIÈRE visite du prof, puis plus jamais — le « déjà vu »
est une donnée du prof, il vit donc EN BASE (pas dans le navigateur : un autre appareil
doit savoir que le guide a déjà été montré). False par défaut pour tous les comptes
existants : l'écran a beaucoup changé, chacun verra le guide une fois.

Revision ID: ff66aa77bb88
Revises: ee55ff66aa77
"""
import sqlalchemy as sa
from alembic import op

revision = "ff66aa77bb88"
down_revision = "ee55ff66aa77"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("guide_creer_vu", sa.Boolean(), nullable=False,
                                     server_default=sa.false()))


def downgrade():
    op.drop_column("users", "guide_creer_vu")
