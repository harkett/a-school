# -*- coding: utf-8 -*-
"""famille_couples : seed initial (152 couples famille <-> niveau)

Donnee de reference semee par migration (puis maintenue via l'interface admin). `famille_id`
resolu par le NOM (SELECT id, nom FROM familles) -> aucun id en dur. Idempotent :
ON CONFLICT (famille_id, niveau_id) DO NOTHING.

Source : table detaillee du document de reference (la table fait foi, pas les en-tetes) ->
FICHE_RNCP = 55 couples, total = 152. REJET ne porte aucun couple.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, Sequence[str], None] = "e4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# famille (par nom) -> niveau_id. Plages : BTS 27..43, Master 44..58, BUT 59..73, LP+CAP 19..23,
# Licence 16..18. Comptes : 20 / 37 / 37 / 55 / 3 / 0 = 152.
_COUPLES = {
    "PROGRAMME_ENSEIGNEMENT": [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 15, 19, 20, 21, 22, 23],
    "REFERENTIEL_ACTIVITES": [19, 20, 21, 22, 23] + list(range(27, 44)) + list(range(59, 74)),
    "REFERENTIEL_CERTIFICATION": [19, 20, 21, 22, 23] + list(range(27, 44)) + list(range(59, 74)),
    "FICHE_RNCP": [19, 20, 21, 22, 23, 16, 17, 18] + list(range(27, 44)) + list(range(44, 59)) + list(range(59, 74)),
    "CATALOGUE_ACTIVITES": [26, 25, 24],
    "REJET": [],
}


def upgrade() -> None:
    conn = op.get_bind()
    fam_id = {nom: id_ for id_, nom in conn.execute(sa.text("SELECT id, nom FROM familles")).fetchall()}
    ins = sa.text(
        "INSERT INTO famille_couples (famille_id, niveau_id) VALUES (:f, :n) "
        "ON CONFLICT (famille_id, niveau_id) DO NOTHING"
    )
    for nom, niveaux in _COUPLES.items():
        fid = fam_id[nom]  # KeyError volontaire si une famille manque (echec visible)
        for niv in niveaux:
            conn.execute(ins, {"f": fid, "n": niv})


def downgrade() -> None:
    op.execute("DELETE FROM famille_couples")
