"""Seme `ai_provider` et `ai_model` : personne ne les semait, le code les inventait.

10/08/2026, suite de f1c9a3e7b5d2. AUCUNE migration n'a jamais ecrit ces deux lignes. Elles
existent sur les bases en service parce qu'un administrateur a un jour ouvert l'ecran et
enregistre ; partout ailleurs, c'est `SETTING_DEFAULTS` qui les fournissait en dur.

CE QUE CA VOULAIT DIRE. Une installation neuve n'avait pas de fournisseur d'IA en base — elle
avait celui du code, et l'ecran Parametres ne montrait aucune ligne. La premiere etape du tableau
de bord (« Choisir le fournisseur d'IA et son modele ») se presentait donc comme deja faite alors
que rien n'avait ete choisi. Le repli en dur ayant ete retire, il faut les semer pour de bon.

LES VALEURS : celles qui etaient ecrites dans le code, a l'identique. `ON CONFLICT DO NOTHING` :
une base qui a deja son choix garde le sien — on ne remet jamais un administrateur sur un
fournisseur qu'il a quitte.

Revision ID: a4d8f2c6e1b9
Revises: f1c9a3e7b5d2
Create Date: 2026-08-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4d8f2c6e1b9'
down_revision: Union[str, Sequence[str], None] = 'f1c9a3e7b5d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Meme forme que f1c9a3e7b5d2 : conftest.py lit cette constante pour monter la base de test.
REGLAGES = {
    "ai_provider": "groq",
    "ai_model": "llama-3.3-70b-versatile",
}


def upgrade() -> None:
    conn = op.get_bind()
    for cle, valeur in REGLAGES.items():
        conn.execute(
            sa.text("INSERT INTO settings (key, value) VALUES (:k, :v) "
                    "ON CONFLICT (key) DO NOTHING"),
            {"k": cle, "v": valeur},
        )


def downgrade() -> None:
    """Retire les deux lignes. Sans elles ET sans repli code, `get_ai_model()` leve : c'est la
    regle maison — une base incomplete se dit, elle ne se rattrape pas en douce."""
    conn = op.get_bind()
    for cle in REGLAGES:
        conn.execute(sa.text("DELETE FROM settings WHERE key = :k"), {"k": cle})
