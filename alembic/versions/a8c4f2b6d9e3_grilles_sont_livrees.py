# -*- coding: utf-8 -*-
"""« Grilles d'évaluation » est livrée — le drapeau, et le tableau de bord qui dit vrai

CONVENTION DE LIVRAISON (16/08/2026) : c'est LA MIGRATION QUI LIVRE une fonctionnalité qui pose
`features_votables.livree = true` sur sa ligne. Le développement sait qu'elle existe,
l'administrateur ne le devine pas — et la carte quitte l'écran « Bientôt disponible » du
professeur le jour du déploiement, sans que personne ait à y penser.

`page` = la clé d'écran du menu du professeur (`Sidebar.jsx`), celle qu'ouvrira le bouton
« Découvrir » de la bande de nouveauté. Vide, la bande dirait « En savoir plus », qui ne promet
que du texte.

CE QUI SE DÉCLENCHE ENSUITE, TOUT SEUL : la carte « Grilles d'évaluation » quitte l'écran
« Bientôt disponible » (LES VOTES DÉJÀ EXPRIMÉS SONT CONSERVÉS — la ligne n'est pas supprimée,
et `feature_votes.feature_key` pointe dessus), et une ligne « Grilles d'évaluation est livrée :
l'annoncer aux professeurs ? » apparaît dans l'encart « À traiter » du tableau de bord admin.
L'annonce reste une DÉCISION HUMAINE : `nouveaute` n'est pas coché ici.

LA SECONDE LIGNE EST AILLEURS. `fonctionnalites` (le tableau de bord) portait « Grilles » à
`a_venir` avec la note « entrée de menu désactivée, aucun écran ». Les deux affirmations sont
maintenant fausses : l'entrée est vivante et deux écrans existent. `composant` cite le fichier qui
la rend — c'est ce qui rend la ligne VÉRIFIABLE, et `tests/test_tableau_de_bord_dit_vrai.py` exige
qu'il existe pour toute ligne qui n'est pas « à venir ».

downgrade : remet les deux lignes dans leur état d'avant, à l'identique.

Revision ID: a8c4f2b6d9e3
Revises: e6b2d9a4c7f1
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8c4f2b6d9e3"
down_revision: Union[str, Sequence[str], None] = "e6b2d9a4c7f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NOTE_AVANT = "entrée de menu désactivée, aucun écran"
COMPOSANT = "src/components/contenus/GrillesContenus.jsx"


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text(
        "UPDATE features_votables SET livree = true, page = 'eval-grilles' "
        "WHERE code = 'eval-grilles'"))

    conn.execute(sa.text(
        "UPDATE fonctionnalites SET etat = 'fait', composant = :composant, note = NULL "
        "WHERE domaine = 'prof' AND ecran = 'Mes évals' AND nom = 'Grilles'"
    ), {"composant": COMPOSANT})


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text(
        "UPDATE features_votables SET livree = false, page = NULL "
        "WHERE code = 'eval-grilles'"))

    conn.execute(sa.text(
        "UPDATE fonctionnalites SET etat = 'a_venir', composant = NULL, note = :note "
        "WHERE domaine = 'prof' AND ecran = 'Mes évals' AND nom = 'Grilles'"
    ), {"note": NOTE_AVANT})
