"""cree la table incidents (journal technique des echecs de generation)

Revision ID: 5ca8e6b20fcc
Revises: ff22aa33bb44
Create Date: 2026-07-26 20:13:07.299824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ca8e6b20fcc'
down_revision: Union[str, Sequence[str], None] = 'ff22aa33bb44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cree la table `incidents` : journal technique des echecs de generation (RÈGLE 4, en base).
    Une ligne par plantage, creee AUTOMATIQUEMENT au moment de l'echec (que le prof signale ou non) ;
    `feedback_id` la relie au message du prof s'il clique « signaler » (sinon NULL)."""
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ref", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("endpoint", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("matiere", sa.String(length=120), nullable=True),
        sa.Column("niveau", sa.String(length=120), nullable=True),
        sa.Column("type_activite", sa.String(length=120), nullable=True),
        sa.Column("consigne", sa.Text(), nullable=True),
        sa.Column("user_email", sa.String(length=255), nullable=True),
        sa.Column("feedback_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["feedback_id"], ["feedbacks.id"]),
    )
    op.create_index("ix_incidents_ref", "incidents", ["ref"], unique=True)
    op.create_index("ix_incidents_feedback_id", "incidents", ["feedback_id"])


def downgrade() -> None:
    """Supprime la table `incidents` (le journal disparait ; la generation continue de fonctionner)."""
    op.drop_index("ix_incidents_feedback_id", table_name="incidents")
    op.drop_index("ix_incidents_ref", table_name="incidents")
    op.drop_table("incidents")
