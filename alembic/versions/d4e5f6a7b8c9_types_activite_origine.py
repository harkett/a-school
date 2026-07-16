"""types_activite : colonne `origine` (systeme | admin | ia)

Le BADGE d'un type coché pour un couple doit refléter l'ORIGINE du type, jamais « qui a coché » :
  - 'systeme' : type fourni par aSchool (catalogue pré-rempli) ;
  - 'admin'   : type ajouté à la main par l'admin via « Ajouter » ;
  - 'ia'      : type issu d'une suggestion IA.

On ajoute la colonne `origine` sur `types_activite` avec server_default 'systeme' : les types déjà
présents (les 14 semés = le defaut + les 13 familles) deviennent donc 'systeme', ce qui est exact.
Les futurs ajouts admin/IA fixeront l'origine explicitement. `source` de la LIAISON reprend cette
origine au moment où l'admin coche (voir cocher_types_activite).

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "types_activite",
        sa.Column("origine", sa.String(length=16), nullable=False, server_default="systeme"),
    )


def downgrade():
    op.drop_column("types_activite", "origine")
