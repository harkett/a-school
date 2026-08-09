"""Ajoute `referentiels.prompt_meta_decoupe` : le meta-prompt de la decoupe, par niveau.

06/08/2026. Jumelle exacte de la revision d5b9c2e4f8a7 (meta-prompt des matieres), pour la
decoupe cette fois. Le meta-prompt est la consigne qui sert a ECRIRE le prompt de decoupe : elle
recoit le document dans {document} et rend un prompt qui, lui, porte {texte}.

Il en existait UN SEUL pour toute l'application : la ligne `prompt_meta_decoupe` de la table
`settings`. Un BTS et un programme de creche ne se decoupent pas selon les memes reperes ; cette
colonne permet a un niveau d'avoir la sienne.

REPLI CONSERVE : colonne NULL = on lit le Setting global, comme avant. Aucun niveau n'est modifie
par cette revision, et rien ne change tant qu'un texte n'y est pas ecrit a la main.

Pas de drapeau `_valide` : ce texte est ecrit par l'admin, jamais par l'IA — il n'y a rien a relire.
"""
from alembic import op
import sqlalchemy as sa


revision = "e2c7a4b8d1f3"
down_revision = "d5b9c2e4f8a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("prompt_meta_decoupe", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("referentiels", "prompt_meta_decoupe")
