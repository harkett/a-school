# -*- coding: utf-8 -*-
"""Le bouton « Propose-moi un exemple » de l'ecran « Detecter les ambiguites »

L'enonce d'exemple que le professeur charge sur cet ecran est ECRIT A LA DEMANDE, pour son
couple, ancre sur les extraits de son referentiel — le meme geste que « Document d'exemple » et
« Propose-moi une idee » : un clic, un appel, rien de range en base. Un texte de demonstration
n'a aucune raison d'etre le meme deux fois.

Deux lignes entrent en base, celles que ce bouton exige :
  - `prompt_ambiguite_exemple_genere` : le texte du prompt (PROMPTS_MAJ, la cle que
    tests/test_prompts_en_base.py relit) ;
  - la ligne `outils_llm` de son appel, sans quoi l'admin n'aurait aucun `max_tokens` a regler
    pour lui (tests/test_outils_llm_en_base.py tombe sinon).

TEXTE GELE, VOLONTAIREMENT RECOPIE ICI (regle de b8e5f2a1c9d7).

downgrade : retire les deux lignes — la ligne de prompt SEULEMENT si elle est restee identique
au texte seme, pour ne pas effacer une correction de l'admin.

Revision ID: b2c4e8f1a7d3
Revises: f2b9d6c4a807
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c4e8f1a7d3"
down_revision: Union[str, Sequence[str], None] = "f2b9d6c4a807"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROMPTS_MAJ = {
    "ambiguite_exemple_genere": "Tu écris un ÉNONCÉ D'EXERCICE VOLONTAIREMENT IMPARFAIT, qui servira de démonstration à un outil de détection d'ambiguïtés.\n\nContexte :\n- Matière : {matiere}\n- Niveau / formation : {niveau}\n\nLes EXTRAITS DU RÉFÉRENTIEL OFFICIEL ci-dessous disent ce que cette matière recouvre réellement à ce niveau : ils te sont donnés pour que tu n'aies pas à l'interpréter. Un intitulé court comme « Langage » ou « Le besoin » ne veut rien dire hors de sa formation — ce sont les extraits qui le disent, pas ton intuition.\n\n{referentiel}\n\nTon énoncé doit ressembler à un vrai sujet donné par un enseignant de cette matière à ce niveau : même vocabulaire métier, même longueur, même ton. Un lecteur pressé ne doit rien y voir d'anormal — les défauts sont ceux qu'on commet sans le vouloir, pas des pièges grossiers.\n\nTu y glisses délibérément UNE ambiguïté de chacun des types suivants, et de ceux-là seulement :\n{criteres}\n\nContraintes :\n- 3 paragraphes maximum, 200 mots environ. Un énoncé qu'on colle en un geste.\n- Le sujet doit porter sur ce que disent les extraits ci-dessus. Ne transpose pas un intitulé dans une autre discipline parce qu'il y ressemble.\n- Chaque défaut doit être réellement présent dans le texte, repérable en citant un extrait exact.\n- Aucun commentaire, aucune balise, aucune marque qui signalerait les défauts : l'énoncé doit se lire comme un sujet ordinaire.\n- Le contenu doit être exact du point de vue de la discipline : un énoncé mal formulé, jamais un énoncé faux.\n\nFormat de réponse : le titre du sujet, puis l'énoncé, ET RIEN D'AUTRE — aucun préambule, aucune liste des défauts, aucune remarque de ta part. Ce texte part tel quel dans la zone de saisie du professeur.",
}


# L'appel rend UN enonce de 200 mots : une valeur basse de `max_tokens` suffit.
OUTILS = [
    ("ambiguite_exemple_genere", "Exemple d'enonce a la demande (ambiguites)", 251,
     "Ecrit l'enonce d'exemple que le professeur demande par « Propose-moi un exemple », pour "
     "son couple et ancre sur son referentiel. Un enonce de 200 mots : une valeur basse suffit."),
]


def upgrade() -> None:
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(
            sa.text("INSERT INTO settings (key, value) VALUES (:key, :value) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"),
            {"key": f"prompt_{cle}", "value": texte},
        )
    for outil, libelle, ordre, aide in OUTILS:
        conn.execute(sa.text(
            "INSERT INTO outils_llm (outil, libelle, aide, ordre) "
            "VALUES (:outil, :libelle, :aide, :ordre) ON CONFLICT (outil) DO NOTHING"
        ), {"outil": outil, "libelle": libelle, "aide": aide, "ordre": ordre})


def downgrade() -> None:
    conn = op.get_bind()
    for outil, _libelle, _ordre, _aide in OUTILS:
        conn.execute(sa.text("DELETE FROM outils_llm WHERE outil = :o"), {"o": outil})
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(
            sa.text("DELETE FROM settings WHERE key = :key AND value = :value"),
            {"key": f"prompt_{cle}", "value": texte},
        )
