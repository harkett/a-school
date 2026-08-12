# -*- coding: utf-8 -*-
"""Le bouton « Propose-moi un exemple » de l'ecran Equite : son prompt et sa longueur

Le troisieme et dernier exemplaire du meme geste (ambiguites, consignes, equite) : le
professeur clique, aSchool ECRIT sur-le-champ — pour SON couple, ancree sur son referentiel —
une evaluation volontairement inequitable, et l'analyse a donc quelque chose a y trouver. Un
clic, un appel, un texte pose dans la zone : rien n'est range en base.

Le prompt d'analyse ne sait pas ecrire : analyser et rediger sont deux actes, donc deux textes.

CE PROMPT A LE DROIT DE NE PAS ECRIRE, et contrairement a son jumeau des consignes, il le SAIT :
le marqueur « === PAS D'EXEMPLE === » est ECRIT DANS LE TEXTE, avec la consigne de s'en servir
quand les extraits ne disent pas assez ce que la matiere recouvre a ce niveau. La route le
reconnait et en fait un refus motive. Un marqueur que seul le serveur connaitrait ne se
declencherait jamais : le modele ne peut pas repondre par une convention qu'on ne lui a pas
donnee.

Deux lignes entrent en base :
  1. `settings.prompt_equite_exemple_genere` (PROMPTS_MAJ, la cle que
     tests/test_prompts_en_base.py relit) ;
  2. `outils_llm` pour `get_max_tokens(db, "equite_exemple_genere")` — l'appel arrive dans le
     meme lot, la ligne n'est donc pas orpheline (ce que tests/test_outils_llm_en_base.py
     refuse).

La FONCTIONNALITE `analyse_equite` a deja ete posee par f4c8a2e6d9b3 : les deux prompts de
l'ecran se rangent sous le meme onglet d'administration, comme chez les ambiguites.

TEXTE GELE, VOLONTAIREMENT RECOPIE ICI (regle de b8e5f2a1c9d7).

downgrade : retire les deux lignes. Le prompt n'est retire que s'il est reste identique au
texte seme, pour ne pas effacer une correction de l'admin.

Revision ID: a7d3f9c2e5b8
Revises: f4c8a2e6d9b3
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7d3f9c2e5b8"
down_revision: Union[str, Sequence[str], None] = "f4c8a2e6d9b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROMPTS_MAJ = {
    "equite_exemple_genere": "Tu écris UNE ÉVALUATION COURTE VOLONTAIREMENT INÉQUITABLE, qui servira de démonstration à un outil d'analyse d'équité.\n\nContexte :\n- Matière : {matiere}\n- Niveau / formation : {niveau}\n\nLes EXTRAITS DU RÉFÉRENTIEL OFFICIEL ci-dessous disent ce que cette matière recouvre réellement à ce niveau : ils te sont donnés pour que tu n'aies pas à l'interpréter. Un intitulé court comme « Langage » ou « Le besoin » ne veut rien dire hors de sa formation — ce sont les extraits qui le disent, pas ton intuition.\n\n{referentiel}\n\nTon évaluation doit ressembler à un vrai sujet donné par un enseignant de cette matière à ce niveau : même vocabulaire métier, même longueur, même ton, points indiqués entre parenthèses après chaque question. Un lecteur pressé ne doit rien y voir d'anormal — les défauts d'équité sont ceux qu'on commet sans le vouloir, jamais des provocations.\n\nTu y glisses délibérément des défauts relevant des biais suivants, et de ceux-là seulement :\n{criteres}\n\nContraintes :\n- UNE évaluation courte : un intitulé, une durée annoncée, 3 ou 4 questions, 150 mots environ. Pas un sujet d'examen complet.\n- L'évaluation doit porter sur ce que disent les extraits ci-dessus. Ne transpose pas un intitulé dans une autre discipline parce qu'il y ressemble.\n- Trois biais suffisent : un sujet de 150 mots qui les cumulerait tous ne ressemblerait plus à rien de crédible.\n- Chaque défaut doit être réellement présent dans le texte, repérable en citant un passage exact.\n- Aucun commentaire, aucune balise, aucune marque qui signalerait les défauts : le sujet doit se lire comme un sujet ordinaire.\n- Le contenu doit être exact du point de vue de la discipline : une évaluation inéquitable, jamais une évaluation fausse.\n- Ne vise JAMAIS un groupe d'élèves de façon insultante. Un biais d'équité est un implicite ordinaire — un contexte de vacances, un matériel supposé, un temps trop court — pas une moquerie.\n\nSI LES EXTRAITS NE TE PERMETTENT PAS d'écrire une évaluation juste du point de vue de la discipline — trop courts, hors sujet, ou muets sur ce qui s'enseigne réellement — n'invente RIEN. Réponds alors exactement ceci, et rien d'autre :\n=== PAS D'EXEMPLE ===\nRaison : (une phrase disant ce qui manque, adressée au professeur)\n\nFormat de réponse : l'évaluation, ET RIEN D'AUTRE — aucun titre ajouté, aucun préambule, aucune liste des défauts, aucune remarque de ta part. Ce texte part tel quel dans la zone de saisie du professeur.",
}


OUTILS = [
    ("equite_exemple_genere", "Exemple d'évaluation à la demande (équité)", 56,
     "Écrit l'évaluation d'exemple que le professeur demande par « Propose-moi un "
     "exemple », pour son couple et ancrée sur son référentiel. Un sujet court "
     "(150 mots environ) : une valeur basse suffit."),
]


def upgrade() -> None:
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(sa.text(
            "INSERT INTO settings (key, value) VALUES (:key, :value) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
        ), {"key": f"prompt_{cle}", "value": texte})

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
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key AND value = :value"),
                     {"key": f"prompt_{cle}", "value": texte})
