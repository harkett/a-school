# -*- coding: utf-8 -*-
"""aligne les noms d'index sur les modeles + retire l'index redondant de cahiers_prof

POURQUOI. `alembic check` sortait en FAILED sur 9 operations reparties sur 3 tables. Rien
n'etait casse fonctionnellement — memes colonnes, memes garanties — mais tant que la
comparaison echoue, elle ne peut plus servir de garde-fou : la PROCHAINE derive se serait
cachee derriere celle-ci. C'est ca qu'on repare, pas les index eux-memes, qui sont bons.

D'OU VIENNENT LES NOMS COURTS. Ils n'ont pas ete choisis, ils sont PERIMES. La migration
c3d4e5f6a7b8 (16/07/2026) a renomme la table `referentiel_activite_types` en
`referentiel_types_activite` ; or `ALTER TABLE ... RENAME` de PostgreSQL NE RENOMME PAS les
index — ni la PK, ni les cles etrangeres. Son propre docstring l'acte : « rename_table
conserve [...] les index (ix_ref_activite_types_*) [...] et les deux cles etrangeres ». Les
noms portent donc l'ANCIEN nom de table. La preuve la plus lisible n'etait meme pas dans le
diff d'alembic (qui ne compare pas les noms de PK) : la cle primaire s'appelait
`referentiel_activite_types_pkey` sur une table nommee `referentiel_types_activite`. Personne
ne choisit ca. Les deux cles etrangeres etaient dans le meme cas.

On repare donc les CINQ residus de ce renommage (2 index, la PK, 2 cles etrangeres), pas
seulement les DEUX qu'alembic sait voir : laisser les trois autres reviendrait a garder la
trace la plus visible du desordre sous pretexte que l'outil est aveugle dessus.

Ce n'etait pas non plus la limite des 63 caracteres de PostgreSQL : le plus long nom cible
fait 59 caracteres, les autres 46 et 44. Rien n'etait force. On aligne donc la BASE sur les
MODELES, et non l'inverse — l'inverse aurait grave un accident du 16/07 comme une intention,
a relire a chaque passage dans models_db.py.

Cas a part : `ix_ref_type_precisions_lien` (e7f8a9b0c1d2) n'est pas perime — il a ete ecrit a
la main sur une table qui portait deja son nom actuel, en abregeant la colonne en « lien ».
C'est une abreviation deliberee, mais d'un nom qui tenait de toute facon, et c'est le seul
index du depot a ne pas suivre la convention. Il rentre dans le rang.

LE DOUBLON DE cahiers_prof. En PostgreSQL une UNIQUE CONSTRAINT **est** un index unique —
c'est son implementation, pas un objet a cote. Il y avait donc DEUX btree sur
cahiers_prof(user_id) : `uq_cahiers_prof_user_id` (unique) et `ix_cahiers_prof_user_id`
(simple). Meme colonne, meme ordre, meme methode : le simple ne peut servir aucune requete
que l'unique ne serve deja, et coute une seconde ecriture a chaque depot de cahier pour zero
garantie supplementaire. Le modele (models_db.py:47) declare `unique=True, index=True`, soit
UN SEUL index unique. On se range sur le modele.

ORDRE ET SURETE. Les quatre renommages sont du catalogue pur (ALTER INDEX ... RENAME TO ne
touche que pg_class : aucune relecture de donnees, aucune reecriture, verrou pris et rendu en
microsecondes). Le seul pas qui lit des donnees est le CREATE UNIQUE INDEX sur cahiers_prof,
table a UNE ligne par prof. Il est place AVANT le retrait de la contrainte, pour que
l'unicite ne soit jamais decouverte, meme une milliseconde. Si un doublon existait, le CREATE
UNIQUE INDEX echoue, la migration se replie dans sa transaction et le deploiement s'arrete
avec l'ancienne contrainte toujours en place : le mode d'echec est sur.

Revision ID: a5e9c3b7f1d2
Revises: f2e3d4c5b6a7
Create Date: 2026-08-02
"""
from typing import Sequence, Union

from alembic import op


revision: str = "a5e9c3b7f1d2"
down_revision: Union[str, Sequence[str], None] = "f2e3d4c5b6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (nom porte par la base, nom declare par les modeles) — alembic n'a pas d'operation
# `rename_index`, on passe donc par le SQL, qui dit exactement ce qui se passe.
RENOMMAGES = [
    ("ix_ref_activite_types_referentiel_id",   "ix_referentiel_types_activite_referentiel_id"),
    ("ix_ref_activite_types_activite_type_id", "ix_referentiel_types_activite_activite_type_id"),
    ("ix_ref_type_precisions_lien",            "ix_referentiel_type_precisions_referentiel_activite_type_id"),
    # Celui-ci, alembic ne le compare pas — on le renomme quand meme : c'est le meme residu du
    # 16/07, et le laisser reviendrait a garder la trace la plus visible du desordre sous
    # pretexte que l'outil est aveugle dessus. Renommer l'index d'une PK renomme aussi la
    # contrainte : PostgreSQL les tient par le meme nom.
    ("referentiel_activite_types_pkey",        "referentiel_types_activite_pkey"),
]

# Les DEUX cles etrangeres de la meme table portent elles aussi l'ancien nom. Alembic est
# aveugle dessus aussi (les modeles ne les nomment pas, il ne compare donc pas leur nom) — on
# les renomme pour la meme raison que la PK : meme accident du 16/07, et rien d'autre ne les
# rattrapera jamais. Une FK n'a pas d'index propre, d'ou RENAME CONSTRAINT et non ALTER INDEX.
#
# NE PAS y ajouter `uq_ref_activite_type` ni `uq_ref_type_precisions_lien_libelle` : ceux-la
# sont nommes explicitement dans les modeles (models_db.py:749 et 776). C'est un choix, pas un
# residu, et la base dit deja exactement ce que le modele declare.
RENOMMAGES_CONTRAINTES = [
    ("referentiel_types_activite",
     "referentiel_activite_types_referentiel_id_fkey",   "referentiel_types_activite_referentiel_id_fkey"),
    ("referentiel_types_activite",
     "referentiel_activite_types_activite_type_id_fkey", "referentiel_types_activite_activite_type_id_fkey"),
]


def upgrade() -> None:
    for ancien, nouveau in RENOMMAGES:
        op.execute(f'ALTER INDEX "{ancien}" RENAME TO "{nouveau}"')
    for table, ancien, nouveau in RENOMMAGES_CONTRAINTES:
        op.execute(f'ALTER TABLE {table} RENAME CONSTRAINT "{ancien}" TO "{nouveau}"')

    # cahiers_prof : de (index simple + contrainte unique) a (un seul index unique).
    op.execute('DROP INDEX "ix_cahiers_prof_user_id"')                 # le redondant s'en va d'abord…
    op.execute('CREATE UNIQUE INDEX "ix_cahiers_prof_user_id" ON cahiers_prof (user_id)')
    op.execute('ALTER TABLE cahiers_prof DROP CONSTRAINT "uq_cahiers_prof_user_id"')  # …et l'unicite n'a jamais ete seule


def downgrade() -> None:
    # Symetrique exact : la contrainte revient AVANT que l'index unique parte.
    op.execute('ALTER TABLE cahiers_prof ADD CONSTRAINT "uq_cahiers_prof_user_id" UNIQUE (user_id)')
    op.execute('DROP INDEX "ix_cahiers_prof_user_id"')
    op.execute('CREATE INDEX "ix_cahiers_prof_user_id" ON cahiers_prof (user_id)')

    for table, ancien, nouveau in reversed(RENOMMAGES_CONTRAINTES):
        op.execute(f'ALTER TABLE {table} RENAME CONSTRAINT "{nouveau}" TO "{ancien}"')
    for ancien, nouveau in reversed(RENOMMAGES):
        op.execute(f'ALTER INDEX "{nouveau}" RENAME TO "{ancien}"')
