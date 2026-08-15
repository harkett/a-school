# -*- coding: utf-8 -*-
"""Le carnet de l'administrateur — un endroit où poser une idée avant de l'oublier

LE DÉFAUT. Les professeurs ont « Mes feedbacks » pour faire remonter une remarque, et
l'administrateur a l'écran qui les reçoit. Lui n'avait rien. Une idée qui lui vient au milieu
d'une autre tâche — « alerter quand un compte tourne sur dix postes » — n'avait aucun endroit où
atterrir : elle se disait, et elle se perdait.

CE QUE LA TABLE N'EST PAS. Ni `taches_planifiees`, qui fait tourner des travaux à l'heure dite ;
ni `fonctionnalites`, qui décrit ce qui existe déjà. Ici rien ne s'exécute : c'est un carnet.

LES TROIS PREMIÈRES LIGNES SONT SEMÉES. Elles viennent de la discussion du 15/08/2026 sur les
connexions, et c'est justement pour ne pas les perdre que le carnet a été créé. Un carnet livré
vide aurait perdu ce qu'il était censé retenir.

downgrade : supprime la table et ce qu'elle contient. Aucune autre table n'en dépend.

Revision ID: e2b6d4f8a1c5
Revises: d1e5a9c3b7f2
Create Date: 2026-08-15
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "e2b6d4f8a1c5"
down_revision: Union[str, Sequence[str], None] = "d1e5a9c3b7f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "taches_a_faire",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("titre", sa.String(200), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("fait", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("fait_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        """
        INSERT INTO taches_a_faire (titre, detail) VALUES
        ('Une seule connexion par prof',
         'Se connecter quelque part déconnecte l''autre poste. Décidé puis mis de côté le '
         '15/08/2026 : la règle gênerait le prof qui passe de la salle de classe à la maison, '
         'alors que la cible réelle est le compte partagé entre plusieurs enseignants. '
         'L''alerte ci-dessous est préférée à la sanction — à trancher.'),
        ('Alerter quand un compte tourne sur trop de postes',
         'Repérer le compte partagé sans gêner l''usage normal : ordinateur de la salle, '
         'ordinateur de la maison et téléphone font trois appareils légitimes. Le seuil et la '
         'fenêtre de temps restent à définir. La matière première est en place : les sessions '
         'gardent navigateur, système, type d''appareil, adresse et lieu.'),
        ('Alerter sur deux connexions géographiquement éloignées',
         'Deux sessions du même compte ouvertes à Lille et à Marseille au même moment ne peuvent '
         'pas être la même personne. Le calcul de distance existe déjà '
         '(backend/systeme/localisation_ip.py, distance_km) et les coordonnées sont écrites sur '
         'chaque session. Reste à choisir le seuil de kilomètres et l''écart de temps toléré.')
        """
    )


def downgrade() -> None:
    op.drop_table("taches_a_faire")
