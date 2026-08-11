# -*- coding: utf-8 -*-
"""Prompt « ambiguite_exemple » : le texte qui fabrique les enonces d'exemple

Le prompt vit EN BASE comme les autres (get_prompt n'a plus de repli sur le code), et se regle
dans Admin -> IA -> Prompts. Il est ECRIT POUR ETRE EXECUTE HORS DE L'APPLICATION : l'admin
copie le texte rempli pour un couple, le fait tourner chez lui, recolle le resultat. Zero appel
paye par l'application, et le meme enonce a chaque ouverture de l'ecran — un exemple genere a
la volee couterait a chaque clic et ne montrerait jamais deux fois la meme chose.

`PROMPTS_MAJ` (et non un simple INSERT) : c'est la cle lue par tests/test_prompts_en_base.py,
qui recompose seed + mises a jour pour verifier que le registre et une base neuve disent la
meme chose.

TEXTE GELE, VOLONTAIREMENT RECOPIE ICI (regle de b8e5f2a1c9d7) : la migration seme dans six
mois exactement ce qu'elle semait aujourd'hui, elle n'importe pas le registre.

downgrade : retire la ligne, mais SEULEMENT si elle est restee identique au texte seme — une
version retouchee par l'admin lui appartient.

Revision ID: c9a2f7e4b613
Revises: b5f8e2a1d740
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9a2f7e4b613"
down_revision: Union[str, Sequence[str], None] = "b5f8e2a1d740"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROMPTS_MAJ = {
    "ambiguite_exemple": 'Tu écris un ÉNONCÉ D\'EXERCICE VOLONTAIREMENT IMPARFAIT, qui servira d\'exemple de démonstration à un outil de détection d\'ambiguïtés.\n\nContexte :\n- Matière : {matiere}\n- Niveau/formation : {niveau}\n\nTon énoncé doit ressembler à un vrai sujet donné par un enseignant de cette matière à ce niveau : même vocabulaire métier, même longueur, même ton. Un lecteur pressé ne doit rien y voir d\'anormal — les défauts sont ceux qu\'on commet sans le vouloir, pas des pièges grossiers.\n\nTu y glisses délibérément UNE ambiguïté de chacun des types suivants, et de ceux-là seulement :\n{criteres}\n\nContraintes :\n- 3 paragraphes maximum, 200 mots environ. Un énoncé qu\'on colle en un geste.\n- Chaque défaut doit être réellement présent dans le texte, repérable en citant un extrait exact.\n- Aucun commentaire, aucune balise, aucune marque qui signalerait les défauts DANS l\'énoncé lui-même : il doit se lire comme un sujet ordinaire.\n- Le contenu doit être exact du point de vue de la discipline : un énoncé mal formulé, jamais un énoncé faux.\n\nFormat de réponse — EXACTEMENT ces deux blocs, rien avant, rien après :\n\n=== ENONCE ===\n(le titre du sujet puis l\'énoncé)\n\n=== DEFAUTS ===\n- Type du défaut — "extrait exact concerné" — en quoi c\'en est un\n(une ligne par défaut, dans l\'ordre des types demandés)',
}


def upgrade() -> None:
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(
            sa.text("INSERT INTO settings (key, value) VALUES (:key, :value) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"),
            {"key": f"prompt_{cle}", "value": texte},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(
            sa.text("DELETE FROM settings WHERE key = :key AND value = :value"),
            {"key": f"prompt_{cle}", "value": texte},
        )
