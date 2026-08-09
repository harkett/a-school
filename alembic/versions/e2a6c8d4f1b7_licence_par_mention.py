# -*- coding: utf-8 -*-
"""Licence : les onze MENTIONS remplacent les niveaux-années L1/L2/L3.

La décision était déjà prise et migrée (bb22cc33dd44, « Licence par SPÉCIALITÉ ») : dans tout le
Supérieur, c'est la spécialité qui porte le référentiel, pas l'année. Mais son garde-fou a
épargné L1/L2/L3 — ils tenaient encore à des paires matière×niveau du seed, table depuis
disparue —, et ces trois niveaux-années sont restés seuls de leur espèce.

Cette migration termine le travail et va un pas plus loin : là où bb22cc33dd44 laissait à l'admin
le soin de créer chaque mention à la main, on les SÈME, comme le seed d'origine l'a fait pour le
BTS, le BUT, le Master et le Doctorat. Un cycle vide n'est pas utilisable : l'admin devait deviner
la liste avant de pouvoir déposer quoi que ce soit.

LES ONZE. Les dix mentions les plus représentées en France par les effectifs, plus l'ergothérapie
demandée pour un besoin propre. Neuf d'entre elles ont déjà leur Master en face dans le seed
d'origine — le parcours licence → master se lit d'un cycle à l'autre.

CE QU'ELLE NE FAIT PAS. Aucun référentiel, aucune matière, aucun prompt : une mention naît vide,
et se remplit par le dépôt de son PDF depuis Admin → Référentiels, comme le BTS CIEL.

GARDE-FOU (contrôle avant DELETE). On ne retire un niveau-année que si RIEN ne s'y rattache :
ni référentiel, ni document déposé, ni utilisateur. Un environnement où quelqu'un aurait bâti sur
L1/L2/L3 les garde intacts, et la migration passe sans rien casser — elle ajoute alors seulement
les mentions.

Revision ID: e2a6c8d4f1b7
Revises: d7c1e9a4b502
Create Date: 2026-08-07
"""
from alembic import op

revision = "e2a6c8d4f1b7"
down_revision = "d7c1e9a4b502"
branch_labels = None
depends_on = None


# Les mentions à semer, dans leur ordre d'affichage. Jamais d'id en dur : un environnement peut
# avoir d'autres ids que le seed, et le cycle est retrouvé par son nom comme dans bb22cc33dd44.
MENTIONS = [
    "Licence Droit",
    "Licence Psychologie",
    "Licence STAPS",
    "Licence Économie-Gestion",
    "Licence Administration économique et sociale (AES)",
    "Licence Langues étrangères appliquées (LEA)",
    "Licence Histoire",
    "Licence Sciences de la vie",
    "Licence Informatique",
    "Licence Mathématiques",
    "Licence Ergothérapie",
]

_ANNEES = "('L1', 'L2', 'L3')"
_NIVEAUX_ANNEES = f"""
    SELECT n.id FROM niveaux n
    JOIN cycles c ON c.id = n.cycle_id
    WHERE c.nom = 'Licence' AND n.nom IN {_ANNEES}
"""


def upgrade() -> None:
    # 1 — Les mentions. ON CONFLICT n'aiderait pas (pas de contrainte d'unicité sur le nom) :
    #     le NOT EXISTS rend la migration rejouable sans doublon.
    for ordre, nom in enumerate(MENTIONS, start=1):
        op.execute(f"""
            INSERT INTO niveaux (cycle_id, nom, ordre)
            SELECT c.id, '{nom.replace("'", "''")}', {ordre}
            FROM cycles c
            WHERE c.nom = 'Licence'
              AND NOT EXISTS (SELECT 1 FROM niveaux n
                              WHERE n.cycle_id = c.id AND n.nom = '{nom.replace("'", "''")}')
        """)

    # 2 — Les niveaux-années, SEULEMENT si plus rien ne s'y rattache.
    op.execute(f"""
        DELETE FROM niveaux n
        WHERE n.id IN ({_NIVEAUX_ANNEES})
          AND NOT EXISTS (SELECT 1 FROM referentiels r WHERE r.niveau_id = n.id)
          AND NOT EXISTS (SELECT 1 FROM referentiel_documents d WHERE d.niveau_id = n.id)
          AND NOT EXISTS (SELECT 1 FROM users u
                          WHERE u.niveau_id = n.id OR u.travail_niveau_id = n.id)
    """)


def downgrade() -> None:
    # Les mentions repartent — sauf celle sur laquelle un référentiel aurait été déposé entre-temps :
    # défaire une migration ne doit pas emporter le travail fait depuis.
    for nom in MENTIONS:
        op.execute(f"""
            DELETE FROM niveaux n
            USING cycles c
            WHERE c.id = n.cycle_id AND c.nom = 'Licence' AND n.nom = '{nom.replace("'", "''")}'
              AND NOT EXISTS (SELECT 1 FROM referentiels r WHERE r.niveau_id = n.id)
              AND NOT EXISTS (SELECT 1 FROM referentiel_documents d WHERE d.niveau_id = n.id)
              AND NOT EXISTS (SELECT 1 FROM users u
                              WHERE u.niveau_id = n.id OR u.travail_niveau_id = n.id)
        """)
    # Et les trois niveaux-années reviennent.
    op.execute("""
        INSERT INTO niveaux (cycle_id, nom, ordre)
        SELECT c.id, v.nom, v.ordre
        FROM cycles c, (VALUES ('L1', 1), ('L2', 2), ('L3', 3)) AS v(nom, ordre)
        WHERE c.nom = 'Licence'
          AND NOT EXISTS (SELECT 1 FROM niveaux n WHERE n.cycle_id = c.id AND n.nom = v.nom)
    """)
