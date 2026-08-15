# -*- coding: utf-8 -*-
"""Crée `taches_planifiees` — les travaux automatiques passent du code à l'écran d'administration

CE QUI CHANGE. L'application fait deux choses toute seule : elle surveille le serveur toutes les
cinq minutes, et elle relève les tarifs des fournisseurs d'IA une fois par jour. L'heure, la
cadence et l'existence de ces travaux étaient écrites dans `main.py` — passer un contrôle de 6 h à
22 h demandait un développeur, une relecture et un redéploiement pour deux chiffres qui ne
regardent que l'exploitation.

CE QUI RESTE DANS LE CODE : la fonction exécutée, retrouvée par `code` dans le registre `TACHES`
de `backend/systeme/planificateur.py`. On ne met pas du Python en base.

LES VALEURS SEMÉES SONT CELLES QUI TOURNAIENT DÉJÀ — surveillance toutes les 5 minutes, veille à
6 h 05 UTC. Une migration qui profite du déménagement pour changer un réglage produirait un
comportement que personne n'a demandé, et que personne ne saurait expliquer trois mois plus tard.

downgrade : supprime la table. Les tâches redeviennent ce qu'elles étaient — du code.

Revision ID: f7a3d9e1c5b8
Revises: f4a1c7e9b3d5
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f7a3d9e1c5b8"
down_revision: Union[str, Sequence[str], None] = "f4a1c7e9b3d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "taches_planifiees",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("type_planif", sa.String(12), nullable=False, server_default="quotidien"),
        sa.Column("heure", sa.Integer(), nullable=True),
        sa.Column("minute", sa.Integer(), nullable=True),
        sa.Column("intervalle_minutes", sa.Integer(), nullable=True),
        sa.Column("destinataire", sa.String(200), nullable=True),
        sa.Column("dernier_passage", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dernier_resultat", sa.Text(), nullable=True),
        sa.Column("dernier_ok", sa.Boolean(), nullable=True),
        sa.Column("derniere_duree_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("code", name="uq_taches_planifiees_code"),
    )
    op.execute(
        "INSERT INTO taches_planifiees (code, actif, type_planif, heure, minute, intervalle_minutes) "
        "VALUES ('surveillance', true, 'intervalle', NULL, NULL, 5), "
        "       ('veille_tarifs', true, 'quotidien', 6, 5, NULL)"
    )


def downgrade() -> None:
    op.drop_table("taches_planifiees")
