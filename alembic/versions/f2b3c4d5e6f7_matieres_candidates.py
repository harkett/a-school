"""cree la table matieres_candidates (matieres candidates d'un couple, EN BASE)

Les matieres candidates d'un couple (cycle+niveau) — proposition a valider par l'admin,
affichee dans la table de l'ecran Referentiels — transitaient par un fichier
matieres-candidates.json (REFERENTIELS/<CYCLE>/<NIVEAU>/). Regle « toute donnee metier en
base » : elles deviennent une table, une ligne par niveau (matieres = tableau JSON de noms).

Aucune donnee a migrer : aucun matieres-candidates.json n'existe (les couples renvoyaient []).

downgrade : supprime la table.

Revision ID: f2b3c4d5e6f7
Revises: e1a2b3c4d5e6
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f2b3c4d5e6f7"
down_revision = "e1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "matieres_candidates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("niveau_id", sa.Integer(), sa.ForeignKey("niveaux.id"), nullable=False),
        sa.Column("matieres", sa.Text(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_matieres_candidates_niveau_id", "matieres_candidates", ["niveau_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_matieres_candidates_niveau_id", table_name="matieres_candidates")
    op.drop_table("matieres_candidates")
