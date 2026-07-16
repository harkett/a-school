"""cree la table activite_types (types d'activite PROPRES a un couple, EN BASE)

Les types d'activite etaient EN DUR dans le code (ACTIVITES_* dans llm/activities.py,
PROMPTS_* dans llm/prompts.py) et generiques pour tous. Regle « toute donnee metier en base
+ specifique par couple » : chaque couple porte desormais SES types dans cette table, avec le
PROMPT du type (colonne prompt) a un seul endroit. Ancree au referentiel du couple
(referentiel_id, CASCADE — meme patron que referentiel_chunks). Unicite (referentiel_id, key).

Aucune donnee a migrer : les types en dur ne sont pas rapatries ici (etape suivante du chantier).

downgrade : supprime la table.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activite_types",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "referentiel_id", sa.Integer(),
            sa.ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("sous_types", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("params", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("referentiel_id", "key", name="uq_activite_types_ref_key"),
    )
    op.create_index("ix_activite_types_referentiel_id", "activite_types", ["referentiel_id"])


def downgrade() -> None:
    op.drop_index("ix_activite_types_referentiel_id", table_name="activite_types")
    op.drop_table("activite_types")
