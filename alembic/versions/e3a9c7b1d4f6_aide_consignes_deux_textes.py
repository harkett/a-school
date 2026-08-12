# -*- coding: utf-8 -*-
"""« Mes analyses -> Consignes » porte deux textes, sa phrase n'en annoncait qu'un

CONSTAT du 12/08/2026, en relisant l'ecran Admin -> IA -> Prompts. La rubrique « Mes analyses ->
Consignes » decrit ce que l'admin va trouver en cliquant dessus. Elle disait « Le texte qui relit
la consigne du professeur... » — au singulier, ce qui etait juste tant qu'il n'y en avait qu'un.
Depuis c5e1a9d7b3f4, elle en porte deux : l'analyse, et celui qui ECRIT la consigne d'exemple.

Sa jumelle « Mes analyses -> Ambiguites » avait recu le meme soin le jour ou son second texte est
arrive (« Le texte qui ANALYSE l'enonce du prof, et celui qui ECRIT son enonce d'exemple. »).
Cette migration met les deux rubriques au meme niveau — meme tournure, meme promesse.

downgrade : remet la phrase d'avant, mot pour mot.

Revision ID: e3a9c7b1d4f6
Revises: d1f5b8c3e7a2
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3a9c7b1d4f6"
down_revision: Union[str, Sequence[str], None] = "d1f5b8c3e7a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CODE = "analyse_consigne"
AVANT = "Le texte qui relit la consigne du professeur et en juge la qualité didactique."
APRES = ("Le texte qui ANALYSE la consigne du prof et en juge la qualité didactique, "
         "et celui qui ÉCRIT sa consigne d'exemple.")


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("UPDATE prompt_fonctionnalites SET aide = :apres WHERE code = :code AND aide = :avant"),
        {"apres": APRES, "avant": AVANT, "code": CODE},
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("UPDATE prompt_fonctionnalites SET aide = :avant WHERE code = :code AND aide = :apres"),
        {"apres": APRES, "avant": AVANT, "code": CODE},
    )
