# -*- coding: utf-8 -*-
"""Les niveaux qu'un référentiel dessert — et le cycle 4 rendu à ses trois années

LE DÉFAUT. Un programme de CYCLE est un seul document pour plusieurs années. Le référentiel du
cycle 4 (id 21) n'était rattaché qu'à la 4e : les profs de 5e et de 3e n'avaient AUCUN référentiel,
donc aucune génération ancrée — `_referentiel_du_niveau` leur rendait None, et l'application
répondait « available: false » sans que rien ne dise pourquoi.

PAS UN RATTACHEMENT AU CYCLE, et c'est le point qu'on ne voit qu'en regardant la base : le cycle
« Collège » porte 6e, 5e, 4e ET 3e, alors que le cycle 4 du BOEN commence en 5e. Rattacher au cycle
donnerait le programme du cycle 4 aux profs de 6e. La liste est donc EXPLICITE, jamais déduite.

CE QUE FAIT CETTE MIGRATION.
  1. Crée `referentiel_niveaux`, avec UNIQUE(niveau_id) : un niveau n'est desservi que par UN
     référentiel. Cette contrainte-là est PLUS FORTE que `uq_referentiels_niveau`, qui ne regarde
     que le niveau porteur — c'est elle qui porte désormais l'invariant.
  2. Sème une ligne par référentiel existant, depuis son `niveau_id` : rien ne change pour les
     cinq référentiels d'un seul niveau, qui se retrouvent rattachés exactement à ce qu'ils
     servaient déjà.
  3. Rattache le référentiel du cycle 4 à ses DEUX autres années. Le rattachement se lit par le
     CYCLE du niveau porteur et par les niveaux réellement présents en base — jamais par un id
     écrit en dur, qui ne voudrait rien dire dans une base neuve ou dans un schéma de démo.

`uq_referentiels_niveau` N'EST PAS RETIRÉE. Elle ne bloquait pas le service de plusieurs niveaux —
c'est l'absence de table de liaison qui le bloquait. Elle garde un sens propre : deux référentiels
ne peuvent pas se ranger dans le même dossier de PDF (`REFERENTIELS/<CYCLE>/<NIVEAU>/`).

IL N'Y A AUCUN ÉCRAN pour remplir cette table (dette assumée le 15/08/2026 : ne pas mêler une
réparation de bug et une fonctionnalité neuve). Le prochain référentiel de cycle demandera soit une
migration écrite à la main, soit la construction de ce geste dans Admin → Référentiels.

downgrade : supprime la table. `referentiels.niveau_id` n'a pas bougé, rien n'est perdu.

Revision ID: b8d3f1a6c9e4
Revises: f7a3d9e1c5b8
Create Date: 2026-08-15
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "b8d3f1a6c9e4"
down_revision: Union[str, Sequence[str], None] = "f7a3d9e1c5b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Le cycle 4 se reconnaît à ce qu'il EST : un référentiel dont le niveau porteur a des voisins
# nommés ainsi dans le même cycle. Les noms viennent de la table `niveaux`, pas d'un id.
CYCLE_4 = ("5e", "4e", "3e")


def upgrade() -> None:
    op.create_table(
        "referentiel_niveaux",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("referentiel_id", sa.Integer(),
                  sa.ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("niveau_id", sa.Integer(), sa.ForeignKey("niveaux.id"), nullable=False),
        sa.UniqueConstraint("niveau_id", name="uq_referentiel_niveaux_niveau"),
    )
    # 1. Chaque référentiel dessert d'abord le niveau qu'il servait déjà.
    op.execute(
        "INSERT INTO referentiel_niveaux (referentiel_id, niveau_id) "
        "SELECT id, niveau_id FROM referentiels"
    )
    # 2. Le référentiel dont le niveau porteur est une année du cycle 4 dessert AUSSI les deux
    #    autres — à condition qu'elles n'aient pas déjà leur propre référentiel (UNIQUE(niveau_id)
    #    refuserait, et à raison : un niveau qui a son document ne se fait pas servir par un autre).
    noms = ", ".join(f"'{n}'" for n in CYCLE_4)
    op.execute(
        f"""
        INSERT INTO referentiel_niveaux (referentiel_id, niveau_id)
        -- DISTINCT ON : si DEUX années du cycle avaient chacune leur référentiel, elles se
        -- disputeraient la troisième et l'insertion violerait UNIQUE(niveau_id). Le plus petit
        -- id gagne — arbitraire mais déterministe, et la migration ne casse pas.
        SELECT DISTINCT ON (autre.id) r.id, autre.id
          FROM referentiels r
          JOIN niveaux porteur ON porteur.id = r.niveau_id
          JOIN niveaux autre   ON autre.cycle_id = porteur.cycle_id
         WHERE porteur.nom IN ({noms})
           AND autre.nom   IN ({noms})
           AND autre.id <> porteur.id
           AND autre.id NOT IN (SELECT niveau_id FROM referentiel_niveaux)
         ORDER BY autre.id, r.id
        """
    )


def downgrade() -> None:
    op.drop_table("referentiel_niveaux")
