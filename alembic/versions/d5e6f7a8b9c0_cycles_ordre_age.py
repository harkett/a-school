# -*- coding: utf-8 -*-
"""cycles : ordre d'affichage par progression d'âge (crèche → doctorat)

Confort de lecture du menu des couples : les cycles s'affichaient dans un ordre arbitraire
(hérité de leur insertion). On repose la colonne `ordre` pour suivre l'âge / le niveau, de la
crèche (le plus jeune) au doctorat (le plus avancé). DONNÉE d'affichage seulement : on ne touche
NI aux `id` (référencés par niveaux.cycle_id, etc.), NI aux noms — uniquement `ordre`. Le match se
fait sur le NOM du cycle (jamais sur l'id), donc robuste quel que soit l'id. Le menu, qui trie déjà
par Cycle.ordre (get, zéro copie), reflète aussitôt la nouvelle séquence.

Downgrade : restaure exactement l'ordre qui existait avant (relevé sur le miroir).

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Nouvel ordre : progression d'âge / niveau, crèche → doctorat. Le supérieur est classé par niveau
# post-bac (BTS bac+2, BUT/Licence bac+3, Master bac+5, Doctorat bac+8).
NOUVEL_ORDRE = {
    "Crèche": 1,
    "École maternelle": 2,
    "École élémentaire": 3,
    "Collège": 4,
    "Lycée": 5,
    "Lycée professionnel": 6,
    "BTS": 7,
    "BUT": 8,
    "Licence": 9,
    "Master": 10,
    "Doctorat": 11,
}

# Ordre AVANT cette migration (relevé sur le miroir) — pour un downgrade fidèle.
ANCIEN_ORDRE = {
    "École élémentaire": 1,
    "Collège": 2,
    "École maternelle": 3,
    "Lycée": 4,
    "Licence": 5,
    "Lycée professionnel": 6,
    "Crèche": 7,
    "BTS": 8,
    "Master": 9,
    "BUT": 10,
    "Doctorat": 11,
}


def _appliquer(mapping: dict) -> None:
    """Pose `ordre` cycle par cycle, en matchant sur le NOM (jamais l'id)."""
    conn = op.get_bind()
    for nom, ordre in mapping.items():
        conn.execute(
            sa.text("UPDATE cycles SET ordre = :ordre WHERE nom = :nom"),
            {"ordre": ordre, "nom": nom},
        )


def upgrade() -> None:
    _appliquer(NOUVEL_ORDRE)


def downgrade() -> None:
    _appliquer(ANCIEN_ORDRE)
