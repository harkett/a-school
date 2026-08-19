# -*- coding: utf-8 -*-
"""L'ecran « Bientot disponible » ne promet plus ce qui est livre

Releve du 16/08/2026 sur l'interface prof. Trois cartes mentaient, et le menu annoncait
quatre chantiers d'evaluation dont un seul etait votable :

1. « analyser-consigne » : l'ecran Consignes EST livre (menu Mes analyses > Consignes).
   On faisait voter les profs pour une fonctionnalite qu'ils utilisent deja -> actif=false
   (la carte quitte l'ecran, les votes restent).

2. « verifier-evaluation » : sa description etait mot pour mot ce que fait l'ecran Equite,
   livre lui aussi. Seule la version CORRIGEE automatiquement n'existe pas : la carte
   n'annonce plus que cela, et passe dans la categorie « Evaluation ».

3. « app-mobile » : l'application s'installe deja sur iPhone et Android (PWA, trois fiches
   d'aide). Ce qui manque n'est pas l'installation mais l'ADAPTATION : sur telephone, c'est
   la version web qui s'affiche telle quelle. La carte le dit desormais.

4. Le menu « Mes evals » annonce Sujets, Grilles, Quiz et CCF ; seul Quiz etait votable.
   Les trois autres entrent au catalogue, et Quiz les rejoint dans « Evaluation » : les deux
   ecrans qui parlent de l'avenir disent enfin la meme chose.

Revision ID: f4b1c8d3a7e9
Revises: a4e7c2f9b135
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4b1c8d3a7e9"
down_revision: Union[str, Sequence[str], None] = "a4e7c2f9b135"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_APP_MOBILE_NEUF = (
    "aSchool s'installe déjà sur votre téléphone, mais il y affiche la version conçue pour "
    "l'ordinateur. Cette option adapte chaque écran au format mobile : lecture, préparation "
    "et retouche d'une activité à une main, sans zoomer."
)
_APP_MOBILE_ANCIEN = (
    "Emportez aSchool sur votre téléphone : préparez, relisez et retrouvez vos activités "
    "où que vous soyez, dans une application pensée pour l'écran mobile."
)

_VERIF_NEUF = (
    "L'analyse d'équité vous dit ce qui pénalise certains élèves ; cette option va plus loin "
    "et réécrit l'évaluation pour vous, question par question, en gardant ce qu'elle mesure."
)
_VERIF_ANCIEN = (
    "Soumettez une évaluation existante — aSchool détecte les questions qui mesurent "
    "autre chose que ce qu'elles prétendent évaluer, les biais de difficulté et les "
    "formulations anxiogènes. Une version corrigée est générée automatiquement."
)

# (code, label, description, categorie, icone, ordre)
_NOUVELLES = [
    (
        "eval-sujets",
        "Sujets d'évaluation",
        "Créez et conservez vos sujets, calés sur votre référentiel et votre niveau, "
        "réutilisables d'une classe à l'autre.",
        "Évaluation", "document", 6,
    ),
    (
        "eval-grilles",
        "Grilles d'évaluation",
        "Construisez vos grilles critériées, réutilisez-les sur plusieurs copies et gardez "
        "la même exigence d'un élève à l'autre.",
        "Évaluation", "grille", 7,
    ),
    (
        "eval-ccf",
        "CCF",
        "Le contrôle en cours de formation : sa situation d'évaluation, sa grille et son "
        "suivi, au format attendu par l'examen.",
        "Évaluation", "diplome", 8,
    ),
]


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text(
        "UPDATE features_votables SET actif = false WHERE code = 'analyser-consigne'"))

    conn.execute(sa.text(
        "UPDATE features_votables SET label = :label, description = :desc, categorie = 'Évaluation' "
        "WHERE code = 'verifier-evaluation'"),
        {"label": "Évaluation corrigée automatiquement", "desc": _VERIF_NEUF})

    conn.execute(sa.text(
        "UPDATE features_votables SET label = :label, description = :desc "
        "WHERE code = 'app-mobile'"),
        {"label": "aSchool adapté au téléphone", "desc": _APP_MOBILE_NEUF})

    conn.execute(sa.text(
        "UPDATE features_votables SET categorie = 'Évaluation' WHERE code = 'quiz-interactif'"))

    insert = sa.text(
        "INSERT INTO features_votables (code, label, description, categorie, icone, ordre, actif) "
        "VALUES (:code, :label, :description, :categorie, :icone, :ordre, true) "
        "ON CONFLICT (code) DO NOTHING"
    )
    for code, label, description, categorie, icone, ordre in _NOUVELLES:
        conn.execute(insert, {
            "code": code, "label": label, "description": description,
            "categorie": categorie, "icone": icone, "ordre": ordre,
        })


def downgrade() -> None:
    conn = op.get_bind()

    for code, *_ in _NOUVELLES:
        conn.execute(sa.text("DELETE FROM feature_votes WHERE feature_key = :code"), {"code": code})
        conn.execute(sa.text("DELETE FROM features_votables WHERE code = :code"), {"code": code})

    conn.execute(sa.text(
        "UPDATE features_votables SET categorie = 'Autre' WHERE code = 'quiz-interactif'"))

    conn.execute(sa.text(
        "UPDATE features_votables SET label = :label, description = :desc "
        "WHERE code = 'app-mobile'"),
        {"label": "Application mobile", "desc": _APP_MOBILE_ANCIEN})

    conn.execute(sa.text(
        "UPDATE features_votables SET label = :label, description = :desc, "
        "categorie = 'Outils pédagogiques' WHERE code = 'verifier-evaluation'"),
        {"label": "Vérifier une évaluation", "desc": _VERIF_ANCIEN})

    conn.execute(sa.text(
        "UPDATE features_votables SET actif = true WHERE code = 'analyser-consigne'"))
