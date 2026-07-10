"""cree la table arbitrage_demandes (statut « en attente » d'un avis demande par mail, EN BASE)

TEMPS 2 de l'arbitrage : quand l'admin ne sait pas trancher un cas flou, il demande l'avis d'un pro
par mail. Le statut « en attente » de cette demande est une donnee saisie via l'app -> il vit EN BASE
(regle « tout en base »), une ligne par cas flou en attente (referentiel + libelle). La DECISION, elle,
reste dans referentiels.arbitrage ; ici on ne stocke QUE l'attente. La ligne est supprimee quand
l'admin tranche. Ancree au referentiel (CASCADE) : supprimer le referentiel purge ses demandes.

Aucune donnee a migrer (fonction neuve).

downgrade : supprime la table.

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d1e2f3a4b5c6"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index("ix_arbitrage_demandes_referentiel_id", table_name="arbitrage_demandes")
    op.drop_table("arbitrage_demandes")
