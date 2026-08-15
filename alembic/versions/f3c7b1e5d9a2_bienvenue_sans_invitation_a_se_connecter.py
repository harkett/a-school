# -*- coding: utf-8 -*-
"""Le mail de bienvenue n'invite plus à se connecter — le professeur l'est déjà

LE DÉFAUT. Ce courriel part à l'instant précis où le compte s'ouvre, et depuis ce jour le clic
sur le lien d'activation ouvre aussi la session : le destinataire est DANS l'application quand il
le reçoit. « Connectez-vous dès maintenant sur aschool.fr » lui demande d'y entrer une seconde
fois. Le gros bouton d'entrée est parti du gabarit (backend/securite/comptes.py) ; restait la
phrase, qui vit en base.

CE QUE LA PHRASE DEVIENT. Ce qu'un mot de bienvenue doit dire : ce qu'on peut faire maintenant,
et où. Pas une porte — il n'y a plus de porte à ouvrir.

REMPLACEMENT PRUDENT. Seules les lignes dont le corps porte ENCORE la phrase d'origine sont
touchées : si l'administrateur a réécrit son texte depuis l'écran « Système → Email », c'est le
sien qui gagne — la base gagne toujours sur le code.

downgrade : remet la phrase d'origine, aux mêmes conditions.

Revision ID: f3c7b1e5d9a2
Revises: e2b6d4f8a1c5
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op


revision: str = "f3c7b1e5d9a2"
down_revision: Union[str, Sequence[str], None] = "e2b6d4f8a1c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Les deux orthographes qui existent en base : celle semée sans accents, celle du code.
ANCIENNES = (
    "Connectez-vous des maintenant sur aschool.fr",
    "Connectez-vous dès maintenant sur aschool.fr",
)
NOUVELLE = "Votre espace vous attend : votre matiere, votre niveau, et vos premieres activites."


def _remplacer(depuis: tuple, vers: str) -> None:
    for ancienne in depuis:
        op.execute(
            f"""
            UPDATE email_templates
               SET corps = REPLACE(corps, '{ancienne}', '{vers}')
             WHERE slug = 'welcome' AND corps LIKE '%{ancienne}%'
            """
        )


def upgrade() -> None:
    _remplacer(ANCIENNES, NOUVELLE)


def downgrade() -> None:
    _remplacer((NOUVELLE,), ANCIENNES[0])
