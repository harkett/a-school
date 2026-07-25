"""Colonne `feedbacks.contexte` (sa demande du 25/07) : le feedback emporte tout seul
l'endroit d'où il part — « Écran Créer une activité · Français × 6e » — au lieu d'obliger
le prof à l'écrire. Fait d'ÉVÉNEMENT (où il était au moment d'envoyer), pas une copie de
donnée vivante ; affiché dans la fenêtre avant envoi (transparence), dans Mes feedbacks,
dans l'écran admin et dans l'e-mail de notification. NULL pour l'historique existant.

Revision ID: aa77bb88cc99
Revises: ff66aa77bb88
"""
import sqlalchemy as sa
from alembic import op

revision = "aa77bb88cc99"
down_revision = "ff66aa77bb88"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("feedbacks", sa.Column("contexte", sa.String(length=160), nullable=True))


def downgrade():
    op.drop_column("feedbacks", "contexte")
