# -*- coding: utf-8 -*-
"""Tableau de bord : « Equite d'une evaluation » passe de a_venir a fait

La ligne disait vrai jusqu'a aujourd'hui : « la page rend Outil en cours de developpement ».
C'etait litteralement le cas — un bloc ecrit en dur dans le routeur, sans composant ni route.

L'ecran existe desormais (src/components/Equite.jsx, backend/analyse/equite.py, catalogue
`equite_criteres`, deux prompts en base), et il est ouvert cote prof : entree du menu degrisee,
carte de l'Accueil ordinaire, encart « En developpement » de la barre laterale retire — il
n'annoncait plus que cette seule chose.

Ces gestes vont ENSEMBLE. Un seul d'entre eux oublie, et deux endroits du produit disent le
contraire l'un de l'autre : c'est exactement ce qui etait arrive aux Consignes (menu grise,
Accueil ouvert) et aux Ambiguites (tableau de bord « fait », ecran grise).

downgrade : remet a_venir et sa note d'origine, figee ici.

Revision ID: c9b4e7a2d6f3
Revises: a7d3f9c2e5b8
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9b4e7a2d6f3"
down_revision: Union[str, Sequence[str], None] = "a7d3f9c2e5b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ECRAN = "Mes analyses"
NOM = "Équité d'une évaluation"
COMPOSANT = "src/components/Equite.jsx"
NOTE_AVANT = "la page rend « Outil en cours de développement »"


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("UPDATE fonctionnalites SET etat = 'fait', note = NULL, composant = :c "
                "WHERE ecran = :e AND nom = :n"),
        {"c": COMPOSANT, "e": ECRAN, "n": NOM},
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("UPDATE fonctionnalites SET etat = 'a_venir', note = :note, composant = NULL "
                "WHERE ecran = :e AND nom = :n"),
        {"note": NOTE_AVANT, "e": ECRAN, "n": NOM},
    )
