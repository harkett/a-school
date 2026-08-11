# -*- coding: utf-8 -*-
"""Criteres d'ambiguite EN BASE (catalogue), pour l'ecran « Detecter les ambiguites »

L'outil cherchait les 6 types d'ambiguite TOUS EN MEME TEMPS : le prof ne pouvait pas dire ce
qu'il voulait faire relire. Il les coche desormais, et l'IA ne cherche que ceux-la.

Les 6 libelles etaient ecrits a deux endroits — la liste numerotee du prompt et l'onglet
« Comment ca marche » (6 <li> en dur dans Ambiguites.jsx). Les cases a cocher, la liste blanche
du serveur et le recollage du `type` rendu par le modele en auraient fait cinq copies. Meme
tranchage que l'etape 9 lot A (seance_modes / seance_styles / langues_lv) : la table est la
source unique, le `code` est la cle metier stable, le `label` peut etre renomme sans rien
casser, `description` porte la phrase de l'ecran d'aide (elle appartient au critere).

`autre` est une ligne comme les autres. Seul son COMPORTEMENT est connu du serveur : c'est
elle qui ouvre le champ de texte libre. Son `description` reste vide — l'ecran d'aide n'a rien
a expliquer d'un critere que le prof ecrit lui-meme.

Pas d'ecran admin : `seance_modes` n'en a pas non plus, la migration fait foi. Pas de cle
etrangere : une analyse d'ambiguites n'est sauvegardee nulle part, il n'y a rien a rattacher.

downgrade : drop de la table (le catalogue n'est reference par aucune autre).

Revision ID: c7a3f1d95b28
Revises: d5b1f8c3e604
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7a3f1d95b28"
down_revision: Union[str, Sequence[str], None] = "d5b1f8c3e604"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (code, label, description, ordre) — les 6 libelles sont repris MOT POUR MOT du prompt et de
# l'onglet d'aide, pour que la bascule ne change pas une virgule de ce que le prof lit.
_CRITERES = [
    ("consigne_vague", "Consigne vague",
     "Verbe trop général (« analysez », « commentez », « étudiez ») sans critères précis.", 0),
    ("vocabulaire_non_defini", "Vocabulaire technique non défini",
     "Terme spécialisé supposé connu, sans garantie qu'il le soit.", 1),
    ("double_sens", "Double sens",
     "Formulation qui peut être interprétée de deux façons différentes.", 2),
    ("criteres_reussite_absents", "Critères de réussite absents",
     "L'élève ne sait pas ce qu'on attend : longueur, forme, nombre de points…", 3),
    ("reference_implicite", "Référence implicite",
     "« le texte », « l'auteur », « le document » sans préciser lequel.", 4),
    ("consigne_trop_longue", "Consigne trop longue",
     "Plusieurs tâches combinées sans séparation claire.", 5),
    ("autre", "Autre", "", 6),
]


def upgrade() -> None:
    op.create_table(
        "ambiguite_criteres",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("code", name="uq_ambiguite_criteres_code"),
    )

    conn = op.get_bind()
    ins = sa.text(
        "INSERT INTO ambiguite_criteres (code, label, description, ordre) "
        "VALUES (:code, :label, :description, :ordre) ON CONFLICT (code) DO NOTHING"
    )
    for code, label, description, ordre in _CRITERES:
        conn.execute(ins, {"code": code, "label": label, "description": description, "ordre": ordre})


def downgrade() -> None:
    op.drop_table("ambiguite_criteres")
