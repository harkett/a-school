# -*- coding: utf-8 -*-
"""Le nom sous lequel un référentiel se montre — tous les niveaux qu'il dessert, pas seulement le sien

LE DÉFAUT. La liste des référentiels affichait « Collège · 4e » pour un document qui sert la 5e,
la 4e ET la 3e. Un administrateur qui vient modifier le programme de la 3e ne trouve aucune ligne
pour la 3e : il en déduit qu'il n'y en a pas, et il en dépose un second. Rien ne le détrompait.

CE QUE PORTE LA COLONNE. Les niveaux desservis, écrits dans l'ordre du cycle et séparés par des
virgules : « 5e, 4e, 3e ». La liste affiche « Collège · 5e, 4e, 3e ». Un référentiel d'un seul
niveau y écrit ce seul niveau — rien ne change pour les cinq autres.

CALCULÉE, JAMAIS SAISIE. Un libellé tapé à la main ment le jour où un rattachement bouge, et
personne ne s'en aperçoit : il n'y a aucun moyen de savoir qu'il est devenu faux. Il est donc
DÉRIVÉ de `referentiel_niveaux`, ici pour l'existant et par `recalculer_nom_affichage()` pour la
suite. La colonne reste une COPIE — c'est assumé : sans elle, la liste devrait agréger à chaque
affichage, et l'écran de consultation ne pourrait plus trier dessus.

downgrade : retire la colonne. Rien n'est perdu, la source est `referentiel_niveaux`.

Revision ID: c9a4e7b2d6f3
Revises: b8d3f1a6c9e4
Create Date: 2026-08-15
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "c9a4e7b2d6f3"
down_revision: Union[str, Sequence[str], None] = "b8d3f1a6c9e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("nom_affichage", sa.Text(), nullable=True))
    # `ORDER BY n.ordre` : l'ordre du cycle, celui que l'administrateur a sous les yeux dans ses
    # menus — jamais l'ordre d'insertion des rattachements, qui ne veut rien dire pour un lecteur.
    op.execute(
        """
        UPDATE referentiels r
           SET nom_affichage = (
               SELECT string_agg(n.nom, ', ' ORDER BY n.ordre)
                 FROM referentiel_niveaux rn
                 JOIN niveaux n ON n.id = rn.niveau_id
                WHERE rn.referentiel_id = r.id)
        """
    )


def downgrade() -> None:
    op.drop_column("referentiels", "nom_affichage")
