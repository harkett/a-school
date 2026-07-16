"""renomme la table referentiel_activite_types -> referentiel_types_activite (francais)

Renommage PUR de la table de LIAISON : rename_table conserve les donnees, la PK, les index
(ix_ref_activite_types_*), la contrainte d'unicite (uq_ref_activite_type) et les deux cles
etrangeres (vers referentiels et vers types_activite), qui suivent automatiquement. La COLONNE
activite_type_id n'est PAS renommee (autre fois). Rien d'autre ne change.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-16
"""
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("referentiel_activite_types", "referentiel_types_activite")


def downgrade():
    op.rename_table("referentiel_types_activite", "referentiel_activite_types")
