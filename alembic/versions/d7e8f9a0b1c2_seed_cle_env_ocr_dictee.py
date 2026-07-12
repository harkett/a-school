# -*- coding: utf-8 -*-
"""seed settings cle_env_ocr / cle_env_dictee (nom des variables d'environnement des cles OCR + dictee)

Depuis la separation des cles Groq par usage (OCR / dictee), chaque usage a SA cle,
pour des statistiques par usage sur le tableau de bord Groq. Le NOM de la variable
d'environnement est une DONNEE METIER -> il vit EN BASE (table settings) ; seule la
VALEUR (le secret) reste dans le .env, jamais en base.

Sans ces 2 lignes, get_cle_api() leve une erreur claire (nom absent). Elles doivent
donc voyager jusqu'a la vraie base -> cette migration. Idempotent : ON CONFLICT (key)
DO NOTHING (ne jamais ecraser une valeur deja editee par l'admin).

downgrade : supprime uniquement ces 2 cles (non destructif pour le reste de settings).

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
Create Date: 2026-07-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d7e8f9a0b1c2"
down_revision: Union[str, Sequence[str], None] = "c6d7e8f9a0b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_CLES = (
    ("cle_env_ocr", "GROQ_API_KEY_OCR"),
    ("cle_env_dictee", "GROQ_API_KEY_DICTEE"),
)


def upgrade() -> None:
    conn = op.get_bind()
    for key, value in _CLES:
        conn.execute(
            sa.text(
                "INSERT INTO settings (key, value) VALUES (:key, :value) "
                "ON CONFLICT (key) DO NOTHING"
            ),
            {"key": key, "value": value},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM settings WHERE key IN ('cle_env_ocr', 'cle_env_dictee')")
    )
