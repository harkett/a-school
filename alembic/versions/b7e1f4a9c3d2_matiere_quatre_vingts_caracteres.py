# -*- coding: utf-8 -*-
"""La colonne `matiere` passe de 64 à 80 caractères, sur les trois tables de contenu.

CONSTAT. Le référentiel de la Licence Ergothérapie porte six matières, qui sont les six
domaines d'unités d'enseignement du diplôme. Deux d'entre elles dépassent la colonne qui
doit les recevoir : « Intégration des savoirs et posture professionnelle de
l'ergothérapeute » fait 70 caractères, « Méthodes, techniques et outils d'intervention de
l'ergothérapeute » en fait 65, et `sequences.matiere`, `seances.matiere` et
`activites.matiere` étaient en varchar(64).

CE QUE ÇA PRODUISAIT. Pas une troncature : un refus. `value too long for type character
varying(64)`. Un professeur de Licence Ergothérapie ne pouvait créer ni séquence, ni séance,
ni activité sur ces deux matières — un tiers de son référentiel, inaccessible sans une seule
ligne d'erreur visible à l'écran.

POURQUOI 80 ET NON Text. Le plafond est choisi, pas subi : 80 laisse dix caractères
au-dessus de la plus longue matière connue. Si un diplôme à venir nomme ses matières plus
largement encore, c'est cette borne qu'il faudra relever — et la borne, au moins, se voit.

CE QUI N'EST PAS TOUCHÉ. Le nom des matières lui-même : `matieres.nom` est en Text et n'a
jamais été en cause. Les libellés se reprennent mot pour mot du référentiel, ici comme
ailleurs.

Revision ID: b7e1f4a9c3d2
Revises: a5c9e3b7d1f4
Create Date: 2026-08-09
"""
from alembic import op
import sqlalchemy as sa


revision = "b7e1f4a9c3d2"
down_revision = "a5c9e3b7d1f4"
branch_labels = None
depends_on = None


# Les trois tables de contenu qui recopient le nom de la matière au moment de la saisie.
_TABLES = ("sequences", "seances", "activites")


def upgrade() -> None:
    for table in _TABLES:
        op.alter_column(
            table, "matiere",
            existing_type=sa.String(64), type_=sa.String(80),
            existing_nullable=True,
        )


def downgrade() -> None:
    # Le retour en arrière tronque : PostgreSQL refuse de rétrécir une colonne dont une
    # valeur dépasse la nouvelle borne. On coupe donc explicitement, plutôt que de laisser
    # la migration échouer sur une base qui contient de l'ergothérapie.
    for table in _TABLES:
        op.execute(f"UPDATE {table} SET matiere = left(matiere, 64) WHERE length(matiere) > 64")
        op.alter_column(
            table, "matiere",
            existing_type=sa.String(80), type_=sa.String(64),
            existing_nullable=True,
        )
