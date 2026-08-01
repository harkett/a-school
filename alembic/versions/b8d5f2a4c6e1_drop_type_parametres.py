"""supprime la table type_parametres, chemin de donnees remplace

Les besoins de saisie d'un type d'activite ne sont plus stockes : ils se deduisent des
TROUS DU PROMPT du couple x type, lus a l'instant (`_trous_du_prompt`, active.py). Le
front consomme ce champ `besoins` ; il n'a jamais lu le champ `params` que cette table
alimentait. La table est donc morte des deux cotes :

  - plus personne ne l'ECRIT : la seule migration qui la remplissait (a1c2e3f4b5d6)
    copiait les colonnes JSON `types_activite.sous_types` / `.params`, supprimees depuis
    par d4c3b2a1f0e9. La source est tarie ;
  - plus personne ne la LIT : la requete et le champ `params` de la reponse partent avec
    cette migration.

Le downgrade recree la table VIDE (sa structure d'origine, migration f0e1d2c3b4a5) : on
ne peut pas ressusciter des lignes dont la source n'existe plus, et il n'y en avait plus.

Revision ID: b8d5f2a4c6e1
Revises: a7c4e1b9d3f5
Create Date: 2026-08-01
"""
from alembic import op
import sqlalchemy as sa

revision = "b8d5f2a4c6e1"
down_revision = "a7c4e1b9d3f5"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_type_parametres_type_activite_id", table_name="type_parametres")
    op.drop_table("type_parametres")


def downgrade():
    op.create_table(
        "type_parametres",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("type_activite_id", sa.Integer(),
                  sa.ForeignKey("types_activite.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cle", sa.String(32), nullable=False),
        sa.Column("source", sa.String(16), nullable=False, server_default="systeme"),
        sa.UniqueConstraint("type_activite_id", "cle", name="uq_type_parametres_type_cle"),
    )
    op.create_index("ix_type_parametres_type_activite_id", "type_parametres", ["type_activite_id"])
