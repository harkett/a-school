# -*- coding: utf-8 -*-
"""L'ecran « Consulter un referentiel » est supprime : sa ligne quitte le tableau de bord.

CE QUI A ETE SUPPRIME (16/08/2026). L'ecran `AdminReferentielsConsulter.jsx`, sa route
`/admin/referentiels-consulter` et son entree de menu. Il montrait exactement ce que montre
l'ecran Referentiel — le PDF, la source, les matieres, le prompt de decoupe — mais sans aucun
bouton qui ecrit. Deux portes vers le meme contenu, dont une que l'administrateur ne se rappelait
meme pas avoir demandee : elle datait du 15/07/2026, restee sans entree de menu jusqu'au 10/08.

POURQUOI CETTE MIGRATION. La table `fonctionnalites` porte une ligne « Consulter un referentiel »
qui cite ce fichier dans sa colonne `composant`. Depuis la migration c3a7e9b1d854, le test
`tests/test_tableau_de_bord_dit_vrai.py` exige que tout composant cite existe reellement : sans ce
DELETE, la suite tombe des le prochain lancement, et le tableau de bord annoncerait un ecran parti.

SUPPRIMER VEUT DIRE SUPPRIMER : la ligne part, elle n'est pas desactivee. Le retour arriere la
recree a l'identique, telle que la posait le seed d'origine.

Revision ID: c9f5a3e8d1b6
Revises: b8e4a2f7d3c9
Create Date: 2026-08-16
"""
from alembic import op
import sqlalchemy as sa


revision = "c9f5a3e8d1b6"
down_revision = "b8e4a2f7d3c9"
branch_labels = None
depends_on = None


ECRAN = "Référentiel"
NOM = "Consulter un référentiel"

# CE QUE LIT `tests/test_tableau_de_bord_dit_vrai.py`. La table (ecran, nom) -> fichier est figee
# dans la migration c3a7e9b1d854, et on ne reecrit pas une migration deja passee. Une ligne
# supprimee se declare donc ICI : le test soustrait ces couples avant d'exiger que chaque fichier
# cite existe. Toute suppression d'ecran a venir suit le meme chemin.
FONCTIONNALITES_RETIREES = {(ECRAN, NOM)}


def upgrade():
    op.execute(
        sa.text("DELETE FROM fonctionnalites WHERE ecran = :ecran AND nom = :nom")
        .bindparams(ecran=ECRAN, nom=NOM)
    )


def downgrade():
    # La ligne telle qu'elle vivait : domaine admin, faite, septieme de l'ecran Referentiel.
    op.execute(
        sa.text(
            "INSERT INTO fonctionnalites (domaine, ecran, nom, etat, ordre, composant) "
            "SELECT 'admin', :ecran, :nom, 'fait', 7, "
            "       'src/pages/AdminReferentielsConsulter.jsx' "
            "WHERE NOT EXISTS ("
            "  SELECT 1 FROM fonctionnalites WHERE ecran = :ecran AND nom = :nom)"
        ).bindparams(ecran=ECRAN, nom=NOM)
    )
