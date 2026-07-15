# -*- coding: utf-8 -*-
"""famille_couples_autorises : clone isole du catalogue des couples autorises + vidage de famille_couples

But : separer DEUX notions qui avaient ete confondues.
  - famille_couples_autorises = CATALOGUE de reference : quels couples (famille + niveau) ont le
    DROIT d'exister. Fige, sert au controle n°2 au depot (lecture seule). Clone du contenu actuel
    de famille_couples (les 152 couples semes). AUCUNE liaison : pas de cle etrangere, table isolee.
  - famille_couples = le REEL : les couples effectivement VALIDES par l'admin. On la VIDE ici ; elle
    ne se remplira plus que par la validation d'un depot (put runtime), jamais par un semis.

upgrade  : cree la table clone, y recopie les couples actuels, puis vide famille_couples.
downgrade: recopie les couples du clone vers famille_couples, puis supprime la table clone.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Table clone, ISOLEE : aucune cle etrangere vers familles/niveaux. Contrainte d'unicite
    #    interne uniquement (pas une liaison, juste l'integrite : un couple n'y figure qu'une fois).
    op.create_table(
        "famille_couples_autorises",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("famille_id", sa.Integer(), nullable=False),
        sa.Column("niveau_id", sa.Integer(), nullable=False),
        sa.UniqueConstraint("famille_id", "niveau_id", name="uq_famille_couples_autorises"),
    )
    # 2) Recopie du contenu actuel (le catalogue) vers le clone.
    op.execute(
        "INSERT INTO famille_couples_autorises (famille_id, niveau_id) "
        "SELECT famille_id, niveau_id FROM famille_couples"
    )
    # 3) Vidage de la vraie table : elle repart a zero et ne se remplit que par les validations admin.
    op.execute("DELETE FROM famille_couples")


def downgrade() -> None:
    # Remet dans famille_couples les couples conserves dans le clone (idempotent), puis supprime le clone.
    op.execute(
        "INSERT INTO famille_couples (famille_id, niveau_id) "
        "SELECT famille_id, niveau_id FROM famille_couples_autorises "
        "ON CONFLICT (famille_id, niveau_id) DO NOTHING"
    )
    op.drop_table("famille_couples_autorises")
