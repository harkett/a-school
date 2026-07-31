# -*- coding: utf-8 -*-
"""suppression d un compte prof : la BASE garantit le nettoyage (ON DELETE)

Bug bloquant releve au check-up admin du 31/07 et VERIFIE sur la base vivante
(pg_constraint.confdeltype = 'a' = aucune action) : DELETE /admin/user purgeait
8 tables a la main, mais 5 liens vers le compte n avaient ni purge ni cascade.
Supprimer un prof qui a vote une fonctionnalite, ou utilise Consigne/Ambiguites,
levait une violation de cle etrangere -> 500, compte NON supprime.

Reparation par la BASE plutot que par une liste a tenir a jour dans le code : une
purge oubliee dans une fonction Python est invisible tant que personne ne teste ce
cas precis, alors qu une contrainte ON DELETE ne s oublie pas (meme choix que
cahiers_prof, deja en CASCADE).

CASCADE (ces lignes n ont aucune vie sans leur prof) :
  feature_votes, tool_usage_logs, few_shot_milestones, user_enseignements.

SET NULL (l incident TECHNIQUE survit au compte) :
  incidents.feedback_id — le modele le dit deja : colonne nullable, « l incident
  existe quand meme ». Sans ca, la purge des feedbacks du prof echouait des qu un
  incident etait rattache a l un d eux. C est le 5e lien, non vu par le check-up.

Rien n est supprime ici : on ne fait que redefinir le COMPORTEMENT des liens.

Revision ID: e4b8c2d6a1f7
Revises: d3a7c1e5f9b2
Create Date: 2026-07-31
"""
from alembic import op


revision = "e4b8c2d6a1f7"
down_revision = "d3a7c1e5f9b2"
branch_labels = None
depends_on = None


# (table, colonne, contrainte, table_cible, comportement)
LIENS = [
    ("feature_votes",       "user_id",     "feature_votes_user_id_fkey",       "users",     "CASCADE"),
    ("tool_usage_logs",     "user_id",     "tool_usage_logs_user_id_fkey",     "users",     "CASCADE"),
    ("few_shot_milestones", "user_id",     "few_shot_milestones_user_id_fkey", "users",     "CASCADE"),
    ("user_enseignements",  "user_id",     "user_enseignements_user_id_fkey",  "users",     "CASCADE"),
    ("incidents",           "feedback_id", "incidents_feedback_id_fkey",       "feedbacks", "SET NULL"),
]


def upgrade():
    for table, col, nom, cible, comportement in LIENS:
        op.drop_constraint(nom, table, type_="foreignkey")
        op.create_foreign_key(nom, table, cible, [col], ["id"], ondelete=comportement)


def downgrade():
    for table, col, nom, cible, _ in LIENS:
        op.drop_constraint(nom, table, type_="foreignkey")
        op.create_foreign_key(nom, table, cible, [col], ["id"])
