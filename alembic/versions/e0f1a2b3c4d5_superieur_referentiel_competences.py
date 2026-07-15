# -*- coding: utf-8 -*-
"""Superieur : 7e famille REFERENTIEL_COMPETENCES + correction du catalogue autorise

Constat : le superieur etait mal range dans famille_couples_autorises (Licence/Master sur FICHE_RNCP
seule, BUT sur pro RAP+certif, Doctorat sans aucune famille). Correction : le superieur = une seule
famille, REFERENTIEL_COMPETENCES (le vrai document = les competences du diplome). La fiche RNCP n'est
qu'un resume de certification, sous-ensemble du referentiel de competences -> on ne la garde pas en
double (RÈGLE zero copie). Un couple du superieur = une famille.

Pilote par NOM (cycle + famille), aucun id en dur -> meme resultat sur toute base de meme structure.
Bilan : 152 -> 137 couples autorises. N'affecte aucun autre cycle.

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e0f1a2b3c4d5"
down_revision: Union[str, Sequence[str], None] = "d9e0f1a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) 7e famille REFERENTIEL_COMPETENCES (idempotent par NOM, id auto -> 7 en pratique)
    conn.execute(sa.text("""
        INSERT INTO familles (nom, description, rejet)
        SELECT 'REFERENTIEL_COMPETENCES',
               'Supérieur : référentiel de compétences du diplômé (Licence, Master, BUT, Doctorat).',
               false
        WHERE NOT EXISTS (SELECT 1 FROM familles WHERE nom = 'REFERENTIEL_COMPETENCES')
    """))
    comp_id = conn.execute(sa.text(
        "SELECT id FROM familles WHERE nom = 'REFERENTIEL_COMPETENCES'"
    )).scalar()

    # 2a) AJOUT : COMPETENCES pour TOUS les niveaux des 4 cycles du superieur.
    conn.execute(sa.text("""
        INSERT INTO famille_couples_autorises (famille_id, niveau_id)
        SELECT :comp, n.id
        FROM niveaux n JOIN cycles c ON c.id = n.cycle_id
        WHERE c.nom IN ('Licence', 'Master', 'BUT', 'Doctorat')
        ON CONFLICT (famille_id, niveau_id) DO NOTHING
    """), {"comp": comp_id})

    # 2b) RETRAIT : les mauvaises familles du superieur.
    #     - FICHE_RNCP sur Licence, Master, BUT
    #     - REFERENTIEL_ACTIVITES + REFERENTIEL_CERTIFICATION sur BUT
    conn.execute(sa.text("""
        DELETE FROM famille_couples_autorises fca
        USING familles f, niveaux n, cycles c
        WHERE fca.famille_id = f.id
          AND fca.niveau_id  = n.id
          AND n.cycle_id      = c.id
          AND (
                (f.nom = 'FICHE_RNCP' AND c.nom IN ('Licence', 'Master', 'BUT'))
             OR (f.nom IN ('REFERENTIEL_ACTIVITES', 'REFERENTIEL_CERTIFICATION') AND c.nom = 'BUT')
          )
    """))


def downgrade() -> None:
    conn = op.get_bind()
    # Enleve les couples COMPETENCES du superieur.
    conn.execute(sa.text("""
        DELETE FROM famille_couples_autorises fca
        USING familles f, niveaux n, cycles c
        WHERE fca.famille_id = f.id AND fca.niveau_id = n.id AND n.cycle_id = c.id
          AND f.nom = 'REFERENTIEL_COMPETENCES'
          AND c.nom IN ('Licence', 'Master', 'BUT', 'Doctorat')
    """))
    # Restaure l'etat d'avant : FICHE_RNCP (Licence/Master/BUT) + ACTIVITES/CERTIF (BUT).
    conn.execute(sa.text("""
        INSERT INTO famille_couples_autorises (famille_id, niveau_id)
        SELECT f.id, n.id
        FROM familles f, niveaux n JOIN cycles c ON c.id = n.cycle_id
        WHERE (f.nom = 'FICHE_RNCP' AND c.nom IN ('Licence', 'Master', 'BUT'))
           OR (f.nom IN ('REFERENTIEL_ACTIVITES', 'REFERENTIEL_CERTIFICATION') AND c.nom = 'BUT')
        ON CONFLICT (famille_id, niveau_id) DO NOTHING
    """))
    # La famille REFERENTIEL_COMPETENCES est laissee en place (pas de suppression auto d'une famille).
