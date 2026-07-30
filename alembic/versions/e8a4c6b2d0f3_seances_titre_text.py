"""`seances.titre` passe de VARCHAR(300) à TEXT.

Constat (bug réel du 30/07) : le titre de la séance = le THÈME saisi par le prof — une zone
libre remplie au clavier, par dictée, par import de fichier ou par « Propose-moi un thème ».
Un thème réel dépasse facilement 300 caractères → l'INSERT était rejeté
(StringDataRightTruncation) et l'auto-save (règle 0) échouait à la première génération.
On élargit la colonne — on ne tronque JAMAIS la saisie du prof.

Revision ID: e8a4c6b2d0f3
Revises: d7f3b5a9c1e2
"""
import sqlalchemy as sa
from alembic import op

revision = "e8a4c6b2d0f3"
down_revision = "d7f3b5a9c1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("seances", "titre", type_=sa.Text(), existing_type=sa.String(300), existing_nullable=False)


def downgrade() -> None:
    # Retour au VARCHAR(300) : les titres plus longs seraient rejetés, pas tronqués — on
    # coupe nous-mêmes proprement avant de resserrer le type.
    op.execute("UPDATE seances SET titre = LEFT(titre, 300) WHERE LENGTH(titre) > 300")
    op.alter_column("seances", "titre", type_=sa.String(300), existing_type=sa.Text(), existing_nullable=False)
