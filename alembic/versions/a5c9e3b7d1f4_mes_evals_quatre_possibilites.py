# -*- coding: utf-8 -*-
"""« Mes évals » : une ligne fourre-tout devient les QUATRE possibilités d'évaluation.

CONSTAT. Le tableau de bord ne portait qu'une ligne pour tout l'écran « Mes évals » :
« Sujets, grilles et quiz », à venir. Trois choses distinctes dans une seule ligne, donc un
seul état pour trois chantiers qui n'avanceront pas ensemble — et le CCF, la forme
d'évaluation la plus pratiquée en BTS et en bac professionnel, n'y figurait nulle part. Une
ligne qui compte pour trois ne peut pas dire où on en est, et ce qu'elle ne nomme pas
s'oublie.

CE QUE FAIT CETTE MIGRATION. Elle remplace la ligne unique par QUATRE : Sujets, Grilles,
Quiz, CCF. Chacune a son état et sa note. Les quatre prennent la place de l'ancienne dans le
classement (les lignes « prof » suivantes se décalent de trois), pour que l'écran ne change
pas d'ordre.

L'ÉTAT RESTE « À VENIR » POUR LES QUATRE. Rien n'a été livré : le menu du prof porte les
quatre entrées grisées, aucun écran derrière — c'est ce que dit la note de chaque ligne.

Revision ID: a5c9e3b7d1f4
Revises: d9e4b7a2c6f1
Create Date: 2026-08-09
"""
from alembic import op
import sqlalchemy as sa


revision = "a5c9e3b7d1f4"
down_revision = "d9e4b7a2c6f1"
branch_labels = None
depends_on = None


ECRAN = "Mes évals"
ANCIENNE = ("Sujets, grilles et quiz", "a_venir", "entrée de menu désactivée, aucun écran")

# Les quatre possibilités d'évaluation — (nom, état, note). L'ordre de la liste EST l'ordre
# à l'écran.
NOUVELLES = [
    ("Sujets", "a_venir", "entrée de menu désactivée, aucun écran"),
    ("Grilles", "a_venir", "entrée de menu désactivée, aucun écran"),
    ("Quiz", "a_venir", "entrée de menu désactivée, aucun écran"),
    ("CCF", "a_venir", "entrée de menu désactivée, aucun écran"),
]


def _ordre_de(conn, nom):
    """L'ordre de la ligne « prof » / « Mes évals » nommée `nom`, ou None si elle n'y est pas."""
    return conn.execute(
        sa.text(
            "SELECT ordre FROM fonctionnalites "
            "WHERE domaine = 'prof' AND ecran = :e AND nom = :n"
        ),
        {"e": ECRAN, "n": nom},
    ).scalar()


def _decale(conn, apres, de):
    """Décale de `de` rangs les lignes « prof » situées après le rang `apres`."""
    conn.execute(
        sa.text("UPDATE fonctionnalites SET ordre = ordre + :de WHERE domaine = 'prof' AND ordre > :a"),
        {"de": de, "a": apres},
    )


def _insere(conn, lignes, depart):
    for i, (nom, etat, note) in enumerate(lignes):
        conn.execute(
            sa.text(
                "INSERT INTO fonctionnalites (domaine, ecran, nom, etat, note, ordre) "
                "VALUES ('prof', :e, :n, :s, :note, :o)"
            ),
            {"e": ECRAN, "n": nom, "s": etat, "note": note, "o": depart + i},
        )


def _supprime(conn, noms):
    for nom in noms:
        conn.execute(
            sa.text("DELETE FROM fonctionnalites WHERE domaine = 'prof' AND ecran = :e AND nom = :n"),
            {"e": ECRAN, "n": nom},
        )


def upgrade() -> None:
    conn = op.get_bind()
    base = _ordre_de(conn, ANCIENNE[0])
    if base is None:
        # La ligne fourre-tout n'est plus là (base déjà retouchée) : les quatre se posent
        # à la suite des lignes « prof », sans rien déplacer.
        base = (conn.execute(
            sa.text("SELECT COALESCE(MAX(ordre), 0) FROM fonctionnalites WHERE domaine = 'prof'")
        ).scalar() or 0) + 1
    else:
        _supprime(conn, [ANCIENNE[0]])
        _decale(conn, base, len(NOUVELLES) - 1)
    _insere(conn, NOUVELLES, base)


def downgrade() -> None:
    conn = op.get_bind()
    base = _ordre_de(conn, NOUVELLES[0][0])
    _supprime(conn, [n for n, _, _ in NOUVELLES])
    if base is None:
        return
    _insere(conn, [ANCIENNE], base)
    _decale(conn, base + len(NOUVELLES) - 1, -(len(NOUVELLES) - 1))
