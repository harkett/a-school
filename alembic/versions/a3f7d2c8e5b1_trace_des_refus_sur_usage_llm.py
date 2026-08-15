# -*- coding: utf-8 -*-
"""Ajoute resultat / code_http / rang sur usage_llm — la trace de ce qui RATE

POURQUOI. Jusqu'ici, `usage_llm` ne recevait une ligne qu'après une réponse reçue : un appel
refusé (quota, panne, clé morte) ne laissait qu'un `log.warning`, c'est-à-dire rien — un journal
défile et s'efface, il ne s'additionne pas. On ne pouvait donc pas répondre à « qu'est-ce qui
refuse, et à quelle fréquence ? », qui est justement la question à laquelle il faut répondre
AVANT de décider dans quel ordre essayer les fournisseurs.

`resultat` — `ok` · `refus` · `coupe`. Trois états, pas deux : la réponse COUPÉE (le modèle a
atteint sa limite de sortie) a bien consommé et se facture, mais elle est inutilisable. La compter
comme un succès masquerait une dépense qui n'a rien produit. Le mot `coupe` était jusqu'ici
déductible de `motif_arret` (`max_tokens` / `length`), mais seulement en connaissant le vocabulaire
de chaque fournisseur : ici, il est dit une fois pour toutes.

`code_http` — ce que le fournisseur a répondu (429, 402, 500…), NULL quand l'appel a abouti.
C'est lui qui distingue « il n'y a plus de quota » de « le service est en panne » : deux refus qui
n'appellent ni le même geste ni le même rang.

`rang` — la place du fournisseur dans la liste au moment de la tentative. NULL tant qu'il n'y a pas
de liste : aujourd'hui un seul fournisseur est appelé, écrire « 1 » inventerait une cascade qui
n'existe pas encore. La colonne est posée maintenant parce que la trace des refus n'a de valeur
qu'avec elle : « Anthropic a refusé » et « Anthropic a refusé en second recours » ne se lisent pas
pareil.

CE QUE ÇA CHANGE AU CONTRAT DE LA TABLE. `usage_llm` cesse d'être la table des seuls appels
réussis. Elle devient la table des TENTATIVES. Les écrans qui comptent la consommation doivent
donc filtrer sur `resultat` — d'où le défaut `ok` sur tout l'historique, qui n'est fait que
d'appels aboutis : leur lecture d'hier reste juste.

CE N'EST PAS UN DOUBLON AVEC `incidents`. Un incident est un événement d'exploitation, lu un par
un ; ici on compte, on additionne, on compare des fournisseurs entre eux. La même mesure pour deux
usages qui ne se remplacent pas.

downgrade : retire les trois colonnes.

Revision ID: a3f7d2c8e5b1
Revises: c8f5a3d7e2b9
Create Date: 2026-08-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3f7d2c8e5b1"
down_revision: Union[str, Sequence[str], None] = "c8f5a3d7e2b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NOT NULL avec défaut « ok » : l'historique est fait d'appels qui ont abouti, l'affirmer est
    # exact. Le défaut reste ensuite, pour qu'une ligne écrite sans le préciser soit un succès —
    # un refus, lui, se déclare toujours.
    op.add_column("usage_llm", sa.Column("resultat", sa.String(10), nullable=False,
                                         server_default="ok"))
    op.add_column("usage_llm", sa.Column("code_http", sa.Integer(), nullable=True))
    op.add_column("usage_llm", sa.Column("rang", sa.Integer(), nullable=True))
    # L'écran des refus lit « les tentatives ratées de la période » : sans index, c'est un
    # balayage de toute la table à chaque affichage, et elle ne fait que grossir.
    op.create_index("ix_usage_llm_resultat", "usage_llm", ["resultat"])


def downgrade() -> None:
    op.drop_index("ix_usage_llm_resultat", table_name="usage_llm")
    op.drop_column("usage_llm", "rang")
    op.drop_column("usage_llm", "code_http")
    op.drop_column("usage_llm", "resultat")
