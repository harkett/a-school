"""ai_modeles : modeles LLM par fournisseur (en base, plus de liste en dur)

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-07-11

Table des modeles LLM texte offerts a l'admin, rattaches a leur fournisseur. DONNEE METIER EN
BASE (remplace la liste SUPPORTED_AI_MODELS en dur). Le modele `recommande` d'un fournisseur
s'affiche en premier ; seuls les `actif` sont selectionnables. Unique (fournisseur, modele).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4b5c6d7e8f9"
down_revision: Union[str, Sequence[str], None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_modeles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("fournisseur", sa.String(length=50), nullable=False),
        sa.Column("modele", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=150), nullable=False),
        sa.Column("recommande", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("fournisseur", "modele", name="uq_ai_modeles_fournisseur_modele"),
    )
    op.create_index("ix_ai_modeles_fournisseur", "ai_modeles", ["fournisseur"])


def downgrade() -> None:
    op.drop_index("ix_ai_modeles_fournisseur", table_name="ai_modeles")
    op.drop_table("ai_modeles")
