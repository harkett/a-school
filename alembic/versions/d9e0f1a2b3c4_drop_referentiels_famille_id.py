# -*- coding: utf-8 -*-
"""referentiels.famille_id : suppression de la colonne morte

Cette colonne dupliquait la famille sur le referentiel alors que le lien famille<->niveau vit
dans les tables dediees (famille_couples / famille_couples_autorises). Ecrite mais jamais relue
-> colonne morte. On la retire (avec sa cle etrangere).

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9e0f1a2b3c4"
down_revision: Union[str, Sequence[str], None] = "c8d9e0f1a2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("fk_referentiels_famille", "referentiels", type_="foreignkey")
    op.drop_column("referentiels", "famille_id")


def downgrade() -> None:
    op.add_column("referentiels", sa.Column("famille_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_referentiels_famille", "referentiels", "familles", ["famille_id"], ["id"])
