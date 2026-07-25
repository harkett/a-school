"""Couple de TRAVAIL du prof EN BASE (décision du 25/07) : `users.travail_matiere` +
`users.travail_niveau`, NULL = le prof travaille sur le couple de son profil.

Avant : le couple de travail (« Changer niveau et/ou matière » sur l'écran Créer) ne vivait
que dans la mémoire de la page — un F5 le remettait silencieusement au profil, et la
génération reposait sur une donnée absente de la base. Désormais la vérité est en base :
Valider = put, « Revenir à mon profil » = effacement (NULL), et le serveur lit CE couple
au moment de générer. Types alignés sur le profil (subject String(64), niveau String(16)).

Revision ID: ee55ff66aa77
Revises: dd44ee55ff66
"""
import sqlalchemy as sa
from alembic import op

revision = "ee55ff66aa77"
down_revision = "dd44ee55ff66"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("travail_matiere", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("travail_niveau", sa.String(length=16), nullable=True))


def downgrade():
    op.drop_column("users", "travail_niveau")
    op.drop_column("users", "travail_matiere")
