# -*- coding: utf-8 -*-
"""referentiels.controle_niveau : la PREUVE du controle n°1 du depot, figee sur la ligne du
referentiel

Pourquoi : au choix du fichier, le serveur cherche les mots du NIVEAU dans le texte du PDF (sans
IA) et refuse le document s'il ne les nomme pas. C'est CE controle qui autorise le depot — mais
son resultat vivait seulement a l'ecran, le temps de la manoeuvre, et disparaissait ensuite. Plus
moyen, apres coup, de dire sur quoi on s'etait appuye pour accepter ce document.

Il ne se recalcule pas : il porte sur le texte du PDF ET sur le nom du niveau tels qu'ils etaient
AU MOMENT du depot. C'est donc une donnee NEUVE, qui va en base, sur la ligne du referentiel,
exactement comme ses deux voisines `forcage_motif` et `verif_couple`.

JSON : {"niveau": str, "trouve": bool, "manquants": [str]}. NULL = depot anterieur a cette
colonne (l'ecran n'affiche alors rien, sans regression).

Revision ID: e5a1c3d7b9f2
Revises: d3b7f5c9e1a2
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa

revision = "e5a1c3d7b9f2"
down_revision = "d3b7f5c9e1a2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("referentiels", sa.Column("controle_niveau", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("referentiels", "controle_niveau")
