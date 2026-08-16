# -*- coding: utf-8 -*-
"""`demos.date_dernier_test` disparait : personne ne l'a jamais remplie.

CE QU'ELLE ETAIT. Une date saisie a la main, le jour ou l'on aurait relu la demonstration. Aucun
code ne la lisait : elle s'affichait dans une colonne du tableau, et c'est tout.

POURQUOI ELLE PART. Meme esprit que les cinq statuts supprimes le meme jour (d1a4c7e2b9f5) : un
rituel de validation qui ne correspond a aucune pratique reelle. L'administrateur, en la voyant a
l'ecran : « je n'ai jamais teste cette base ». Une colonne qu'on ne remplit pas ment deux fois —
elle affiche un vide qui ressemble a un oubli, et elle laisse croire qu'un controle existe.

CE QUI RESTE. `date_generation`, la date de fabrication : elle dit de quand date le contenu d'une
demonstration, ce qui se sait et sert.

Revision ID: e2b6d8a4f1c7
Revises: d1a4c7e2b9f5
Create Date: 2026-08-16
"""
from alembic import op
import sqlalchemy as sa


revision = "e2b6d8a4f1c7"
down_revision = "d1a4c7e2b9f5"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("demos", "date_dernier_test")


def downgrade():
    op.add_column("demos", sa.Column("date_dernier_test", sa.DateTime(), nullable=True))
