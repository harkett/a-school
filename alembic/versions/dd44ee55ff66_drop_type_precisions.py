"""Suppression de la table morte `type_precisions` (précisions de catalogue GLOBAL).

Constat du 24/07 : depuis le passage des précisions PAR COUPLE (e7f8a9b0c1d2, table
`referentiel_type_precisions`), plus personne ne lisait `type_precisions` — côté prof,
activites.py lit les précisions du couple ; côté admin, la cartouche Types lit/écrit
celles du couple. Ses seuls clients restants étaient les 5 endpoints orphelins
`/admin/activite-types*` (aucun écran depuis la suppression de l'ancienne page Types
d'activité), retirés dans le même geste. Barrière règle 4 : ce que plus personne ne lit,
on ne le garde pas — les 48 lignes dormantes partent avec la table (décision utilisateur).

Downgrade : recrée la table VIDE, au schéma d'origine (f0e1d2c3b4a5) — les données
dormantes ne sont pas restaurées.

Revision ID: dd44ee55ff66
Revises: cc33dd44ee55
"""
import sqlalchemy as sa
from alembic import op

revision = "dd44ee55ff66"
down_revision = "cc33dd44ee55"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_type_precisions_type_activite_id", table_name="type_precisions")
    op.drop_table("type_precisions")


def downgrade():
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
