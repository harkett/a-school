"""Ajoute `url` a la table `demos` : l'adresse de l'instance qui sert cette base.

07/08/2026. Une base de demonstration ne se visite pas depuis l'application reelle : elle a sa
PROPRE instance, branchee dessus, sur sa propre adresse. C'est cette adresse qui relie le niveau
d'un prof a son bac a sable — sans elle, l'entree « Demonstration » du menu ne saurait ou aller.

NULL = l'instance n'est pas encore montee. L'entree du menu reste alors grisee : une fiche peut
exister (la base est fabriquee) longtemps avant que quiconque puisse s'y rendre.
"""
from alembic import op
import sqlalchemy as sa


revision = "c9e4b1a7d306"
down_revision = "b3f7d2a9c1e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("demos", sa.Column("url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("demos", "url")
