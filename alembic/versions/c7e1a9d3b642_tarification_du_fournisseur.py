# -*- coding: utf-8 -*-
"""Ajoute `tarification` sur ai_fournisseurs — gratuit ou payant, dit par l'administrateur

POURQUOI CETTE COLONNE. L'écran des fournisseurs range désormais la liste en deux zones : ceux qui
ne coûtent rien, ceux qui se facturent. Rien en base ne portait cette information — ni le tarif des
modèles, ni la présence d'une clé ne permettent de la déduire :

  - un tarif à zéro peut vouloir dire « offert » comme « pas encore relevé » ;
  - un modèle gratuit chez un fournisseur payant ne rend pas le fournisseur gratuit ;
  - un plan gratuit peut devenir payant du jour au lendemain sans qu'aucun chiffre ne bouge chez
    nous.

C'est donc une DÉCISION, pas un calcul : l'administrateur la prend, sur la fiche du fournisseur, et
la base la garde. Aucune règle automatique ne la remplace ni ne la corrige.

DÉFAUT « payant ». Le défaut doit être celui qui ne peut pas tromper : annoncer « gratuit » à tort
ferait appeler en premier un service qui facture. L'inverse ne fait que ranger un fournisseur dans
la mauvaise zone, ce que l'administrateur corrige d'un clic en le voyant.

CE QUE CETTE COLONNE NE FAIT PAS : elle ne touche pas l'ordre d'appel. La boucle descend la liste
dans l'ordre du catalogue, gratuits et payants confondus ; ranger l'écran ne change pas qui répond.

downgrade : retire la colonne.

Revision ID: c7e1a9d3b642
Revises: d5b8c1f4e7a2
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7e1a9d3b642"
down_revision: Union[str, Sequence[str], None] = "d5b8c1f4e7a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_fournisseurs", sa.Column("tarification", sa.String(10), nullable=False,
                                               server_default="payant"))


def downgrade() -> None:
    op.drop_column("ai_fournisseurs", "tarification")
