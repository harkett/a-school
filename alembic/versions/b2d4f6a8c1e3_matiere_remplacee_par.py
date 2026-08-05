"""`profs_bloques_maj.remplacee_par` : la matière qui a PRIS LA PLACE de l'ancienne.

Le déblocage rebranchait par le nom seul : nom retrouvé à l'identique, ou « matière disparue ».
Un programme qui change ne supprime presque jamais une matière — il la renomme ou la fusionne.
L'admin désigne donc désormais, pour chaque matière attendue, celle qui la remplace ; le nom
CHOISI se range ici, à côté du nom d'origine (`matiere_nom`).

Nullable : NULL = rien n'a été remplacé (nom retrouvé à l'identique, ou matière réellement
disparue). Le NOM et non l'identifiant, comme `matiere_nom` — pour la même raison : ce que le
prof lira doit survivre à la prochaine suppression du référentiel.

Revision ID: b2d4f6a8c1e3
Revises: e5a7c9b1d3f6
"""
import sqlalchemy as sa
from alembic import op

revision = "b2d4f6a8c1e3"
down_revision = "e5a7c9b1d3f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profs_bloques_maj", sa.Column("remplacee_par", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("profs_bloques_maj", "remplacee_par")
