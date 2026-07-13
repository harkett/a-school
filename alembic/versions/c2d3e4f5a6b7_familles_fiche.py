# -*- coding: utf-8 -*-
"""familles : fiche complete par famille (motif / conteneurs_ignorer / decoupe / consignes_ia / rejet)

Ajoute 5 colonnes a `familles` puis remplit les 6 fiches (donnee de reference) :
lignes 1->5 mises a jour, ligne 5 renommee REFERENTIEL_LIBRE -> REJET_NON_RECONNU (rejet=true,
etat interne jamais renvoye par l'IA), ligne 6 PROGRAMME_ENSEIGNEMENT ajoutee. Ajout des colonnes
non destructif (server_default). UPDATE/INSERT parametres (psycopg echappe : aucun quoting a la main).

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Les 6 fiches, verbatim. id figes ; rejet = etat interne (seule la ligne 5).
_FICHES = [
    {"id": 1, "nom": "UNITÉS_OFFICIELLES",
     "description": "Référentiels structurés en unités officielles (BTS, Bac Pro, etc.)",
     "motif": "Code officiel d'unité (U1, U2, U3…) ou intitulé d'unité",
     "conteneurs_ignorer": "Préface, objectifs généraux, annexes, notes hors unités",
     "decoupe": "Une unité = un bloc officiel (U1, U2…). Sous-parties internes restent dans l'unité.",
     "consignes_ia": "Document structuré par unités numérotées. Respecter les frontières officielles. Ne jamais découper sur les sous-titres internes. Conserver le verbatim.",
     "rejet": False},
    {"id": 2, "nom": "ACTIVITÉS_PRO",
     "description": "Référentiels organisés par activités professionnelles",
     "motif": "Titre d'activité (A1, A2…) ou intitulé métier/tâche",
     "conteneurs_ignorer": "Contexte métier, glossaire, annexes",
     "decoupe": "Une unité = une activité professionnelle. Sous-tâches restent dans l'activité.",
     "consignes_ia": "Document structuré par activités. Ne jamais découper sur les sous-tâches. Conserver le verbatim.",
     "rejet": False},
    {"id": 3, "nom": "RNCP_BLOCS",
     "description": "Référentiels découpés en blocs de compétences RNCP",
     "motif": "Bloc RNCP (B1, B2…) ou intitulé « Bloc de compétences »",
     "conteneurs_ignorer": "Présentation RNCP, cadre légal, annexes",
     "decoupe": "Une unité = un bloc RNCP. Les compétences internes restent dans le bloc.",
     "consignes_ia": "Document structuré par blocs RNCP. Ne jamais découper sur les compétences internes. Conserver le verbatim.",
     "rejet": False},
    {"id": 4, "nom": "GRILLES_TABLEAUX",
     "description": "Documents structurés en tableaux/grilles",
     "motif": "Début d'un tableau ou grille (colonnes/items)",
     "conteneurs_ignorer": "Titres de sections, textes hors tableau",
     "decoupe": "Une unité = un tableau. Chaque tableau est une unité complète.",
     "consignes_ia": "Document structuré en tableaux. Ne jamais découper à l'intérieur d'un tableau. Conserver la structure tabulaire.",
     "rejet": False},
    {"id": 5, "nom": "REJET_NON_RECONNU",
     "description": "Document dont la structure ne correspond à aucune famille connue",
     "motif": "Aucun motif valide",
     "conteneurs_ignorer": "Tout le document",
     "decoupe": "Aucune découpe : rejet.",
     "consignes_ia": "Document non reconnu. Ne pas découper. Signaler à l'admin que la structure est invalide.",
     "rejet": True},
    {"id": 6, "nom": "PROGRAMME_ENSEIGNEMENT",
     "description": "Programmes officiels d'enseignement (BO). Prose organisée par matière.",
     "motif": "Titre de matière (« Français — 5e », « Mathématiques — 5e »)",
     "conteneurs_ignorer": "En-tête (sources), règles de rattachement, notes de méthode",
     "decoupe": "Une unité = une matière. Sous-parties internes (Oral/Lecture, A/B/C) restent dans l'unité.",
     "consignes_ia": "Document de programme : prose, attendus, notions. Pas de codes, pas de blocs, pas de tableaux. Le titre de matière est la seule frontière. Ne jamais découper sur les sous-titres.",
     "rejet": False},
]


def upgrade() -> None:
    op.add_column("familles", sa.Column("motif", sa.Text(), nullable=False, server_default=""))
    op.add_column("familles", sa.Column("conteneurs_ignorer", sa.Text(), nullable=False, server_default=""))
    op.add_column("familles", sa.Column("decoupe", sa.Text(), nullable=False, server_default=""))
    op.add_column("familles", sa.Column("consignes_ia", sa.Text(), nullable=False, server_default=""))
    op.add_column("familles", sa.Column("rejet", sa.Boolean(), nullable=False, server_default="false"))

    conn = op.get_bind()
    up = sa.text(
        "UPDATE familles SET nom=:nom, description=:description, motif=:motif, "
        "conteneurs_ignorer=:conteneurs_ignorer, decoupe=:decoupe, consignes_ia=:consignes_ia, "
        "rejet=:rejet WHERE id=:id"
    )
    ins = sa.text(
        "INSERT INTO familles (id, nom, description, motif, conteneurs_ignorer, decoupe, consignes_ia, rejet) "
        "VALUES (:id, :nom, :description, :motif, :conteneurs_ignorer, :decoupe, :consignes_ia, :rejet) "
        "ON CONFLICT (id) DO NOTHING"
    )
    for f in _FICHES:
        if f["id"] <= 5:
            conn.execute(up, f)
        else:
            conn.execute(ins, f)
    conn.execute(sa.text(
        "SELECT setval('familles_id_seq', GREATEST((SELECT last_value FROM familles_id_seq), 6), true)"
    ))


def downgrade() -> None:
    op.drop_column("familles", "rejet")
    op.drop_column("familles", "consignes_ia")
    op.drop_column("familles", "decoupe")
    op.drop_column("familles", "conteneurs_ignorer")
    op.drop_column("familles", "motif")
