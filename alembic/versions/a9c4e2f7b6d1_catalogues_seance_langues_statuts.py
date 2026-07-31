# -*- coding: utf-8 -*-
"""Catalogues EN BASE : modes et styles de seance, langues vivantes, description des statuts

Etape 9 lot A du programme PROF — « la base est la source unique ». Quatre listes de
reference vivaient en dur, recopiees a plusieurs endroits :

- les 4 MODES de seance : MODES_SEANCE (mes_contenus.py), MODES (SeanceEcran.jsx),
  MODE_LABELS (SeancesContenus.jsx) — trois copies qui pouvaient diverger ;
- les 4 STYLES de production : STYLES_SEANCE (mes_contenus.py), STYLES (SeanceEcran.jsx) ;
- les 8 LANGUES VIVANTES : LANGUES_LV (MonProfil.jsx), nulle part cote serveur ;
- la description des 4 STATUTS de feedback : recopiee dans Aide.jsx alors que la table
  `feedback_statuts` existe deja — il n'y manquait que la phrase d'explication.

`code` = cle metier stable ; c'est LUI qui nomme le prompt (seance_<code> pour un mode,
seance_style_<code> pour un style), convention deja en place. Le `label` peut donc etre
renomme sans rien casser. Pas de cle etrangere posee ici sur seances.mode / seances.style :
ce serait un changement de comportement, a decider sur les valeurs reellement presentes en
production. Le serveur continue de refuser un mode inconnu — en lisant la table.

MATIERES.DEMANDE_LANGUE — le vrai defaut repare ici. L'injection de {langue} dans le prompt
reconnaissait la matiere a son LIBELLE exact (« Langues Vivantes (LV) »). Constat en base de
dev : la matiere s'appelle « Langue vivante » — le test etait donc DEJA faux, en silence.
La reconnaissance passe sur un indicateur porte par la ligne matiere : renommer la matiere ne
casse plus rien. Le rattrapage ci-dessous est un ONE-SHOT au mieux (les libelles connus) ;
l'admin corrige ensuite a la main depuis l'ecran Programmes & contenu.

Seed sans id explicite (serial) + ON CONFLICT (code) DO NOTHING — moule `feedback_statuts`.

downgrade : drop des trois tables et des deux colonnes.

Revision ID: a9c4e2f7b6d1
Revises: f4d8b1e7c3a9
Create Date: 2026-07-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9c4e2f7b6d1"
down_revision: Union[str, Sequence[str], None] = "f4d8b1e7c3a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (code, label, description, ordre) — descriptions reprises MOT POUR MOT de l'ecran, pour
# que la bascule ne change pas une virgule de ce que le prof lit aujourd'hui.
_MODES = [
    ("standard", "Séance standard", "Nouvelle séance sur le thème", 0),
    ("remediation", "Remédiation", "La classe n'a pas compris, on recommence autrement", 1),
    ("approfondissement", "Approfondissement", "Aller plus loin sur un thème déjà acquis", 2),
    ("autonomie", "Autonomie guidée", "Les élèves travaillent seuls, la séance les guide", 3),
]

_STYLES = [
    ("classique", "Classique",
     "Une fiche de préparation traditionnelle : présentation sobre, intitulés neutres — comme dans un classeur de prép.", 0),
    ("ludique", "Ludique",
     "La séance passe par le jeu : défis, énigmes, jeux de rôle… chaque phase a sa mécanique ludique, sans perdre l'objectif d'apprentissage.", 1),
    ("structure", "Structuré",
     "Un découpage très net : phases minutées, objectifs en listes à puces, transitions explicites, matériel rappelé phase par phase.", 2),
    ("concis", "Très concis",
     "Le format télégraphique : phrases très courtes, rien de superflu — la séance tient sur une page.", 3),
]

# `label` = ce qui est ECRIT dans users.langue_lv aujourd'hui (colonne texte) : le seed le
# reprend tel quel, aucune donnee existante n'est a reecrire.
_LANGUES = [
    ("anglais", "Anglais", 0),
    ("espagnol", "Espagnol", 1),
    ("allemand", "Allemand", 2),
    ("italien", "Italien", 3),
    ("portugais", "Portugais", 4),
    ("arabe", "Arabe", 5),
    ("chinois", "Chinois", 6),
    ("autre", "Autre", 7),
]

_DESCRIPTIONS_STATUT = [
    ("nouveau", "Reçu, pas encore traité."),
    ("en_cours", "Pris en charge par l'équipe."),
    ("traite", "Résolu ou intégré."),
    ("archive", "Clôturé."),
]


def _table_catalogue(nom: str) -> None:
    op.create_table(
        nom,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("code", name=f"uq_{nom}_code"),
    )


def upgrade() -> None:
    conn = op.get_bind()

    for nom in ("seance_modes", "seance_styles"):
        _table_catalogue(nom)
    op.create_table(
        "langues_lv",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("code", name="uq_langues_lv_code"),
    )

    for nom, lignes in (("seance_modes", _MODES), ("seance_styles", _STYLES)):
        ins = sa.text(
            f"INSERT INTO {nom} (code, label, description, ordre) "
            "VALUES (:code, :label, :description, :ordre) ON CONFLICT (code) DO NOTHING"
        )
        for code, label, description, ordre in lignes:
            conn.execute(ins, {"code": code, "label": label, "description": description, "ordre": ordre})

    ins_langue = sa.text(
        "INSERT INTO langues_lv (code, label, ordre) VALUES (:code, :label, :ordre) "
        "ON CONFLICT (code) DO NOTHING"
    )
    for code, label, ordre in _LANGUES:
        conn.execute(ins_langue, {"code": code, "label": label, "ordre": ordre})

    # Statuts de feedback : la table existe, il lui manquait la phrase d'explication que
    # l'ecran d'aide recopiait.
    op.add_column("feedback_statuts",
                  sa.Column("description", sa.Text(), nullable=False, server_default=""))
    maj = sa.text("UPDATE feedback_statuts SET description = :d WHERE code = :c")
    for code, description in _DESCRIPTIONS_STATUT:
        conn.execute(maj, {"c": code, "d": description})

    # L'indicateur qui remplace la comparaison de libelle. Rattrapage au mieux : les
    # intitules qui designent la matiere « langue vivante » quelle que soit la graphie.
    op.add_column("matieres",
                  sa.Column("demande_langue", sa.Boolean(), nullable=False, server_default=sa.false()))
    conn.execute(sa.text(
        "UPDATE matieres SET demande_langue = true "
        "WHERE nom ILIKE '%langue%vivante%' OR nom ILIKE '%(lv)%'"
    ))


def downgrade() -> None:
    op.drop_column("matieres", "demande_langue")
    op.drop_column("feedback_statuts", "description")
    op.drop_table("langues_lv")
    op.drop_table("seance_styles")
    op.drop_table("seance_modes")
