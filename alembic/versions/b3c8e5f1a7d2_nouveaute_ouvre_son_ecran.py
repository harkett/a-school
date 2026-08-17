# -*- coding: utf-8 -*-
"""« Decouvrir » ouvre l'ecran de la fonctionnalite annoncee

La bande de nouveaute disait « Decouvrir » et n'emmenait nulle part : elle depliait le texte
de l'annonce, rien d'autre. Un mot qui promet d'emmener quelque part doit emmener quelque
part, sinon il ment.

D'ou une colonne `page` : la CLE DE L'ECRAN du professeur (celle du menu, `Sidebar.jsx`) que
la nouveaute ouvre quand on clique. Elle reste vide tant que la fonctionnalite n'existe pas —
une carte « a venir » n'a aucun ecran a montrer — et la bande dit alors « En savoir plus » au
lieu de « Decouvrir ». Le mot suit ce que le clic fait vraiment.

`analyser-consigne` est la seule livree a ce jour : son ecran est « Mes analyses > Consignes ».

Revision ID: b3c8e5f1a7d2
Revises: d7a2f4e9c1b8
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3c8e5f1a7d2"
down_revision: Union[str, Sequence[str], None] = "d7a2f4e9c1b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (code, cle d'ecran du menu prof) — seulement ce qui EXISTE deja.
_PAGES = [
    ("analyser-consigne", "consigne"),
]


def upgrade() -> None:
    op.add_column("features_votables",
                  sa.Column("page", sa.String(length=48), nullable=True))
    conn = op.get_bind()
    for code, page in _PAGES:
        conn.execute(sa.text("UPDATE features_votables SET page = :page WHERE code = :code"),
                     {"page": page, "code": code})


def downgrade() -> None:
    op.drop_column("features_votables", "page")
