"""embedding 384 -> 1024 (BGE-M3)

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-07-10

Passe referentiel_chunks.embedding de vector(384) (ancien modele MiniLM) a
vector(1024) (BGE-M3, le modele reellement utilise a l'ingestion ET a la recherche
- cf. backend/rag/embeddings.py). Recree l'index HNSW cosinus (un index vectoriel
est lie a la dimension de la colonne).

Les vecteurs sont une donnee GENEREE, reconstruite par re-ingestion : la table est
vide au moment du changement, aucun cast de donnees.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Colonne embedding 384 -> 1024 + recreation de l'index HNSW cosinus."""
    op.drop_index("ix_referentiel_chunks_embedding_hnsw", table_name="referentiel_chunks")
    op.execute("ALTER TABLE referentiel_chunks ALTER COLUMN embedding TYPE vector(1024)")
    op.create_index(
        "ix_referentiel_chunks_embedding_hnsw",
        "referentiel_chunks", ["embedding"], unique=False,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    """Retour a 384 (defait exactement upgrade())."""
    op.drop_index("ix_referentiel_chunks_embedding_hnsw", table_name="referentiel_chunks")
    op.execute("ALTER TABLE referentiel_chunks ALTER COLUMN embedding TYPE vector(384)")
    op.create_index(
        "ix_referentiel_chunks_embedding_hnsw",
        "referentiel_chunks", ["embedding"], unique=False,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
