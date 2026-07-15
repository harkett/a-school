# -*- coding: utf-8 -*-
"""famille_couples : rapatriement des 137 couples depuis le clone, puis vidage du clone

Chemin INVERSE de c8d9e0f1a2b3 (qui avait clone famille_couples -> famille_couples_autorises puis
vide famille_couples). On revient a UNE seule table : famille_couples, RELIEE par cles etrangeres
(famille_id -> familles, niveau_id -> niveaux). Le clone isole (sans FK) etait une copie ; on la
supprime au sens donnee (table videe ici, structure otee plus tard au rebranchement des lectures).

upgrade  : recopie les couples du clone vers famille_couples (les FK VALIDENT chaque ligne : une
           ligne orpheline serait refusee), puis VIDE famille_couples_autorises. Deplacement en une
           fois -> zero copie persistante, source unique restauree. Idempotent (ON CONFLICT DO NOTHING).
downgrade: chemin symetrique -> recopie de famille_couples vers le clone, puis vide famille_couples.

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e0f1a2b3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # 1) Rapatriement : les FK de famille_couples verifient au passage que chaque couple pointe vers
    #    une vraie famille et un vrai niveau (le clone isole ne pouvait pas le garantir).
    conn.execute(sa.text(
        "INSERT INTO famille_couples (famille_id, niveau_id) "
        "SELECT famille_id, niveau_id FROM famille_couples_autorises "
        "ON CONFLICT (famille_id, niveau_id) DO NOTHING"
    ))
    # 2) Vidage du clone : la donnee vit desormais dans l'unique table reliee.
    conn.execute(sa.text("DELETE FROM famille_couples_autorises"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "INSERT INTO famille_couples_autorises (famille_id, niveau_id) "
        "SELECT famille_id, niveau_id FROM famille_couples "
        "ON CONFLICT (famille_id, niveau_id) DO NOTHING"
    ))
    conn.execute(sa.text("DELETE FROM famille_couples"))
