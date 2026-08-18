"""la recette entre dans le carnet des taches

Revision ID: e4a8c1d7f395
Revises: a7f3c2e9b481

Cocher une note ne suffit plus : la recette doit passer. Trois colonnes portent ce verdict —
l etat (NULL jamais tentee, verte, ratee), la date du passage, et le motif de l echec en clair.

Toutes les notes existantes partent a NULL, y compris celles deja cochees : elles ont ete faites
avant que la regle existe, et leur inventer une recette verte serait une preuve fabriquee.
"""
from alembic import op
import sqlalchemy as sa

revision = 'e4a8c1d7f395'
down_revision = 'a7f3c2e9b481'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('taches_a_faire', sa.Column('recette_etat', sa.String(length=10), nullable=True))
    op.add_column('taches_a_faire', sa.Column('recette_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('taches_a_faire', sa.Column('recette_detail', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('taches_a_faire', 'recette_detail')
    op.drop_column('taches_a_faire', 'recette_at')
    op.drop_column('taches_a_faire', 'recette_etat')
