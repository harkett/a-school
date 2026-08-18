# -*- coding: utf-8 -*-
"""Crée les quatre tables de la GRILLE D'ÉVALUATION du professeur

CE QUE C'EST. « Mes évals → Grilles » n'existait nulle part : entrée de menu grisée, aucun
écran, aucune table. Une grille critériée est un TABLEAU — des critères en lignes, des niveaux
de maîtrise en colonnes, et dans chaque case le descripteur qui dit ce qu'il faut avoir fait
pour obtenir ce niveau sur ce critère. C'est ce texte-là que le professeur lit, que l'IA écrit,
et que tout ce qui viendra ensuite consommera.

POURQUOI QUATRE TABLES ET NON TROIS. Les niveaux de maîtrise appartiennent à la GRILLE, pas au
critère. Rattachés au critère, chaque ligne aurait sa propre échelle : le tableau cesserait
d'être un tableau, aucune colonne ne s'alignerait à l'écran ni à l'impression, et le professeur
lirait une juxtaposition de listes. Une échelle commune est ce qui fait qu'une grille se lit
d'un coup d'œil. Les cases vivent donc dans leur propre table, au croisement.

POURQUOI PAS UN CHAMP TEXTE. Le moule de « Mes contenus » range son résultat dans une colonne
Text (`activites.resultat`), et c'est juste pour un texte. Une grille rangée en markdown serait
belle à l'écran et inutilisable ailleurs : il faudrait la relire au parseur pour en ressortir
quoi que ce soit. La grille se range EN DONNÉES ; le document, c'est ce qu'on en imprime.

OÙ VONT LES POINTS, ET CE QUE ÇA COÛTE. Sur le CRITÈRE (`poids`) et sur le NIVEAU DE MAÎTRISE
(`points`), jamais dans la case. Conséquence assumée : les barèmes non linéaires sont hors de
portée — une grille où « Satisfaisant » vaudrait 3 points sur un critère et 5 sur un autre ne
rentre pas ici. C'est un choix pris le 17/08/2026, pas un oubli à découvrir plus tard.

`grille_niveaux_maitrise` ET NON `grille_niveaux` : dans tout le reste du produit, `niveau`
désigne une classe (6e, BTS…) — `niveaux`, `referentiel_niveaux`, `activites.niveau`. Deux sens
pour un même mot dans un même schéma se paient au premier lecteur pressé. Le nom dit lequel des
deux, et c'est celui de l'écran : « niveau de maîtrise ».

ELLE REFERME AUSSI LA BRANCHE. Deux têtes cohabitaient — `b3c8e5f1a7d2` (la nouveauté ouvre son
écran) et `f4b1c8d3a7e9` (« Bientôt disponible » dit vrai), posées par deux chantiers parallèles.
`alembic upgrade head` refuse de tourner sur deux têtes. Celle-ci les rejoint, sans toucher à
aucun des deux fichiers : ils restent ceux que leur auteur a écrits. Ce rabattage est aussi ce
qui rend applicable la ligne `eval-grilles` de `features_votables`, que la migration de
livraison ira marquer `livree`.

downgrade : supprime les quatre tables, dans l'ordre inverse des dépendances.

Revision ID: c9e4b7f2a1d6
Revises: b3c8e5f1a7d2, f4b1c8d3a7e9
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9e4b7f2a1d6"
down_revision: Union[str, Sequence[str], None] = ("b3c8e5f1a7d2", "f4b1c8d3a7e9")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grilles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        # Titre = ce que le professeur évalue, saisi par lui (zone libre) → Text, jamais borné :
        # même leçon que les titres de séance, qu'une borne avait tronqués.
        sa.Column("titre", sa.Text(), nullable=False),
        # La DEMANDE du professeur, gardée telle qu'il l'a écrite — ce sur quoi la génération
        # s'appuie, et ce qu'il relit l'année suivante avant de régénérer.
        sa.Column("contexte", sa.Text(), nullable=False, server_default=""),
        sa.Column("matiere", sa.String(80), nullable=True),
        sa.Column("niveau", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # LES COLONNES DU TABLEAU. `points` = ce que vaut cet échelon ; `ordre` = de gauche à
    # droite, du moins maîtrisé au plus maîtrisé. UNIQUE sur le libellé : deux colonnes
    # « Satisfaisant » dans la même grille ne veulent rien dire.
    op.create_table(
        "grille_niveaux_maitrise",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("grille_id", sa.Integer(),
                  sa.ForeignKey("grilles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("libelle", sa.String(64), nullable=False),
        sa.Column("points", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("grille_id", "libelle", name="uq_grille_niveaux_maitrise_libelle"),
    )

    # LES LIGNES DU TABLEAU. `poids` = l'importance relative du critère dans la note ; il se
    # multiplie aux points de l'échelon coché. Le libellé est Text : un critère réel est une
    # phrase (« Rend un raisonnement dont chaque étape se justifie »), pas une étiquette.
    op.create_table(
        "grille_criteres",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("grille_id", sa.Integer(),
                  sa.ForeignKey("grilles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("libelle", sa.Text(), nullable=False),
        sa.Column("poids", sa.Float(), nullable=False, server_default="1"),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
    )

    # LES CASES. Une ligne par croisement réellement rempli — une case vide n'a pas de ligne,
    # l'absence est le vide (même règle que `outils_llm`, où l'absence est le réglage). UNIQUE
    # sur le couple : une case, un descripteur, jamais deux qui se contrediraient.
    op.create_table(
        "grille_cellules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("critere_id", sa.Integer(),
                  sa.ForeignKey("grille_criteres.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("niveau_maitrise_id", sa.Integer(),
                  sa.ForeignKey("grille_niveaux_maitrise.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("descripteur", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("critere_id", "niveau_maitrise_id", name="uq_grille_cellules_croisement"),
    )


def downgrade() -> None:
    op.drop_table("grille_cellules")
    op.drop_table("grille_criteres")
    op.drop_table("grille_niveaux_maitrise")
    op.drop_table("grilles")
