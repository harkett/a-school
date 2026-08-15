# -*- coding: utf-8 -*-
"""Le contenu de la crèche suit le renommage de son niveau — séquences, séances ET activités

LE DÉFAUT. La migration `d2b6f9c3a7e1` a partagé la crèche en deux sections et renommé le niveau
`BMG_0-3` en « Bébés (0-1 an) » / « Moyens-Grands (1-3 ans) ». Elle n'a pas touché au contenu déjà
écrit, qui porte le nom du niveau EN TEXTE. Résultat : chaque séquence, séance et activité de la
démonstration crèche désigne un niveau qui n'existe plus. Le professeur ouvre la démonstration et
ne voit rien — le contenu est là, mais aucun filtre ne le retrouve.

LES TROIS TABLES, PAS UNE. `sequences`, `seances` et `activites` portent toutes les trois la
colonne `niveau`. Mesuré sur le schéma de démonstration avant cette migration : 10 séquences déjà
corrigées à la main, mais 30 séances et 61 activités encore sur l'ancien code. Ne corriger que les
séquences aurait laissé 91 lignes orphelines sur 101 — et le défaut serait passé pour réparé.

POURQUOI « MOYENS-GRANDS » ET PAS « BÉBÉS ». Le contenu de la démonstration a été écrit pour les
1-3 ans : les cinquante occurrences des fichiers SQL versionnés (`demos/creche_demo/`) le disent,
et les séquences déjà reprises à la main pointent là. Aucune fiche n'était réservée aux 0-1 an.

ELLE PASSE PARTOUT. Alembic applique la migration au schéma courant : sur le réel comme sur chaque
schéma de démonstration (`alembic -x schema=creche upgrade head`). Une base sans ligne concernée
n'est pas touchée — la clause WHERE ne trouve rien, et c'est très bien.

downgrade : rend l'ancien code aux mêmes lignes. Réversible sans perte.

Revision ID: d4a8b2f6c9e3
Revises: c8f2a6d4e9b1
Create Date: 2026-08-15
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "d4a8b2f6c9e3"
down_revision: Union[str, Sequence[str], None] = "c8f2a6d4e9b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ANCIEN = "BMG_0-3"
NOUVEAU = "Moyens-Grands (1-3 ans)"

# `incidents` porte aussi une colonne `niveau`, et elle n'est PAS dans cette liste : c'est la
# trace de ce qui s'est passé à un moment donné. Réécrire un journal pour qu'il colle au présent
# lui retire ce qui fait sa valeur.
TABLES = ("sequences", "seances", "activites")


def _renommer(depuis: str, vers: str) -> None:
    for table in TABLES:
        op.execute(
            sa.text(f"UPDATE {table} SET niveau = :vers WHERE niveau = :depuis")
            .bindparams(vers=vers, depuis=depuis)
        )


def upgrade() -> None:
    _renommer(ANCIEN, NOUVEAU)


def downgrade() -> None:
    _renommer(NOUVEAU, ANCIEN)
