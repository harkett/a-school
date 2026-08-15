# -*- coding: utf-8 -*-
"""Une note au carnet : comment tester la surveillance des connexions

POURQUOI ELLE EXISTE. La surveillance des connexions est livrée et prouvée par ses tests, mais
personne ne l'a encore vue tourner à l'écran. Une procédure gardée dans une conversation se perd ;
gardée ici, elle attend qu'on ait le temps.

POURQUOI EN MIGRATION. Comme les autres notes : une ligne ajoutée à la main en développement ne
suit pas jusqu'au serveur, et c'est précisément là que ce test-là comptera — l'alerte « connexions
éloignées » ne PEUT PAS être vérifiée en local, toutes les sessions y venant du même réseau.

downgrade : retire la note.

Revision ID: c8f2a6d4e9b1
Revises: b7e3c5a9d2f4
Create Date: 2026-08-15
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "c8f2a6d4e9b1"
down_revision: Union[str, Sequence[str], None] = "b7e3c5a9d2f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TITRE = "Tester la surveillance des connexions"

DETAIL = """LA PROCÉDURE, ÉTAPE PAR ÉTAPE.

1. Supervision → Alertes. Le bouton « Seuils », en haut à droite, ouvre les sept valeurs qui déclenchent les alertes.

2. Baisser « Appareils simultanés tolérés par compte » à 1, puis Valider.

3. Se connecter côté prof depuis DEUX navigateurs différents — Chrome et Firefox par exemple. Deux navigateurs distincts font deux appareils ; deux onglets du même navigateur n'en font qu'un, c'est voulu.

4. Système → Planificateur → « Surveillance du serveur » → « Exécuter maintenant ». C'est exactement le chemin qu'emprunte le passage automatique de toutes les 5 minutes : ce qu'on voit là est ce qui se produira tout seul.

5. Revenir sur Supervision → Alertes. L'alerte « Compte utilisé sur plusieurs postes » doit apparaître, avec le courriel du professeur, le nombre d'appareils mesuré, le seuil, et un lien « Aller voir » qui mène à l'écran des Sessions.

6. Vérifier que RIEN N'A ÉTÉ FERMÉ : les deux navigateurs doivent toujours être connectés. C'est le principe posé le 15/08/2026 — surveiller, ne pas interdire.

7. Remettre le seuil à 4.

CE QUI NE SE TESTE PAS EN LOCAL : l'alerte « Connexions géographiquement éloignées ». Toutes les sessions de développement viennent du même réseau, il n'y a aucune distance à mesurer et aucune ville derrière une adresse privée. Elle ne pourra être vérifiée qu'une fois déployée, avec deux connexions réellement distantes.

À VÉRIFIER AUSSI APRÈS LE DÉPLOIEMENT : que les adresses IP remontent vraiment. Les services systemd ont reçu « --proxy-headers » ; sans lui l'application voyait l'adresse de nginx pour tout le monde, et le lieu d'une connexion ne voulait rien dire."""


def upgrade() -> None:
    op.execute(
        sa.text("INSERT INTO taches_a_faire (titre, detail) VALUES (:titre, :detail)")
        .bindparams(titre=TITRE, detail=DETAIL)
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM taches_a_faire WHERE titre = :titre").bindparams(titre=TITRE)
    )
