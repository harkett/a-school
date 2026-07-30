# -*- coding: utf-8 -*-
"""drop de l ancien monde : activites_sauvegardees + sequences_sauvegardees

Aboutissement du demantelement du 30/07 (decision utilisateur : « le monde ancien doit
disparaitre completement »). Chronologie tenue avant ce drop : ecrans rebranches sur les
tables neuves (bandeau Mes contenus, Accueil, Mes stats, Analytique admin), ecrans/routes/
endpoints de l ancien monde supprimes (MesActivites, MesSequences, SequenceForm, MonReseau,
mes-outils, creer-activite legacy, optimiseur, routers mes_activites/sequence/optimiseur/
bibliotheque), modeles retires de models_db. Plus AUCUNE ligne de code ne cite ces tables.

Ordre FK : aucune table ne reference ces deux-la (FK sortantes uniquement, vers users et
types_activite) -> drop direct.

downgrade : re-creation du SCHEMA seul (tables vides) — les donnees de l ancien monde
sont perdues par construction, le metier a ete supprime, il n y a plus rien a restaurer.

Revision ID: d3a7c1e5f9b2
Revises: c2f6a8b4d0e3
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa


revision = "d3a7c1e5f9b2"
down_revision = "c2f6a8b4d0e3"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("activites_sauvegardees")
    op.drop_table("sequences_sauvegardees")


def downgrade():
    op.create_table(
        "sequences_sauvegardees",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("matiere", sa.String(64), nullable=False),
        sa.Column("niveau", sa.String(32), nullable=False),
        sa.Column("theme", sa.String(300), nullable=False),
        sa.Column("duree", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("description_classe", sa.Text(), nullable=False),
        sa.Column("resultat", sa.Text(), nullable=False),
        sa.Column("partagee", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("anonyme", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "activites_sauvegardees",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("activite_type_id", sa.Integer(), sa.ForeignKey("types_activite.id"), nullable=False, index=True),
        sa.Column("activite_label", sa.String(128), nullable=False),
        sa.Column("niveau", sa.String(32), nullable=False),
        sa.Column("sous_type", sa.String(64), nullable=True),
        sa.Column("nb", sa.Integer(), nullable=True),
        sa.Column("avec_correction", sa.Boolean(), nullable=False),
        sa.Column("matiere", sa.String(64), nullable=True),
        sa.Column("objet", sa.String(150), nullable=True),
        sa.Column("partagee", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("anonyme", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("texte_source", sa.Text(), nullable=False),
        sa.Column("resultat", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
