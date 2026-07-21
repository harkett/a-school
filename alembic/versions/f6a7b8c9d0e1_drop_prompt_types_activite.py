"""suppression de la colonne prompt du catalogue global types_activite

Le prompt de generation est SPECIFIQUE au couple (referentiel x type) : il vit desormais sur la
liaison `referentiel_types_activite.prompt` (migration e5f6a7b8c9d0). La colonne `prompt` du
catalogue global `types_activite` n'est plus lue par personne (la generation lit la liaison) :
c'est une donnee en double qui laisse croire, a tort, qu'on travaille PAR TYPE et non PAR COUPLE.
On la supprime — une donnee, une seule place (regle 4).

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-21
"""
from alembic import op
import sqlalchemy as sa

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("types_activite", "prompt")


def downgrade():
    op.add_column(
        "types_activite",
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
    )
