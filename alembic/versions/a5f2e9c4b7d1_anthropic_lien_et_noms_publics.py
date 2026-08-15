# -*- coding: utf-8 -*-
"""Anthropic : son adresse tarifaire et les noms sous lesquels il publie ses modèles

CONSTATÉ EN LISANT SA PAGE (15/08/2026). Anthropic fait comme Infomaniak : le nom d'appel n'est pas
le nom publié.

  appel                 grille tarifaire
  claude-sonnet-5   ->  Sonnet 5
  claude-opus-4-8   ->  Opus 4.8

Sans ces deux correspondances, le relevé cherche « claude-sonnet-5 » sur une page qui ne l'écrit
nulle part, et repart les mains vides — alors que le tarif y est, en toutes lettres.

L'ADRESSE : `claude.com/pricing`. `anthropic.com/pricing` sert exactement la même page (vérifié :
34 241 caractères des deux côtés) ; on garde la première, c'est celle du produit.

GROQ N'EST PAS ICI, ET C'EST VOLONTAIRE. Sa page de tarifs tient en 1 010 caractères : tout est
construit en JavaScript côté navigateur, il n'y a rien à lire côté serveur. Lui poser une adresse
donnerait un bouton qui échoue à chaque clic. Ses deux modèles sont à 0 (plan gratuit), donc rien
ne manque.

downgrade : efface le lien et les deux noms publics.

Revision ID: a5f2e9c4b7d1
Revises: e3c8b5d7f2a9
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op


revision: str = "a5f2e9c4b7d1"
down_revision: Union[str, Sequence[str], None] = "e3c8b5d7f2a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOMS = {"claude-sonnet-5": "Sonnet 5", "claude-opus-4-8": "Opus 4.8"}


def upgrade() -> None:
    op.execute("UPDATE ai_fournisseurs SET lien_tarifs = 'https://claude.com/pricing' "
               "WHERE code = 'anthropic'")
    for modele, public in NOMS.items():
        op.execute(f"UPDATE ai_modeles SET nom_fournisseur = '{public}' "
                   f"WHERE fournisseur = 'anthropic' AND modele = '{modele}'")


def downgrade() -> None:
    op.execute("UPDATE ai_fournisseurs SET lien_tarifs = NULL WHERE code = 'anthropic'")
    op.execute("UPDATE ai_modeles SET nom_fournisseur = NULL WHERE fournisseur = 'anthropic'")
