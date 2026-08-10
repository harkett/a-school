# -*- coding: utf-8 -*-
"""Suppression de `few_shot_milestones` : une table jamais alimentée.

CE QU'ELLE DEVAIT ÊTRE. Le jalon « aSchool reconnaît votre façon de travailler », posé une fois
par couple (prof, type d'activité) au franchissement du seuil few-shot.

CE QU'ELLE ÉTAIT. Vide, et écrite par personne : aucune ligne de code applicatif ne l'insérait
ni ne la lisait — seul un test l'alimentait à la main pour éprouver la cascade de suppression
d'un compte. Sa colonne `reached_at` était la seule de toute la base jamais citée dans le code.
Le mécanisme few-shot, lui, fonctionne sans elle (`backend/contenu/activites.py`,
`few_shot_du_prof`) : c'est le JALON qui n'a jamais été branché.

POURQUOI ON L'ENLÈVE PLUTÔT QUE DE L'ATTENDRE. Elle était entretenue à chaque chantier —
cascade de suppression d'un prof, carte de la base, sauvegardes, tests — pour une fonctionnalité
qui n'existe pas. Une table jamais alimentée n'est pas une fonctionnalité en attente : c'est une
affirmation fausse sur l'état du produit. Si le jalon revient, il se recrée en cinq lignes.

downgrade : recrée la table à l'identique (colonnes, index unique, clés étrangères). Les lignes,
elles, ne reviennent pas — il n'y en avait aucune.

Revision ID: b3f7a1d5c8e2
Revises: b7e1f4a9c3d2
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa


revision = "b3f7a1d5c8e2"
down_revision = "b7e1f4a9c3d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_few_shot_milestones_unique", table_name="few_shot_milestones")
    op.drop_table("few_shot_milestones")


def downgrade() -> None:
    op.create_table(
        "few_shot_milestones",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activite_type_id", sa.Integer(),
                  sa.ForeignKey("types_activite.id"), nullable=False),
        sa.Column("reached_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_few_shot_milestones_user_id", "few_shot_milestones", ["user_id"])
    op.create_index("ix_few_shot_milestones_unique", "few_shot_milestones",
                    ["user_id", "activite_type_id"], unique=True)
