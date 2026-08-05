# -*- coding: utf-8 -*-
"""fournisseur `infomaniak` (AI Tools) + son modele texte

TROISIEME fournisseur LLM texte, a cote de groq et anthropic. Il entre par la BASE, comme les
deux autres : une ligne dans `ai_fournisseurs`, une ligne dans `ai_modeles`. L'ecran admin les
lit deja (GET /admin/ai-providers et /admin/ai-models n'ont AUCUNE liste en dur) : le fournisseur
apparait dans la combo sans qu'une ligne de front ou de router soit retouchee.

- `cle_env` = AITOOLS_API_KEY : le NOM de la variable, jamais sa valeur (le secret reste au .env).
- Le modele porte l'id API EXACT attendu par Infomaniak : `mistral24b`. Ce n'est pas un choix de
  style — l'API refuse tout autre libelle en 422 (« The selected model is invalid », valeurs
  admises : mistral24b, mistral3, qwen3). Le nom long du catalogue
  (mistralai/Ministral-3-14B-Instruct-2512) n'est PAS accepte a l'appel.
- Fenetre d'entree annoncee par Infomaniak pour ce modele : 100 000 tokens — de quoi lire un
  referentiel entier (~49 000 mesures), qui est l'usage vise.

L'URL d'appel, elle, n'est pas ici : elle se construit avec le NUMERO DE PRODUIT du compte
(AITOOLS_PRODUCT_ID, .env) — https://api.infomaniak.com/1/ai/{produit}/openai/chat/completions.
Voir backend/config.py et generator._url_chat.

Idempotent : ON CONFLICT DO NOTHING des deux cotes. Le fournisseur est insere AVANT son modele
(ai_modeles.fournisseur porte une FK vers ai_fournisseurs.code).

downgrade : retire les deux lignes, dans l'ordre inverse.

Revision ID: c8b3d5e7f9a1
Revises: b4e8d2a6f1c9
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8b3d5e7f9a1"
down_revision: Union[str, Sequence[str], None] = "b4e8d2a6f1c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_FOURNISSEUR = {
    "code": "infomaniak",
    "label": "Infomaniak (AI Tools)",
    "actif": True,
    "ordre": 3,
    "cle_env": "AITOOLS_API_KEY",
}

# `modele` = l'id API exact (seul mistral24b / mistral3 / qwen3 sont acceptes) ; `label` = ce que
# l'admin lit dans la combo.
_MODELE = {
    "fournisseur": "infomaniak",
    "modele": "mistral24b",
    "label": "AITools",
    "recommande": True,
    "actif": True,
    "ordre": 0,
}


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO ai_fournisseurs (code, label, actif, ordre, cle_env) "
            "VALUES (:code, :label, :actif, :ordre, :cle_env) "
            "ON CONFLICT (code) DO NOTHING"
        ),
        _FOURNISSEUR,
    )
    conn.execute(
        sa.text(
            "INSERT INTO ai_modeles (fournisseur, modele, label, recommande, actif, ordre) "
            "VALUES (:fournisseur, :modele, :label, :recommande, :actif, :ordre) "
            "ON CONFLICT (fournisseur, modele) DO NOTHING"
        ),
        _MODELE,
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM ai_modeles WHERE fournisseur = :fournisseur AND modele = :modele"),
        {"fournisseur": _MODELE["fournisseur"], "modele": _MODELE["modele"]},
    )
    conn.execute(
        sa.text("DELETE FROM ai_fournisseurs WHERE code = :code"),
        {"code": _FOURNISSEUR["code"]},
    )
