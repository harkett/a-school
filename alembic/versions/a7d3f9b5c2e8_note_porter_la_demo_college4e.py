# -*- coding: utf-8 -*-
"""Une note au carnet : porter la démonstration Collège 4e en production

CONSTATÉ LE 16/08/2026. La démonstration Collège 4e — 39 séquences, 168 activités — vit dans le
schéma `college4e` du poste. Le serveur n'en a que cinq : elle n'a jamais traversé, et elle ne
traversera pas toute seule (un déploiement porte le code et la structure, jamais les données).

CE QUI EST DÉJÀ FAIT : sa ligne est posée dans `deploy/demos.conf`, donc le prochain
`installer-demos.sh` lui donnera son certificat, son aiguillage nginx et la mise à jour de son
schéma. Il ne manque que le CONTENU.

downgrade : retire la note.

Revision ID: a7d3f9b5c2e8
Revises: f6a2c8e4b1d7
Create Date: 2026-08-16
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "a7d3f9b5c2e8"
down_revision: Union[str, Sequence[str], None] = "f6a2c8e4b1d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TITRE = "Porter la démonstration Collège 4e en production"

DETAIL = """CE QUI MANQUE : le contenu. Le schéma `college4e` (39 séquences, 168 activités) est sur le poste, pas sur le serveur. Sa ligne est déjà dans `deploy/demos.conf` — le prochain `installer-demos.sh` posera le certificat, l'aiguillage nginx et la mise à jour du schéma, mais il ne remplit rien.

AUCUN OUTIL À ÉCRIRE. Une démonstration est un schéma entier et isolé : PostgreSQL sait l'extraire et le reposer ailleurs. Trois commandes.

1. SUR LE POSTE — extraire le schéma :
   docker compose exec -T db pg_dump -U aschool -d aschool_demos -n college4e > college4e.sql

2. LE PORTER sur le serveur (scp, ou tout autre moyen).

3. SUR LE SERVEUR — le verser dans la base des démonstrations :
   psql -d aschool_demos -f college4e.sql

LE PIÈGE, DÉJÀ RENCONTRÉ EN PRODUCTION LE 11/08/2026, sur les cinq démonstrations à la fois : un schéma versé par `pg_dump` appartient au rôle qui a lancé le versement. Versé en `postgres`, il reste invisible pour l'application, qui se connecte sous un autre rôle — et le serveur répond 404 sur une démonstration parfaitement présente. Il faut donc verser sous le rôle de l'application (`aschool`), ou reprendre la propriété après coup :
   ALTER SCHEMA college4e OWNER TO aschool;
   puis chaque table, séquence et index du schéma.
La lecture de `schema_existe` (backend/core/schema_requete.py) explique pourquoi le symptôme est un 404 muet et pas une erreur.

APRÈS LE VERSEMENT : relancer `bash deploy/installer-demos.sh`. Il mettra le schéma à `head` (l'étape ajoutée le 15/08) et vérifiera que `demo-college4e.aschool.fr` répond vraiment — c'est ce contrôle qui dira si la propriété du schéma est la bonne.

À VÉRIFIER AUSSI : la ligne de `demos` en production porte une adresse locale (`http://localhost:8096`). Elle sert l'écran d'administration, pas le routage — mais elle ment sur le serveur."""


def upgrade() -> None:
    op.execute(
        sa.text("INSERT INTO taches_a_faire (titre, detail) VALUES (:titre, :detail)")
        .bindparams(titre=TITRE, detail=DETAIL)
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM taches_a_faire WHERE titre = :titre").bindparams(titre=TITRE)
    )
