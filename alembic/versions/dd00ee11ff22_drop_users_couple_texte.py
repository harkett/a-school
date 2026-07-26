# -*- coding: utf-8 -*-
"""users : suppression des noms recopies du couple (subject / niveau / travail_matiere / travail_niveau)

Etape finale du chantier REGLE 4 sur le profil. Les 4 cles etrangeres (subject_id / niveau_id /
travail_matiere_id / travail_niveau_id) sont en place et remplies (migration bb88cc99dd00), et
TOUT le code lit/ecrit desormais par la cle : le nom se relit par jointure sur matieres/niveaux
(matiere_nom_de_id / niveau_nom_de_id). On SUPPRIME donc les 4 colonnes texte recopiees — une
donnee, une place (zero copie). Reversible : le downgrade recree les colonnes et rebackfille le
nom depuis la cle.

Revision ID: dd00ee11ff22
Revises: cc99dd00ee11
Create Date: 2026-07-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "dd00ee11ff22"
down_revision: Union[str, Sequence[str], None] = "cc99dd00ee11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "travail_niveau")
    op.drop_column("users", "travail_matiere")
    op.drop_column("users", "niveau")
    op.drop_column("users", "subject")


def downgrade() -> None:
    op.add_column("users", sa.Column("subject", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("niveau", sa.String(length=16), nullable=True))
    op.add_column("users", sa.Column("travail_matiere", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("travail_niveau", sa.String(length=16), nullable=True))
    # Rebackfill nom <- cle (le nom vit dans matieres/niveaux) pour restaurer l'ancienne colonne texte.
    op.execute("UPDATE users u SET subject = m.nom FROM matieres m WHERE u.subject_id = m.id")
    op.execute("UPDATE users u SET niveau = n.nom FROM niveaux n WHERE u.niveau_id = n.id")
    op.execute("UPDATE users u SET travail_matiere = m.nom FROM matieres m WHERE u.travail_matiere_id = m.id")
    op.execute("UPDATE users u SET travail_niveau = n.nom FROM niveaux n WHERE u.travail_niveau_id = n.id")
