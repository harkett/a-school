"""Licence par SPÉCIALITÉ — retrait des niveaux-années L1/L2/L3.

Constat : le seed d'origine (c6d7e8f9a0b1) a rangé la Licence par ANNÉES (L1/L2/L3) alors que
toutes les autres filières du Supérieur sont par SPÉCIALITÉ (BTS SIO, BUT Informatique,
Master Droit, Doctorat Physique…) — c'est la spécialité qui porte le référentiel, pas l'année.
On aligne : les niveaux du cycle Licence sont des spécialités créées par l'admin (écran
Programmes, « + Niveau », ex. « Licence Ergothérapie ») ; L1/L2/L3 disparaissent.

GARDE-FOU (règle 4, contrôle avant DELETE) : on ne supprime un niveau-année QUE s'il n'est
référencé par rien de vivant — aucun référentiel, aucun enseignement de prof. Les paires
matière×niveau posées par le seed (et leurs candidates) sont retirées d'abord, mais seulement
si aucun prof n'enseigne dessus. Un environnement où quelqu'un aurait bâti sur L1/L2/L3
garde ses lignes intactes (la migration passe sans rien casser).

Revision ID: bb22cc33dd44
Revises: aa11bb22cc33
"""
from alembic import op

revision = "bb22cc33dd44"
down_revision = "aa11bb22cc33"
branch_labels = None
depends_on = None

# Les niveaux-années à retirer, ciblés PAR NOM sous le cycle Licence (jamais par id en dur :
# un environnement peut avoir d'autres ids que le seed).
_ANNEES = "('L1', 'L2', 'L3')"
_NIVEAUX_ANNEES = f"""
    SELECT n.id FROM niveaux n
    JOIN cycles c ON c.id = n.cycle_id
    WHERE c.nom = 'Licence' AND n.nom IN {_ANNEES}
"""


def upgrade():
    # 1 — Candidates de matières du seed sur ces niveaux (aucun contrôle : simple proposition).
    op.execute(f"DELETE FROM matieres_candidates WHERE niveau_id IN ({_NIVEAUX_ANNEES})")

    # 2 — Paires matière×niveau du seed, SEULEMENT si aucun prof n'enseigne dessus.
    op.execute(f"""
        DELETE FROM matiere_niveaux mn
        WHERE mn.niveau_id IN ({_NIVEAUX_ANNEES})
          AND NOT EXISTS (SELECT 1 FROM user_enseignements ue WHERE ue.matiere_niveau_id = mn.id)
    """)

    # 3 — Les niveaux-années eux-mêmes, SEULEMENT si plus rien ne les référence
    #     (ni référentiel, ni paire restante — une paire épargnée à l'étape 2 protège son niveau).
    op.execute(f"""
        DELETE FROM niveaux n
        WHERE n.id IN ({_NIVEAUX_ANNEES})
          AND NOT EXISTS (SELECT 1 FROM referentiels r WHERE r.niveau_id = n.id)
          AND NOT EXISTS (SELECT 1 FROM matiere_niveaux mn WHERE mn.niveau_id = n.id)
          AND NOT EXISTS (SELECT 1 FROM matieres_candidates mc WHERE mc.niveau_id = n.id)
    """)


def downgrade():
    # Restaure les trois niveaux-années sous le cycle Licence (sans les paires du seed :
    # elles appartenaient au seed d'origine, pas à cette migration).
    op.execute(f"""
        INSERT INTO niveaux (cycle_id, nom, ordre)
        SELECT c.id, v.nom, v.ordre
        FROM cycles c, (VALUES ('L1', 1), ('L2', 2), ('L3', 3)) AS v(nom, ordre)
        WHERE c.nom = 'Licence'
          AND NOT EXISTS (
              SELECT 1 FROM niveaux n WHERE n.cycle_id = c.id AND n.nom = v.nom)
    """)
