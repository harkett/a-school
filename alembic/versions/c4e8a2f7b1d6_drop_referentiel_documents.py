"""Supprime `referentiel_documents` : le depot en plusieurs morceaux du LABO.

10/08/2026. CE QUE CETTE TABLE FAISAIT. Un couple cycle · niveau pouvait recevoir PLUSIEURS PDF
(au lycee le programme n'existe qu'eclate, un par matiere et par serie). Chaque morceau avait sa
ligne ; « constituer » les assemblait en un `referentiel.pdf` et creait la ligne `referentiels`.

POURQUOI ELLE PART. Elle n'etait ecrite et lue que par `referentiels_labo.py`, le back du labo —
supprime aujourd'hui avec son ecran. L'ecran en service, Admin > Referentiels, ne connait qu'un
document unique par couple et n'a jamais touche cette table. Une table que plus aucun code ne
regarde n'est pas une reserve : c'est un piege pour la prochaine lecture du schema.

LES DONNEES PERDUES : 2 lignes d'essai du 04/08/2026 (le meme PDF BTS CIEL depose sur les niveaux
42 et 43), `referentiel_id` NULL sur les deux — jamais constituees, donc jamais devenues un
referentiel. Les PDF eux-memes restent sur le disque.

LE DEPOT EN PLUSIEURS MORCEAUX N'EST PAS ABANDONNE : il se relit dans l'historique git
(`referentiels_labo.py`, `pages/Labo.jsx`) le jour ou il sera porte dans l'ecran en service.

Revision ID: c4e8a2f7b1d6
Revises: b3f7a1d5c8e2
Create Date: 2026-08-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e8a2f7b1d6'
down_revision: Union[str, Sequence[str], None] = 'b3f7a1d5c8e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_ref_documents_empreinte", table_name="referentiel_documents")
    op.drop_index("ix_ref_documents_referentiel", table_name="referentiel_documents")
    op.drop_index("ix_ref_documents_niveau", table_name="referentiel_documents")
    op.drop_table("referentiel_documents")


def downgrade() -> None:
    op.create_table(
        "referentiel_documents",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("niveau_id", sa.Integer(),
                  sa.ForeignKey("niveaux.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referentiel_id", sa.Integer(),
                  sa.ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=True),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fichier_origine", sa.Text(), nullable=False),
        sa.Column("fichier_disque", sa.Text(), nullable=False),
        sa.Column("empreinte", sa.String(length=64), nullable=False),
        sa.Column("taille_ko", sa.Integer(), nullable=False),
        sa.Column("pages", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("url_source", sa.Text(), nullable=True),
        sa.Column("apercu", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("niveau_id", "fichier_disque", name="uq_ref_documents_fichier"),
    )
    op.create_index("ix_ref_documents_niveau", "referentiel_documents", ["niveau_id"])
    op.create_index("ix_ref_documents_referentiel", "referentiel_documents", ["referentiel_id"])
    op.create_index("ix_ref_documents_empreinte", "referentiel_documents", ["empreinte"])
