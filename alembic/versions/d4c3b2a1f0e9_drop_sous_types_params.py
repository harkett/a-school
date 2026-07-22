"""suppression des colonnes JSON sous_types / params de types_activite

Les precisions et parametres vivent desormais dans leurs tables filles (type_precisions /
type_parametres), lues par jointure. Plus personne ne lit les blobs JSON `sous_types` / `params`
du catalogue : on les supprime — une donnee = une seule place (regle 4).

downgrade : recree les deux colonnes et les REMPLIT depuis les tables filles (json_agg ordonne),
pour un retour arriere fidele.

Revision ID: d4c3b2a1f0e9
Revises: a1c2e3f4b5d6
Create Date: 2026-07-21
"""
from alembic import op
import sqlalchemy as sa

revision = "d4c3b2a1f0e9"
down_revision = "a1c2e3f4b5d6"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("types_activite", "sous_types")
    op.drop_column("types_activite", "params")


def downgrade():
    op.add_column(
        "types_activite",
        sa.Column("sous_types", sa.Text(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "types_activite",
        sa.Column("params", sa.Text(), nullable=False, server_default="[]"),
    )
    # Reconstitue les blobs JSON depuis les tables filles (retour arriere fidele).
    op.execute(
        "UPDATE types_activite t SET sous_types = COALESCE("
        "  (SELECT json_agg(p.libelle ORDER BY p.ordre)::text"
        "   FROM type_precisions p WHERE p.type_activite_id = t.id), '[]')"
    )
    op.execute(
        "UPDATE types_activite t SET params = COALESCE("
        "  (SELECT json_agg(x.cle)::text"
        "   FROM type_parametres x WHERE x.type_activite_id = t.id), '[]')"
    )
