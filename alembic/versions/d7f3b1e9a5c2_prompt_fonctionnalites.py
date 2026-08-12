# -*- coding: utf-8 -*-
"""Les FONCTIONNALITES de l'ecran admin « Prompts » : une table, un rangement qui dit vrai

L'ecran rangeait ses 36 prompts en « Prof » et « Admin ». Deux etiquettes qui ne trient rien :
l'admin est le seul a les lire tous, et tous servent le professeur au bout du compte. Elles
separaient meme les jumeaux — l'analyse de consigne d'un cote, celle des ambiguites de l'autre,
parce qu'un jour l'une avait ete rangee par public et l'autre par fonctionnalite.

Un prompt se cherche par CE QU'IL FAIT a l'ecran du professeur. Le `label` d'une ligne est donc
le CHEMIN dans son menu (« Mes contenus → Seance ») : c'est ainsi qu'on retrouve un texte quand
on vient de voir le bouton qui le declenche.

La cle porte le lien : chaque prompt du registre declare la fonctionnalite qu'il sert. Une
fonctionnalite sans prompt ne s'affiche pas — l'ecran ne fabrique pas de ligne vide.

Revision ID: d7f3b1e9a5c2
Revises: b2c4e8f1a7d3
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7f3b1e9a5c2"
down_revision: Union[str, Sequence[str], None] = "b2c4e8f1a7d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (code, label, aide, ordre) — TEXTE GELE, recopie ici volontairement : une migration seme ce
# qu'elle semait le jour de son ecriture, jamais ce que le code dira plus tard.
FONCTIONNALITES = [
    ('creer_activite', 'Mes contenus → Activité', "Les textes de l'écran qui crée une activité : les deux tons, le corrigé, le contrôle qualité, la manière du professeur, et les deux boutons qui écrivent sa demande.", 10),
    ('seance', 'Mes contenus → Séance', "Les quatre modes de séance, les quatre styles de rédaction, et les cinq boutons « Propose-moi… » de l'écran.", 20),
    ('sequence', 'Mes contenus → Séquence', 'Le plan de séquence et les deux boutons « Propose-moi… » de son écran.', 30),
    ('analyse_consigne', 'Mes analyses → Consignes', 'Le texte qui relit la consigne du professeur et en juge la qualité didactique.', 40),
    ('analyse_ambiguites', 'Mes analyses → Ambiguïtés', "Le texte qui ANALYSE l'énoncé du prof, et celui qui ÉCRIT son énoncé d'exemple.", 50),
]


def upgrade() -> None:
    op.create_table(
        "prompt_fonctionnalites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("label", sa.String(150), nullable=False),
        sa.Column("aide", sa.Text(), nullable=False, server_default=""),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("code", name="uq_prompt_fonctionnalites_code"),
    )
    conn = op.get_bind()
    for code, label, aide, ordre in FONCTIONNALITES:
        conn.execute(sa.text(
            "INSERT INTO prompt_fonctionnalites (code, label, aide, ordre, actif) "
            "VALUES (:code, :label, :aide, :ordre, true) ON CONFLICT (code) DO NOTHING"
        ), {"code": code, "label": label, "aide": aide, "ordre": ordre})


def downgrade() -> None:
    op.drop_table("prompt_fonctionnalites")
