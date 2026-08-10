# -*- coding: utf-8 -*-
"""`connexion_logs.action` passe de 16 a 32 caracteres : « inactivite_logout » n'y entrait pas.

LE DEFAUT, trouve le 10/08/2026 en ecrivant le test qui manquait a la route. La colonne est
declaree `String(16)` avec, en commentaire, « signup | login » — les deux seules valeurs du jour
ou elle est nee. Deux autres sont arrivees depuis :

    admin_login          11 caracteres  -> passe
    inactivite_logout    17 caracteres  -> NE PASSE PAS

`POST /api/auth/logout-inactivite` inserait donc une ligne trop longue et PostgreSQL la refusait :
`StringDataRightTruncation`, erreur 500 chez le prof qu'on venait de deconnecter. La preuve que ca
n'a jamais fonctionne est en base : `connexion_logs` ne contient que `login` (22), `admin_login`
(55) et `signup` (1) — pas une seule sortie pour inactivite, alors que le front appelle cette
route depuis qu'elle existe.

POURQUOI 32 ET NON 17. Une largeur ajustee au mot le plus long d'aujourd'hui reproduirait le
defaut au premier mot suivant. 32 laisse la place a « inactivite_logout » et a ce qui viendra,
sans peser : la colonne est courte par nature.

AUCUNE DONNEE NE BOUGE : elargir un VARCHAR ne reecrit pas la table et n'invalide rien.

Revision ID: d5b1f8c3e604
Revises: c3a7e9b1d854
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa


revision = "d5b1f8c3e604"
down_revision = "c3a7e9b1d854"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("connexion_logs", "action",
                    existing_type=sa.String(16), type_=sa.String(32), existing_nullable=False)


def downgrade() -> None:
    """Retrecir a 16 REFUSERAIT les lignes « inactivite_logout » deja ecrites. On les retire
    d'abord : c'est le seul moyen de revenir en arriere sans que PostgreSQL bloque, et elles
    n'existaient pas avant cette migration de toute facon."""
    op.execute("DELETE FROM connexion_logs WHERE length(action) > 16")
    op.alter_column("connexion_logs", "action",
                    existing_type=sa.String(32), type_=sa.String(16), existing_nullable=False)
