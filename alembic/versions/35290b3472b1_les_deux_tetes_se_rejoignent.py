"""les deux tetes se rejoignent

Revision ID: 35290b3472b1
Revises: b7d4e1a9c3f6, d3b9e5a7c2f8
Create Date: 2026-08-17 16:10:02.938475

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35290b3472b1'
down_revision: Union[str, Sequence[str], None] = ('b7d4e1a9c3f6', 'd3b9e5a7c2f8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
