"""ajoute email_templates.description (a quoi sert le mail) + renseigne 'welcome'

Chaque modele porte une phrase expliquant a quoi il sert, affichee au-dessus de
l'editeur (hors contenu du mail). Editable ; le mail de bienvenue est pre-rempli.

downgrade : supprime la colonne.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None

_WELCOME_DESC = "Envoye automatiquement a chaque enseignant qui vient d'activer son compte."


def upgrade() -> None:
    op.add_column(
        "email_templates",
        sa.Column("description", sa.String(length=255), nullable=False, server_default=""),
    )
    op.execute(
        sa.text("UPDATE email_templates SET description = :d WHERE slug = 'welcome'")
        .bindparams(d=_WELCOME_DESC)
    )


def downgrade() -> None:
    op.drop_column("email_templates", "description")
