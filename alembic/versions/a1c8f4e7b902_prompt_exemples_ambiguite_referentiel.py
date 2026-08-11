# -*- coding: utf-8 -*-
"""Prompt « ambiguite_exemples_referentiel » : les enonces d'exemple de TOUT un referentiel

Le prompt « ambiguite_exemple » ne traitait qu'un couple : 47 aller-retours pour cinq
referentiels. Celui-ci porte toutes les matieres d'un referentiel d'un coup — un aller-retour
par referentiel, dans la cartouche « Ambiguites » de la procedure Referentiel.

Sa sortie est STRICTE (### matiere / === ENONCE === / === DEFAUTS === / === NON TRAITEES ===).
Le redacteur qui hesitait laissait jusqu'ici des notes « (NB : ... ) » en fin de bloc : elles
finissaient dans la colonne des defauts, et un enonce parti sur un contresens entrait quand
meme en base. Une matiere dont il n'est pas sur se declare desormais dans le dernier bloc, et
son couple reste vide. Vide plutot que faux — un couple faux est invisible.

`PROMPTS_MAJ` (et non un simple INSERT) : c'est la cle lue par tests/test_prompts_en_base.py.

TEXTE GELE, VOLONTAIREMENT RECOPIE ICI (regle de b8e5f2a1c9d7).

downgrade : retire la ligne, mais SEULEMENT si elle est restee identique au texte seme.

Revision ID: a1c8f4e7b902
Revises: c9a2f7e4b613
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1c8f4e7b902"
down_revision: Union[str, Sequence[str], None] = "c9a2f7e4b613"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROMPTS_MAJ = {
    "ambiguite_exemples_referentiel": 'Tu écris UN ÉNONCÉ D\'EXERCICE VOLONTAIREMENT IMPARFAIT PAR MATIÈRE, pour la formation ci-dessous. Ces énoncés serviront d\'exemples de démonstration à un outil de détection d\'ambiguïtés.\n\nNiveau / formation : {niveau}\n\nMatières à traiter, une par une, dans cet ordre. Sous chaque nom figurent des EXTRAITS DU RÉFÉRENTIEL OFFICIEL de cette formation, qui disent ce que la matière recouvre réellement : ils te sont donnés pour que tu n\'aies pas à l\'interpréter. Un intitulé court comme « Langage » ou « Le besoin » ne veut rien dire hors de sa formation — ce sont les extraits qui le disent, pas ton intuition.\n{matieres}\n\nChaque énoncé doit ressembler à un vrai sujet donné par un enseignant de CETTE matière à CE niveau : même vocabulaire métier, même longueur, même ton. Un lecteur pressé ne doit rien y voir d\'anormal — les défauts sont ceux qu\'on commet sans le vouloir, pas des pièges grossiers.\n\nDans chaque énoncé, tu glisses délibérément UNE ambiguïté de chacun des types suivants, et de ceux-là seulement :\n{criteres}\n\nContraintes, pour chaque énoncé :\n- 3 paragraphes maximum, 200 mots environ. Un énoncé qu\'on colle en un geste.\n- Chaque défaut doit être réellement présent dans le texte, repérable en citant un extrait exact.\n- Aucun commentaire, aucune balise, aucune marque qui signalerait les défauts DANS l\'énoncé lui-même : il doit se lire comme un sujet ordinaire.\n- Le contenu doit être exact du point de vue de la discipline : un énoncé mal formulé, jamais un énoncé faux.\n- Le sujet doit porter sur ce que disent les extraits de CETTE matière. Ne transpose pas un intitulé dans une autre discipline parce qu\'il y ressemble.\n\nSI LES EXTRAITS NE SUFFISENT PAS À DÉTERMINER CE QUE RECOUVRE UNE MATIÈRE, tu ne l\'écris pas. Tu ne devines pas, tu ne choisis pas l\'interprétation la plus probable : tu la reportes dans le bloc final. Un exemple hors sujet serait invisible pour l\'enseignant qui le lirait.\n\nFormat de réponse — EXACTEMENT ces blocs, rien avant, rien après, aucune note, aucun commentaire, aucune remarque de ta part :\n\n### Nom exact de la première matière\n=== ENONCE ===\n(le titre du sujet puis l\'énoncé)\n\n=== DEFAUTS ===\n- Type du défaut — "extrait exact concerné" — en quoi c\'en est un\n(une ligne par défaut, dans l\'ordre des types demandés)\n\n### Nom exact de la matière suivante\n=== ENONCE ===\n...\n\n=== DEFAUTS ===\n...\n\n(et ainsi de suite pour chaque matière que tu as pu traiter)\n\n=== NON TRAITEES ===\n- Nom exact de la matière — ce que tu n\'as pas pu déterminer\n(une ligne par matière écartée ; ce bloc reste vide si tu les as toutes traitées, mais il doit toujours être présent)',
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
