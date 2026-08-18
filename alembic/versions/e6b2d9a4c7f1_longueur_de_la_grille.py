# -*- coding: utf-8 -*-
"""La génération d'une grille entre dans les longueurs réglables

Le bouton « Générer la grille » de l'écran « Mes évals → Grilles » appelle le modèle
(`get_max_tokens(db, "grille_generation")`, backend/contenu/grilles.py). Sans sa ligne ici,
l'administrateur n'aurait aucun champ pour la régler et la valeur par défaut s'appliquerait en
silence — exactement le trou que `tests/test_outils_llm_en_base.py` interdit.

LE PROMPT, LUI, EST ARRIVÉ AVANT (`d2a8f6c4b1e7`), et la ligne d'outil ne pouvait pas
l'accompagner : l'appel n'existait pas encore, le réglage aurait été orphelin — l'administrateur
se serait vu proposer la longueur d'une génération que rien ne déclenchait, et
`test_aucune_ligne_orpheline` a effectivement fait tomber la migration qui l'essayait. Même ordre
que pour les consignes : le prompt par `c5e1a9d7b3f4`, l'outil seulement par `d1f5b8c3e7a2`.

C'EST LA SORTIE LA PLUS LONGUE DU PRODUIT APRÈS LA DÉCOUPE D'UN RÉFÉRENTIEL. Une grille, c'est
quatre à six critères, une échelle de quatre échelons, et un descripteur rédigé dans chaque case
— vingt à trente cases, en JSON. Une valeur basse ne tronquerait pas la fin d'un texte, elle
couperait le JSON en plein milieu : la réponse entière devient illisible, et le professeur paie
un appel pour rien.

downgrade : retire la ligne.

Revision ID: e6b2d9a4c7f1
Revises: d2a8f6c4b1e7
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e6b2d9a4c7f1"
down_revision: Union[str, Sequence[str], None] = "d2a8f6c4b1e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OUTILS = [
    ("grille_generation", "Génération d'une grille d'évaluation", 70,
     "Écrit la grille entière en une fois : quatre à six critères, l'échelle, et un descripteur "
     "rédigé dans chaque case — vingt à trente cases. La réponse est un JSON : une valeur basse "
     "le couperait en plein milieu et rendrait toute la génération inutilisable."),
]


def upgrade() -> None:
    conn = op.get_bind()
    for outil, libelle, ordre, aide in OUTILS:
        conn.execute(sa.text(
            "INSERT INTO outils_llm (outil, libelle, aide, ordre) "
            "VALUES (:outil, :libelle, :aide, :ordre) ON CONFLICT (outil) DO NOTHING"
        ), {"outil": outil, "libelle": libelle, "aide": aide, "ordre": ordre})


def downgrade() -> None:
    conn = op.get_bind()
    for outil, _libelle, _ordre, _aide in OUTILS:
        conn.execute(sa.text("DELETE FROM outils_llm WHERE outil = :o"), {"o": outil})
