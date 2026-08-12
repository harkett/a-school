# -*- coding: utf-8 -*-
"""L'appel « Exemple de la consigne » entre dans les longueurs reglables

Le bouton « Propose-moi un exemple » de l'ecran « Analyser une consigne » appelle le modele
(`get_max_tokens(db, "consigne_exemple_genere")`). Sans sa ligne ici, l'admin n'aurait aucun
champ pour le regler et la valeur par defaut s'appliquerait en silence — exactement le trou que
`tests/test_outils_llm_en_base.py` interdit.

La ligne du PROMPT, elle, a ete posee par c5e1a9d7b3f4 : le texte est arrive avant l'appel qui
s'en sert, et une ligne `outils_llm` posee ce jour-la aurait ete un reglage orphelin.

L'appel rend UNE consigne de 40 mots, ou un court refus motive : une valeur basse suffit.

ELLE REFERME AUSSI LA BRANCHE. Deux migrations ont ete posees le meme jour sur le meme parent
(`d7f3b1e9a5c2`) par deux chantiers paralleles : `c5e1a9d7b3f4` (le prompt d'exemple de consigne)
et `a4e7c2f9b135` (l'etat « en cours » de la fonctionnalite Ambiguites). Deux tetes, et
`alembic upgrade head` refuse de tourner. Celle-ci les rejoint — un merge, au sens d'alembic —
sans toucher a aucun des deux fichiers : ils restent ceux que leur auteur a ecrits.

downgrade : retire la ligne.

Revision ID: d1f5b8c3e7a2
Revises: a4e7c2f9b135, c5e1a9d7b3f4
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1f5b8c3e7a2"
down_revision: Union[str, Sequence[str], None] = ("a4e7c2f9b135", "c5e1a9d7b3f4")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OUTILS = [
    ("consigne_exemple_genere", "Exemple de consigne a la demande (consignes)", 252,
     "Ecrit la consigne d'exemple que le professeur demande par « Propose-moi un exemple », pour "
     "son couple et ancree sur son referentiel. Une consigne de 40 mots : une valeur basse suffit."),
]


def upgrade() -> None:
    conn = op.get_bind()
    for outil, libelle, ordre, aide in OUTILS:
        conn.execute(sa.text(
            "INSERT INTO outils_llm (outil, libelle, aide, ordre) "
            "VALUES (:outil, :libelle, :aide, :ordre) ON CONFLICT (outil) DO NOTHING"
        ), {"outil": outil, "libelle": libelle, "aide": aide, "ordre": ordre})


def downgrade() -> None:
    conn = op.get_bind()
    for outil, _libelle, _ordre, _aide in OUTILS:
        conn.execute(sa.text("DELETE FROM outils_llm WHERE outil = :o"), {"o": outil})
