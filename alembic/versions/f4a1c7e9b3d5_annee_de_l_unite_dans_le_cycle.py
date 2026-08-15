# -*- coding: utf-8 -*-
"""L'année de l'unité dans son cycle — et NULL quand elle vaut pour tout le cycle

LE DÉFAUT. Un programme de cycle est UN document pour TROIS années. Le cycle 4 (référentiel 21,
BOEN n°31) contient les entrées de français et les thèmes d'histoire-géographie des trois
années : un prof de 4e pouvait recevoir une activité bâtie sur un contenu de 5e ou de 3e. Le cas
se reproduira sur les cycles du lycée et sur la crèche.

CE QUE PORTE LA COLONNE. `annee` = l'année à laquelle l'unité appartient ('5e', '4e', '3e' ici),
et NULL quand le document ne la rattache à aucune — Volet 1, Volet 2, compétences travaillées,
croisements, et tous les « repères de progressivité », qui décrivent une progression sur les
trois ans et valent donc pour les trois. NULL n'est PAS « on ne sait pas » : c'est « commun ».
C'est ce qui permet au filtre RAG de lire `annee IS NULL OR annee = <année du prof>` sans jamais
amputer un prof de la moitié de son référentiel — même esprit que `option_ab`, où l'unité sans
option appartient à tout le monde.

D'OÙ VIENT LE REMPLISSAGE. De `option_ab`, déjà en base, écrit par la découpe IA. Les 33 unités
datées du référentiel 21 y portent leur année en toutes lettres ('Cinquième', 'Histoire, 5e',
'Géographie, 4e'…). On la NORMALISE ici, une fois, en SQL — zéro appel IA, et surtout aucune
re-découpe : le document a 158 unités relues et validées, et la découpe n'est pas reproductible
à l'identique d'une fois sur l'autre. Refaire sortir l'année du modèle coûterait ces 158 unités.
Le prompt de découpe apprendra à la rendre POUR LA SUITE, pas pour refaire ce qui est fait.

LA DÉRIVATION NE LIT QUE `option_ab`, jamais le texte. Le texte piège : « quatrième
proportionnelle » (mathématiques) et « à partir des acquis de la classe de 5e, on aborde en 4e »
(géographie, thème de 4e) donneraient deux marquages faux. `option_ab` ne contient qu'un
libellé de section, il ne piège pas. Vérifié sur toute la base au 15/08/2026 : aucun autre
référentiel n'a d'option qui cite une année (BTS CIEL n'a que 'A'/'B', les autres sont vides) —
la règle est générique sans rien marquer par erreur ailleurs.

downgrade : retire la colonne. Aucune donnée d'origine n'est perdue, `option_ab` la porte encore.

Revision ID: f4a1c7e9b3d5
Revises: a5f2e9c4b7d1
Create Date: 2026-08-15
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "f4a1c7e9b3d5"
down_revision: Union[str, Sequence[str], None] = "a5f2e9c4b7d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Les deux écritures que la découpe produit : le mot ('Cinquième') et le rang ('Histoire, 5e').
# Le point de 'cinqui.me' absorbe le 'è' quel que soit l'encodage rendu par l'extraction PDF.
ANNEES = (("5e", r"cinqui.me|\m5 ?e"),
          ("4e", r"quatri.me|\m4 ?e"),
          ("3e", r"troisi.me|\m3 ?e"))


def upgrade() -> None:
    op.add_column("referentiel_chunks", sa.Column("annee", sa.Text(), nullable=True))
    # WHERE annee IS NULL : la migration se rejoue sans écraser un marquage plus fin posé après.
    branches = " ".join(f"WHEN option_ab ~* '({motif})' THEN '{an}'" for an, motif in ANNEES)
    op.execute(f"UPDATE referentiel_chunks SET annee = CASE {branches} END WHERE annee IS NULL")


def downgrade() -> None:
    op.drop_column("referentiel_chunks", "annee")
