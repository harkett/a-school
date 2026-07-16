"""renomme la table activite_types -> types_activite (francais : « type d'activite »)

Renommage PUR : rename_table conserve les donnees, la PK, les index (ux_default,
uq_activite_types_key) et la cle etrangere de referentiel_activite_types (qui suit
automatiquement, car elle reference la table par son identifiant interne, pas par son nom).
La table de LIAISON referentiel_activite_types n'est PAS renommee (autre fois). Rien d'autre
ne change : ni colonnes, ni donnees, ni contraintes.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-16
"""
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("activite_types", "types_activite")


def downgrade():
    op.rename_table("types_activite", "activite_types")
