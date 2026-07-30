"""`sequences` prend la forme du formulaire de l'écran Séquence (chantier Mes contenus).

Décisions utilisateur du 30/07 (étape 2 du chantier Séquence) :
- `titre` passe en TEXT : le titre = l'OBJECTIF GÉNÉRAL saisi par le prof, une zone d'apport
  complète comme le thème de la séance — on ne rejoue pas le bug de troncature corrigé par
  e8a4c6b2d0f3 (StringDataRightTruncation sur les titres de séance > 300 caractères) ;
- AJOUT des colonnes du formulaire (reprise complète, même moule que `seances`) :
  `contexte` (texte libre), `ampleur` (ampleur souhaitée, libre : « une dizaine de
  séances », « sur deux ans »…), `competences` (liste JSON de chaînes) ;
- RETRAIT de `duree_totale_minutes` : la durée totale se CALCULE depuis les séances, le
  nombre de séances se COMPTE — rien de dérivable ne se stocke (zéro copie) ;
- RETRAIT des colonnes du socle que RIEN ne lit (vérifié : le modèle `Sequence` n'est
  interrogé que par le lister de mes_contenus.py, qui ne sert que titre/matiere/niveau) :
  `description`, `objectifs`, `tags` — pas de colonne morte.

Revision ID: b9d2e4f6a8c1
Revises: e8a4c6b2d0f3
"""
import sqlalchemy as sa
from alembic import op

revision = "b9d2e4f6a8c1"
down_revision = "e8a4c6b2d0f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("sequences", "titre", type_=sa.Text(), existing_type=sa.String(300), existing_nullable=False)
    op.add_column("sequences", sa.Column("contexte", sa.Text(), nullable=False, server_default=""))
    op.add_column("sequences", sa.Column("ampleur", sa.Text(), nullable=False, server_default=""))
    op.add_column("sequences", sa.Column("competences", sa.Text(), nullable=False, server_default="[]"))
    op.drop_column("sequences", "duree_totale_minutes")
    op.drop_column("sequences", "description")
    op.drop_column("sequences", "objectifs")
    op.drop_column("sequences", "tags")


def downgrade() -> None:
    # Retour à la forme du socle : les colonnes retirées reviennent avec leurs défauts
    # d'origine (leur contenu, lui, est perdu — elles n'étaient lues par personne).
    op.add_column("sequences", sa.Column("tags", sa.Text(), nullable=False, server_default=""))
    op.add_column("sequences", sa.Column("objectifs", sa.Text(), nullable=False, server_default=""))
    op.add_column("sequences", sa.Column("description", sa.Text(), nullable=False, server_default=""))
    op.add_column("sequences", sa.Column("duree_totale_minutes", sa.Integer(), nullable=True))
    op.drop_column("sequences", "competences")
    op.drop_column("sequences", "ampleur")
    op.drop_column("sequences", "contexte")
    # Retour au VARCHAR(300) : on coupe nous-mêmes proprement avant de resserrer le type
    # (même geste que le downgrade de e8a4c6b2d0f3 — jamais de rejet en bloc).
    op.execute("UPDATE sequences SET titre = LEFT(titre, 300) WHERE LENGTH(titre) > 300")
    op.alter_column("sequences", "titre", type_=sa.String(300), existing_type=sa.Text(), existing_nullable=False)
