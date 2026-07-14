# -*- coding: utf-8 -*-
"""feedback_statuts : catalogue des statuts de feedback (donnee de reference, EN BASE)

Remplace les deux constantes en dur `_STATUTS_VALIDES` (admin.py) et `STATUTS_MODIFIABLES`
(feedback.py) par une table de reference. `code` unique = cle metier ; `modifiable` porte la
notion SOURCE (statut ou l'auteur peut encore editer), distincte des statuts assignables
(toutes les lignes). Une FK `feedbacks.statut -> feedback_statuts.code` fait de la base
l'autorite : un statut invalide est refuse par la base, pas seulement par le code.

Seed 4 lignes sans id explicite (serial) -> aucune desync de sequence. Idempotent :
ON CONFLICT (code) DO NOTHING. FK posee APRES le seed (les statuts references existent).

downgrade : drop FK puis drop table.

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (code, label, modifiable, ordre). modifiable=true -> l'auteur peut encore editer le feedback.
_STATUTS = [
    ("nouveau", "Nouveau", True, 0),
    ("en_cours", "En cours", True, 1),
    ("traite", "Traité", False, 2),
    ("archive", "Archivé", False, 3),
]


def upgrade() -> None:
    op.create_table(
        "feedback_statuts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("modifiable", sa.Boolean(), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("code", name="uq_feedback_statuts_code"),
    )
    conn = op.get_bind()
    ins = sa.text(
        "INSERT INTO feedback_statuts (code, label, modifiable, ordre) "
        "VALUES (:code, :label, :modifiable, :ordre) ON CONFLICT (code) DO NOTHING"
    )
    for code, label, modifiable, ordre in _STATUTS:
        conn.execute(ins, {"code": code, "label": label, "modifiable": modifiable, "ordre": ordre})
    # FK APRES le seed : les codes references existent deja (les feedbacks presents portent
    # des statuts issus de cette meme liste).
    op.create_foreign_key(
        "fk_feedbacks_statut_feedback_statuts",
        "feedbacks", "feedback_statuts",
        ["statut"], ["code"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_feedbacks_statut_feedback_statuts", "feedbacks", type_="foreignkey")
    op.drop_table("feedback_statuts")
