# -*- coding: utf-8 -*-
"""Une note au carnet : l'adresse d'envoi doit changer pour que DKIM soit possible

POURQUOI EN MIGRATION plutôt que saisie à l'écran. C'est la même raison que pour les trois
premières notes : une note ajoutée à la main en développement ne suit pas jusqu'au serveur, et
c'est justement là qu'on la relira. Le carnet ne sert qu'à condition de survivre au déploiement.

CE QU'ELLE RETIENT. Le problème n'est pas « activer DKIM » — c'est que l'adresse actuelle ne le
permet pas. La nuance se perd en trois mois, et on repart chercher une case à cocher qui n'existe
pas.

LE TEXTE PASSE PAR UN PARAMÈTRE, jamais par concaténation : il contient des apostrophes et des
retours à la ligne, et un texte recollé à la main dans du SQL finit toujours par casser sur l'un
des deux.

downgrade : retire la note.

Revision ID: a4d8f2b6c1e3
Revises: d2b6f9c3a7e1
Create Date: 2026-08-15
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "a4d8f2b6c1e3"
down_revision: Union[str, Sequence[str], None] = "d2b6f9c3a7e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TITRE = "Adresse d'envoi : passer sur une boîte qui accepte DKIM"

DETAIL = """LE VRAI PROBLÈME. Les mails partent aujourd'hui de contact@aschool.fr, l'adresse gratuite fournie avec le nom de domaine. Cette formule n'autorise pas la configuration DKIM : les messages ne peuvent pas être signés, donc ni Outlook ni Gmail ne peuvent vérifier qu'ils viennent de nous, et ils tombent en indésirables. Ce n'est donc pas une case à cocher — il faut une vraie boîte payante chez Infomaniak.

CE QU'ON VEUT GARDER : l'adresse affichée, contact@aschool.fr. Deux chemins possibles. Soit libérer la gratuite (la renommer ou la supprimer) puis recréer le même nom sur la boîte payante. Soit prendre un autre nom et poser contact@aschool.fr en ALIAS dessus. Les anciennes adresses peuvent rester en alias sur la nouvelle boîte.

LE PIÈGE À NE PAS OUBLIER : les identifiants SMTP changent avec la boîte. Il faut reporter SMTP_USERNAME et SMTP_PASSWORD dans le .env LOCAL et sur le SERVEUR, et vérifier que SMTP_FROM désigne bien le compte qui envoie. Un désalignement entre les deux fait retomber les mails en indésirables — et un identifiant oublié fait qu'aucun mail ne part du tout.

ÉCRANS CONCERNÉS : inscription, renvoi de lien, bienvenue, mail groupé, alertes de surveillance."""


def upgrade() -> None:
    op.execute(
        sa.text("INSERT INTO taches_a_faire (titre, detail) VALUES (:titre, :detail)")
        .bindparams(titre=TITRE, detail=DETAIL)
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM taches_a_faire WHERE titre = :titre").bindparams(titre=TITRE)
    )
