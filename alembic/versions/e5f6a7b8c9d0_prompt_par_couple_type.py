"""colonne prompt sur le lien referentiel_types_activite (prompt PAR couple x type)

Le prompt de generation d'un type d'activite est SPECIFIQUE au couple (referentiel x type),
donc il vit sur la LIGNE de liaison `referentiel_types_activite`, pas sur le catalogue global.
Colonne `prompt` TEXT, non nulle, defaut '' (vide = pas encore genere). Ecrite automatiquement
au coche, reecrite a l'edition. Le decoche ne la touche pas (le prompt reste).

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-21
"""
from alembic import op
import sqlalchemy as sa

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "referentiel_types_activite",
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
    )


def downgrade():
    op.drop_column("referentiel_types_activite", "prompt")
