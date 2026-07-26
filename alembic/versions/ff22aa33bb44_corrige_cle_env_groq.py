# -*- coding: utf-8 -*-
"""corrige ai_fournisseurs.cle_env (groq) : GROQ_API_KEY -> GROQ_API_KEY_TEXTE

ai_fournisseurs.cle_env = NOM de la variable d'env de la cle TEXTE du fournisseur
(source UNIQUE, lue par le backend ; la valeur secrete reste au .env). Pour groq la
valeur semee etait GROQ_API_KEY, alors que le .env fournit GROQ_API_KEY_TEXTE
(convention _TEXTE, comme CLAUDE_API_KEY_TEXTE / GROQ_API_KEY_OCR / GROQ_API_KEY_DICTEE).
On corrige la SOURCE en base. Idempotent (garde sur l'ancienne valeur).

Revision ID: ff22aa33bb44
Revises: ee11ff22aa33
Create Date: 2026-07-26
"""
from typing import Sequence, Union

from alembic import op


revision: str = "ff22aa33bb44"
down_revision: Union[str, Sequence[str], None] = "ee11ff22aa33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE ai_fournisseurs SET cle_env = 'GROQ_API_KEY_TEXTE' "
        "WHERE code = 'groq' AND cle_env = 'GROQ_API_KEY'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE ai_fournisseurs SET cle_env = 'GROQ_API_KEY' "
        "WHERE code = 'groq' AND cle_env = 'GROQ_API_KEY_TEXTE'"
    )
