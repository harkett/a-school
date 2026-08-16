# -*- coding: utf-8 -*-
"""Une note au carnet : la fenêtre standard doit être propre une fois pour toutes

CONSTATÉ LE 16/08/2026, sur la fenêtre de transfert d'un référentiel : le texte collé aux bords,
et un grand vide blanc sous un contenu court. Le défaut n'est pas dans cet écran — il est dans la
coquille commune à toute l'application.

CE QUI EST DÉJÀ FAIT : la fenêtre du transfert pose sa propre marge et demande une hauteur
« auto ». C'est un pansement local, à retirer quand la coquille sera reprise.

downgrade : retire la note.

Revision ID: f6a2c8e4b1d7
Revises: e5c9d3a7b2f4
Create Date: 2026-08-16
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "f6a2c8e4b1d7"
down_revision: Union[str, Sequence[str], None] = "e5c9d3a7b2f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TITRE = "Fenêtre standard : marge et hauteur, une bonne fois pour tout le projet"

DETAIL = """LE DÉFAUT, dans `frontend/src/components/FenetrePro.jsx` — la coquille de TOUTES les fenêtres de l'application :

1. AUCUNE MARGE INTÉRIEURE. Le contenu est posé tel quel contre les bords. Chaque écran doit donc poser la sienne, chacun à sa façon — ou l'oublier, ce qui donne un texte collé au cadre.

2. LA HAUTEUR EST IMPOSÉE, pas déduite. Elle vaut « 72 % de l'écran » quel que soit le contenu : une fenêtre courte laisse un grand vide blanc en dessous. Il faut une hauteur qui s'ajuste au contenu, avec un plafond au-delà duquel l'ascenseur prend le relais. La poignée d'étirement reste.

CE QU'IL FAUT FAIRE : corriger la coquille, puis retirer les marges que les écrans posent aujourd'hui chacun de leur côté. Une seule règle, appliquée partout, plus rien à décider écran par écran.

POURQUOI ÇA N'A PAS ÉTÉ FAIT LE JOUR MÊME : quinze fenêtres l'utilisent, dont tous les guides du professeur (séquence, séance, activités, ambiguïtés, équité, consigne, démonstrations) et l'aide de l'administration. Les corriger d'un coup demande de les regarder toutes — c'est un travail court mais qui se vérifie à l'œil, pas par un test.

PANSEMENT EN PLACE, à retirer ensuite : la fenêtre de transfert d'un référentiel (AdminReferentiels.jsx) pose sa propre marge et demande une hauteur « auto ». Elle sert de modèle de ce que la coquille devra faire seule.

LA RÈGLE À TENIR : une fenêtre de cette application ne se dessine jamais sur mesure. On prend la coquille, elle est propre, et on n'y touche plus."""


def upgrade() -> None:
    op.execute(
        sa.text("INSERT INTO taches_a_faire (titre, detail) VALUES (:titre, :detail)")
        .bindparams(titre=TITRE, detail=DETAIL)
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM taches_a_faire WHERE titre = :titre").bindparams(titre=TITRE)
    )
