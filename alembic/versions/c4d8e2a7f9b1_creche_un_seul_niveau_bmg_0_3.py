# -*- coding: utf-8 -*-
"""La crèche cesse de faire semblant d'avoir trois niveaux : elle n'en a qu'un, « BMG_0-3 ».

CONSTAT. Le cycle Crèche portait trois niveaux — Bébés (0-1 an), Moyens (1-2 ans), Grands (2-3
ans) — pour UN seul référentiel, déposé sur Bébés. Les deux autres étaient vides : ni document,
ni matière, ni unité, ni prof. Trois portes qui ouvraient sur la même pièce, et deux qui
n'ouvraient sur rien.

CE QUE LE NIVEAU FAIT VRAIMENT, ET POURQUOI TROIS NE SERVAIENT À RIEN. Un niveau décide de trois
choses : les matières proposées au prof (elles se résolvent DANS le référentiel du niveau,
`resolution_couple.matiere_id_du_nom`), le référentiel que le RAG interroge (un référentiel par
niveau), et le nom qui part dans le prompt (`llm/prompts._bloc_referentiel`). Avec un seul
référentiel crèche, les deux premiers sont constants quel que soit le niveau choisi : le choix
n'apportait aucune information. Restait le troisième — et c'est le vrai sujet, traité ailleurs.

L'ÂGE N'EST PAS UN NIVEAU. Sur le terrain, l'animatrice fait les bébés le matin et les grands
l'après-midi. Un niveau, ici, aurait été un profil à changer deux fois par jour. L'âge est un
paramètre de la DEMANDE, pas de l'identité du prof : il se saisit à la génération, comme le type
d'activité. Cette migration ne le pose pas — elle se contente de retirer l'endroit où il n'aurait
jamais dû être.

CE QU'ELLE FAIT.
  1. Le niveau 0-1 est RENOMMÉ « BMG_0-3 » (B pour bébés, M pour moyens, G pour grands). Renommé,
     pas recréé : son id ne bouge pas, donc le référentiel, ses 27 unités, ses 5 matières et le
     prof qui y est rattaché restent en place sans un seul lien à refaire.
  2. `nom_fixe` et `collection` du référentiel suivent le nom du niveau : `bebes_0_1_an` devient
     `bmg_0_3`, la valeur qu'aurait produite un dépôt sur ce niveau (`nommage.dossier_cle` en
     minuscules). Les laisser aurait fait mentir la clé du RAG sur ce qu'elle désigne.
  3. Les niveaux Moyens et Grands sont SUPPRIMÉS — un vrai DELETE, pas un drapeau.

LE GARDE-FOU. La suppression ne s'exécute que si les deux niveaux sont RÉELLEMENT vides :
aucun référentiel, aucun document, aucun prof (ni profil, ni couple de travail). Un seul lien
trouvé et la migration s'arrête sur une erreur qui le nomme, plutôt que d'emporter la donnée
d'un tiers en silence.

CE QU'ELLE NE TOUCHE PAS. Le PDF déposé dans REFERENTIELS/CRECHE/ : les dossiers sur disque sont
la copie de travail de l'admin, pas la base. Le dossier attendu par la convention devient
`BMG_0_3` (dossier_cle remplace le tiret par un souligné).

Revision ID: c4d8e2a7f9b1
Revises: f3b7d9c2e5a8
Create Date: 2026-08-08
"""
from alembic import op
import sqlalchemy as sa


revision = "c4d8e2a7f9b1"
down_revision = "f3b7d9c2e5a8"
branch_labels = None
depends_on = None


CYCLE = "Crèche"
NIVEAU_GARDE = "Bébés (0-1 an)"      # celui qui porte le référentiel : il devient le niveau unique
NIVEAU_NOUVEAU = "BMG_0-3"
NIVEAUX_VIDES = ("Moyens (1-2 ans)", "Grands (2-3 ans)")

# `nommage.dossier_cle("BMG_0-3").lower()` — recopié plutôt qu'importé : une migration décrit
# l'état de la base au jour où elle est écrite et ne doit pas changer de résultat si la règle
# de nommage évolue plus tard.
NOM_FIXE = "bmg_0_3"


def upgrade() -> None:
    conn = op.get_bind()

    cycle_id = conn.execute(
        sa.text("SELECT id FROM cycles WHERE nom = :n"), {"n": CYCLE}
    ).scalar()
    if cycle_id is None:
        return   # pas de cycle Crèche sur cette base : rien à réorganiser

    def niveau_id(nom: str) -> int | None:
        return conn.execute(
            sa.text("SELECT id FROM niveaux WHERE cycle_id = :c AND nom = :n"),
            {"c": cycle_id, "n": nom},
        ).scalar()

    garde = niveau_id(NIVEAU_GARDE)
    if garde is None:
        # Déjà renommé (migration rejouée) ou base montée autrement : on ne force rien.
        return

    # --- 1. Le niveau qui reste : renommé, et remis en tête de son cycle -----------------------
    conn.execute(
        sa.text("UPDATE niveaux SET nom = :nouveau, ordre = 1 WHERE id = :id"),
        {"nouveau": NIVEAU_NOUVEAU, "id": garde},
    )

    # --- 2. La clé du référentiel suit le nom du niveau ----------------------------------------
    conn.execute(
        sa.text("UPDATE referentiels SET nom_fixe = :f, collection = :f WHERE niveau_id = :id"),
        {"f": NOM_FIXE, "id": garde},
    )

    # --- 3. Les deux niveaux vides : contrôlés un par un, puis supprimés -----------------------
    for nom in NIVEAUX_VIDES:
        nid = niveau_id(nom)
        if nid is None:
            continue
        for table, colonne, quoi in (
            ("referentiels", "niveau_id", "un référentiel"),
            ("referentiel_documents", "niveau_id", "un document déposé"),
            ("users", "niveau_id", "le profil d'un enseignant"),
            ("users", "travail_niveau_id", "le couple de travail d'un enseignant"),
        ):
            n = conn.execute(
                sa.text(f"SELECT count(*) FROM {table} WHERE {colonne} = :id"), {"id": nid}
            ).scalar()
            if n:
                raise RuntimeError(
                    f"Suppression refusée : le niveau « {nom} » est encore lié à {quoi} "
                    f"({n} ligne(s) dans {table}.{colonne}). Détachez-les d'abord."
                )
        conn.execute(sa.text("DELETE FROM niveaux WHERE id = :id"), {"id": nid})


def downgrade() -> None:
    """Rend son nom au niveau et recrée les deux niveaux vides — vides, comme ils l'étaient.

    Leurs ids d'origine (24, 25) ne sont pas restitués : ils étaient attribués par la séquence et
    ne désignaient rien. Rien ne les référençait, c'est précisément ce que le garde-fou de
    l'upgrade a vérifié avant de les supprimer."""
    conn = op.get_bind()

    cycle_id = conn.execute(
        sa.text("SELECT id FROM cycles WHERE nom = :n"), {"n": CYCLE}
    ).scalar()
    if cycle_id is None:
        return

    garde = conn.execute(
        sa.text("SELECT id FROM niveaux WHERE cycle_id = :c AND nom = :n"),
        {"c": cycle_id, "n": NIVEAU_NOUVEAU},
    ).scalar()
    if garde is not None:
        conn.execute(
            sa.text("UPDATE niveaux SET nom = :ancien, ordre = 3 WHERE id = :id"),
            {"ancien": NIVEAU_GARDE, "id": garde},
        )
        conn.execute(
            sa.text("UPDATE referentiels SET nom_fixe = :f, collection = :f WHERE niveau_id = :id"),
            {"f": "bebes_0_1_an", "id": garde},
        )

    for ordre, nom in enumerate(NIVEAUX_VIDES, start=1):
        deja = conn.execute(
            sa.text("SELECT id FROM niveaux WHERE cycle_id = :c AND nom = :n"),
            {"c": cycle_id, "n": nom},
        ).scalar()
        if deja is None:
            conn.execute(
                sa.text("INSERT INTO niveaux (cycle_id, nom, ordre) VALUES (:c, :n, :o)"),
                {"c": cycle_id, "n": nom, "o": ordre},
            )
