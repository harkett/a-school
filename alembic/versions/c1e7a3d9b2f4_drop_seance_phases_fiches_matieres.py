"""supprime seance_phases et fiches_matieres, deux tables jamais construites

ATTENTION, ces deux-la ne sont PAS du meme genre que type_parametres (migration
b8d5f2a4c6e1) : celle-la portait un chemin REMPLACE — on lui avait trouve un
successeur (`besoins`). Ici, rien n'a jamais ete branche. Les deux tables sont nees
avec leur migration et n'ont jamais recu une ligne ni un lecteur :

  seance_phases    — 0 ligne. Aucun import de SeancePhase hors sa declaration. La
                     docstring de mes_contenus.py annoncait pourtant que le module
                     l'ecrivait : promesse fausse, corrigee dans le meme geste.
  fiches_matieres  — 0 ligne. Aucun import de FicheMatiere hors sa declaration.
                     Colonnes statut/accroche/pour_qui : une fiche editoriale par
                     matiere, concue puis jamais reliee a un ecran.

Verifie sur aschool_dev le 01/08/2026 : 0 ligne chacune, zero lecteur dans backend/,
tests/, frontend/src/ et alembic/ (hors creation).

Le downgrade les recree a l'IDENTIQUE, colonnes et index compris : si l'une de ces
deux fonctionnalites revient, sa structure est ici, intacte.

Revision ID: c1e7a3d9b2f4
Revises: b8d5f2a4c6e1
Create Date: 2026-08-01
"""
from alembic import op
import sqlalchemy as sa

revision = "c1e7a3d9b2f4"
down_revision = "b8d5f2a4c6e1"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_seance_phases_seance_id", table_name="seance_phases")
    op.drop_table("seance_phases")
    op.drop_index("ix_fiches_matieres_matiere_key", table_name="fiches_matieres")
    op.drop_table("fiches_matieres")


def downgrade():
    op.create_table(
        "seance_phases",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("seance_id", sa.Integer(),
                  sa.ForeignKey("seances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("titre", sa.String(300), nullable=False, server_default=""),
        sa.Column("contenu", sa.Text(), nullable=False, server_default=""),
        sa.Column("duree_minutes", sa.Integer(), nullable=True),
    )
    op.create_index("ix_seance_phases_seance_id", "seance_phases", ["seance_id"])

    op.create_table(
        "fiches_matieres",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("matiere_key", sa.String(64), nullable=False),
        sa.Column("statut", sa.String(16), nullable=False),
        sa.Column("accroche", sa.Text(), nullable=True),
        sa.Column("pour_qui", sa.Text(), nullable=True),
        sa.Column("ameliorations", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_fiches_matieres_matiere_key", "fiches_matieres", ["matiere_key"], unique=True)
