"""Socle « Mes contenus » : tables `sequences`, `seances`, `seance_phases`.

Le modèle playlist à 3 niveaux : une séquence contient des séances, une séance contient
des activités — et le parent est TOUJOURS facultatif (une séance ou une activité peut
vivre seule, « non rangée »). Ces trois tables sont le socle (brique 1) ; le niveau
« activité » reste porté par la table EXISTANTE `activites_sauvegardees` (zéro copie,
zéro doublon — son lien de rangement arrivera avec la brique rattachement).

Pourquoi des tables NEUVES : l'outil « Séquence » actuel (`sequences_sauvegardees`)
génère en réalité des SÉANCES (le prompt prépare « une séance de X minutes » en 5-6
phases) — ces lignes seront IMPORTÉES dans `seances` à la brique suivante, puis
l'ancienne table sera éteinte. On ne construit pas le nouveau modèle sur un nom faux.

Choix de clés :
- `seances.sequence_id` → ON DELETE SET NULL : supprimer une séquence rend ses séances
  « non rangées », elle ne les détruit jamais (le contenu appartient au prof).
- `seance_phases.seance_id` → ON DELETE CASCADE : une phase n'existe pas sans sa séance.

Revision ID: a3c7e9d1b5f2
Revises: f1e2d3c4b5a6
"""
import sqlalchemy as sa
from alembic import op

revision = "a3c7e9d1b5f2"
down_revision = "f1e2d3c4b5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sequences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("titre", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("objectifs", sa.Text(), nullable=False, server_default=""),
        sa.Column("tags", sa.Text(), nullable=False, server_default=""),
        sa.Column("duree_totale_minutes", sa.Integer(), nullable=True),
        sa.Column("matiere", sa.String(64), nullable=True),
        sa.Column("niveau", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sequences_user_id", "sequences", ["user_id"])

    op.create_table(
        "seances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sequence_id", sa.Integer(),
                  sa.ForeignKey("sequences.id", ondelete="SET NULL"), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("titre", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("matiere", sa.String(64), nullable=True),
        sa.Column("niveau", sa.String(32), nullable=True),
        sa.Column("duree_minutes", sa.Integer(), nullable=True),
        sa.Column("resultat", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seances_user_id", "seances", ["user_id"])
    op.create_index("ix_seances_sequence_id", "seances", ["sequence_id"])

    op.create_table(
        "seance_phases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("seance_id", sa.Integer(),
                  sa.ForeignKey("seances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("titre", sa.String(300), nullable=False, server_default=""),
        sa.Column("contenu", sa.Text(), nullable=False, server_default=""),
        sa.Column("duree_minutes", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seance_phases_seance_id", "seance_phases", ["seance_id"])


def downgrade() -> None:
    op.drop_index("ix_seance_phases_seance_id", table_name="seance_phases")
    op.drop_table("seance_phases")
    op.drop_index("ix_seances_sequence_id", table_name="seances")
    op.drop_index("ix_seances_user_id", table_name="seances")
    op.drop_table("seances")
    op.drop_index("ix_sequences_user_id", table_name="sequences")
    op.drop_table("sequences")
