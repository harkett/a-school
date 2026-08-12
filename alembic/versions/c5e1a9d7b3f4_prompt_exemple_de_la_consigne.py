# -*- coding: utf-8 -*-
"""Le prompt « Exemple de la consigne » — l'onglet jumeau de celui des ambiguites

L'ecran « Analyser une consigne » recoit le meme geste que « Detecter les ambiguites » : le
professeur clique sur « Propose-moi un exemple » et aSchool ECRIT sur-le-champ, pour SON couple
et ancree sur son referentiel, une consigne volontairement imparfaite. Le prompt d'analyse ne
sait pas ecrire — analyser et rediger sont deux actes, donc deux textes.

Une seule ligne entre en base : `prompt_consigne_exemple_genere` (PROMPTS_MAJ, la cle que
tests/test_prompts_en_base.py relit).

PAS de ligne `outils_llm` ici, VOLONTAIREMENT : la route qui appelle ce prompt n'existe pas
encore. Une ligne posee d'avance serait un reglage orphelin, et c'est exactement ce que
tests/test_outils_llm_en_base.py refuse. Elle viendra avec l'appel.

TEXTE GELE, VOLONTAIREMENT RECOPIE ICI (regle de b8e5f2a1c9d7).

downgrade : retire la ligne SEULEMENT si elle est restee identique au texte seme, pour ne pas
effacer une correction de l'admin.

Revision ID: c5e1a9d7b3f4
Revises: d7f3b1e9a5c2
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5e1a9d7b3f4"
down_revision: Union[str, Sequence[str], None] = "d7f3b1e9a5c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROMPTS_MAJ = {
    "consigne_exemple_genere": "Tu écris UNE CONSIGNE D'EXERCICE VOLONTAIREMENT IMPARFAITE, qui servira de démonstration à un outil d'analyse de consignes.\n\nContexte :\n- Matière : {matiere}\n- Niveau / formation : {niveau}\n\nLes EXTRAITS DU RÉFÉRENTIEL OFFICIEL ci-dessous disent ce que cette matière recouvre réellement à ce niveau : ils te sont donnés pour que tu n'aies pas à l'interpréter. Un intitulé court comme « Langage » ou « Le besoin » ne veut rien dire hors de sa formation — ce sont les extraits qui le disent, pas ton intuition.\n\n{referentiel}\n\nTa consigne doit ressembler à une vraie consigne donnée par un enseignant de cette matière à ce niveau : même vocabulaire métier, même longueur, même ton. Un lecteur pressé ne doit rien y voir d'anormal — les défauts sont ceux qu'on commet sans le vouloir, pas des pièges grossiers.\n\nTu y glisses délibérément des défauts relevant des axes suivants, et de ceux-là seulement :\n- Clarté linguistique — formulation floue, vague, trop longue ou mal construite\n- Précision didactique — la consigne ne dit pas exactement ce qui est attendu ni évalué\n- Ambiguïté conceptuelle — mot à double sens, terme polysémique (« analyser », « expliquer », « produit », « simplifier »…)\n- Structure logique — étape implicite, tâches multiples non séparées, saut logique\n- Risque d'erreurs typiques — formulation qui provoque une erreur récurrente chez les élèves de ce niveau\n\nContraintes :\n- UNE SEULE CONSIGNE, 2 phrases maximum, 40 mots environ. Pas un exercice, pas un sujet, pas une série de questions : l'instruction adressée à l'élève, et rien d'autre.\n- La consigne doit porter sur ce que disent les extraits ci-dessus. Ne transpose pas un intitulé dans une autre discipline parce qu'il y ressemble.\n- Chaque défaut doit être réellement présent dans le texte, repérable en citant un extrait exact.\n- Trois axes touchés suffisent : une consigne de 40 mots qui cumulerait les cinq ne ressemblerait plus à rien de crédible.\n- Aucun commentaire, aucune balise, aucune marque qui signalerait les défauts : la consigne doit se lire comme une consigne ordinaire.\n- Le contenu doit être exact du point de vue de la discipline : une consigne mal formulée, jamais une consigne fausse.\n\nFormat de réponse : la consigne, ET RIEN D'AUTRE — aucun titre, aucun préambule, aucune liste des défauts, aucune remarque de ta part. Ce texte part tel quel dans la zone de saisie du professeur.",
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
