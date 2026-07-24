"""Intitulé de matière élargi à 255 caractères.

Constat du 24/07 : « Récupérer » (enregistrement des matières d'un couple) explosait en 500
(StringDataRightTruncation) sur « Conception et réalisation d'orthèses temporaires et d'aides
techniques » (70 caractères) — les intitulés officiels des référentiels dépassent les
64 caractères du schéma d'origine. On élargit matieres.nom à VARCHAR(255) (standard libellé).

Downgrade symétrique, PROTÉGÉ par PostgreSQL lui-même : revenir à 64 est REFUSÉ par le moteur
si un intitulé plus long existe en base — jamais de troncature silencieuse d'une donnée.

Revision ID: cc33dd44ee55
Revises: bb22cc33dd44
"""
import sqlalchemy as sa
from alembic import op

revision = "cc33dd44ee55"
down_revision = "bb22cc33dd44"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("matieres", "nom", type_=sa.String(255),
                    existing_type=sa.String(64), existing_nullable=False)


def downgrade():
    op.alter_column("matieres", "nom", type_=sa.String(64),
                    existing_type=sa.String(255), existing_nullable=False)
