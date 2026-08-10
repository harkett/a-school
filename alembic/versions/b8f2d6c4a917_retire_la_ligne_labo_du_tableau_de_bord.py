# -*- coding: utf-8 -*-
"""Le tableau de bord annonce encore le Labo « fait » — l'ecran n'existe plus.

CONSTAT du 10/08/2026. La ligne 29 de `fonctionnalites` (domaine admin, ecran Outils, nom
« Labo ») porte l'etat `fait`. Or le Labo a ete supprime le meme jour, en entier : l'ecran
`Labo.jsx`, sa page d'administration, le module `pedagogie/referentiels_labo.py` et ses treize
routes, sa suite de tests, son entree de menu. Le tableau de bord affirmait donc une
fonctionnalite livree que plus une ligne de code ne porte.

C'est exactement le defaut que le point 11 de la liste de verification nomme : « chaque ligne
fait / en cours / a venir verifiee dans le code ». Il n'a rien casse, et c'est ce qui le rend
insidieux : un ecran d'etat qui se trompe ne leve aucune erreur, il se contente de mentir.

CE QUE FAIT CETTE MIGRATION. Elle SUPPRIME la ligne. Pas de passage a `a_venir` : le Labo n'est
pas remis a plus tard, il a ete retire parce que son travail est passe dans Admin > Referentiels.
Une ligne « a venir » annoncerait un chantier qui n'existe pas.

L'ORDRE DES DEUX LIGNES SUIVANTES est repris pour combler le trou : « Mon compte » passe de 30 a
29, « Aide » de 31 a 30. L'ecran classe par `ordre`, un trou ne se verrait pas — mais la prochaine
ligne ajoutee a la main reprendrait un numero deja pris.

Revision ID: b8f2d6c4a917
Revises: a4d8f2c6e1b9
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa


revision = "b8f2d6c4a917"
down_revision = "a4d8f2c6e1b9"
branch_labels = None
depends_on = None


ECRAN = "Outils"
NOM = "Labo"
# (nom, ancien ordre, nouvel ordre) — les lignes qui suivaient le Labo sur le meme ecran.
DECALEES = [("Mon compte", 30, 29), ("Aide", 31, 30)]


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM fonctionnalites WHERE ecran = :e AND nom = :n"),
                 {"e": ECRAN, "n": NOM})
    for nom, _avant, apres in DECALEES:
        conn.execute(sa.text("UPDATE fonctionnalites SET ordre = :o WHERE ecran = :e AND nom = :n"),
                     {"o": apres, "e": ECRAN, "n": nom})


def downgrade() -> None:
    """Remet la ligne et son ordre d'origine. Elle redira « fait » d'un ecran absent : c'est le
    propre d'un retour arriere qui ne ressuscite pas le code."""
    conn = op.get_bind()
    for nom, avant, _apres in DECALEES:
        conn.execute(sa.text("UPDATE fonctionnalites SET ordre = :o WHERE ecran = :e AND nom = :n"),
                     {"o": avant, "e": ECRAN, "n": nom})
    conn.execute(sa.text(
        "INSERT INTO fonctionnalites (domaine, ecran, nom, etat, note, ordre) "
        "VALUES ('admin', :e, :n, 'fait', NULL, 29)"), {"e": ECRAN, "n": NOM})
