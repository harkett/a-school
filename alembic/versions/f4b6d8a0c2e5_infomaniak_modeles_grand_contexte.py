# -*- coding: utf-8 -*-
"""Infomaniak : les deux modeles a grand contexte, et mistral3 recommande

`mistral24b` etait le seul modele Infomaniak seme, choisi sur la foi de son nom. C'est le plus
PETIT des trois que le produit accepte : sa fenetre s'arrete a 32 000 tokens, quand un referentiel
complet en pese ~46 000. Il refusait donc en 400 tout document entier — l'usage meme qui a motive
l'ajout du fournisseur.

Mesure faite sur l'API (84 000 tokens d'entree envoyes aux trois) :

  mistral24b   32 000 de contexte   -> refuse
  mistral3    100 000 de contexte   -> passe
  qwen3       100 000 de contexte   -> passe

`mistral3` devient donc le modele RECOMMANDE d'Infomaniak, et `mistral24b` perd cette marque : le
premier de la liste doit etre celui qui fait le travail demande.

La sortie reste plafonnee a 5 000 tokens pour les trois : ce n'est pas une limite du modele mais du
produit AI Tools, verifiee sur chacun.

Les identifiants sont ceux que l'API accepte (mistral24b, mistral3, qwen3) ; le catalogue publie
des noms longs (mistralai/Ministral-3-14B-Instruct-2512) qu'elle REFUSE a l'appel.

downgrade : retire les deux lignes et rend a mistral24b sa marque « recommande ».

Revision ID: f4b6d8a0c2e5
Revises: e2a4c6b8d0f3
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4b6d8a0c2e5"
down_revision: Union[str, Sequence[str], None] = "e2a4c6b8d0f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_MODELES = [
    {"fournisseur": "infomaniak", "modele": "mistral3", "label": "AITools — Mistral 3 (100k)",
     "recommande": True, "actif": True, "ordre": 0, "sortie_max": 5000, "contexte_max": 100000},
    {"fournisseur": "infomaniak", "modele": "qwen3", "label": "AITools — Qwen 3 (100k)",
     "recommande": False, "actif": True, "ordre": 2, "sortie_max": 5000, "contexte_max": 100000},
]


def upgrade() -> None:
    conn = op.get_bind()
    for m in _MODELES:
        conn.execute(
            sa.text(
                "INSERT INTO ai_modeles (fournisseur, modele, label, recommande, actif, ordre, "
                "sortie_max, contexte_max) VALUES (:fournisseur, :modele, :label, :recommande, "
                ":actif, :ordre, :sortie_max, :contexte_max) "
                "ON CONFLICT (fournisseur, modele) DO NOTHING"
            ),
            m,
        )
    # mistral24b reste offert (une fenetre plus petite suffit aux textes courts), mais il n'est
    # plus celui que l'ecran met en avant.
    conn.execute(
        sa.text("UPDATE ai_modeles SET recommande = false, ordre = 1 "
                "WHERE fournisseur = 'infomaniak' AND modele = 'mistral24b'")
    )


def downgrade() -> None:
    conn = op.get_bind()
    for m in _MODELES:
        conn.execute(
            sa.text("DELETE FROM ai_modeles WHERE fournisseur = :fournisseur AND modele = :modele"),
            {"fournisseur": m["fournisseur"], "modele": m["modele"]},
        )
    conn.execute(
        sa.text("UPDATE ai_modeles SET recommande = true, ordre = 0 "
                "WHERE fournisseur = 'infomaniak' AND modele = 'mistral24b'")
    )
