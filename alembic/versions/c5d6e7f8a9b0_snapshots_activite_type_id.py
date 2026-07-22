"""activites_sauvegardees / few_shot_milestones : activite_key (texte) -> activite_type_id (FK)

On remplace la reference TEXTE au type (chaine 'activite_key', copie fragile) par une vraie CLE
ETRANGERE 'activite_type_id' vers types_activite.id (regle 4 : on relie par identifiant, jamais
par une chaine recopiee). Donnees de dev PURGEES (aucun prof reel ; les sequences a type bidon
'sequence' n'ont de toute facon pas d'id catalogue). FK OBLIGATOIRE, zero NULL, zero cas particulier.

Revision ID: c5d6e7f8a9b0
Revises: d4c3b2a1f0e9
Create Date: 2026-07-21
"""
from alembic import op
import sqlalchemy as sa

revision = "c5d6e7f8a9b0"
down_revision = "d4c3b2a1f0e9"
branch_labels = None
depends_on = None


def upgrade():
    # Purge des donnees de dev (references par chaine) — on repart propre pour une FID obligatoire.
    op.execute("DELETE FROM few_shot_milestones")
    op.execute("DELETE FROM activites_sauvegardees")

    # activites_sauvegardees : activite_key -> activite_type_id (FK obligatoire)
    op.add_column("activites_sauvegardees",
                  sa.Column("activite_type_id", sa.Integer(),
                            sa.ForeignKey("types_activite.id"), nullable=False))
    op.create_index("ix_activites_sauvegardees_activite_type_id",
                    "activites_sauvegardees", ["activite_type_id"])
    op.drop_column("activites_sauvegardees", "activite_key")

    # few_shot_milestones : unicite (user_id, activite_key) -> (user_id, activite_type_id)
    op.drop_index("ix_few_shot_milestones_unique", table_name="few_shot_milestones")
    op.add_column("few_shot_milestones",
                  sa.Column("activite_type_id", sa.Integer(),
                            sa.ForeignKey("types_activite.id"), nullable=False))
    op.drop_column("few_shot_milestones", "activite_key")
    op.create_index("ix_few_shot_milestones_unique",
                    "few_shot_milestones", ["user_id", "activite_type_id"], unique=True)


def downgrade():
    op.drop_index("ix_few_shot_milestones_unique", table_name="few_shot_milestones")
    op.add_column("few_shot_milestones",
                  sa.Column("activite_key", sa.String(length=64), nullable=False))
    op.drop_column("few_shot_milestones", "activite_type_id")
    op.create_index("ix_few_shot_milestones_unique",
                    "few_shot_milestones", ["user_id", "activite_key"], unique=True)

    op.drop_index("ix_activites_sauvegardees_activite_type_id", table_name="activites_sauvegardees")
    op.add_column("activites_sauvegardees",
                  sa.Column("activite_key", sa.String(length=64), nullable=False))
    op.drop_column("activites_sauvegardees", "activite_type_id")
