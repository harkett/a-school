# -*- coding: utf-8 -*-
"""la matiere appartient au REFERENTIEL (fin du catalogue global de matieres)

LOT 1 du chantier Matiere — la BASE seule. Le code applicatif parle encore de l'ancien
modele : il est repris au lot 2, et c'est LUI qui appliquera cette migration a la base dev.

CE QUI CHANGE
  - `matieres` recoit `referentiel_id` NOT NULL : une matiere n'existe QUE dans le
    referentiel qui la nomme, avec l'orthographe du document. Unicite sur
    (referentiel_id, nom) : deux referentiels peuvent avoir chacun leur « Mathematiques »,
    et ils ne se croisent jamais. `validee` distingue la matiere PROPOSEE par la detection
    (false) de celle RETENUE par l'admin (true).
  - `matiere_niveaux` disparait : le referentiel connait deja son niveau, la paire faisait
    doublon. Sa colonne `variante` (LV A/B) part avec elle — un document qui distingue LV1 et
    LV2 donne desormais DEUX matieres du referentiel.
  - `matieres_candidates` disparait : la detection ecrit directement dans `matieres` avec
    `validee = false`, l'admin coche. Plus de liste de noms a cote de la table qu'elle double.
  - `referentiels.matiere_id` disparait : un referentiel = un niveau (constate avant travaux :
    8 referentiels, 8 a NULL, 0 avec une matiere). L'unicite passe sur `niveau_id` seul.
  - `user_enseignements` disparait : sa cle etrangere pointait sur la paire, et la table
    n'avait ni ligne (0) ni lecteur applicatif (verifie : aucun import, aucun endpoint).

AUCUNE REPRISE DE DONNEES (decision du 01/08/2026, les deux bases sont jetables) : les
matieres existantes sont EFFACEES, le profil des profs est detache (subject_id /
travail_matiere_id remis a NULL). Les matieres reviennent par le redepot des PDF.
Le seed c6d7e8f9a0b1 est ampute de sa partie matieres/paires dans le meme geste : une matiere
sans referentiel ne doit plus pouvoir naitre, meme sur une base neuve.

downgrade : rend le SCHEMA d'avant (tables et colonnes recreees, vides). Les donnees, elles,
ne reviennent pas — elles sont volontairement detruites ici.

Revision ID: f8b3d5c7a1e9
Revises: b8e5f2a1c9d7
Create Date: 2026-08-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f8b3d5c7a1e9"
down_revision: Union[str, Sequence[str], None] = "b8e5f2a1c9d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1 — Detacher ce qui pointe vers une matiere, AVANT de vider la table (FK RESTRICT).
    #     Le couple de profil et le couple de travail se rechoisissent apres redepot.
    op.execute("UPDATE users SET subject_id = NULL, travail_matiere_id = NULL")

    # 2 — Les tables qui disparaissent. Ordre impose par les FK : user_enseignements pointe
    #     sur matiere_niveaux, qui pointe sur matieres.
    op.drop_table("user_enseignements")
    op.drop_index("ix_matiere_niveaux_unique", table_name="matiere_niveaux")
    op.drop_table("matiere_niveaux")
    op.drop_index("ix_matieres_candidates_niveau_id", table_name="matieres_candidates")
    op.drop_table("matieres_candidates")

    # 3 — Un referentiel = un niveau. DROP COLUMN emporte avec lui la FK vers matieres et
    #     l'unique (niveau_id, matiere_id) qui l'utilisait ; l'unicite se repose sur le niveau.
    op.drop_column("referentiels", "matiere_id")
    op.create_unique_constraint("uq_referentiels_niveau", "referentiels", ["niveau_id"])

    # 4 — La matiere appartient a son referentiel. Table VIDEE d'abord : `referentiel_id` peut
    #     donc naitre NOT NULL sans valeur de remplissage inventee.
    op.execute("DELETE FROM matieres")
    op.add_column("matieres", sa.Column("referentiel_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "matieres_referentiel_id_fkey", "matieres", "referentiels",
        ["referentiel_id"], ["id"], ondelete="CASCADE",
    )
    op.create_index("ix_matieres_referentiel_id", "matieres", ["referentiel_id"])
    # PROPOSEE par la detection (false) vs RETENUE par l'admin (true). Defaut false : une
    # matiere qui arrive de l'IA n'est jamais validee d'office.
    op.add_column("matieres", sa.Column("validee", sa.Boolean(), nullable=False,
                                        server_default=sa.text("false")))
    # Deux matieres de meme nom dans le MEME referentiel : impossible. Dans deux referentiels
    # differents : normal, et elles restent deux matieres distinctes.
    op.create_unique_constraint("uq_matieres_referentiel_nom", "matieres", ["referentiel_id", "nom"])


def downgrade() -> None:
    # Retour au SCHEMA d'avant, vide de donnees (le vidage de l'upgrade est definitif).
    op.drop_constraint("uq_matieres_referentiel_nom", "matieres", type_="unique")
    op.drop_column("matieres", "validee")
    op.drop_index("ix_matieres_referentiel_id", table_name="matieres")
    op.drop_constraint("matieres_referentiel_id_fkey", "matieres", type_="foreignkey")
    op.drop_column("matieres", "referentiel_id")

    op.drop_constraint("uq_referentiels_niveau", "referentiels", type_="unique")
    op.add_column("referentiels", sa.Column("matiere_id", sa.Integer(), nullable=True))
    op.create_foreign_key("referentiels_matiere_id_fkey", "referentiels", "matieres",
                          ["matiere_id"], ["id"])
    op.create_unique_constraint("referentiels_niveau_id_matiere_id_key", "referentiels",
                                ["niveau_id", "matiere_id"])

    op.create_table(
        "matieres_candidates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("niveau_id", sa.Integer(), sa.ForeignKey("niveaux.id"), nullable=False),
        sa.Column("matieres", sa.Text(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_matieres_candidates_niveau_id", "matieres_candidates", ["niveau_id"], unique=True)

    op.create_table(
        "matiere_niveaux",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("matiere_id", sa.Integer(), nullable=False),
        sa.Column("niveau_id", sa.Integer(), nullable=False),
        sa.Column("actif", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("variante", sa.String(length=32), server_default="", nullable=False),
        sa.ForeignKeyConstraint(["matiere_id"], ["matieres.id"]),
        sa.ForeignKeyConstraint(["niveau_id"], ["niveaux.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_matiere_niveaux_matiere_id"), "matiere_niveaux", ["matiere_id"], unique=False)
    op.create_index(op.f("ix_matiere_niveaux_niveau_id"), "matiere_niveaux", ["niveau_id"], unique=False)
    op.create_index("ix_matiere_niveaux_unique", "matiere_niveaux",
                    ["matiere_id", "niveau_id", "variante"], unique=True)

    op.create_table(
        "user_enseignements",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("matiere_niveau_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["matiere_niveau_id"], ["matiere_niveaux.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "matiere_niveau_id"),
    )
