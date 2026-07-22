"""suppression de la colonne key (slug) de types_activite

Le type d'activite est desormais identifie PARTOUT par son `id` (generation, sauvegarde, liaison,
usage). Le slug `key` etait un SECOND identifiant redondant — un doublon d'identite (regle 4) qui,
en plus, cachait du metier dans la chaine (prefixe 'lv_'). On le supprime : une ligne, un seul
identifiant (l'id). L'anti-doublon du catalogue reste par `label` (insensible a la casse).

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-07-22
"""
from alembic import op
import sqlalchemy as sa

revision = "d6e7f8a9b0c1"
down_revision = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("uq_activite_types_key", "types_activite", type_="unique")
    op.drop_column("types_activite", "key")


def downgrade():
    # Recree la colonne. NB : les slugs d'origine sont perdus ; on repart d'un slug derive de l'id
    # (unicite garantie) pour satisfaire NOT NULL + UNIQUE. Purement pour reversibilite de schema.
    op.add_column("types_activite", sa.Column("key", sa.String(length=64), nullable=True))
    op.execute("UPDATE types_activite SET key = 'type_' || id")
    op.alter_column("types_activite", "key", nullable=False)
    op.create_unique_constraint("uq_activite_types_key", "types_activite", ["key"])
