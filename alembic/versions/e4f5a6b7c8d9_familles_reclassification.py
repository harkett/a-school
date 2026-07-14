# -*- coding: utf-8 -*-
"""familles : reclassification (6 types de document) + retrait des 4 colonnes de decoupe

Une famille = ce que le document EST (sa nature), pas ce qu'il contient. On reecrit les 6
lignes et on SUPPRIME motif/conteneurs_ignorer/decoupe/consignes_ia (elles figeaient un cas
particulier). familles redevient de la classification pure : id, nom, description, rejet.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "d3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 6 familles, ids figes 1..6. REJET porte rejet=true.
_FAMILLES = [
    {"id": 1, "nom": "PROGRAMME_ENSEIGNEMENT",
     "description": "Programme officiel du BO : prose organisee par matiere.", "rejet": False},
    {"id": 2, "nom": "REFERENTIEL_ACTIVITES",
     "description": "Le metier : activites, taches, conditions d'exercice (RAP).", "rejet": False},
    {"id": 3, "nom": "REFERENTIEL_CERTIFICATION",
     "description": "L'evaluation : competences, savoirs, unites, epreuves.", "rejet": False},
    {"id": 4, "nom": "FICHE_RNCP",
     "description": "Fiche du repertoire national : blocs de competences.", "rejet": False},
    {"id": 5, "nom": "CATALOGUE_ACTIVITES",
     "description": "Recueil d'activites concretes a mener, sans competences ni epreuves.", "rejet": False},
    {"id": 6, "nom": "REJET",
     "description": "Aucune structure reconnue : le document n'est pas ingere.", "rejet": True},
]


def upgrade() -> None:
    conn = op.get_bind()
    # Phase 1 : noms temporaires -> evite toute collision transitoire avec l'unique sur `nom`
    # (ex. l'ancien id6 s'appelle deja PROGRAMME_ENSEIGNEMENT).
    conn.execute(sa.text("UPDATE familles SET nom = 'TMP_' || id WHERE id BETWEEN 1 AND 6"))
    # Phase 2 : valeurs definitives.
    up = sa.text("UPDATE familles SET nom=:nom, description=:description, rejet=:rejet WHERE id=:id")
    for f in _FAMILLES:
        conn.execute(up, f)
    conn.execute(sa.text(
        "SELECT setval('familles_id_seq', GREATEST((SELECT last_value FROM familles_id_seq), 6), true)"))
    # Retrait des 4 colonnes de decoupe.
    op.drop_column("familles", "consignes_ia")
    op.drop_column("familles", "decoupe")
    op.drop_column("familles", "conteneurs_ignorer")
    op.drop_column("familles", "motif")


def downgrade() -> None:
    op.add_column("familles", sa.Column("motif", sa.Text(), nullable=False, server_default=""))
    op.add_column("familles", sa.Column("conteneurs_ignorer", sa.Text(), nullable=False, server_default=""))
    op.add_column("familles", sa.Column("decoupe", sa.Text(), nullable=False, server_default=""))
    op.add_column("familles", sa.Column("consignes_ia", sa.Text(), nullable=False, server_default=""))
    # (les anciens noms de familles ne sont pas restaures : downgrade rare, non necessaire)
