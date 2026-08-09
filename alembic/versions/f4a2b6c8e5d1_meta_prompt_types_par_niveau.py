"""Ajoute `referentiels.prompt_meta_types` : le meta-prompt des types d'activite, par niveau.

06/08/2026. Troisieme et derniere jumelle de d5b9c2e4f8a7 (matieres) et e2c7a4b8d1f3 (decoupe).
Le meta-prompt est la consigne qui sert a ECRIRE le prompt de lecture des types : elle recoit le
document dans {document} et rend un prompt qui, lui, porte {texte}.

Il en existait UN SEUL pour toute l'application : la ligne `prompt_meta_types` de la table
`settings`. C'etait le dernier des trois couples a n'avoir aucune case par niveau — la recette qui
fait ecrire le prompt des types d'un BTS n'est pas celle d'un programme de creche.

REPLI CONSERVE : colonne NULL = on lit le Setting global, comme avant. Aucun niveau n'est modifie
par cette revision, et rien ne change tant qu'un texte n'y est pas ecrit a la main.

Pas de drapeau `_valide` : ce texte est ecrit par l'admin, jamais par l'IA.
"""
from alembic import op
import sqlalchemy as sa


revision = "f4a2b6c8e5d1"
down_revision = "e2c7a4b8d1f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("prompt_meta_types", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("referentiels", "prompt_meta_types")
