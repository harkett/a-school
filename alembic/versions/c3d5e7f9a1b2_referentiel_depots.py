"""Table `referentiel_depots` : le PDF déposé existe enfin EN BASE.

Aujourd'hui `_stage()` écrit le PDF dans data/referentiels_staging/<token>.pdf et rend le
jeton au navigateur — et c'est tout. Aucune ligne en base ne connaît ce fichier : le jeton ne
vit que dans l'état React. L'admin recharge la page et le document devient un orphelin que
plus rien ne référence ; le ménage (`_nettoyer_staging`) ne passe que si quelqu'un dépose un
autre document — d'où les 33 aperçus abandonnés, 202 Mo, que le code lui-même raconte.

Pourquoi une table à part et non `referentiels` : au dépôt, le couple n'est pas encore connu,
or `referentiels.niveau_id` est NOT NULL et UNIQUE (un référentiel par niveau), à côté de
`nom_fixe` et `collection` NOT NULL. Y écrire un dépôt obligerait à inventer un niveau,
interdirait deux essais sur le même niveau, et un dépôt abandonné n'y serait plus effaçable
sans emporter ses matières et ses chunks (CASCADE depuis `matieres`, `referentiel_chunks`,
`referentiel_types_activite`). Le dépôt PRÉCÈDE le référentiel : il a sa propre table, et
aucun lien vers `referentiels` tant que la validation ne le pose pas.

`token` unique : c'est le jeton rendu au navigateur ET le nom du fichier sur disque — la
jointure entre la ligne et le fichier. Pas d'index sur `created_at` : la zone d'attente est
transitoire et se compte en dizaines de lignes, un balayage suffit.

Cette migration ne fait que POSER le rangement — `_stage()` n'est pas touché, rien n'écrit
encore dans cette table.

Revision ID: c3d5e7f9a1b2
Revises: b6d1f4a8c2e7
"""
import sqlalchemy as sa
from alembic import op

revision = "c3d5e7f9a1b2"
down_revision = "b6d1f4a8c2e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "referentiel_depots",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("token", sa.String(length=32), nullable=False),
        sa.Column("fichier_origine", sa.Text(), nullable=False),
        sa.Column("chemin", sa.Text(), nullable=False),
        sa.Column("taille_ko", sa.Integer(), nullable=False),
        sa.Column("pages", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("url_source", sa.Text(), nullable=True),
        sa.Column("apercu", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_referentiel_depots_token"),
    )


def downgrade() -> None:
    op.drop_table("referentiel_depots")
