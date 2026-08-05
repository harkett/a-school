# -*- coding: utf-8 -*-
"""Demande aux deux meta-prompts de placer {texte} EN TETE du prompt qu'ils redigent

POURQUOI. Les prompts de decoupe et de matieres ne sont pas ecrits a la main : une IA les REDIGE a
partir d'un referentiel exemple, sur consigne d'un meta-prompt, puis l'admin les relit. Le
meta-prompt demandait seulement de « contenir le marqueur {texte} a l'endroit ou le texte du
document sera insere » — une consigne de PRESENCE, pas de POSITION. L'IA le placait donc la ou il
tombe naturellement en francais : a la fin, apres les consignes.

Consequence mesuree le 05/08/2026 sur les quatre prompts deja generes : {texte} se trouvait en
position ~4 000 sur ~4 020 caracteres. Le document arrivait donc tout a la fin de la requete. Or
le cache de prompt du fournisseur ne sait garder qu'un PREFIXE — le debut. Sur la decoupe, qui est
l'appel LE PLUS CHER du logiciel (~70 000 tokens d'entree), l'economie etait nulle, alors que les
six prompts ecrits a la main venaient d'etre reordonnes precisement pour l'obtenir.

CE QUE FAIT CETTE MIGRATION. La consigne devient une consigne de POSITION.

REMPLACEMENT CIBLE, PAS REECRITURE. On ne reecrit PAS le prompt entier : on echange UNE LIGNE, par
`REPLACE()`. La raison est concrete — la base de developpement porte deja une version retouchee de
`prompt_meta_decoupe` (accentuee) qui differe du registre. Ecraser le texte complet aurait detruit
ce travail sans le dire. Un prompt est une donnee que l'admin possede : on y touche au scalpel.
Les deux orthographes rencontrees sont traitees, et une base ou la ligne n'existe pas est laissee
telle quelle (`REPLACE` sur une sous-chaine absente ne change rien).

CE QU'ELLE NE FAIT PAS. Elle ne touche pas aux prompts DEJA generes et valides par l'admin
(`cycles.prompt_decoupe`, `referentiels.prompt_decoupe`). Ceux-la ont ete relus et acceptes : les
reecrire mecaniquement reviendrait a modifier un texte valide sans que personne l'ait demande. Ils
continuent de fonctionner — sans l'economie, jusqu'a ce qu'on les regenere.

downgrade : remet la consigne d'origine (celle du registre, sans accents parasites).

Revision ID: fa1b5c9e7d24
Revises: f9e4c8b2a6d3
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fa1b5c9e7d24"
down_revision: Union[str, Sequence[str], None] = "f9e4c8b2a6d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# La nouvelle consigne, commune aux deux meta-prompts.
NOUVELLE = (
    "- COMMENCER par le marqueur {texte}, en toute PREMIÈRE position : le texte du document doit "
    "être le tout début du prompt, avant la moindre consigne. Aucune phrase, aucun titre, aucun "
    "mot ne doit le précéder — les consignes viennent APRÈS lui, séparées par une ligne « --- ». "
    "Rédige-les en désignant le document comme étant « ci-dessus » ;"
)

# Les formulations rencontrees. Deux orthographes pour `meta_decoupe` : celle du registre et celle,
# accentuee, qui vit en base de developpement. On traite les deux plutot que d'en imposer une.
ANCIENNES = (
    "- contenir le marqueur {texte} a l'endroit ou le texte brut du document sera insere ;",
    "- contenir le marqueur {texte} à l'endroit où le texte brut du document sera inséré ;",
    "- contenir le marqueur {texte} à l'endroit où le texte du document sera inséré ;",
    "- contenir le marqueur {texte} a l'endroit ou le texte du document sera insere ;",
)

CLES = ("prompt_meta_decoupe", "prompt_meta_matieres")


# CE QU'UNE BASE NEUVE CONTIENDRA, texte complet — ce que `tests/test_prompts_en_base.py`
# compose pour verifier que le registre et les migrations disent la meme chose. L'`upgrade`
# ci-dessous n'ecrit PAS ces textes en bloc : il echange une ligne. Sur une base neuve, ou le semis
# a pose le texte du registre, les deux reviennent au meme ; sur une base ou l'admin a retouche son
# prompt, seul le remplacement ciblé preserve son travail.
PROMPTS_MAJ = {
    "meta_decoupe": """Tu prepares le decoupage d'un referentiel officiel pour un logiciel pedagogique.

On te donne le TEXTE BRUT d'un referentiel (extrait d'un PDF) :
---
{document}
---

Ta mission : REDIGER un PROMPT de decoupe sur mesure pour CE document precis. Ce prompt sera ensuite donne a une IA pour qu'elle decoupe le document en ne gardant QUE ses vraies unites de contenu (les elements concrets et decrits que l'utilisateur exploitera : activites, fiches, competences... selon ce que contient ce document), et en ecartant tout le texte qui les entoure (page de titre, avertissements, introduction, mode d'emploi, en-tetes de partie ou de section, notes, renvois, listes de simples mentions, sources et attribution).

Le prompt que tu rediges DOIT :
- etre adapte a la structure reelle de CE document : nomme les reperes concrets que tu observes (comment une vraie unite de contenu se presente ici ; ce qui n'est que du texte d'entourage) ;
- demander, pour chaque unite retenue, UNIQUEMENT sa ligne de titre recopiee exactement telle qu'elle apparait dans le texte ;
- COMMENCER par le marqueur {texte}, en toute PREMIÈRE position : le texte du document doit être le tout début du prompt, avant la moindre consigne. Aucune phrase, aucun titre, aucun mot ne doit le précéder — les consignes viennent APRÈS lui, séparées par une ligne « --- ». Rédige-les en désignant le document comme étant « ci-dessus » ;
- imposer une sortie JSON stricte : {"unites":[{"titre":"..."}]} et rien d'autre autour.

Reponds UNIQUEMENT par le texte du prompt de decoupe, sans aucun commentaire autour.""",

    "meta_matieres": """Tu prépares la lecture des MATIÈRES d'un référentiel officiel pour un logiciel pédagogique.

On te donne le TEXTE BRUT d'un référentiel (extrait d'un PDF), pris comme EXEMPLE de sa famille :
---
{document}
---

Ta tâche : RÉDIGER LE PROMPT qui, appliqué à un référentiel de cette famille, en sortira la liste COMPLÈTE de ses matières. Tu ne listes aucune matière toi-même.

Observe d'abord CE document : où ses matières sont-elles énumérées ? Un tableau d'horaires, une liste d'unités, une suite de domaines, des titres de parties — chaque famille de référentiel a sa façon de faire. Décris ces repères concrets dans le prompt que tu rédiges, en reprenant les mots du document.

Le prompt que tu rédiges DOIT :
- viser la FAMILLE, pas cet exemplaire : un autre référentiel du même type doit pouvoir passer dedans (ne cite jamais une matière précise en exemple, ni un intitulé propre à ce document) ;
- dire OÙ regarder dans le document, avec les repères que tu viens d'observer ;
- exiger la liste ENTIÈRE de l'endroit repéré, ligne à ligne, y compris les sous-lignes, les enseignements secondaires et les options facultatives — ne rien laisser de côté sous prétexte que c'est un détail ;
- écarter ce qui ne concerne pas le référentiel visé : autre option du même diplôme, autre niveau, tableaux de correspondance avec un ancien programme ;
- demander le nom de chaque matière TEL QU'IL APPARAÎT dans le document (orthographe, majuscules, accents), sans le normaliser ni le reformuler ;
- demander une relecture avant de répondre : toute ligne de l'endroit repéré a-t-elle été reprise ?
- COMMENCER par le marqueur {texte}, en toute PREMIÈRE position : le texte du document doit être le tout début du prompt, avant la moindre consigne. Aucune phrase, aucun titre, aucun mot ne doit le précéder — les consignes viennent APRÈS lui, séparées par une ligne « --- ». Rédige-les en désignant le document comme étant « ci-dessus » ;
- imposer une sortie JSON stricte : {"matieres":["...","..."]} et rien d'autre autour.

Réponds UNIQUEMENT par le texte du prompt, sans aucun commentaire autour.""",

}


def _echanger(avant: tuple, apres: str) -> None:
    bind = op.get_bind()
    for cle in CLES:
        for ancienne in avant:
            bind.execute(
                sa.text("UPDATE settings SET value = REPLACE(value, :a, :b) WHERE key = :k"),
                {"a": ancienne, "b": apres, "k": cle},
            )


def upgrade() -> None:
    _echanger(ANCIENNES, NOUVELLE)


def downgrade() -> None:
    # On remet la formulation du REGISTRE : celle qui accompagne le code, sans supposer laquelle
    # des variantes accentuees etait en place avant.
    bind = op.get_bind()
    bind.execute(
        sa.text("UPDATE settings SET value = REPLACE(value, :a, :b) WHERE key = 'prompt_meta_decoupe'"),
        {"a": NOUVELLE,
         "b": "- contenir le marqueur {texte} a l'endroit ou le texte brut du document sera insere ;"},
    )
    bind.execute(
        sa.text("UPDATE settings SET value = REPLACE(value, :a, :b) WHERE key = 'prompt_meta_matieres'"),
        {"a": NOUVELLE,
         "b": "- contenir le marqueur {texte} à l'endroit où le texte du document sera inséré ;"},
    )
