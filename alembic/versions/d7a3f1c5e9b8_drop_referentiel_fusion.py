"""Retire la FUSION des documents : outil LLM, reglages et prompt, partis avec le labo.

10/08/2026, suite de `c4e8a2f7b1d6`. La fusion assemblait plusieurs PDF en un seul referentiel.
Elle n'existait qu'au labo (`referentiels_labo.py`), supprime le meme jour : plus une ligne de
code ne lit ces valeurs, mais l'ecran d'administration continuait de les PROPOSER au reglage.

CE QUI PART, ET POURQUOI CHACUN :
  • `outils_llm.referentiel_fusion` — l'ecran « max tokens » le listait ; un admin aurait regle
    une borne que personne ne lit. C'est exactement le defaut que `test_aucune_ligne_orpheline`
    surveille, et c'est lui qui l'a signale.
  • `settings.max_tokens_referentiel_fusion` — la borne elle-meme.
  • `settings.fusion_max_pages` — le nombre de pages vise pour le document fusionne.
  • `settings.prompt_referentiel_fusion` — le texte du prompt, seede par une migration
    anterieure. Sa constante `PROMPT_REFERENTIEL_FUSION` et son entree au registre
    (`llm_prompts.py`) partent dans le meme geste.

CE QUI RESTE INTACT : les lignes d'`usage_llm` deja ecrites avec `outil = 'referentiel_fusion'`.
Elles racontent des appels qui ont vraiment eu lieu et qui ont vraiment coute — les effacer
fausserait l'historique de facturation. L'ecran des statistiques affichera le code brut faute de
libelle, ce qui est la verite : l'outil n'existe plus.

Revision ID: d7a3f1c5e9b8
Revises: c4e8a2f7b1d6
Create Date: 2026-08-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7a3f1c5e9b8'
down_revision: Union[str, Sequence[str], None] = 'c4e8a2f7b1d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Lus par les tests et par conftest.py, qui rejouent la chaine des migrations sans l'appliquer :
# une migration qui SEME s'annonce par `OUTILS` / `PROMPTS_MAJ`, une qui RETIRE par les deux
# constantes ci-dessous. Sans elles, la base de test recevrait eternellement une ligne que la
# prod n'a plus, et les filets accuseraient le code au lieu du seed.
OUTILS_RETIRES = ["referentiel_fusion"]
PROMPTS_RETIRES = ["referentiel_fusion"]

_CLES = ("max_tokens_referentiel_fusion", "fusion_max_pages", "prompt_referentiel_fusion")


def upgrade() -> None:
    op.execute(
        sa.text("DELETE FROM outils_llm WHERE outil = ANY(:o)").bindparams(
            sa.bindparam("o", value=OUTILS_RETIRES, type_=sa.ARRAY(sa.String()))
        )
    )
    op.execute(
        sa.text("DELETE FROM settings WHERE key = ANY(:c)").bindparams(
            sa.bindparam("c", value=list(_CLES), type_=sa.ARRAY(sa.String()))
        )
    )


def downgrade() -> None:
    # L'outil se recree ; les reglages, non. Un `max_tokens` ou un plafond de pages sont des
    # valeurs CHOISIES par l'admin : les reinventer ici poserait un chiffre que personne n'a
    # decide. L'ecran les recreera au premier reglage, comme pour tout outil neuf.
    op.execute(
        "INSERT INTO outils_llm (outil, libelle, aide, ordre) VALUES "
        "('referentiel_fusion', 'Fusion des documents d''un référentiel', "
        "'Tire UN seul référentiel des PDF déposés pour un couple.', 100) "
        "ON CONFLICT (outil) DO NOTHING"
    )
