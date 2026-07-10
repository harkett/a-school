"""ajoute la colonne doutes_ia sur referentiels (verdict d'analyse amont, calcule une fois)

L'analyse amont par l'IA (quelles unites sont douteuses) doit etre calculee UNE seule fois puis
relue par l'apercu ET par l'ingestion — sinon deux appels IA separes divergent (l'IA n'est pas
parfaitement repetable) et les deux cotes se contredisent. On range donc le verdict EN BASE, a cote
de la regle de decoupe et de l'arbitrage (regle « toute donnee metier en base »).

Colonne :
  - doutes_ia (Text) : JSON = liste des libelles d'age juges douteux par l'IA. NULL = pas encore
    analyse (calcule au 1er besoin) ; vide quand la regle du couple change (nouvelle analyse propre).

downgrade : supprime la colonne.

Revision ID: c1d2e3f4a5b6
Revises: a3c4d5e6f7a8
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c1d2e3f4a5b6"
down_revision = "a3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("doutes_ia", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("referentiels", "doutes_ia")
