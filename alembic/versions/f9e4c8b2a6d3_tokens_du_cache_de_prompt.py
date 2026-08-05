# -*- coding: utf-8 -*-
"""Ajoute tokens_cache_ecriture / tokens_cache_lecture sur usage_llm

POURQUOI, ET POURQUOI CE N'EST PAS FACULTATIF. Le cache de prompt d'Anthropic permet de ne payer
que 10 % d'un preambule deja vu — ce qui compte beaucoup ici, ou six outils envoient le MEME
referentiel (~70 000 tokens) pour rendre trois lignes.

Mais Anthropic ne compte PAS ces tokens dans `input_tokens` : il les rend a part, dans
`cache_creation_input_tokens` et `cache_read_input_tokens`. Sans ces deux colonnes, un appel qui
relit 70 000 tokens depuis le cache s'enregistrerait comme un appel de 200 tokens. L'ecran
« IA > Statistiques » afficherait alors une facture DIX FOIS TROP BASSE, et le gain apparent du
cache serait pour l'essentiel une erreur de mesure. Mesurer une economie mal, c'est ne pas la
mesurer.

DEUX COLONNES ET NON UNE, parce que les deux ne se paient pas au meme prix : l'ecriture coute
1,25x le tarif d'entree (on fait garder le texte), la relecture 0,10x. Les additionner
interdirait de calculer le montant.

A NE PAS CONFONDRE avec `depuis_cache`, pose la veille : celui-la est NOTRE cache disque de
developpement (rejeu local, zero token, zero dollar). Ici, l'appel part bel et bien chez le
fournisseur — il coute simplement moins cher.

NULLABLE, sans valeur par defaut : `NULL` veut dire « le fournisseur n'a rien dit » (Groq et
Infomaniak n'ont pas cette mecanique), ce qui n'est pas la meme chose que zero. L'historique reste
donc muet la-dessus au lieu d'affirmer qu'aucun cache n'a servi.

downgrade : retire les deux colonnes.

Revision ID: f9e4c8b2a6d3
Revises: f8d3b7a5c1e9
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9e4c8b2a6d3"
down_revision: Union[str, Sequence[str], None] = "f8d3b7a5c1e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("usage_llm", sa.Column("tokens_cache_ecriture", sa.Integer(), nullable=True))
    op.add_column("usage_llm", sa.Column("tokens_cache_lecture", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("usage_llm", "tokens_cache_lecture")
    op.drop_column("usage_llm", "tokens_cache_ecriture")
