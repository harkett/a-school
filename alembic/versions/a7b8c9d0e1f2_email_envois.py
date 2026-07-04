"""cree la table email_envois (journal des envois d'email — onglet Suivi)

Une ligne par envoi reel : mail manuel (ex. UNICEF) ET mail de bienvenue auto.
Structure ce que l'Audit ne porte qu'en texte libre (date, destinataire, statut).

downgrade : supprime la table (le suivi disparait, les envois continuent).

Revision ID: a7b8c9d0e1f2
Revises: f3a1b2c3d4e5
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a7b8c9d0e1f2"
down_revision = "f3a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_envois",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("modele_slug", sa.String(length=64), nullable=False),
        sa.Column("modele_nom", sa.String(length=128), nullable=False),
        sa.Column("destinataire", sa.String(length=255), nullable=False),
        sa.Column("objet", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("statut", sa.String(length=16), nullable=False),
        sa.Column("erreur", sa.Text(), nullable=True),
        sa.Column("envoye_le", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_envois_envoye_le", "email_envois", ["envoye_le"])


def downgrade() -> None:
    op.drop_index("ix_email_envois_envoye_le", table_name="email_envois")
    op.drop_table("email_envois")
