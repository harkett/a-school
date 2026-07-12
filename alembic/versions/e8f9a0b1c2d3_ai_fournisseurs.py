# -*- coding: utf-8 -*-
"""ai_fournisseurs : fournisseurs LLM offerts a l'admin (en base, plus de liste en dur)

Table des fournisseurs LLM texte offerts a l'admin. DONNEE METIER EN BASE (remplace les
listes SUPPORTED_AI_PROVIDERS / ALL_AI_PROVIDERS en dur). Seuls les `actif` sont
selectionnables ; les autres apparaissent grises « pas encore disponible ». `code` =
identifiant technique du moteur ; `cle_env` = NOM de la variable d'env de la cle TEXTE
du fournisseur (la valeur, le secret, reste dans le .env). Unique (code).

Contenu seed = les 2 fournisseurs operationnels aujourd'hui (groq, anthropic), avec le
nom de leur variable de cle texte. Idempotent : ON CONFLICT (code) DO NOTHING.

downgrade : drop de la table (structure jeune, aucune FK entrante).

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8f9a0b1c2d3"
down_revision: Union[str, Sequence[str], None] = "d7e8f9a0b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_FOURNISSEURS = [
    {"code": "groq", "label": "Groq", "actif": True, "ordre": 1, "cle_env": "GROQ_API_KEY"},
    {"code": "anthropic", "label": "Anthropic (Claude)", "actif": True, "ordre": 2, "cle_env": "CLAUDE_API_KEY_TEXTE"},
]


def upgrade() -> None:
    op.create_table(
        "ai_fournisseurs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=150), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cle_env", sa.String(length=100), nullable=False, server_default=""),
        sa.UniqueConstraint("code", name="uq_ai_fournisseurs_code"),
    )
    conn = op.get_bind()
    for f in _FOURNISSEURS:
        conn.execute(
            sa.text(
                "INSERT INTO ai_fournisseurs (code, label, actif, ordre, cle_env) "
                "VALUES (:code, :label, :actif, :ordre, :cle_env) "
                "ON CONFLICT (code) DO NOTHING"
            ),
            f,
        )


def downgrade() -> None:
    op.drop_table("ai_fournisseurs")
