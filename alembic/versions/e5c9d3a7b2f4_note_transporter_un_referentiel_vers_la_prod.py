# -*- coding: utf-8 -*-
"""Une note au carnet : transporter un référentiel du poste vers la production

POURQUOI ELLE EXISTE. Un référentiel se construit sur le poste — la procédure est longue, elle
demande des allers-retours, et on ne veut pas la refaire une seconde fois en production. Or un
déploiement porte le CODE et la STRUCTURE de la base, jamais son contenu : le référentiel reste
donc sur le poste. Constaté le 16/08/2026 sur le référentiel Collège (5e, 4e, 3e), absent du
serveur après un déploiement pourtant complet.

downgrade : retire la note.

Revision ID: e5c9d3a7b2f4
Revises: d4a8b2f6c9e3
Create Date: 2026-08-16
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "e5c9d3a7b2f4"
down_revision: Union[str, Sequence[str], None] = "d4a8b2f6c9e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TITRE = "Transporter un référentiel du poste vers la production"

DETAIL = """LE BESOIN. Les référentiels se construisent sur le poste, jamais en production : la procédure est longue et se reprend en plusieurs fois. Une fois terminée, il faut porter le résultat sur le serveur — sans la refaire.

POURQUOI ÇA NE SE FAIT PAS TOUT SEUL. Un déploiement porte le CODE et la STRUCTURE de la base (les migrations ajoutent des colonnes, des tables). Il ne transporte AUCUNE donnée. Le poste et le serveur ont deux bases distinctes qui ne se croisent jamais. Constaté le 16/08/2026 : le référentiel Collège était absent du serveur après un déploiement pourtant complet — le code et les colonnes étaient bien arrivés, la ligne non.

LE PIÈGE À NE SURTOUT PAS PRENDRE : `deploy/restaurer-bases.sh` transporte bien des données, mais il ÉCRASE la base du serveur en entier — les comptes des professeurs inscrits avec. Son propre en-tête le disait : « la base réelle du VPS n'a jamais servi ; le jour où ce ne sera plus vrai, ce script devra changer. » Ce jour est arrivé, il y a de vrais inscrits en production.

CE QU'IL FAUT ÉCRIRE : un transport CIBLÉ, un référentiel à la fois, qui ne touche à rien d'autre. Mesuré sur le référentiel Collège (id 21), voici ce qui doit voyager avec lui :
  - `referentiels` : la ligne elle-même (le document, ses prompts, ses drapeaux de validation)
  - `referentiel_niveaux` : 3 lignes (les niveaux desservis)
  - `referentiel_chunks` : 158 lignes AVEC leurs vecteurs
  - `matieres` : 13 lignes
  - `types_activite` : 25 lignes, et les précisions qui leur sont rattachées

CE QUE ÇA NE COÛTE PAS : aucun appel d'IA. Les unités sont déjà vectorisées sur le poste, on recopie les vecteurs tels quels. C'est le point qui rend l'opération intéressante — refaire la procédure en production coûterait du temps ET des appels payants.

DEUX POINTS À TRANCHER EN L'ÉCRIVANT :
  1. les identifiants. Le référentiel porte l'id 21 sur le poste ; rien ne garantit qu'il soit libre en production. Le transport doit soit réattribuer les identifiants et refaire les liens, soit refuser proprement si l'identifiant est pris — jamais écraser en silence une ligne qui existe.
  2. le rejeu. Transporter deux fois le même référentiel ne doit pas le dupliquer. Prévoir le cas dès le départ : c'est la première chose qu'on fera après une erreur.

À PRÉVOIR AUSSI : le PDF du référentiel vit hors base, dans `REFERENTIELS/`, qui n'est pas dans le dépôt. Il voyage séparément."""


def upgrade() -> None:
    op.execute(
        sa.text("INSERT INTO taches_a_faire (titre, detail) VALUES (:titre, :detail)")
        .bindparams(titre=TITRE, detail=DETAIL)
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM taches_a_faire WHERE titre = :titre").bindparams(titre=TITRE)
    )
