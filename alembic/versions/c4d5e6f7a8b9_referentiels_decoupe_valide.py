# -*- coding: utf-8 -*-
"""referentiels : colonne decoupe_valide (derniere etape — fait passer la puce au vert)

L'admin controle le resultat de la decoupe et l'accepte via le bouton final « Valider le
decoupage ». Cet etat « decoupe validee » = le referentiel est ARRIVE AU BOUT de la procedure ;
c'est lui (et lui seul) qui fait passer la puce du menu au VERT. Donnee NEUVE (n'existe nulle
part ailleurs) -> nouvelle colonne booleenne sur referentiels. false par defaut = pas encore
validee (puce rouge).

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "referentiels",
        sa.Column("decoupe_valide", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("referentiels", "decoupe_valide")
