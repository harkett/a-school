"""Retire les reglages `max_tokens_*` de `settings` : l'ecran des longueurs n'existe plus.

10/08/2026. CE QU'ILS ETAIENT. Un defaut global (`max_tokens_default`) et une surcharge par outil
(`max_tokens_<outil>`), regles depuis l'onglet « Longueur (tokens) » de Systeme > Generation.

POURQUOI ILS PARTENT. Le moteur ne les lit PLUS depuis la refonte du 05/08 : `get_max_tokens()`
rend le `max_tokens` de la fiche du modele en service (sinon celui de son fournisseur, sinon le
filet `MAX_TOKENS_SANS_FICHE`). Les lignes restaient en base et l'ecran continuait de les ecrire.
Le constat qui l'a montre : la base annoncait un defaut de 320 000 et 5 000 pour `decoupe_amont`,
alors que le moteur appliquait 4 096 — le filet, faute de fiche renseignee pour le modele en
service. L'admin reglait un couperet fictif et croyait l'avoir regle.

C'est exactement l'histoire de `max_tokens_optimiseur` (migration b6d1f4a8c2e7), a une echelle
plus grande : une valeur proposee au reglage que plus rien ne relit.

CE QUI PART AVEC : les deux routes `GET`/`PUT /api/admin/max-tokens`, leur formulaire (dont
l'entree d'onglet avait deja disparu du front) et la borne `MAX_TOKENS_MIN`.

OU SE REGLE LA LONGUEUR MAINTENANT : IA > Fournisseurs & modeles, champ `max_tokens` de la fiche.
C'est ce que le service ACCEPTE d'ecrire, pas un souhait — et c'est la seule valeur qui agisse.

Revision ID: e2b6d4a8f7c1
Revises: d7a3f1c5e9b8
Create Date: 2026-08-10
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e2b6d4a8f7c1'
down_revision: Union[str, Sequence[str], None] = 'd7a3f1c5e9b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM settings WHERE key LIKE 'max_tokens\\_%'")


def downgrade() -> None:
    """Rien a remettre, et c'est voulu.

    Ces lignes portaient des chiffres CHOISIS par l'admin. En reinventer ici poserait des valeurs
    que personne n'a decidees — et surtout : plus une ligne de code ne les lirait de toute facon,
    puisque le downgrade ne ressuscite pas l'ecran. Le schema, lui, est identique dans les deux
    sens : `settings` est une table cle/valeur, aucune colonne ne bouge."""
