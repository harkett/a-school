# -*- coding: utf-8 -*-
"""Table usage_llm : garder la trace de chaque appel IA, et les tarifs Anthropic

L'ecran « IA > Statistiques » existait en disant « rien n'est encore mesure ». Ce n'etait pas un
ecran a finir : il n'avait rien a lire. Les tokens de chaque appel etaient bien calcules, puis
ecrits dans le journal applicatif — c'est-a-dire perdus. Un journal defile et s'efface, il ne
s'additionne pas.

Cette migration cree l'endroit ou la trace se pose. A partir de la, chaque appel LLM reussi laisse
une ligne : quand, quel fournisseur, quel modele, quel outil, combien de tokens entree et sortie,
combien de temps, et pourquoi le modele s'est arrete.

CE QUI N'EST PAS STOCKE : le cout. Le prix vit dans `ai_modeles` et se corrige ; le figer ici
obligerait a reecrire l'historique a chaque correction de grille. Il est donc calcule a la lecture.
Ni le prompt ni la reponse : cette table sert a compter, pas a relire.

LES TARIFS. La migration e2a4c6b8d0f3 a cree `cout_entree_million` / `cout_sortie_million` en les
laissant VIDES, avec la bonne raison : aucun tarif ne s'invente. On remplit ici les SEULS que l'on
peut citer — la grille publique Anthropic ($ par million de tokens, relevee le 05/08/2026) :

  claude-opus-5     5.00 entree / 25.00 sortie
  claude-opus-4-8   5.00 / 25.00
  claude-sonnet-5   3.00 / 15.00
  claude-haiku-4-5  1.00 /  5.00

Groq et Infomaniak restent VIDES : leur grille n'a pas ete relevee, et un tarif approximatif serait
pire qu'un tarif absent — l'ecran affiche alors les tokens sans montant, ce qui se voit, plutot
qu'un montant faux, qui ne se voit pas. L'UPDATE est cible par (fournisseur, modele) : il ne touche
que les lignes deja presentes et n'en cree aucune.

downgrade : supprime la table et revide les deux colonnes de tarif.

Revision ID: a1c3e5f7b9d2
Revises: f4b6d8a0c2e5
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1c3e5f7b9d2"
down_revision: Union[str, Sequence[str], None] = "f4b6d8a0c2e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TARIFS = [
    {"fournisseur": "anthropic", "modele": "claude-opus-5", "entree": "5.0000", "sortie": "25.0000"},
    {"fournisseur": "anthropic", "modele": "claude-opus-4-8", "entree": "5.0000", "sortie": "25.0000"},
    {"fournisseur": "anthropic", "modele": "claude-sonnet-5", "entree": "3.0000", "sortie": "15.0000"},
    {"fournisseur": "anthropic", "modele": "claude-haiku-4-5", "entree": "1.0000", "sortie": "5.0000"},
]


def upgrade() -> None:
    op.create_table(
        "usage_llm",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("fournisseur", sa.String(length=50), nullable=False),
        sa.Column("modele", sa.String(length=100), nullable=False),
        # Pas de cle etrangere vers outils_llm : une statistique ne doit jamais refuser une ligne.
        # Un appel dont l'outil n'est pas encore nomme se compte sous « non precise ».
        sa.Column("outil", sa.String(length=50), nullable=True),
        sa.Column("tokens_entree", sa.Integer(), nullable=True),
        sa.Column("tokens_sortie", sa.Integer(), nullable=True),
        sa.Column("duree_ms", sa.Integer(), nullable=True),
        sa.Column("motif_arret", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # Les trois axes de l'ecran : par periode, par modele, par tache.
    op.create_index("ix_usage_llm_created_at", "usage_llm", ["created_at"])
    op.create_index("ix_usage_llm_modele", "usage_llm", ["modele"])
    op.create_index("ix_usage_llm_outil", "usage_llm", ["outil"])

    connexion = op.get_bind()
    for t in _TARIFS:
        connexion.execute(
            sa.text("UPDATE ai_modeles SET cout_entree_million = :entree, "
                    "cout_sortie_million = :sortie "
                    "WHERE fournisseur = :fournisseur AND modele = :modele"),
            t,
        )


def downgrade() -> None:
    connexion = op.get_bind()
    for t in _TARIFS:
        connexion.execute(
            sa.text("UPDATE ai_modeles SET cout_entree_million = NULL, cout_sortie_million = NULL "
                    "WHERE fournisseur = :fournisseur AND modele = :modele"),
            {"fournisseur": t["fournisseur"], "modele": t["modele"]},
        )
    op.drop_index("ix_usage_llm_outil", table_name="usage_llm")
    op.drop_index("ix_usage_llm_modele", table_name="usage_llm")
    op.drop_index("ix_usage_llm_created_at", table_name="usage_llm")
    op.drop_table("usage_llm")
