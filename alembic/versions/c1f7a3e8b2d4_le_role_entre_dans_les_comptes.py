"""Le rôle entre dans les comptes — users.role

L'administration n'était pas un compte : un identifiant et un mot de passe dans les variables
d'environnement, un seul jeu. Impossible d'en avoir deux, impossible de savoir lequel a agi, et
rien de ce que la maison sait déjà faire pour un compte (mot de passe oublié, sessions,
révocation, journal des connexions) ne s'appliquait à lui.

La colonne le fait entrer dans `users`, là où sont déjà les professeurs.

TOUS LES COMPTES EXISTANTS SONT DES PROFESSEURS. C'est vrai par construction : jusqu'ici, seuls
les professeurs avaient une ligne. Le défaut `prof` est posé EN BASE et non seulement dans le
modèle — un compte créé par un chemin qui ignorerait la colonne ne doit pas naître
administrateur par accident.

Cette migration ne touche PAS à la façon dont l'administration s'authentifie : la colonne existe,
personne ne la lit encore. Le branchement est un second geste, qui se teste seul.

Revision ID: c1f7a3e8b2d4
Revises: a8c4f2b6d9e3
Create Date: 2026-08-17
"""
from alembic import op
import sqlalchemy as sa

revision = 'c1f7a3e8b2d4'
down_revision = 'a8c4f2b6d9e3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('role', sa.String(length=20),
                                     nullable=False, server_default='prof'))
    # Un index : toute lecture « qui sont les administrateurs ? » passe par là, et la table des
    # comptes est la plus lue de la base.
    op.create_index('ix_users_role', 'users', ['role'])


def downgrade():
    op.drop_index('ix_users_role', table_name='users')
    op.drop_column('users', 'role')
