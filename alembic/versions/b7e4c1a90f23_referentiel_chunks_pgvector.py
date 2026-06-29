"""referentiel_chunks (RAG pgvector)

Revision ID: b7e4c1a90f23
Revises: c9ffe00af0fd
Create Date: 2026-06-29

Crée la table des chunks de référentiel + leur embedding (RAG sur PostgreSQL/pgvector,
remplace ChromaDB). N'active PAS l'extension : CREATE EXTENSION est un geste superuser,
hors migration (déjà fait). Tourne sous le rôle applicatif `aschool` : table + index seulement.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'b7e4c1a90f23'
down_revision: Union[str, Sequence[str], None] = 'c9ffe00af0fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crée la table referentiel_chunks + ses 3 index (B-tree x2, HNSW cosinus)."""
    op.create_table(
        'referentiel_chunks',
        sa.Column('id', sa.Integer(), sa.Identity(), nullable=False),
        sa.Column('referentiel_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('option_ab', sa.Text(), nullable=False),
        sa.Column('page', sa.Integer(), nullable=False),
        sa.Column('texte', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=False),
        sa.Column('embedding_model', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['referentiel_id'], ['referentiels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_referentiel_chunks_referentiel_id',
                    'referentiel_chunks', ['referentiel_id'], unique=False)
    op.create_index('ix_referentiel_chunks_ref_option',
                    'referentiel_chunks', ['referentiel_id', 'option_ab'], unique=False)
    op.create_index(
        'ix_referentiel_chunks_embedding_hnsw',
        'referentiel_chunks', ['embedding'], unique=False,
        postgresql_using='hnsw',
        postgresql_ops={'embedding': 'vector_cosine_ops'},
    )


def downgrade() -> None:
    """Défait exactement upgrade() : les 3 index, puis la table."""
    op.drop_index('ix_referentiel_chunks_embedding_hnsw', table_name='referentiel_chunks')
    op.drop_index('ix_referentiel_chunks_ref_option', table_name='referentiel_chunks')
    op.drop_index('ix_referentiel_chunks_referentiel_id', table_name='referentiel_chunks')
    op.drop_table('referentiel_chunks')
