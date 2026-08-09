"""Retrait de `cycles.prompt_matieres` : ce prompt appartient au REFERENTIEL.

06/08/2026. Le prompt qui lit les matieres etait range sur le CYCLE. C'etait faux, et prouve :
le cycle « BTS » porte dix-huit niveaux, et le prompt ecrit sur le premier (BTS CIEL option A,
avec ses options reseau) etait ensuite servi a tous les autres — il n'apprend rien sur le BTS
CRSA. Une famille de diplomes n'est pas une famille de documents.

La colonne d'accueil `referentiels.prompt_matieres` existe depuis la revision a1f3d7b5c2e8. Le
code la lit et l'ecrit depuis ce jour. Cette revision-ci ferme la parenthese : elle SUPPRIME les
deux colonnes du cycle, pour qu'aucune session — humaine ou non — ne les retrouve plus tard et ne
croie qu'elles servent. Un nom faux qu'on garde « en attendant » ne s'oublie pas, il se recopie.

AUCUNE RECOPIE vers les referentiels : le seul prompt en base (cycle BTS, 1871 caracteres) a ete
ecrit pour le BTS CIEL. Le deverser sur les dix-huit BTS reinstallerait exactement le defaut qu'on
retire. Il a ete remis a l'admin, qui le colle a la main sur le referentiel qui le merite — geste
gratuit, aucun appel IA.

`downgrade()` recree les colonnes VIDES : le texte, lui, ne se retrouve pas. C'est assume — il
n'existait qu'en un exemplaire et il vit maintenant sur les referentiels.
"""
from alembic import op
import sqlalchemy as sa


revision = "b7e1c4d9a3f2"
down_revision = "a1f3d7b5c2e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("cycles", "prompt_matieres_valide")
    op.drop_column("cycles", "prompt_matieres")


def downgrade() -> None:
    op.add_column("cycles", sa.Column("prompt_matieres", sa.Text(), nullable=True))
    op.add_column("cycles", sa.Column("prompt_matieres_valide", sa.Boolean(),
                                      nullable=False, server_default="0"))
