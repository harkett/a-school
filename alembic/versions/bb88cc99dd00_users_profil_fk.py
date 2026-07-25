# -*- coding: utf-8 -*-
"""users : cles etrangeres profil (subject_id, niveau_id, travail_matiere_id, travail_niveau_id)

Etape 1 du chantier REGLE 4 sur le profil. La table users pointait le niveau et la matiere par
leur NOM recopie (users.subject / users.niveau / users.travail_matiere / users.travail_niveau)
au lieu de leur cle -> copie qui peut diverger + resolution par nom ambigue (aucune contrainte
d'unicite sur niveaux.nom). On AJOUTE les 4 cles etrangeres (nullable) et on les REMPLIT depuis
les noms existants : chaque nom -> un seul id ; si 0 ou plusieurs correspondances -> NULL (on ne
devine pas un id ambigu). Les colonnes texte RESTENT a cette etape : aucune lecture/ecriture ne
change encore, rien ne casse. Additif pur, reversible (downgrade = drop des 4 colonnes).

Revision ID: bb88cc99dd00
Revises: aa77bb88cc99
Create Date: 2026-07-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "bb88cc99dd00"
down_revision: Union[str, Sequence[str], None] = "aa77bb88cc99"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("subject_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("niveau_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("travail_matiere_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("travail_niveau_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_users_subject_id", "users", "matieres", ["subject_id"], ["id"])
    op.create_foreign_key("fk_users_niveau_id", "users", "niveaux", ["niveau_id"], ["id"])
    op.create_foreign_key("fk_users_travail_matiere_id", "users", "matieres", ["travail_matiere_id"], ["id"])
    op.create_foreign_key("fk_users_travail_niveau_id", "users", "niveaux", ["travail_niveau_id"], ["id"])

    # Backfill nom -> id, UNIQUEMENT si le nom correspond a EXACTEMENT un enregistrement (sinon on
    # laisse NULL : on ne devine pas un id ambigu). matiere = identite table matieres ; niveau =
    # identite table niveaux. Idempotent (rejouable sans effet de bord).
    op.execute(
        "UPDATE users u SET subject_id = m.id FROM matieres m "
        "WHERE u.subject IS NOT NULL AND m.nom = u.subject "
        "AND (SELECT count(*) FROM matieres m2 WHERE m2.nom = u.subject) = 1"
    )
    op.execute(
        "UPDATE users u SET niveau_id = n.id FROM niveaux n "
        "WHERE u.niveau IS NOT NULL AND n.nom = u.niveau "
        "AND (SELECT count(*) FROM niveaux n2 WHERE n2.nom = u.niveau) = 1"
    )
    op.execute(
        "UPDATE users u SET travail_matiere_id = m.id FROM matieres m "
        "WHERE u.travail_matiere IS NOT NULL AND m.nom = u.travail_matiere "
        "AND (SELECT count(*) FROM matieres m2 WHERE m2.nom = u.travail_matiere) = 1"
    )
    op.execute(
        "UPDATE users u SET travail_niveau_id = n.id FROM niveaux n "
        "WHERE u.travail_niveau IS NOT NULL AND n.nom = u.travail_niveau "
        "AND (SELECT count(*) FROM niveaux n2 WHERE n2.nom = u.travail_niveau) = 1"
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_travail_niveau_id", "users", type_="foreignkey")
    op.drop_constraint("fk_users_travail_matiere_id", "users", type_="foreignkey")
    op.drop_constraint("fk_users_niveau_id", "users", type_="foreignkey")
    op.drop_constraint("fk_users_subject_id", "users", type_="foreignkey")
    op.drop_column("users", "travail_niveau_id")
    op.drop_column("users", "travail_matiere_id")
    op.drop_column("users", "niveau_id")
    op.drop_column("users", "subject_id")
