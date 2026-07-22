"""tables type_precisions et type_parametres (fin des blobs JSON sous_types / params)

Les precisions (choix « Precision » offerts au prof) et les parametres (champs saisis, ex. « nb »)
d'un type d'activite vivaient dans deux colonnes JSON de `types_activite` (sous_types / params) :
un blob non atomique, que la base ne peut ni requeter, ni relier, ni controler (regle 4). On cree
ici les deux tables filles — une ligne par valeur, reliee au type par cle etrangere (CASCADE),
unicite par type. Tables VIDES a ce stade : ni deplacement de donnees, ni suppression des colonnes
JSON, ni rebranchement — ce sont les taches suivantes.

Revision ID: f0e1d2c3b4a5
Revises: f6a7b8c9d0e1
Create Date: 2026-07-21
"""
from alembic import op
import sqlalchemy as sa

revision = "f0e1d2c3b4a5"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "type_precisions",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "type_activite_id", sa.Integer(),
            sa.ForeignKey("types_activite.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("libelle", sa.String(length=128), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source", sa.String(length=16), nullable=False, server_default="systeme"),
        sa.UniqueConstraint("type_activite_id", "libelle", name="uq_type_precisions_type_libelle"),
    )
    op.create_index("ix_type_precisions_type_activite_id", "type_precisions", ["type_activite_id"])

    op.create_table(
        "type_parametres",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "type_activite_id", sa.Integer(),
            sa.ForeignKey("types_activite.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("cle", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False, server_default="systeme"),
        sa.UniqueConstraint("type_activite_id", "cle", name="uq_type_parametres_type_cle"),
    )
    op.create_index("ix_type_parametres_type_activite_id", "type_parametres", ["type_activite_id"])


def downgrade():
    op.drop_index("ix_type_parametres_type_activite_id", table_name="type_parametres")
    op.drop_table("type_parametres")
    op.drop_index("ix_type_precisions_type_activite_id", table_name="type_precisions")
    op.drop_table("type_precisions")
