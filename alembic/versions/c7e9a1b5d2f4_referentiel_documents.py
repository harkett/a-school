"""`referentiel_documents` : les PDF d'un couple, avant et après la fusion.

Un niveau n'a pas toujours un document unique. Au collège et à l'école, le programme complet du
cycle tient en un PDF ; au lycée, il n'existe qu'éclaté — un fichier par matière et par série. Le
couple doit donc pouvoir recevoir plusieurs documents, les garder, les ordonner, en retirer un,
puis les fusionner en un seul `referentiel.pdf`.

La base dit ce qui existe, le disque ne porte que les octets : une ligne par fichier rangé dans
REFERENTIELS/<CYCLE>/<NIVEAU>/. Deux liens — `niveau_id` posé dès le dépôt (la ligne `referentiels`
n'existe pas encore, elle naît à la fusion), `referentiel_id` rempli à la fusion.

Supprime au passage `referentiel_depots`, la zone d'attente à jeton : morte depuis que le couple
est demandé AVANT le document (la destination étant connue d'entrée, plus rien n'attend). Aucune
ligne n'y a jamais été écrite par le labo ; la reconstruire, si besoin, est un `downgrade`.

Revision ID: c7e9a1b5d2f4
Revises: b2d4f6a8c1e3
"""
import sqlalchemy as sa
from alembic import op

revision = "c7e9a1b5d2f4"
down_revision = "b2d4f6a8c1e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "referentiel_documents",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("niveau_id", sa.Integer(),
                  sa.ForeignKey("niveaux.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referentiel_id", sa.Integer(),
                  sa.ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=True),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fichier_origine", sa.Text(), nullable=False),
        sa.Column("fichier_disque", sa.Text(), nullable=False),
        sa.Column("empreinte", sa.String(64), nullable=False),
        sa.Column("taille_ko", sa.Integer(), nullable=False),
        sa.Column("pages", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(10), nullable=False),
        sa.Column("url_source", sa.Text(), nullable=True),
        sa.Column("apercu", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("niveau_id", "fichier_disque", name="uq_ref_documents_fichier"),
    )
    op.create_index("ix_ref_documents_niveau", "referentiel_documents", ["niveau_id"])
    op.create_index("ix_ref_documents_referentiel", "referentiel_documents", ["referentiel_id"])
    op.create_index("ix_ref_documents_empreinte", "referentiel_documents", ["empreinte"])
    op.drop_table("referentiel_depots")


def downgrade() -> None:
    op.create_table(
        "referentiel_depots",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("token", sa.String(32), nullable=False),
        sa.Column("empreinte", sa.String(64), nullable=False),
        sa.Column("fichier_origine", sa.Text(), nullable=False),
        sa.Column("chemin", sa.Text(), nullable=False),
        sa.Column("taille_ko", sa.Integer(), nullable=False),
        sa.Column("pages", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(10), nullable=False),
        sa.Column("url_source", sa.Text(), nullable=True),
        sa.Column("apercu", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("token", name="uq_referentiel_depots_token"),
    )
    op.create_index("ix_referentiel_depots_empreinte", "referentiel_depots", ["empreinte"])
    op.drop_index("ix_ref_documents_empreinte", table_name="referentiel_documents")
    op.drop_index("ix_ref_documents_referentiel", table_name="referentiel_documents")
    op.drop_index("ix_ref_documents_niveau", table_name="referentiel_documents")
    op.drop_table("referentiel_documents")
