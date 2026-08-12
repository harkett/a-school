# -*- coding: utf-8 -*-
"""Le prompt « Exemple de la consigne » recoit le marqueur que sa route attend depuis toujours

`analyse/consigne.py` guette « === PAS DE CONSIGNE === » dans la reponse du modele et en fait un
refus motive, montre au professeur. Le marqueur n etait ECRIT DANS AUCUN PROMPT : le modele ne
pouvait pas repondre par une convention qu on ne lui avait pas donnee. Le droit de ne pas ecrire
existait dans le code et ne s est jamais declenche une seule fois.

Consequence concrete : faute d extraits parlants, le modele ecrivait quand meme une consigne —
plausible, mais devinee hors du programme du couple. Le professeur, lui, la croyait tiree de SA
formation. C est exactement ce que le refus devait empecher.

Le texte gagne donc le bloc de sortie, calque sur celui du prompt d exemple de l equite
(a7d3f9c2e5b8), ou il a ete ecrit correctement des le premier jour.

TEXTE GELE, VOLONTAIREMENT RECOPIE ICI (regle de b8e5f2a1c9d7).

downgrade : remet le texte sans le bloc de refus (fige lui aussi).

Revision ID: d2a8c6f4b1e9
Revises: c9b4e7a2d6f3
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2a8c6f4b1e9"
down_revision: Union[str, Sequence[str], None] = "c9b4e7a2d6f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROMPTS_MAJ = {
    "consigne_exemple_genere": "Tu écris UNE CONSIGNE D'EXERCICE VOLONTAIREMENT IMPARFAITE, qui servira de démonstration à un outil d'analyse de consignes.\n\nContexte :\n- Matière : {matiere}\n- Niveau / formation : {niveau}\n\nLes EXTRAITS DU RÉFÉRENTIEL OFFICIEL ci-dessous disent ce que cette matière recouvre réellement à ce niveau : ils te sont donnés pour que tu n'aies pas à l'interpréter. Un intitulé court comme « Langage » ou « Le besoin » ne veut rien dire hors de sa formation — ce sont les extraits qui le disent, pas ton intuition.\n\n{referentiel}\n\nTa consigne doit ressembler à une vraie consigne donnée par un enseignant de cette matière à ce niveau : même vocabulaire métier, même longueur, même ton. Un lecteur pressé ne doit rien y voir d'anormal — les défauts sont ceux qu'on commet sans le vouloir, pas des pièges grossiers.\n\nTu y glisses délibérément des défauts relevant des axes suivants, et de ceux-là seulement :\n- Clarté linguistique — formulation floue, vague, trop longue ou mal construite\n- Précision didactique — la consigne ne dit pas exactement ce qui est attendu ni évalué\n- Ambiguïté conceptuelle — mot à double sens, terme polysémique (« analyser », « expliquer », « produit », « simplifier »…)\n- Structure logique — étape implicite, tâches multiples non séparées, saut logique\n- Risque d'erreurs typiques — formulation qui provoque une erreur récurrente chez les élèves de ce niveau\n\nContraintes :\n- UNE SEULE CONSIGNE, 2 phrases maximum, 40 mots environ. Pas un exercice, pas un sujet, pas une série de questions : l'instruction adressée à l'élève, et rien d'autre.\n- La consigne doit porter sur ce que disent les extraits ci-dessus. Ne transpose pas un intitulé dans une autre discipline parce qu'il y ressemble.\n- Chaque défaut doit être réellement présent dans le texte, repérable en citant un extrait exact.\n- Trois axes touchés suffisent : une consigne de 40 mots qui cumulerait les cinq ne ressemblerait plus à rien de crédible.\n- Aucun commentaire, aucune balise, aucune marque qui signalerait les défauts : la consigne doit se lire comme une consigne ordinaire.\n- Le contenu doit être exact du point de vue de la discipline : une consigne mal formulée, jamais une consigne fausse.\n\nSI LES EXTRAITS NE TE PERMETTENT PAS d'écrire une consigne juste du point de vue de la discipline — trop courts, hors sujet, ou muets sur ce qui s'enseigne réellement — n'invente RIEN. Réponds alors exactement ceci, et rien d'autre :\n=== PAS DE CONSIGNE ===\nRaison : (une phrase disant ce qui manque, adressée au professeur)\n\nFormat de réponse : la consigne, ET RIEN D'AUTRE — aucun titre, aucun préambule, aucune liste des défauts, aucune remarque de ta part. Ce texte part tel quel dans la zone de saisie du professeur.",
}


_AVANT = {
    "consigne_exemple_genere": "Tu écris UNE CONSIGNE D'EXERCICE VOLONTAIREMENT IMPARFAITE, qui servira de démonstration à un outil d'analyse de consignes.\n\nContexte :\n- Matière : {matiere}\n- Niveau / formation : {niveau}\n\nLes EXTRAITS DU RÉFÉRENTIEL OFFICIEL ci-dessous disent ce que cette matière recouvre réellement à ce niveau : ils te sont donnés pour que tu n'aies pas à l'interpréter. Un intitulé court comme « Langage » ou « Le besoin » ne veut rien dire hors de sa formation — ce sont les extraits qui le disent, pas ton intuition.\n\n{referentiel}\n\nTa consigne doit ressembler à une vraie consigne donnée par un enseignant de cette matière à ce niveau : même vocabulaire métier, même longueur, même ton. Un lecteur pressé ne doit rien y voir d'anormal — les défauts sont ceux qu'on commet sans le vouloir, pas des pièges grossiers.\n\nTu y glisses délibérément des défauts relevant des axes suivants, et de ceux-là seulement :\n- Clarté linguistique — formulation floue, vague, trop longue ou mal construite\n- Précision didactique — la consigne ne dit pas exactement ce qui est attendu ni évalué\n- Ambiguïté conceptuelle — mot à double sens, terme polysémique (« analyser », « expliquer », « produit », « simplifier »…)\n- Structure logique — étape implicite, tâches multiples non séparées, saut logique\n- Risque d'erreurs typiques — formulation qui provoque une erreur récurrente chez les élèves de ce niveau\n\nContraintes :\n- UNE SEULE CONSIGNE, 2 phrases maximum, 40 mots environ. Pas un exercice, pas un sujet, pas une série de questions : l'instruction adressée à l'élève, et rien d'autre.\n- La consigne doit porter sur ce que disent les extraits ci-dessus. Ne transpose pas un intitulé dans une autre discipline parce qu'il y ressemble.\n- Chaque défaut doit être réellement présent dans le texte, repérable en citant un extrait exact.\n- Trois axes touchés suffisent : une consigne de 40 mots qui cumulerait les cinq ne ressemblerait plus à rien de crédible.\n- Aucun commentaire, aucune balise, aucune marque qui signalerait les défauts : la consigne doit se lire comme une consigne ordinaire.\n- Le contenu doit être exact du point de vue de la discipline : une consigne mal formulée, jamais une consigne fausse.\n\nFormat de réponse : la consigne, ET RIEN D'AUTRE — aucun titre, aucun préambule, aucune liste des défauts, aucune remarque de ta part. Ce texte part tel quel dans la zone de saisie du professeur.",
}


_SQL = sa.text(
    "INSERT INTO settings (key, value) VALUES (:key, :value) "
    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
)


def _ecrire(textes: dict) -> None:
    conn = op.get_bind()
    for cle, texte in textes.items():
        conn.execute(_SQL, {"key": f"prompt_{cle}", "value": texte})


def upgrade() -> None:
    _ecrire(PROMPTS_MAJ)


def downgrade() -> None:
    _ecrire(_AVANT)
