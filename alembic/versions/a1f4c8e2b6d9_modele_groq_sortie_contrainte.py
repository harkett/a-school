"""ai_modeles : un modele Groq capable de SORTIE CONTRAINTE (json_schema)

POURQUOI. Le fournisseur de secours n'en est pas un s'il ne peut pas faire tourner
l'application. Groq n'offrait qu'un seul modele en base — `llama-3.3-70b-versatile` — et
ce modele REFUSE `response_format: json_schema` (mesure le 05/08 : HTTP 400
« This model does not support response format `json_schema` »). Or la lecture des
matieres, la detection du couple et la DECOUPE d'un referentiel passent toutes par une
sortie contrainte : basculer sur Groq les cassait net, au moment precis ou l'on bascule
— c'est-a-dire quand l'autre fournisseur est deja en panne.

CE QUI EST AJOUTE. `openai/gpt-oss-120b`, verifie sur l'API Groq le 05/08 : il accepte le
schema complet et rend bien `titre` / `option` / `garder`. Teste modele par modele sur la
cle du projet ; les autres offerts par Groq (llama-3.1-8b, llama-3.3-70b, qwen3.6-27b) le
refusent tous.

LE « RECOMMANDE » CHANGE DE MODELE, et ce n'est pas cosmetique : c'est lui que l'ecran
PRESELECTIONNE quand l'admin choisit un fournisseur. Laisser la recommandation sur Llama
3.3 revenait a proposer d'office, en secours, le seul modele qui ne sait pas travailler.
Llama reste offert (il convient aux generations libres), il n'est simplement plus le
premier propose.

Idempotent : ON CONFLICT DO NOTHING sur l'insert. L'UPDATE du drapeau ne touche que les
deux lignes Groq nommees ici, jamais Anthropic.

Revision ID: a1f4c8e2b6d9
Revises: a9d4e2f6b8c3
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1f4c8e2b6d9"
down_revision: Union[str, Sequence[str], None] = "a9d4e2f6b8c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NOUVEAU = {
    "fournisseur": "groq",
    "modele": "openai/gpt-oss-120b",   # id API exact
    "label": "GPT-OSS 120B",
    "recommande": True,
    "actif": True,
    "ordre": 0,
}
_ANCIEN = "llama-3.3-70b-versatile"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO ai_modeles (fournisseur, modele, label, recommande, actif, ordre) "
            "VALUES (:fournisseur, :modele, :label, :recommande, :actif, :ordre) "
            "ON CONFLICT (fournisseur, modele) DO NOTHING"
        ),
        _NOUVEAU,
    )
    # Un seul recommande par fournisseur : Llama recule d'un rang, il reste selectionnable.
    conn.execute(
        sa.text("UPDATE ai_modeles SET recommande = false, ordre = 1 "
                "WHERE fournisseur = 'groq' AND modele = :ancien"),
        {"ancien": _ANCIEN},
    )
    conn.execute(
        sa.text("UPDATE ai_modeles SET recommande = true, ordre = 0 "
                "WHERE fournisseur = 'groq' AND modele = :nouveau"),
        {"nouveau": _NOUVEAU["modele"]},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM ai_modeles WHERE fournisseur = 'groq' AND modele = :modele"),
        {"modele": _NOUVEAU["modele"]},
    )
    conn.execute(
        sa.text("UPDATE ai_modeles SET recommande = true, ordre = 0 "
                "WHERE fournisseur = 'groq' AND modele = :ancien"),
        {"ancien": _ANCIEN},
    )
