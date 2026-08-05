# -*- coding: utf-8 -*-
"""Ajoute depuis_cache sur usage_llm — distinguer un appel PAYE d'un rejeu gratuit

POURQUOI. Le cout en developpement ne vient pas du modele choisi, il vient de rappeler l'API a
chaque essai : une decoupe de referentiel envoie ~210 000 tokens, et la relancer trois fois pour
regler un detail d'affichage la fait payer trois fois pour une reponse identique. Un cache disque
(dev uniquement, `LLM_CACHE=1`) rejoue desormais la reponse deja obtenue.

Reste la question de la mesure. Un rejeu ne consomme rien, mais il a bien eu lieu : sans ligne,
l'ecran « IA > Statistiques » afficherait 3 appels quand l'admin en a lance 10, et le cache
travaillerait invisible — impossible de savoir s'il sert.

D'ou cette colonne. Le rejeu POSE SA LIGNE, avec ses vrais modele et outil, a 0 token et 0 dollar,
marquee `depuis_cache`.

UNE COLONNE, ET NON UN FAUX FOURNISSEUR « cache ». Nommer le fournisseur « cache » aurait perdu le
modele et l'outil, c'est-a-dire exactement ce qu'on veut lire : « la decoupe sur Sonnet 5 a ete
rejouee ». La colonne garde les deux et repond en plus a « combien d'appels evites ».

VALEUR SEMEE. `false` : tout ce qui est deja en base a bien ete envoye et paye. Aucune ligne
existante n'est reecrite.

downgrade : retire la colonne.

Revision ID: d4f6b8a0c2e3
Revises: c3e5a7b9d1f4
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4f6b8a0c2e3"
down_revision: Union[str, Sequence[str], None] = "c3e5a7b9d1f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usage_llm",
        sa.Column("depuis_cache", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("usage_llm", "depuis_cache")
