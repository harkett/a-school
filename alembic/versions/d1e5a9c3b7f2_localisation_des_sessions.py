# -*- coding: utf-8 -*-
"""D'où vient une session — la ville, à côté de l'adresse IP

LE DÉFAUT. L'écran des sessions montrait l'adresse IP. Personne ne lit une adresse IP. Un compte
ouvert en même temps à Lille et à Marseille est un compte partagé entre deux personnes, et rien
à l'écran ne permettait de le voir.

CE QUE PORTENT LES COLONNES. `localisation` est faite pour l'œil — « Lyon, France ». Les deux
coordonnées sont faites pour le calcul : elles servent à mesurer l'écart entre deux sessions du
même compte, ce que deux noms de ville ne permettent pas.

REMPLIES APRÈS COUP, JAMAIS PENDANT. Elles restent vides à la création de la session : résoudre
une adresse demande d'interroger un service extérieur, et aucune page de professeur n'attend
après un tiers. La résolution se fait quand l'administrateur ouvre l'écran — une fois par
session, le résultat est gardé ici.

Rien n'est rempli ici pour l'existant : une session vieille de plusieurs heures ne prouve plus
rien, et son adresse sera résolue au premier affichage si elle est encore active.

downgrade : retire les trois colonnes. Rien n'est perdu — l'adresse IP, elle, reste.

Revision ID: d1e5a9c3b7f2
Revises: c9a4e7b2d6f3
Create Date: 2026-08-15
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "d1e5a9c3b7f2"
down_revision: Union[str, Sequence[str], None] = "c9a4e7b2d6f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_sessions", sa.Column("localisation", sa.String(120), nullable=True))
    op.add_column("user_sessions", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("user_sessions", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_sessions", "longitude")
    op.drop_column("user_sessions", "latitude")
    op.drop_column("user_sessions", "localisation")
