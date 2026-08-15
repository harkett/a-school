# -*- coding: utf-8 -*-
"""seme les 4 gabarits de meta-prompt, poses sur un referentiel neuf

CE QUE CETTE MIGRATION REPARE. Un meta-prompt vit SUR le referentiel depuis d9e4b7a2c6f1
(08/08/2026) : il regarde CE document pour ecrire le prompt qui le lira, et le repli sur un
meta commun a ete retire — il faisait chercher une grille d'horaires dans un programme de creche.

Mais rien n'a ete prevu pour un referentiel NEUF. Constat du 14/08/2026, College . 4e : les
quatre colonnes vides, et l'ecran qui repond « aucun meta-prompt en base » aux quatre etapes.
Les cinq referentiels deja en service avaient les leurs — saisis a la main, un par un.

Ces quatre lignes sont donc des GABARITS, sur le modele de `prompt_gabarit_type` : recopies sur
le referentiel a sa validation, puis lui appartenant. Retoucher le gabarit ne reecrit jamais un
referentiel deja pose.

Le TEXTE est FIGE ici, jamais importe de `llm_prompts` (cf. tests/test_prompts_en_base.py).

ON CONFLICT DO NOTHING : ces quatre cles sont neuves, mais une base ou un administrateur les
aurait deja posees garde son texte.

downgrade : retire les quatre lignes semees ici.

Revision ID: e3f7b1d5a8c2
Revises: d2a8c6f4b1e9
Create Date: 2026-08-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3f7b1d5a8c2"
down_revision: Union[str, Sequence[str], None] = "d2a8c6f4b1e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Texte FIGE des 4 gabarits (cle du registre -> texte).
PROMPTS_MAJ = {
    "gabarit_meta_matieres": """Tu prépares la lecture des MATIÈRES d'un référentiel officiel pour un logiciel pédagogique.

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

Réponds UNIQUEMENT par le texte du prompt, SANS aucun commentaire.""",

    "gabarit_meta_decoupe": """Tu prépares le découpage des référentiels d'un NIVEAU de diplôme pour un logiciel pédagogique.

On te donne le TEXTE BRUT d'un référentiel (extrait d'un PDF), pris comme EXEMPLE de ce niveau :
---
{document}
---

Ta mission : RÉDIGER LE PROMPT qui découpera N'IMPORTE QUEL référentiel de ce niveau. Ce prompt sera ensuite donné à une IA pour qu'elle repère, dans le texte, à la fois les vraies unités de contenu ET les frontières qui séparent CES UNITÉS ENTRE ELLES, par un alignement qui associe à chaque titre listé une position réelle dans le texte, en respectant l'ordre. Une frontière absente ferait déborder le contenu de l'unité qui la précède ; une occurrence d'un même texte de titre non tracée dans la liste, alors que ce texte réapparaît ailleurs comme une vraie unité, peut faire échouer l'alignement de la vraie occurrence.

Le prompt que tu rédiges DOIT :
- viser le NIVEAU, pas cet exemplaire : un autre référentiel du même type doit pouvoir passer dedans, sans jamais nommer la spécialité de celui-ci ;
- décrire des FORMES, pas des codes précis. Si tu donnes un code en exemple, présente-le comme un exemple parmi d'autres, jamais comme la règle ;
- ne borner AUCUNE série : un identifiant peut compter un ou plusieurs chiffres et changer de forme d'une spécialité à l'autre. Le prompt doit exiger la série entière ;
- désigner ce qu'on écarte PAR NATURE (règlement d'examen, grille horaire, tableaux de correspondance, tableaux de synthèse, dispenses, modalités administratives, sommaire, page de titre, avertissements, introductions, mode d'emploi, en-têtes de partie ou de section, notes, renvois, sources), jamais par numéro d'annexe ou de section ;
- prévoir les documents à plusieurs options sans les supposer ;
- EXIGER UNE ENTRÉE PAR OCCURRENCE, TOUJOURS, SANS JAMAIS FUSIONNER NI JUGER : le prompt ne doit jamais demander de décider si deux occurrences désignent « la même » unité — cette décision revient à un traitement automatique ultérieur ;
- TRAITER LES MENTIONS NUES (un code ou intitulé cité dans une simple liste récapitulative, sans développement à cet endroit) COMME DES FRONTIÈRES (garder:false), jamais ignorées silencieusement si le même texte réapparaît ailleurs comme unité développée ;
- demander, pour chaque unité ET pour chaque tête de section retenue comme frontière, UNIQUEMENT sa ligne de titre recopiée EXACTEMENT telle qu'elle apparaît dans le texte — jamais son contenu, son déroulé ni son détail ;
- TRAITER LES RUBRIQUES INTERNES D'UNE UNITÉ : une unité développe son contenu à l'aide de lignes courtes de type étiquette (tâches associées, moyens et ressources, conditions de réalisation, autonomie, résultats attendus, indicateurs de performance, savoir-faire, ou tout autre nom que ce document leur donne). Le prompt généré doit INTERDIRE de les faire figurer dans la liste, que ce soit avec garder:true ou garder:false, et demander qu'elles restent à l'intérieur du texte de l'unité qui les porte ; en cas de doute sur une ligne courte de type label, s'abstenir de la lister plutôt que risquer de couper une unité de son propre contenu ;
- DISTINGUER UN EN-TÊTE RÉPÉTÉ DE SES SOUS-PARTIES : le prompt généré doit exiger qu'un intitulé de rubrique de savoirs, de connaissances ou d'enseignements qui se répète à l'identique à plusieurs endroits (en-tête de tableau, de page ou de colonne) soit traité comme une FRONTIÈRE répétée (garder:false à chaque occurrence) et jamais comme une unité, et que le contenu soit cherché dans ses sous-parties numérotées de la forme « intitulé.numéro », chacune tracée en unité (garder:true) dès lors qu'elle développe à cet endroit un contenu qui lui est propre ;
- EXIGER QU'UN TITRE SOIT UNE SEULE LIGNE PHYSIQUE, JAMAIS DEUX : le prompt généré doit interdire explicitement d'assembler un titre à partir de deux lignes voisines — y compris quand l'une porte un intitulé de regroupement (pôle, fonction, domaine) et l'autre le numéro et l'intitulé de l'unité — et exiger qu'une ligne qui paraît tronquée soit recopiée tronquée, le texte faisant foi et non ce que le titre devrait être ;
- IMPOSER UNE RECOPIE STRICTEMENT LITTÉRALE, SANS LA MOINDRE NORMALISATION : mêmes espaces (y compris une éventuelle espace entre un sigle et un chiffre), même casse, même ponctuation, même coupure en plein mot ou en pleine phrase si la ligne s'arrête là dans le texte source. Interdiction d'ajouter/supprimer un espace, d'uniformiser une casse, de compléter une ligne tronquée avec la ligne suivante, de reconstruire un titre à partir de plusieurs lignes voisines, ou de supposer qu'un code précède toujours l'intitulé sur la même ligne ;
- COMMENCER LE PROMPT GÉNÉRÉ PAR LE MARQUEUR LITTÉRAL {texte}, SEUL, SUR LA PREMIÈRE LIGNE, sans aucun mot avant lui ; la ligne suivante vide, puis "---", puis les consignes, qui désignent le document comme « ci-dessus » ;
- imposer une sortie JSON stricte avec exactement trois champs par unité : {"unites":[{"titre":"...","option":"...","garder":true}]} — "titre" la ligne de titre recopiée telle quelle, "option" la lettre de l'option concernée si le document en a plusieurs (chaîne vide sinon, ou si l'élément est commun à toutes), "garder" à true pour une vraie unité de contenu à conserver, et à false pour toute tête de section, de partie, d'annexe ou de regroupement qui sépare deux unités — y compris les mentions nues. Réponds sans aucun texte ni balise markdown autour du JSON.

Réponds UNIQUEMENT par le texte du prompt de découpe, sans aucun commentaire autour.""",

    "gabarit_meta_types": """Tu prépares la lecture des TYPES D'ACTIVITÉ d'un référentiel officiel pour un logiciel pédagogique.

Un type d'activité est un FORMAT de travail que le document met en œuvre, pas une matière ni une compétence. Tu n'en cites aucun toi-même : c'est le document lu qui les donnera.

On te donne le TEXTE BRUT d'un référentiel (extrait d'un PDF), pris comme EXEMPLE de sa famille :
---
{document}
---

Ta tâche : RÉDIGER LE PROMPT qui, appliqué à un référentiel de cette famille, en sortira la liste COMPLÈTE des types d'activité qu'il met en œuvre. Tu ne nommes aucun type toi-même.

Observe d'abord CE document : où ses formats de travail apparaissent-ils ? Des modalités décrites dans les unités, un tableau d'activités professionnelles, des verbes de mise en œuvre répétés, une partie « démarche pédagogique » — chaque famille de référentiel a sa façon de faire. Décris ces repères concrets dans le prompt que tu rédiges, en reprenant les mots du document.

Le prompt que tu rédiges DOIT :
- viser la FAMILLE, pas cet exemplaire : un autre référentiel du même type doit pouvoir passer dedans (ne cite jamais un type précis en exemple, ni un intitulé propre à ce document) ;
- dire OÙ regarder dans le document, avec les repères que tu viens d'observer ;
- s'en tenir aux formats RÉELLEMENT mis en œuvre par le document, sans compléter par ce qui se pratique ailleurs dans l'enseignement ;
- demander des libellés COURTS et lisibles (le nom du format, pas une phrase), avec les mots du document ;
- écarter ce qui n'est pas un format de travail : matières, compétences, savoirs, blocs de certification ;
- contenir le marqueur {texte} à l'endroit où le texte du document sera inséré ;
- demander une sortie JSON {"types":["...","..."]}, sans rien autour.

Réponds UNIQUEMENT par le texte du prompt, sans aucun commentaire autour""",

    "gabarit_meta_precisions": """Tu prépares la génération de PRÉCISIONS pour une activité pédagogique (logiciel pédagogique).

Une précision est une courte piste de sujet (2 à 4 mots, en minuscules) qui affine un type d'activité déjà choisi en l'ancrant dans le métier réel du référentiel — ce n'est ni une matière, ni une compétence, ni un type d'activité en soi.

On te donne le TEXTE BRUT d'un référentiel (extrait d'un PDF), pris comme EXEMPLE de sa famille :
---
{document}
---

Ta tâche : RÉDIGER LE PROMPT qui, appliqué à un référentiel de cette famille, pour un type d'activité donné, proposera 3 à 6 précisions ancrées dans le vocabulaire réel de ce document.

Observe d'abord CE document : où son vocabulaire métier concret apparaît-il (activités professionnelles, tâches, moyens et ressources, épreuves, livrables...) ? Repère les mots précis employés, que le prompt devra réutiliser plutôt que d'inventer des généralités.

Le prompt que tu rédiges DOIT :
- viser la FAMILLE, pas cet exemplaire : généralisable à un autre référentiel du même type (ne cite jamais un intitulé propre à ce document en exemple) ;
- contenir le marqueur {texte} à l'endroit où le texte du référentiel sera inséré, et le marqueur {label} à l'endroit où le type d'activité choisi sera inséré ;
- placer {texte} en tête du prompt, avant toute consigne, pour profiter du cache de préfixe ;
- exiger que chaque précision s'inspire directement du vocabulaire réel du document (activités, tâches, livrables, épreuves mentionnées) — jamais une généralité déconnectée du document ;
- adapter le contenu des précisions au type d'activité reçu via {label} sans jamais répéter ce type dans chaque précision (le mot reçu par {label} ne se réécrit pas dedans) ;
- demander entre 3 et 6 précisions, chacune 2 à 4 mots, en minuscules ;
- demander une sortie JSON {"precisions":["...","..."]}, sans rien autour.

Réponds UNIQUEMENT par le texte du prompt, sans aucun commentaire autour.""",

}


def upgrade() -> None:
    for cle, texte in PROMPTS_MAJ.items():
        op.execute(sa.text(
            "INSERT INTO settings (key, value) VALUES (:k, :v) ON CONFLICT (key) DO NOTHING"
        ).bindparams(k=f"prompt_{cle}", v=texte))


def downgrade() -> None:
    for cle in PROMPTS_MAJ:
        op.execute(sa.text("DELETE FROM settings WHERE key = :k").bindparams(k=f"prompt_{cle}"))
