"""ajoute matiere_niveaux.variante + index unique (matiere_id, niveau_id, variante)

Une meme matiere peut etre declinee au meme niveau (ex. Langue vivante A / B en 3e).
On ne dedouble PAS la matiere : la variante est portee sur la paire, dans
`matiere_niveaux.variante` (NOT NULL default '' ; '' = pas de variante). L'index unique
passe donc de (matiere_id, niveau_id) a (matiere_id, niveau_id, variante) — cf. regle
« Matiere, variante, specialite » de CLAUDE.md. NOT NULL default '' plutot que NULL :
l'unique protege partout, sans le piege PostgreSQL « NULL != NULL ».

downgrade : rebascule l'unique sur (matiere_id, niveau_id) puis supprime la colonne.
ATTENTION : si des couples ne different QUE par la variante (ex. Langue vivante A et B
sur le meme niveau) ont deja ete inseres, la recreation de l'unique a 2 colonnes
echouera (doublons) — c'est attendu : un retour arriere n'a de sens qu'avant injection.

Revision ID: e1f2a3b4c5d6
Revises: a1c2e3f40506
Create Date: 2026-07-02
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e1f2a3b4c5d6"
down_revision = "a1c2e3f40506"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NOT NULL default '' : backfill automatique des lignes existantes a ''.
    op.add_column(
        "matiere_niveaux",
        sa.Column("variante", sa.String(length=32), nullable=False, server_default=""),
    )
    # Remplacer l'unique (matiere_id, niveau_id) par (matiere_id, niveau_id, variante).
    op.drop_index("ix_matiere_niveaux_unique", table_name="matiere_niveaux")
    op.create_index(
        "ix_matiere_niveaux_unique",
        "matiere_niveaux",
        ["matiere_id", "niveau_id", "variante"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_matiere_niveaux_unique", table_name="matiere_niveaux")
    op.create_index(
        "ix_matiere_niveaux_unique",
        "matiere_niveaux",
        ["matiere_id", "niveau_id"],
        unique=True,
    )
    op.drop_column("matiere_niveaux", "variante")
