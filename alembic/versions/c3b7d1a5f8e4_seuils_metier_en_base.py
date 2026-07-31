# -*- coding: utf-8 -*-
"""Seuils metier EN BASE : pieces jointes, duree d'une seance, cahier des charges

Etape 9 lot B du programme PROF. Cinq nombres decidaient du comportement de l'application
depuis le code, dont trois recopies cote ecran :

- taille max d'une piece jointe (5 Mo) : ecrite dans feedback.py, dans MesFeedbacks.jsx, dans
  le message d'erreur du meme fichier, dans son libelle de champ, et dans le texte de l'Aide ;
- nombre max de pieces jointes (5) : ecrit UNIQUEMENT dans l'ecran — le serveur ne l'a jamais
  fait respecter ;
- duree d'une seance (5 a 300 minutes) : ecrite dans mes_contenus.py et a TROIS endroits de
  SeanceEcran.jsx (le calcul « pret a generer », le controle avant envoi, les bornes du champ) ;
- taille max du cahier des charges depose par le prof (20 Mo), en dur dans profil.py.

Semes ici, lus par `_reglage_entier` (admin.py) : ligne absente = erreur explicite, jamais un
repli silencieux. Meme geste que few_shot_seuil / few_shot_extrait_max.

Ces cles ne passent PAS par SETTING_DEFAULTS : ce dictionnaire est partage avec le chantier
e-mail, et un reglage seme par migration n'a pas besoin d'un defaut de code — c'est meme
exactement ce que cette etape retire.

Idempotent : ON CONFLICT (key) DO NOTHING.

Revision ID: c3b7d1a5f8e4
Revises: a9c4e2f7b6d1
Create Date: 2026-07-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3b7d1a5f8e4"
down_revision: Union[str, Sequence[str], None] = "a9c4e2f7b6d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Valeurs IDENTIQUES a celles qui etaient en dur : cette migration deplace, elle ne change rien
# de ce que le prof constate aujourd'hui.
_REGLAGES = [
    ("feedback_piece_jointe_max_mo", "5"),
    ("feedback_pieces_jointes_max", "5"),
    ("seance_duree_min", "5"),
    ("seance_duree_max", "300"),
    ("cahier_max_mo", "20"),
]


def upgrade() -> None:
    conn = op.get_bind()
    ins = sa.text("INSERT INTO settings (key, value) VALUES (:key, :value) "
                  "ON CONFLICT (key) DO NOTHING")
    for cle, valeur in _REGLAGES:
        conn.execute(ins, {"key": cle, "value": valeur})


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM settings WHERE key = ANY(:cles)"),
                 {"cles": [cle for cle, _ in _REGLAGES]})
