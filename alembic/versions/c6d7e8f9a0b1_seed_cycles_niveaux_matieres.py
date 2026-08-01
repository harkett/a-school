# -*- coding: utf-8 -*-
"""seed cycles / niveaux (donnees de reference structurelles)

AMPUTEE le 01/08/2026 (chantier Matiere, lot 1) : elle semait aussi 103 matieres et 203
paires matiere-niveau. Depuis f8b3d5c7a1e9, une matiere appartient a son referentiel et la
table matiere_niveaux n'existe plus -> ces lignes ne peuvent plus exister. Les matieres
arrivent par le DEPOT du PDF. Ce fichier ne seme donc plus que les cycles et les niveaux ;
son revision id et son nom de fichier ne bougent pas (l'historique reste lisible).

Ces tables portent le referentiel (cycles, niveaux). AUCUNE migration ne les recreait ->
trou de deploiement (elles n'existaient que sur le miroir). Cette migration comble le trou :
les lignes voyagent donc jusqu'a la vraie base.

Contenu EXTRAIT du dump nettoye (aschool_referentiel_4tables_20260711_CLEAN.sql) : rien
tape a la main. IDs explicites preserves. Idempotent : ON CONFLICT DO NOTHING sur chaque
INSERT (rejouable sans doublon, sur PK id comme sur les uniques). Ordre FK-safe :
cycles -> niveaux.

Les sequences sont recalees en fin d'upgrade avec GREATEST(valeur_en_base, valeur_dump)
-> une sequence deja plus haute ne redescend jamais (pas de collision de PK a la 1re
creation admin en prod).

downgrade : pass volontaire (non destructif). 7 FK RESTRICT pointent vers ces tables ;
un DELETE echouerait ou orphelinerait des referentiels vivants.

Revision ID: c6d7e8f9a0b1
Revises: b5c6d7e8f9a0
Create Date: 2026-07-11
"""
from typing import Sequence, Union

from alembic import op


revision: str = "c6d7e8f9a0b1"
down_revision: Union[str, Sequence[str], None] = "b5c6d7e8f9a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_CYCLES = [
    "INSERT INTO cycles (id, nom, ordre) VALUES (1, 'École élémentaire', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO cycles (id, nom, ordre) VALUES (2, 'Collège', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO cycles (id, nom, ordre) VALUES (3, 'École maternelle', 3) ON CONFLICT DO NOTHING",
    "INSERT INTO cycles (id, nom, ordre) VALUES (5, 'Licence', 5) ON CONFLICT DO NOTHING",
    "INSERT INTO cycles (id, nom, ordre) VALUES (6, 'Lycée professionnel', 6) ON CONFLICT DO NOTHING",
    "INSERT INTO cycles (id, nom, ordre) VALUES (7, 'Crèche', 7) ON CONFLICT DO NOTHING",
    "INSERT INTO cycles (id, nom, ordre) VALUES (8, 'BTS', 8) ON CONFLICT DO NOTHING",
    "INSERT INTO cycles (id, nom, ordre) VALUES (9, 'Master', 9) ON CONFLICT DO NOTHING",
    "INSERT INTO cycles (id, nom, ordre) VALUES (10, 'BUT', 10) ON CONFLICT DO NOTHING",
    "INSERT INTO cycles (id, nom, ordre) VALUES (11, 'Doctorat', 11) ON CONFLICT DO NOTHING",
    "INSERT INTO cycles (id, nom, ordre) VALUES (4, 'Lycée', 4) ON CONFLICT DO NOTHING",
]

_NIVEAUX = [
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (1, 1, 'CP', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (2, 1, 'CE1', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (3, 1, 'CE2', 3) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (4, 1, 'CM1', 4) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (5, 1, 'CM2', 5) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (6, 2, '6e', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (7, 2, '5e', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (8, 2, '4e', 3) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (9, 2, '3e', 4) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (10, 3, 'Petite section (PS)', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (11, 3, 'Moyenne section (MS)', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (12, 3, 'Grande section (GS)', 3) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (16, 5, 'L1', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (17, 5, 'L2', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (18, 5, 'L3', 3) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (19, 6, 'Seconde Pro', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (20, 6, 'Première Pro', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (21, 6, 'Terminale Pro', 3) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (22, 6, 'CAP 1re année', 4) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (23, 6, 'CAP 2e année', 5) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (24, 7, 'Grands (2-3 ans)', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (25, 7, 'Moyens (1-2 ans)', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (26, 7, 'Bébés (0-1 an)', 3) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (27, 8, 'BTS SIO', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (28, 8, 'BTS Commerce International', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (29, 8, 'BTS NDRC', 3) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (30, 8, 'BTS MCO', 4) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (31, 8, 'BTS Comptabilité & Gestion (CG)', 5) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (32, 8, 'BTS SAM', 6) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (33, 8, 'BTS Électrotechnique', 7) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (34, 8, 'BTS Génie Civil', 8) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (35, 8, 'BTS Bâtiment', 9) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (36, 8, 'BTS Professions Immobilières', 10) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (37, 8, 'BTS Banque', 11) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (38, 8, 'BTS Assurance', 12) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (39, 8, 'BTS Tourisme', 13) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (40, 8, 'BTS Audiovisuel', 14) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (41, 8, 'BTS Design / Arts appliqués', 15) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (42, 8, 'BTS CIEL Option A', 16) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (43, 8, 'BTS CIEL Option B', 17) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (44, 9, 'Master Droit', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (45, 9, 'Master Psychologie', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (46, 9, 'Master STAPS', 3) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (47, 9, 'Master Informatique', 4) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (48, 9, 'Master Management / Gestion (IAE)', 5) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (49, 9, 'Master Finance', 6) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (50, 9, 'Master Marketing', 7) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (51, 9, 'Master Ressources Humaines', 8) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (52, 9, 'Master Économie', 9) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (53, 9, 'Master Sciences de l''Éducation', 10) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (54, 9, 'Master AES / Administration publique', 11) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (55, 9, 'Master Biologie', 12) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (56, 9, 'Master Chimie', 13) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (57, 9, 'Master Physique', 14) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (58, 9, 'Master Mathématiques', 15) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (59, 10, 'BUT Informatique', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (60, 10, 'BUT GEA', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (61, 10, 'BUT TC', 3) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (62, 10, 'BUT GMP', 4) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (63, 10, 'BUT GEII', 5) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (64, 10, 'BUT MMI', 6) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (65, 10, 'BUT R&T', 7) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (66, 10, 'BUT GCCD', 8) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (67, 10, 'BUT QLIO', 9) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (68, 10, 'BUT Chimie', 10) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (69, 10, 'BUT Biologie (ex-GB)', 11) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (70, 10, 'BUT Carrières Juridiques', 12) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (71, 10, 'BUT Carrières Sociales', 13) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (72, 10, 'BUT STID', 14) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (73, 10, 'BUT IIA', 15) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (74, 11, 'Doctorat Sciences de l''ingénieur', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (75, 11, 'Doctorat Sciences de la vie / Biologie', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (76, 11, 'Doctorat Physique', 3) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (77, 11, 'Doctorat Chimie', 4) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (78, 11, 'Doctorat Mathématiques', 5) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (79, 11, 'Doctorat Informatique', 6) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (80, 11, 'Doctorat Environnement / Géosciences', 7) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (81, 11, 'Doctorat Droit', 8) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (82, 11, 'Doctorat Économie', 9) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (83, 11, 'Doctorat Sciences de gestion', 10) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (84, 11, 'Doctorat Lettres / Langues', 11) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (85, 11, 'Doctorat Histoire', 12) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (86, 11, 'Doctorat Sociologie', 13) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (87, 11, 'Doctorat Psychologie', 14) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (88, 11, 'Doctorat Philosophie', 15) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (13, 4, 'Seconde', 1) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (14, 4, 'Première', 2) ON CONFLICT DO NOTHING",
    "INSERT INTO niveaux (id, cycle_id, nom, ordre) VALUES (15, 4, 'Terminale', 3) ON CONFLICT DO NOTHING",
]

# _MATIERES / _MATIERE_NIVEAUX : RETIRES le 01/08/2026 (chantier Matiere, lot 1).
# Ce seed inserait 103 matieres et 203 paires, dont la plupart pour des niveaux SANS
# referentiel. Depuis f8b3d5c7a1e9, une matiere appartient a un referentiel
# (matieres.referentiel_id NOT NULL) et la table matiere_niveaux n'existe plus : ces lignes
# n'ont donc plus de maison possible. Les matieres arrivent desormais par le DEPOT du PDF du
# referentiel, avec l'orthographe du document. Une base neuve part sans aucune matiere, et
# c'est voulu. Les cycles et les niveaux, eux, restent semes ici.

# Recalage des sequences : jamais de descente (GREATEST).
_SETVALS = [
    "SELECT setval('cycles_id_seq', GREATEST((SELECT last_value FROM cycles_id_seq), 13), true)",
    "SELECT setval('niveaux_id_seq', GREATEST((SELECT last_value FROM niveaux_id_seq), 88), true)",
    # matieres_id_seq / matiere_niveaux_id_seq : partis avec leurs INSERT (voir ci-dessus).
]


def upgrade() -> None:
    for stmt in _CYCLES + _NIVEAUX:
        op.execute(stmt)
    for stmt in _SETVALS:
        op.execute(stmt)


def downgrade() -> None:
    # Seed de donnees de reference structurelles. Pas de downgrade destructif :
    # 7 FK RESTRICT pointent vers ces tables -> un DELETE echouerait ou detruirait
    # de la donnee de reference vivante. Rollback = restauration depuis sauvegarde.
    pass
