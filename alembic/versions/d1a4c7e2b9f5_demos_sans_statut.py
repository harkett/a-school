# -*- coding: utf-8 -*-
"""`demos.statut` disparait : une demonstration est visitable des qu'elle a une adresse.

CE QU'IL Y AVAIT. Cinq mots, du vide au livrable — a_faire, en_cours, fait, teste, valide — une
pastille de couleur dans l'ecran admin et un selecteur dans le formulaire.

CE QU'ILS FAISAIENT REELLEMENT. Deux d'entre eux, et a UN SEUL endroit du programme : ouvrir
l'entree « Demonstration » du menu prof (`_STATUTS_VISITABLES`, backend/prof/demo.py). Les trois
autres la fermaient. Aucune autre ligne de code ne lisait cette colonne.

POURQUOI ILS PARTENT. Le controle existait deja en double : une demonstration qui n'est pas prete
n'a pas d'adresse, et cette absence suffisait a la tenir fermee. Restaient cinq mots a comprendre
et a tenir a jour pour une regle qui tient en une phrase — celle qui reste :

    une demonstration est visitable des qu'elle a une adresse.

SUPPRIMER VEUT DIRE SUPPRIMER : la colonne part, elle n'est pas laissee morte dans la table. Le
retour arriere la recree avec son defaut d'origine ; l'etat de chaque fiche, lui, n'est pas
restituable — il ne se deduit d'aucune autre donnee, et c'est bien la preuve qu'il ne servait a rien.

Revision ID: d1a4c7e2b9f5
Revises: c9f5a3e8d1b6
Create Date: 2026-08-16
"""
from alembic import op
import sqlalchemy as sa


revision = "d1a4c7e2b9f5"
down_revision = "c9f5a3e8d1b6"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("demos", "statut")


def downgrade():
    op.add_column(
        "demos",
        sa.Column("statut", sa.String(16), nullable=False, server_default="a_faire"),
    )
