"""supprime l'ancien systeme de decoupe (regle regex + arbitrage des cas flous)

L'ancien decoupage etait pilote par une fiche en dur (crèche) + une regle regex et un arbitrage
des tranches d'age, portes EN BASE sur `referentiels` (regle_*, arbitrage, doutes_ia) + la table
`arbitrage_demandes` (avis pro « en attente »). Ce systeme est remplace par la decoupe GENERIQUE
par l'IA (prompt validé du couple). On retire donc ces colonnes/table devenues inutiles.

`score_min` (seuil de pertinence RAG) N'EST PAS touche : ce n'est pas du decoupe, c'est un reglage
de la recherche, toujours en service.

downgrade : recree les colonnes et la table (structure d'origine ; les donnees ne sont pas restaurees).

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Table « avis pro en attente » (TEMPS 2 de l'arbitrage).
    op.drop_index("ix_arbitrage_demandes_referentiel_id", table_name="arbitrage_demandes")
    op.drop_table("arbitrage_demandes")
    # Colonnes de l'ancien decoupe sur referentiels.
    op.drop_column("referentiels", "doutes_ia")
    op.drop_column("referentiels", "arbitrage")
    op.drop_column("referentiels", "regle_valide")
    op.drop_column("referentiels", "regle_depose_par")
    op.drop_column("referentiels", "regle_motif")
    op.drop_column("referentiels", "regle_explication")


def downgrade() -> None:
    op.add_column("referentiels", sa.Column("regle_explication", sa.Text(), nullable=True))
    op.add_column("referentiels", sa.Column("regle_motif", sa.Text(), nullable=True))
    op.add_column("referentiels", sa.Column("regle_depose_par", sa.Text(), nullable=True))
    op.add_column("referentiels", sa.Column("regle_valide", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("referentiels", sa.Column("arbitrage", sa.Text(), nullable=True))
    op.add_column("referentiels", sa.Column("doutes_ia", sa.Text(), nullable=True))
    op.create_table(
        "arbitrage_demandes",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("referentiel_id", sa.Integer(),
                  sa.ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("destinataire", sa.String(length=255), nullable=False),
        sa.Column("demande_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("referentiel_id", "label", name="uq_arbitrage_demandes_ref_label"),
    )
    op.create_index("ix_arbitrage_demandes_referentiel_id", "arbitrage_demandes", ["referentiel_id"])
