# -*- coding: utf-8 -*-
"""Ajoute supporte_temperature sur ai_modeles, et retire le « si Anthropic » du moteur

POURQUOI. Le moteur portait une regle en dur : « temperature : volontairement IGNOREE — les
modeles Claude Opus 4.x la rejettent (400) ». Ecrite deux fois, dans les deux voies Anthropic.

Trois defauts, le meme que celui deja corrige pour `max_tokens` :

  1. L'admin regle une temperature sur l'ecran Generation, valide, et la valeur est jetee en
     silence. Rien ne le lui dit. Il croit avoir agi.
  2. La regle vise un FOURNISSEUR entier alors que la contrainte tient au MODELE : un futur
     modele Anthropic qui accepterait la temperature resterait bride par le code.
  3. Un modele d'un autre fournisseur qui la refuserait demanderait une modification du moteur,
     alors que `type_api` a justement ete cree pour que le moteur cesse de connaitre les
     fournisseurs par leur nom.

La fiche du modele porte deja `supporte_schema` et `supporte_stream` : la meme question, posee de
la meme facon, avec la meme reponse. `supporte_temperature` rejoint ses deux voisines.

VALEURS SEMEES. `true` par defaut — c'est le cas general, et le comportement des fournisseurs a
dialecte OpenAI (Groq, Infomaniak), qui l'acceptent tous aujourd'hui. Puis `false` sur les modeles
Anthropic presents, qui la refusent en 400. Cible par (fournisseur, modele) : aucune ligne creee,
seules celles qui existent sont mises a jour.

downgrade : retire la colonne.

Revision ID: c3e5a7b9d1f4
Revises: b2d4f6a8c0e1
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3e5a7b9d1f4"
down_revision: Union[str, Sequence[str], None] = "b2d4f6a8c0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_modeles",
        sa.Column("supporte_temperature", sa.Boolean(), nullable=False, server_default="true"),
    )
    # Les Claude Opus 4.x et les modeles 5 rejettent `temperature` en 400 : la case dit ce que le
    # code disait, mais par modele et modifiable sans toucher au moteur.
    op.get_bind().execute(
        sa.text("UPDATE ai_modeles SET supporte_temperature = false WHERE fournisseur = 'anthropic'")
    )


def downgrade() -> None:
    op.drop_column("ai_modeles", "supporte_temperature")
