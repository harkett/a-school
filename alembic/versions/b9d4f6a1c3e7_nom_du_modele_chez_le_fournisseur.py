# -*- coding: utf-8 -*-
"""Ajoute `nom_fournisseur` sur ai_modeles — le nom public, à côté du nom d'appel

LE CONSTAT (15/08/2026, vérifié en appelant l'API). Infomaniak désigne le même modèle de deux
façons :

  - `mistral3` — le SEUL nom que son API accepte dans un appel. Le nom long est refusé
    (« validation_failed »), et la réponse renvoie « mistral3 » ;
  - `mistralai/Ministral-3-14B-Instruct-2512` — le nom de sa liste publique (`GET /1/ai/models`)
    et de sa grille tarifaire.

Aucun des deux n'est inventé par nous : ce sont deux noms DU FOURNISSEUR, pour deux usages. Le
premier sert à appeler, le second à retrouver ce que le modèle coûte. Sans le second, relever un
tarif sur sa page demande de deviner quelle ligne va avec quel modèle — c'est cette devinette que
la colonne supprime.

CE QU'ELLE NE FAIT PAS : remplacer `modele`. La colonne `modele` reste l'identifiant d'appel, celui
qui part dans la requête. `nom_fournisseur` ne sert qu'à lire — un tarif, une fiche technique.

VIDE = LES DEUX NOMS SONT LE MÊME. C'est le cas d'Anthropic (« claude-sonnet-5 » partout) et de
Groq (« openai/gpt-oss-120b »). On n'écrit donc que là où les deux diffèrent.

CE QUE CETTE MIGRATION REMPLIT : `mistral3` seulement. Son nom public est certain — c'est le seul
modèle « ready » de la liste d'Infomaniak, et sa fenêtre (100 000) est exactement celle qu'on a en
base. `qwen3` et `mistral24b` répondent encore à l'appel mais ne figurent plus dans cette liste :
leur nom public reste donc vide, ce qui est un FAIT, pas un oubli.

downgrade : retire la colonne.

Revision ID: b9d4f6a1c3e7
Revises: c7e1a9d3b642
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b9d4f6a1c3e7"
down_revision: Union[str, Sequence[str], None] = "c7e1a9d3b642"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_modeles", sa.Column("nom_fournisseur", sa.String(200), nullable=True))
    op.execute("UPDATE ai_modeles "
               "SET nom_fournisseur = 'mistralai/Ministral-3-14B-Instruct-2512' "
               "WHERE fournisseur = 'infomaniak' AND modele = 'mistral3'")


def downgrade() -> None:
    op.drop_column("ai_modeles", "nom_fournisseur")
