# -*- coding: utf-8 -*-
"""Outil LLM « ambiguite_exemples » : la voie payante de la cartouche Ambiguites

La cartouche « Ambiguites » de la procedure Referentiel a deux voies, comme les autres etapes :
gratuite (l'admin prend le prompt, l'execute chez lui, recolle) et payante (l'application
appelle le moteur elle-meme). La voie payante a besoin de SA ligne dans `outils_llm` — c'est
elle qui donne a l'admin un `max_tokens` reglable pour cet appel-la.

C'est l'appel le plus LONG en sortie de toute l'application : un enonce de 200 mots par matiere,
et un referentiel en compte jusqu'a quinze. Sans reglage propre, il serait tronque en silence au
milieu d'une matiere — et l'admin ne verrait qu'un bloc manquant, sans savoir pourquoi.

Revision ID: d3b7c1f8e5a4
Revises: a1c8f4e7b902
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3b7c1f8e5a4"
down_revision: Union[str, Sequence[str], None] = "a1c8f4e7b902"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OUTILS = [
    ("ambiguite_exemples", "Exemples d'enonces (ambiguites)", 250,
     "Ecrit un enonce d'exemple par matiere pour TOUT un referentiel, en un seul appel. "
     "C'est la sortie la plus longue du logiciel : 200 mots par matiere, jusqu'a quinze "
     "matieres. Une valeur trop basse coupe la reponse au milieu d'une matiere."),
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
