# -*- coding: utf-8 -*-
"""lien base : FK ai_modeles.fournisseur -> ai_fournisseurs.code

Rend explicite et integre la relation « un modele appartient a un fournisseur » : la
colonne ai_modeles.fournisseur (deja « groq »/« anthropic ») pointe desormais vers
ai_fournisseurs.code (unique). Impossible d'avoir un modele rattache a un fournisseur
inexistant. Toutes les lignes ai_modeles existantes ont un fournisseur present dans
ai_fournisseurs (seed de la migration precedente) -> creation de la FK sans echec.

downgrade : drop de la contrainte (colonne inchangee).

Revision ID: f9a0b1c2d3e4
Revises: e8f9a0b1c2d3
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op


revision: str = "f9a0b1c2d3e4"
down_revision: Union[str, Sequence[str], None] = "e8f9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_ai_modeles_fournisseur",
        "ai_modeles", "ai_fournisseurs",
        ["fournisseur"], ["code"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_ai_modeles_fournisseur", "ai_modeles", type_="foreignkey")
