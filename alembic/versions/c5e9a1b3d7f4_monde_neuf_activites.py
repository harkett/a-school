"""Monde neuf « Mes contenus » : tables `activites` + `activite_versions` (règle 0 native).

La brique de base du modèle playlist (séquence ⊃ séances ⊃ activités). Contrairement à
l'ancien monde (`activites_sauvegardees`, née à l'époque du bouton « Sauvegarder »), cette
table applique la règle 0 dès sa naissance : l'activité est écrite en base À LA GÉNÉRATION
(auto-save, plus aucun bouton d'enregistrement), et chaque jalon (génération, plus tard
édition/restauration) fige une VERSION restaurable dans `activite_versions` — l'historique
s'empile, on n'écrase jamais.

Clés :
- `activites.seance_id` → ON DELETE SET NULL : supprimer une séance rend ses activités
  « non rangées », ne les détruit jamais (parent toujours facultatif).
- `activites.activite_type_id` → FK au catalogue partagé `types_activite` (référentiel,
  pas une donnée de l'ancien monde) + `activite_label` figé pour l'historique.
- `activite_versions.activite_id` → ON DELETE CASCADE : les versions suivent leur activité.

L'ancien monde n'est PAS touché : `activites_sauvegardees` vit sa vie dans Mes outils
jusqu'à sa suppression finale (décision utilisateur, à la fin du chantier).

Revision ID: c5e9a1b3d7f4
Revises: a3c7e9d1b5f2
"""
import sqlalchemy as sa
from alembic import op

revision = "c5e9a1b3d7f4"
down_revision = "a3c7e9d1b5f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("seance_id", sa.Integer(),
                  sa.ForeignKey("seances.id", ondelete="SET NULL"), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("activite_type_id", sa.Integer(),
                  sa.ForeignKey("types_activite.id"), nullable=False),
        sa.Column("activite_label", sa.String(128), nullable=False),
        sa.Column("sous_type", sa.String(64), nullable=True),
        sa.Column("nb", sa.Integer(), nullable=True),
        sa.Column("avec_correction", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("objet", sa.String(150), nullable=True),
        sa.Column("matiere", sa.String(64), nullable=True),
        sa.Column("niveau", sa.String(32), nullable=True),
        sa.Column("ton", sa.String(32), nullable=True),
        sa.Column("texte_source", sa.Text(), nullable=False, server_default=""),
        sa.Column("resultat", sa.Text(), nullable=False, server_default=""),
        sa.Column("statut", sa.String(32), nullable=False, server_default="brouillon"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activites_user_id", "activites", ["user_id"])
    op.create_index("ix_activites_seance_id", "activites", ["seance_id"])
    op.create_index("ix_activites_activite_type_id", "activites", ["activite_type_id"])

    op.create_table(
        "activite_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("activite_id", sa.Integer(),
                  sa.ForeignKey("activites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jalon", sa.String(32), nullable=False),
        sa.Column("ton", sa.String(32), nullable=True),
        sa.Column("resultat", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activite_versions_activite_id", "activite_versions", ["activite_id"])


def downgrade() -> None:
    op.drop_index("ix_activite_versions_activite_id", table_name="activite_versions")
    op.drop_table("activite_versions")
    op.drop_index("ix_activites_activite_type_id", table_name="activites")
    op.drop_index("ix_activites_seance_id", table_name="activites")
    op.drop_index("ix_activites_user_id", table_name="activites")
    op.drop_table("activites")
