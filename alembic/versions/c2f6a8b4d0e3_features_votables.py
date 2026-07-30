# -*- coding: utf-8 -*-
"""features_votables : catalogue des fonctionnalites votables (donnee de reference, EN BASE)

Remplace les TROIS listes en dur qui avaient diverge : FEATURES (BientotDisponible.jsx,
6 cartes), VALID_KEYS + FEATURE_LABELS (votes.py, 5 codes differents). Consequence vecue :
voter « ambiguites-cognitives » -> 400 « Feature inconnue » pendant que l'ecran gardait le
vote affiche. Desormais l'ecran, le serveur et l'admin lisent CETTE table.

`code` unique = cle metier ; `actif=false` retire la carte de l'ecran sans perdre les votes ;
`icone` = nom d'un pictogramme du mapping front (le dessin SVG reste de l'affichage).
Une FK `feature_votes.feature_key -> features_votables.code` fait de la base l'autorite.

Graine = l'etat du jour : « ambiguites-cognitives » n'y entre PAS (l'outil Ambiguites est
livre, on ne vote plus pour lui) ; « app-mobile » entre a l'ecran (votable cote serveur mais
jamais affiche jusqu'ici). Contenu retouchable en base sans toucher au code.

Seed sans id explicite (serial) -> aucune desync de sequence. Idempotent :
ON CONFLICT (code) DO NOTHING. FK posee APRES le seed (les votes presents en base ne portent
que des codes issus de l'ancien VALID_KEYS, tous repris dans la graine).

downgrade : drop FK puis drop table.

Revision ID: c2f6a8b4d0e3
Revises: b9d2e4f6a8c1
Create Date: 2026-07-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2f6a8b4d0e3"
down_revision: Union[str, Sequence[str], None] = "b9d2e4f6a8c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (code, label, description, categorie, icone, ordre, actif)
_FEATURES = [
    (
        "analyser-consigne",
        "Analyser une consigne",
        "Collez n'importe quelle consigne — aSchool détecte les ambiguïtés, les étapes "
        "implicites, les mots à double sens et les risques d'erreur typiques. Résultat : "
        "une version clarifiée, précise et didactiquement solide.",
        "Outils pédagogiques", "loupe", 0, True,
    ),
    (
        "verifier-evaluation",
        "Vérifier une évaluation",
        "Soumettez une évaluation existante — aSchool détecte les questions qui mesurent "
        "autre chose que ce qu'elles prétendent évaluer, les biais de difficulté et les "
        "formulations anxiogènes. Une version corrigée est générée automatiquement.",
        "Outils pédagogiques", "coche", 1, True,
    ),
    (
        "coherence-curriculaire",
        "Cohérence inter-disciplines",
        "Vérifiez si vos progressions s'articulent avec celles des autres matières. aSchool "
        "aligne automatiquement notions et calendriers pédagogiques pour éviter les doublons "
        "et les contradictions entre disciplines.",
        "Outils pédagogiques", "reseau", 2, True,
    ),
    (
        "quiz-interactif",
        "Quiz interactif élèves",
        "Générez un quiz depuis une activité, partagez un lien à vos élèves, et suivez leurs "
        "réponses en direct sur votre écran. Sans inscription pour les élèves — un simple "
        "lien suffit.",
        "Autre", "horloge", 3, True,
    ),
    (
        "app-mobile",
        "Application mobile",
        "Emportez aSchool sur votre téléphone : préparez, relisez et retrouvez vos activités "
        "où que vous soyez, dans une application pensée pour l'écran mobile.",
        "Autre", "mobile", 4, True,
    ),
    (
        "escape-game",
        "Escape Game pédagogique",
        "Générez un scénario complet avec énigmes adaptées au niveau et épreuve finale de "
        "validation. Évaluez vos élèves de manière ludique et collaborative.",
        "Autre", "fusee", 5, True,
    ),
]


def upgrade() -> None:
    op.create_table(
        "features_votables",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("categorie", sa.String(length=32), nullable=False),
        sa.Column("icone", sa.String(length=32), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("code", name="uq_features_votables_code"),
    )
    conn = op.get_bind()
    ins = sa.text(
        "INSERT INTO features_votables (code, label, description, categorie, icone, ordre, actif) "
        "VALUES (:code, :label, :description, :categorie, :icone, :ordre, :actif) "
        "ON CONFLICT (code) DO NOTHING"
    )
    for code, label, description, categorie, icone, ordre, actif in _FEATURES:
        conn.execute(ins, {
            "code": code, "label": label, "description": description,
            "categorie": categorie, "icone": icone, "ordre": ordre, "actif": actif,
        })
    # FK APRES le seed : les votes deja en base ne portent que des codes de l'ancien
    # VALID_KEYS serveur (seule porte d'entree), tous presents dans la graine.
    op.create_foreign_key(
        "fk_feature_votes_feature_key_features_votables",
        "feature_votes", "features_votables",
        ["feature_key"], ["code"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_feature_votes_feature_key_features_votables", "feature_votes", type_="foreignkey")
    op.drop_table("features_votables")
