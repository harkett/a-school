# -*- coding: utf-8 -*-
"""Exemples d'enonces pour « Detecter les ambiguites » — un par couple, EN BASE

Le bouton « Tester un exemple » de l'ecran Ambiguites etait une facade : il repondait « Pas
d'exemple disponible pour le moment ». Avant lui, un texte fige PAR MATIERE avait ete retire
parce qu'il ignorait le niveau (cf. l'en-tete de backend/pedagogie/exemple_referentiel.py).

Ici le couple tient dans `matiere_id` SEUL : une matiere appartient au referentiel d'un niveau,
le niveau est donc deja dedans. Un exemple par matiere = un exemple par couple, sans cle
composee. Le BTS CIEL en STI a le sien, le BTS CIEL en Francais le sien.

Deux colonnes, comme l'a demande l'utilisateur : le TEXTE a coller, et les DEFAUTS qu'on y a
glisses. Un exemple de demonstration ne vaut que s'il y a quelque chose a trouver — et le prof
doit pouvoir verifier apres coup que l'analyse l'a bien trouve.

Table VIDE au depart : les exemples s'ecrivent depuis l'ecran admin, a partir du prompt
`ambiguite_exemple` execute hors de l'application (zero appel payant). Rien n'est seme ici,
une valeur inventee par la migration serait un enonce que personne n'a relu.

downgrade : drop de la table.

Revision ID: b5f8e2a1d740
Revises: f2b9d6c4a807
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b5f8e2a1d740"
down_revision: Union[str, Sequence[str], None] = "f2b9d6c4a807"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ambiguite_exemples",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("matiere_id", sa.Integer(), nullable=False),
        sa.Column("texte", sa.Text(), nullable=False),
        sa.Column("defauts", sa.Text(), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["matiere_id"], ["matieres.id"], ondelete="CASCADE"),
    )
    # UN exemple par couple : l'index unique porte À LA FOIS l'unicité et la recherche par
    # matière — c'est ce que declare le modèle (`unique=True, index=True`). Une contrainte
    # d'unicité EN PLUS de l'index ferait diverger le schéma migré des modèles.
    op.create_index("ix_ambiguite_exemples_matiere_id", "ambiguite_exemples", ["matiere_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_ambiguite_exemples_matiere_id", table_name="ambiguite_exemples")
    op.drop_table("ambiguite_exemples")
