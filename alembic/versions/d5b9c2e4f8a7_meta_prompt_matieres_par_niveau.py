"""Ajoute `referentiels.prompt_meta_matieres` : le meta-prompt des matieres, par niveau.

06/08/2026. Le meta-prompt est la consigne qui sert a ECRIRE le prompt de lecture (elle recoit le
document dans {document} et rend un prompt qui, lui, porte {texte}). Il en existait UN SEUL pour
toute l'application : la ligne `prompt_meta_matieres` de la table `settings`.

Un seul meta-prompt pour tous les diplomes pose le meme probleme que le prompt de lecture qu'on
vient de descendre du cycle : la facon de trouver les matieres dans un BTS (une grille horaire) n'a
rien a voir avec celle d'un programme de creche. Cette colonne permet a un niveau d'avoir la sienne.

REPLI CONSERVE : colonne NULL = on lit le Setting global, comme avant. Aucun niveau n'est modifie
par cette revision, et rien ne change tant qu'un texte n'y est pas ecrit a la main.

Pas de drapeau `_valide` : ce texte est ecrit par l'admin, jamais par l'IA — il n'y a rien a relire.
"""
from alembic import op
import sqlalchemy as sa


revision = "d5b9c2e4f8a7"
down_revision = "c3d8f5a1e7b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("prompt_meta_matieres", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("referentiels", "prompt_meta_matieres")
