"""drop colonne legacy 'cle' de matieres

Le lien vers une matiere se fait par son id ; l'anti-doublon est assure UNIQUEMENT
par le code a chaque porte de saisie (script, extraction PDF, ecran admin) — il n'y a
plus aucune contrainte unique en base. On retire donc la colonne 'cle' (legacy).

downgrade : recree 'cle' en NULLABLE (pas NOT NULL) et SANS contrainte unique, pour
qu'un retour arriere ne plante pas sur une table deja peuplee.

Revision ID: a1c2e3f40506
Revises: b7e4c1a90f23
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1c2e3f40506"
down_revision = "b7e4c1a90f23"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Supprimer la colonne retire aussi sa contrainte unique (PostgreSQL).
    op.drop_column("matieres", "cle")


def downgrade() -> None:
    op.add_column("matieres", sa.Column("cle", sa.String(length=64), nullable=True))
