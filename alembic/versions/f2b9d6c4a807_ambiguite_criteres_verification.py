# -*- coding: utf-8 -*-
"""Criteres d'ambiguite : le CONTROLE a effectuer, ecrit sous chaque type

Constat sur un enonce reel (BTS CIEL, architecture reseau) : le modele a rendu quatre cartes
de vocabulaire — DMZ, VLAN, zero trust, durcissement — et laisse passer les deux types
couteux. « Le document fourni », « Appuyez-vous sur le document » : reference implicite, non
signalee. Aucune longueur, aucun format, aucun bareme : criteres de reussite absents, non
signale non plus. Un libelle seul (« Reference implicite ») laisse le modele choisir OU il
cherche, et il choisit ce qui se voit le plus vite.

Chaque type porte donc desormais SA verification, en toutes lettres. C'est une donnee du
critere, pas une phrase du prompt : muscler un controle, ou en ecrire un pour un huitieme
type, se fait en base.

`autre` reste vide : c'est le prof qui ecrit ce qu'il veut faire verifier.

downgrade : drop de la colonne.

Revision ID: f2b9d6c4a807
Revises: e9d4c2b7a615
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2b9d6c4a807"
down_revision: Union[str, Sequence[str], None] = "e9d4c2b7a615"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_VERIFICATIONS = [
    ("consigne_vague",
     "Relève les verbes de consigne (analysez, commentez, étudiez, proposez, réfléchissez…). "
     "Pour chacun : l'énoncé dit-il sur quoi porter l'effort et jusqu'où aller ? Un verbe qui "
     "laisse le champ entièrement ouvert est à signaler."),
    ("vocabulaire_non_defini",
     "Relève tous les termes techniques, sigles et acronymes de l'énoncé. Pour chacun : est-il "
     "défini dans l'énoncé, ou peut-il être tenu pour acquis à ce niveau et dans cette matière ? "
     "Ne signale que ceux qui ne le sont ni l'un ni l'autre."),
    ("double_sens",
     "Cherche les tournures qui acceptent deux lectures dans ce contexte : pronoms sans "
     "antécédent certain, « ou » qu'on peut lire inclusif ou exclusif, termes polysémiques, "
     "négations portant sur plusieurs éléments. Donne les deux lectures possibles."),
    ("criteres_reussite_absents",
     "Vérifie précisément, pour CHAQUE production demandée : la longueur attendue est-elle "
     "indiquée ? le nombre d'éléments ou de points ? le format du rendu ? un barème ou des "
     "critères d'évaluation ? Si aucun de ces repères n'est cité, signale-le."),
    ("reference_implicite",
     "Vérifie chaque renvoi à un support : « le document », « le texte », « l'auteur », « la "
     "figure », « l'annexe », « ci-joint ». L'énoncé dit-il DE QUEL support il s'agit (titre, "
     "numéro, page) ? Un renvoi non identifié est à signaler même si le support est distribué "
     "à part."),
    ("consigne_trop_longue",
     "Compte les tâches distinctes phrase par phrase. Une phrase qui enchaîne plus de deux "
     "actions à réaliser, ou qui mêle la production et sa justification, est à signaler — "
     "l'élève ne sait alors ni par quoi commencer ni ce qu'il doit rendre."),
]


def upgrade() -> None:
    op.add_column("ambiguite_criteres",
                  sa.Column("verification", sa.Text(), nullable=False, server_default=""))
    conn = op.get_bind()
    maj = sa.text("UPDATE ambiguite_criteres SET verification = :v WHERE code = :c")
    for code, verification in _VERIFICATIONS:
        conn.execute(maj, {"c": code, "v": verification})


def downgrade() -> None:
    op.drop_column("ambiguite_criteres", "verification")
