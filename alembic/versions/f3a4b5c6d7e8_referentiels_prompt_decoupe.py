"""referentiels : prompt_decoupe + prompt_decoupe_valide

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-07-11

Prompt de découpe PAR COUPLE — généré par l'IA (méta-prompt en base), affiché/corrigé/validé
par l'admin. DONNÉE MÉTIER EN BASE (aucun prompt en dur dans le code). Le garde-fou
`prompt_decoupe_valide` refuse la découpe tant qu'il est False.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, Sequence[str], None] = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("prompt_decoupe", sa.Text(), nullable=True))
    op.add_column(
        "referentiels",
        sa.Column("prompt_decoupe_valide", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("referentiels", "prompt_decoupe_valide")
    op.drop_column("referentiels", "prompt_decoupe")
