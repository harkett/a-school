# -*- coding: utf-8 -*-
"""le gabarit meta-matieres nomme le piege des rubriques internes

CE QUE CETTE MIGRATION CORRIGE. Le gabarit pose la veille (e3f7b1d5a8c2) demandait d'ecarter
« les parties generales du programme (finalites, contributions au socle commun, reperes de
progressivite), les domaines de competences, les annexes ». Formule ainsi, il annonce un bloc
UNIQUE, pose en tete de document, qu'il suffirait de sauter.

C'est faux. Mesure du 14/08/2026 sur le texte epure du programme du cycle 4 : « Attendus de fin
de cycle » y revient 34 fois, « Reperes de progressivite » 17 fois, « Competences travaillees »
13 fois — soit exactement le nombre d'enseignements — et « Croisements entre enseignements »
11 fois. Ce sont des RUBRIQUES INTERNES, repetees a l'identique dans chaque matiere. Un modele
qui suit l'ancienne consigne cherche une section a ecarter la ou elle n'est pas, et rend une
liste gonflee de fausses matieres.

La lecon etait deja tiree cote DECOUPE — le gabarit `gabarit_meta_decoupe` consacre deux puces
entieres aux rubriques internes et aux en-tetes repetes, heritees du BTS CIEL. Elle n'avait
jamais ete portee cote MATIERES.

DEUXIEME CHANGEMENT, de forme. Le gabarit deroulait huit puces « le prompt DOIT ». Ces
meta-prompts sont executes par les modeles de raisonnement les plus recents, sur lesquels une
consigne trop prescriptive DEGRADE la sortie. Le nouveau texte pose le probleme (la difficulte
principale, nommee) et laisse la methode au modele, en ne gardant en imperatif que les
contraintes de forme non negociables : marqueur {texte} en tete, sortie JSON stricte, aucun
intitulé reel cite.

UPDATE CONDITIONNEL. Le remplacement ne s'applique QUE si la base porte encore, mot pour mot,
le texte de e3f7b1d5a8c2. Un gabarit retouche a la main par un administrateur n'est pas ecrase.

CE QUI NE BOUGE PAS. Un gabarit n'est qu'un modele recopie sur le referentiel a sa validation :
les referentiels DEJA poses gardent leur meta-prompt, cette migration ne les touche pas.

Les DEUX textes sont FIGES ici, jamais importes de `llm_prompts` (cf. tests/test_prompts_en_base.py).

downgrade : remet le texte de e3f7b1d5a8c2, aux memes conditions.

Revision ID: b6e2c4a9f7d1
Revises: e3f7b1d5a8c2
Create Date: 2026-08-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b6e2c4a9f7d1"
down_revision: Union[str, Sequence[str], None] = "e3f7b1d5a8c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CLE = "gabarit_meta_matieres"

ANCIEN = """Tu prépares la lecture des MATIÈRES d'un référentiel officiel pour un logiciel pédagogique.

On te donne le TEXTE BRUT d'un référentiel (extrait d'un PDF) :
---
{document}
---

Ta tâche : RÉDIGER LE PROMPT qui, appliqué à ce référentiel, en sortira la liste COMPLÈTE de ses matières. Tu ne listes aucune matière toi-même — tu écris seulement le prompt qui les fera lister.

D'abord, observe ce document : à quel endroit précis ses matières sont-elles énumérées ? (grille d'horaires, liste d'unités, suite de domaines ou d'enseignements, titres de parties…). Repère l'endroit qui fait FOI — celui qui porte la liste la plus complète — et note les mots exacts qui le délimitent : titre de section, en-têtes de colonnes, formulation récurrente.

Le prompt que tu rédiges DOIT :
- dire OÙ regarder, en citant les repères concrets que tu viens d'observer dans le document ;
- exiger la liste ENTIÈRE de cet endroit, ligne à ligne : sous-lignes, enseignements secondaires et options facultatives compris — ne rien écarter sous prétexte que c'est un détail ;
- exclure ce qui ne relève pas du référentiel lu : autre option du même diplôme, autre niveau, tableaux de correspondance avec un ancien programme ;
- rendre chaque nom de matière TEL QU'IL APPARAÎT (orthographe, majuscules, accents), sans le normaliser ni le reformuler ;
- ne JAMAIS citer en exemple une matière réelle ni un intitulé propre à ce document : le prompt décrit où et comment lire, pas quoi trouver ;
- imposer une relecture avant de répondre : chaque ligne de l'endroit repéré a-t-elle bien été reprise ?
- COMMENCER par le marqueur {texte} en TOUTE PREMIÈRE position — le document ouvre le prompt, avant la moindre consigne ; les consignes viennent APRÈS, séparées par une ligne « --- », et désignent le document comme « ci-dessus » ;
- imposer une sortie JSON stricte : {"matieres":["...","..."]} et rien autour.

Réponds UNIQUEMENT par le texte du prompt, SANS aucun commentaire."""


NOUVEAU = """Un logiciel pédagogique doit extraire, d'un référentiel officiel, la liste complète de ses matières. Ce n'est pas toi qui les listes : tu rédiges le PROMPT qui les fera lister par un autre modèle, à qui on donnera ce même document.

Le document :
---
{document}
---

Lis-le d'abord pour comprendre comment il est bâti. Repère où ses matières sont énumérées — grille d'horaires, liste d'unités, suite de domaines ou d'enseignements, titres de parties. Un référentiel les annonce souvent à deux endroits : une liste récapitulative, puis une partie développée où chacune a sa section. Ces deux endroits ne concordent pas toujours. Décide lequel fait foi, et note les mots exacts qui permettent de le retrouver : titre de section, en-têtes de colonnes, formulation récurrente.

LA DIFFICULTÉ PRINCIPALE, celle qui fait échouer les lectures naïves : dans la partie développée, chaque matière est structurée par les mêmes rubriques internes, qui reviennent donc autant de fois qu'il y a de matières — quel que soit le nom que ce document leur donne. Elles ressemblent à des titres et occupent la même place qu'eux. Un lecteur pressé les prend pour des matières et rend une liste gonflée de fausses entrées. Le prompt que tu écris doit protéger son lecteur de cette confusion : à toi de trouver comment, en t'appuyant sur ce que tu observes réellement dans ce document.

Le prompt devra aussi :
- exiger la liste ENTIÈRE de l'endroit qui fait foi, ligne à ligne — sous-lignes, enseignements secondaires et options facultatives compris, rien écarté sous prétexte que c'est un détail ;
- écarter ce qui ne relève pas du référentiel lu : autre option du même diplôme, autre niveau ou autre année quand le document en couvre plusieurs, tableaux de correspondance avec un ancien programme, annexes administratives ;
- rendre chaque intitulé TEL QU'IL APPARAÎT — orthographe, majuscules, accents, parenthèses comprises — sans le raccourcir ni le reformuler ; une mise en page peut couper un intitulé, c'est le texte qui fait foi.

Deux contraintes de forme, non négociables :
- le prompt commence par le marqueur littéral {texte}, seul sur sa première ligne, sans un mot avant lui ; puis une ligne vide, puis « --- », puis les consignes, qui désignent le document comme « ci-dessus » ;
- il impose une sortie JSON stricte : {"matieres":["...","..."]} et rien autour.

Enfin, une règle qui prime sur tout le reste : ton prompt ne doit citer AUCUNE matière réelle ni aucun intitulé propre à ce document. Il décrit où et comment lire, jamais quoi trouver — sinon il souffle la réponse et l'on ne peut plus vérifier le travail.

Réponds uniquement par le texte du prompt, sans aucun commentaire autour."""


# Le texte QUE PORTERA une base neuve, sous la forme attendue par tests/test_prompts_en_base.py :
# ce fichier compose le seed d'origine avec les `PROMPTS_MAJ` de la chaine.
PROMPTS_MAJ = {CLE: NOUVEAU}


def _remplacer(avant: str, apres: str) -> None:
    """UPDATE conditionnel : le gabarit retouche a la main par un administrateur n'est pas ecrase."""
    op.execute(sa.text(
        "UPDATE settings SET value = :apres WHERE key = :k AND value = :avant"
    ).bindparams(k=f"prompt_{CLE}", avant=avant, apres=apres))


def upgrade() -> None:
    _remplacer(ANCIEN, NOUVEAU)


def downgrade() -> None:
    _remplacer(NOUVEAU, ANCIEN)
