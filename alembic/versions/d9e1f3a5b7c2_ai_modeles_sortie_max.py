# -*- coding: utf-8 -*-
"""ai_modeles.sortie_max : le plafond de sortie que le fournisseur impose au modele

Infomaniak REFUSE toute demande au-dela de 5 000 tokens de sortie — 422 « The max tokens must be
between 1 and 5000 », rien n'est genere. Nos reglages de longueur sont au-dessus
(max_tokens_default = 32 000), donc TOUTE generation par ce fournisseur echouait, et l'ecran
n'affichait qu'un « le service a refuse la demande » qui ne disait pas quoi corriger.

Ce plafond n'est ni un reglage d'admin ni un defaut de code : c'est une CARACTERISTIQUE du modele,
imposee par son fournisseur. Elle descend donc en base, a cote du modele, et la resolution de
max_tokens s'y borne (get_sortie_max / get_max_tokens). L'admin garde son reglage : il est
simplement ramene a ce que le modele accepte, au lieu de partir en erreur.

NULL = aucun plafond connu (Groq, Anthropic) -> le reglage admin s'applique tel quel. Seul
`infomaniak/mistral24b` recoit une valeur, mesuree sur l'API elle-meme.

Premiere colonne de l'extension des tables prevue par la specification « gestion des fournisseurs
IA » ; les autres (contexte_max, couts, type_api, base_url) viendront avec leur ecran.

downgrade : drop de la colonne.

Revision ID: d9e1f3a5b7c2
Revises: c8b3d5e7f9a1
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9e1f3a5b7c2"
down_revision: Union[str, Sequence[str], None] = "c8b3d5e7f9a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_modeles", sa.Column("sortie_max", sa.Integer(), nullable=True))
    op.get_bind().execute(
        sa.text(
            "UPDATE ai_modeles SET sortie_max = 5000 "
            "WHERE fournisseur = 'infomaniak' AND modele = 'mistral24b'"
        )
    )


def downgrade() -> None:
    op.drop_column("ai_modeles", "sortie_max")
