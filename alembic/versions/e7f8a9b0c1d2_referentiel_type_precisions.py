"""table referentiel_type_precisions : precisions PAR COUPLE x type (fille de la liaison)

La precision d'un type etait GLOBALE (`type_precisions`, cle sur le type seul) : la meme valeur servie
a la creche et au doctorat. Faille corrigee ici : on cree une table fille de la liaison
`referentiel_types_activite` (couple x type), ou vit deja le `prompt`. Chaque couple a donc SES
precisions. Table VIDE a ce stade ; le remplissage (saisie admin, plus tard suggestions IA) se fait
par le get-put de l'ecran Referentiels. On NE touche PAS a `type_precisions` (catalogue global, encore
affiche en lecture seule sur l'ecran Types d'activite).

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-07-22
"""
from alembic import op
import sqlalchemy as sa

revision = "e7f8a9b0c1d2"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "referentiel_type_precisions",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "referentiel_activite_type_id", sa.Integer(),
            sa.ForeignKey("referentiel_types_activite.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("libelle", sa.String(length=128), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source", sa.String(length=16), nullable=False, server_default="admin"),
        sa.UniqueConstraint("referentiel_activite_type_id", "libelle", name="uq_ref_type_precisions_lien_libelle"),
    )
    op.create_index("ix_ref_type_precisions_lien", "referentiel_type_precisions", ["referentiel_activite_type_id"])


def downgrade():
    op.drop_index("ix_ref_type_precisions_lien", table_name="referentiel_type_precisions")
    op.drop_table("referentiel_type_precisions")
