# -*- coding: utf-8 -*-
"""Les prompts MATIERES et TYPES descendent du cycle vers le REFERENTIEL (le couple)

Constat du 06/08/2026, prouve en base : le cycle « BTS » porte 18 niveaux et UNE seule case
`prompt_matieres`. Le prompt qui s'y trouve a ete redige a partir du BTS CIEL option A — il aurait
donc lu le BTS CRSA avec les reperes du CIEL. Un cycle n'est pas une famille de documents batis
pareil : c'est juste un tiroir de l'arbre.

La bonne cle, c'est le COUPLE cycle + niveau. Il existe deja : `referentiels`, une ligne par
couple (`uq_referentiels_niveau`), et cette ligne porte DEJA `prompt_decoupe` /
`prompt_decoupe_valide`. Les donnees que ces prompts produisent — `matieres`, `types_activite`,
`referentiel_chunks` — pointent deja sur `referentiel_id`. La recette rejoint donc son resultat.

Ce que fait cette migration, et RIEN de plus :
  - ajoute `referentiels.prompt_matieres` / `prompt_matieres_valide` ;
  - ajoute `referentiels.prompt_types` / `prompt_types_valide`.

Ce qu'elle NE fait PAS, volontairement :
  - elle ne recopie AUCUNE valeur depuis `cycles` : le prompt du cycle BTS a ete ecrit pour le
    CIEL, le descendre d'office sur les 18 niveaux referait l'erreur qu'on corrige ;
  - elle ne SUPPRIME PAS les colonnes de `cycles` : le code les lit encore. Elles partiront quand
    il aura fini de basculer, dans une migration a elle.

Revision ID: a1f3d7b5c2e8
Revises: fb2d6e8a4c19
Create Date: 2026-08-06
"""
from alembic import op
import sqlalchemy as sa

revision = "a1f3d7b5c2e8"
down_revision = "fb2d6e8a4c19"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("prompt_matieres", sa.Text(), nullable=True))
    op.add_column("referentiels", sa.Column("prompt_matieres_valide", sa.Boolean(),
                                            nullable=False, server_default=sa.text("false")))
    op.add_column("referentiels", sa.Column("prompt_types", sa.Text(), nullable=True))
    op.add_column("referentiels", sa.Column("prompt_types_valide", sa.Boolean(),
                                            nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    op.drop_column("referentiels", "prompt_types_valide")
    op.drop_column("referentiels", "prompt_types")
    op.drop_column("referentiels", "prompt_matieres_valide")
    op.drop_column("referentiels", "prompt_matieres")
