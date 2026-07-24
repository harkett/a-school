"""suppression totale de la notion de famille (tables familles + famille_couples)

La famille ne pilotait plus RIEN : son metier d'origine (piloter la decoupe) a ete retire
par 1e5fcb0, il ne restait qu'une classification pure que personne ne consommait en aval
(audit exhaustif : zero lecteur cote prof / generation / decoupe / RAG). Au depot d'un
referentiel, le choix du couple devient cycle -> niveau (cascade sur l'existant), la
protection = la seule verif n°1 (verifier_couple, IA) + le forcage motive.

Ordre FK : famille_couples (porte les FK) puis familles. Aucune autre table ne reference
ces deux-la (verifie en base : seules FamilleCouple.famille_id -> familles.id et
FamilleCouple.niveau_id -> niveaux.id existent, aucune FK entrante).

Nettoyage defensif des surcharges Settings des 3 prompts famille supprimes du registre
(orphelines si un admin les avait editees) — prompt_* et max_tokens_*.

Revision ID: b0c1d2e3f4a5
Revises: e7f8a9b0c1d2
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa

revision = "b0c1d2e3f4a5"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None

# Les clés Settings devenues orphelines avec le retrait des 3 outils IA famille du registre.
_CLES_ORPHELINES = (
    "prompt_classer_famille", "prompt_suggerer_cycles", "prompt_suggerer_niveaux",
    "max_tokens_classer_famille", "max_tokens_suggerer_cycles", "max_tokens_suggerer_niveaux",
)


def upgrade():
    op.drop_table("famille_couples")
    op.drop_table("familles")
    op.execute(
        "DELETE FROM settings WHERE key IN ("
        + ", ".join(f"'{c}'" for c in _CLES_ORPHELINES)
        + ")"
    )


def downgrade():
    # Re-création du SCHÉMA seul (tables vides) : les données famille sont perdues par
    # construction — la notion a été supprimée du métier, il n'y a plus rien à restaurer.
    op.create_table(
        "familles",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("nom", sa.String(64), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rejet", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_table(
        "famille_couples",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("famille_id", sa.Integer(), sa.ForeignKey("familles.id"), nullable=False, index=True),
        sa.Column("niveau_id", sa.Integer(), sa.ForeignKey("niveaux.id"), nullable=False, index=True),
        sa.UniqueConstraint("famille_id", "niveau_id", name="uq_famille_couples_famille_niveau"),
    )
