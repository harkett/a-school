# -*- coding: utf-8 -*-
"""Ajoute `devise` sur ai_modeles — les tarifs ne sont pas tous en dollars

POURQUOI. Les deux colonnes de tarif s'appelaient « $/million » dans leur commentaire, et tout le
monde a fait comme si c'était vrai. Ça ne l'est pas : Infomaniak publie ses prix en FRANCS SUISSES,
Anthropic et OpenAI en dollars. Comparer 0,30 CHF à 3,00 USD sans le savoir, c'est se tromper de
plus de 40 % — et c'est ce chiffre-là qui décide de l'ordre dans lequel on appelle les fournisseurs.

CE QU'ON NE FAIT PAS : convertir à l'écriture. Un montant converti une fois est faux le lendemain,
et faux en silence. Le tarif reste donc stocké TEL QUE LE FOURNISSEUR L'AFFICHE sur sa page — un
administrateur peut le vérifier d'un coup d'œil, sans calcul — et l'euro se calcule à l'affichage,
au taux du jour de la Banque centrale européenne (`backend/core/devises.py`).

DÉFAUT « USD » : c'est la monnaie des tarifs déjà saisis (Anthropic), et celle de la majorité des
fournisseurs. L'affirmer sur l'existant est donc exact ; ce sont les lignes d'Infomaniak qu'il
faudra passer en CHF, et elles n'ont encore aucun tarif.

downgrade : retire la colonne.

Revision ID: d5b8c1f4e7a2
Revises: f4c9e2b7a5d3
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5b8c1f4e7a2"
down_revision: Union[str, Sequence[str], None] = "f4c9e2b7a5d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_modeles", sa.Column("devise", sa.String(3), nullable=False,
                                          server_default="USD"))


def downgrade() -> None:
    op.drop_column("ai_modeles", "devise")
