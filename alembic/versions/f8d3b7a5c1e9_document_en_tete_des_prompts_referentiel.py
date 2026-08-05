# -*- coding: utf-8 -*-
"""Met le DOCUMENT EN TETE des six prompts qui lisent un referentiel entier

POURQUOI. Six outils envoient le referentiel COMPLET (~70 000 tokens) pour rendre trois lignes :
decoupe, detection des matieres, detection des types d'activite, verification du couple, detection
du couple, suggestion de precisions. Un depot de referentiel paie donc cinq a six fois le meme
document. C'est le poste de depense numero un du logiciel.

Anthropic sait ne facturer que 10 % d'un PREFIXE DEJA VU (prompt caching). Mais un prefixe, c'est
le DEBUT de la requete, au caractere pres. Or chacun de ces prompts commencait par sa propre
introduction — 40 a 80 tokens differents d'un outil a l'autre — avant d'injecter le document :

    "Tu lis un referentiel officiel et tu en degages la liste des MATIERES...

     Texte du referentiel :
     {texte}
     ..."

Deux outils n'avaient donc AUCUN prefixe commun, et le cache n'aurait strictement rien rapporte.
Trois d'entre eux etaient pires encore : `verifier_couple`, `detecter_couple` et
`suggerer_precisions_type` inseraient des VARIABLES ({cycle}, {niveau}, {cycles_existants},
{label}) avant le document — un texte qui change a chaque appel, donc un prefixe qui ne se repete
meme pas d'un appel a l'autre du MEME outil.

CE QUE FAIT CETTE MIGRATION. `{texte}` passe en toute premiere position ; l'introduction, les
variables et les consignes descendent apres, derriere un separateur. Le document devient alors le
prefixe commun aux six outils : le premier appel le paie, les cinq suivants le relisent a 10 %.

CE N'EST PAS UN COMPROMIS SUR LA QUALITE. Placer un long document AVANT la question est la forme
recommandee pour les prompts longs : le modele lit la matiere, puis ce qu'on lui demande d'en
faire. Aucune consigne n'est retiree ni reformulee au fond — seul l'ORDRE change, et le texte qui
annoncait le document ("Texte du referentiel :") devient un rappel qui le suit ("Ci-dessus...").

POURQUOI EN BASE ET PAS A L'ENVOI. On aurait pu reassembler la requete dans le moteur en laissant
les prompts tels quels. C'aurait fait mentir l'ecran admin : l'administrateur lit un prompt qui
commence par une phrase, alors que le modele en recevrait un autre. La regle de la maison est que
l'ecran dit ce que le code fait. Le prompt change donc LA, ou l'admin le voit.

PROMPTS_MAJ expose les textes figes : c'est ce que `tests/test_prompts_en_base.py` compose pour
verifier qu'une installation neuve recoit exactement ce que dit le registre.

downgrade : remet les six textes d'origine.

Revision ID: f8d3b7a5c1e9
Revises: f5b8d3c1a9e7
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# `f5b8d3c1a9e7` et non `d4f6b8a0c2e3` : deux migrations (types d'activite par referentiel, puis
# ses prompts) se sont posees entre-temps. Se chainer derriere la tete REELLE evite une branche —
# et surtout, `f5b8d3c1a9e7` touche lui aussi `detecter_types_activite` : passer apres lui est ce
# qui garantit que c'est bien ce texte-ci qu'une installation neuve recevra.
# L'IDENTIFIANT N'EST PAS TIRE AU HASARD. `tests/test_prompts_en_base.py` rejoue les mises a jour
# de prompts en suivant la chaine `down_revision`, et se rabat sur l'ORDRE ALPHABETIQUE des que
# deux migrations a `PROMPTS_MAJ` ne se suivent pas immediatement — ce qui est le cas ici. Un
# identifiant en « a… » aurait donc ete rejoue AVANT `f5b8d3c1a9e7`, qui touche lui aussi
# `detecter_types_activite` : ce test aurait signale une divergence a jamais. « f8… » trie apres
# tous les identifiants deja poses, ce qui est aussi l'ordre reel de la chaine.
revision: str = "f8d3b7a5c1e9"
down_revision: Union[str, Sequence[str], None] = "f5b8d3c1a9e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROMPTS_MAJ = {
    "decoupe_amont": """{texte}

---

Ci-dessus, le TEXTE BRUT d'un référentiel officiel, extrait d'un PDF. Tu ne connais rien de ce document à l'avance : tu le comprends en le lisant.

Ta mission : DÉCOUPER ce document et ne garder QUE ses vraies UNITÉS DE CONTENU. Une unité de contenu = un élément concret, décrit pour lui-même avec sa propre description, que l'utilisateur exploitera directement (par exemple une activité, une fiche, une compétence…) — tu déduis leur nature en lisant, on ne te souffle aucun critère.

Ne retiens QUE ces unités. Le texte qui ENTOURE les unités n'est PAS une unité, tu l'écartes entièrement :
- la page de titre, les avertissements et mentions (ex. « DOCUMENT DE TRAVAIL ») ;
- l'introduction, le mode d'emploi, les explications générales de cadrage ;
- les en-têtes de partie ou de domaine qui ne font qu'annoncer une section (ex. « DOMAINE 1 - Parler et réfléchir ») ;
- les listes de Sources, d'attribution ou de références ;
- tout RENVOI ou pointeur vers une unité décrite ailleurs (une ligne « voir … » ou marquée « (renvoi) ») : ne garde jamais un pointeur qui répète une unité déjà présente ;
- tout élément SEULEMENT MENTIONNÉ dans une liste (par exemple une section « à valider », une énumération à puces) : une simple puce d'une ou deux lignes, sans description propre, n'est PAS une unité même si elle nomme une activité.

Repère qui tranche : une vraie unité a SA PROPRE description complète (de quoi la réaliser en la lisant : son matériel, ses objectifs, son déroulé…). Un titre de section, un texte de cadrage, un renvoi ou une simple puce de liste n'ont pas cette description — ils présentent, encadrent ou évoquent les unités, mais n'en sont pas : on les écarte.

Pour chaque unité RETENUE, rends UNIQUEMENT la LIGNE DE TITRE qui la commence, RECOPIÉE EXACTEMENT telle qu'elle apparaît dans le texte (mêmes mots, même casse, rien ajouté, rien enlevé). Tu ne réécris pas le contenu : la ligne de titre sert à retrouver la frontière dans le texte réel.

Format — JSON strict, rien autour :
{{
  "unites": [
    {{ "titre": "la ligne de titre exacte qui commence l'unité" }}
  ]
}}

Règles :
- Une entrée par unité, dans l'ORDRE du document.
- Recopie chaque titre À L'IDENTIQUE depuis le texte. N'invente aucun titre, n'en fusionne pas deux.
- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON.""",

    "detecter_matieres": """{texte}

---

Ci-dessus, le texte d'un référentiel officiel. Tu le lis et tu en dégages la liste des MATIÈRES (disciplines, domaines d'apprentissage) qu'il structure à ce niveau.

Ta tâche :
- Repère les matières, disciplines ou domaines d'apprentissage que ce référentiel organise (ses grands champs).
- Donne le nom de chaque matière TEL QU'IL APPARAÎT DANS LE DOCUMENT : son orthographe, ses majuscules, ses accents. Ce document nomme SES matières ; il n'y a aucune liste extérieure à laquelle les ramener, et aucun nom à normaliser.
- Garde des noms courts et lisibles : le nom de la matière, pas une phrase ni un intitulé de chapitre.
- Ne sépare jamais un intitulé qui désigne UNE seule discipline, même si son nom est composé (par exemple « Prévention-santé-environnement » ou « Éducation physique et sportive » restent entières).
- Sépare en revanche un intitulé qui en énumère visiblement plusieurs (par exemple « Mathématiques et physique-chimie » donne deux matières), en gardant pour chacune le nom que le document lui donne.

Règle :
- "matieres" : la liste des noms de matières, sans doublon.
- N'invente aucune matière absente du document. Si aucune n'apparaît clairement, renvoie une liste vide.

Réponds UNIQUEMENT en JSON, avec exactement cette clé : matieres (un tableau de chaînes).""",

    "detecter_types_activite": """{texte}

---

Ci-dessus, le texte d'un référentiel officiel. Tu le lis et tu en dégages la liste des TYPES D'ACTIVITÉ (formats ou modalités d'activité pédagogique) qu'il met en œuvre à ce niveau.

Ta tâche :
- Repère les types d'activité, formats ou modalités de travail que ce référentiel met réellement en œuvre (par exemple : atelier, mise en situation, travaux pratiques, projet, évaluation — selon ce qui apparaît réellement).
- Donne le nom de chaque type TEL QU'IL RESSORT DU DOCUMENT : ses mots, son orthographe. Ce document met en œuvre SES formats de travail ; il n'existe aucune liste extérieure à laquelle les ramener, et aucun libellé à normaliser.
- Garde des libellés courts et lisibles : le nom du type, pas une phrase ni un intitulé de chapitre.

Règle :
- "types" : la liste des libellés de types d'activité, sans doublon.
- N'invente aucun type absent du document. Si aucun n'apparaît clairement, renvoie une liste vide.

Réponds UNIQUEMENT en JSON, avec exactement cette clé : types (un tableau de chaînes).""",

    "verifier_couple": """{texte}

---

Ci-dessus, le texte d'un document officiel. Tu vérifies qu'il correspond bien au couple (cycle + niveau) déclaré.

Couple déclaré par l'administrateur :
- Cycle : {cycle}
- Niveau : {niveau}

Ta tâche :
- Lis à quel cycle et à quel niveau ce document s'adresse réellement.
- Dis s'il correspond au couple déclaré ci-dessus.

Règle :
- "correspond" = true si le document vise bien ce cycle et ce niveau (même si la formulation diffère), false sinon.
- "niveau_lu" : le cycle et le niveau que le document vise réellement, tels que tu les lis (une courte phrase).
- "raison" : pourquoi cela correspond ou non, en une phrase.

Réponds UNIQUEMENT en JSON, avec exactement ces clés : correspond, niveau_lu, raison.""",

    "detecter_couple": """{texte}

---

Ci-dessus, le début d'un référentiel officiel. Tu le lis et tu identifies à quel CYCLE et à quel NIVEAU (diplôme, spécialité ou tranche d'âge) il s'adresse.

Cycles et niveaux déjà connus de l'application (un cycle par ligne, suivi de ses niveaux) :
{cycles_existants}

Ta tâche :
- Lis à quel cycle et à quel niveau ce document s'adresse réellement.
- Fais CORRESPONDRE ce que tu lis avec la liste ci-dessus :
  - Si le cycle visé correspond à un cycle de la liste, reprends EXACTEMENT son nom (même orthographe, mêmes majuscules).
  - Si le niveau visé correspond à un niveau de ce cycle dans la liste, reprends EXACTEMENT son nom.
  - Sinon, donne le nom tel qu'il ressort du document, court et lisible (le nom exact du diplôme ou du niveau, pas une phrase).

Règle :
- "cycle_lu" : le cycle visé par le document (nom de la liste si correspondance, sinon nom lu). Chaîne vide si le document ne permet pas de le dire.
- "niveau_lu" : le niveau, diplôme ou spécialité visé (nom de la liste si correspondance, sinon nom lu). Chaîne vide si le document ne permet pas de le dire.
- N'invente rien : la liste sert à faire correspondre, jamais à choisir un cycle que le document ne vise pas.

Réponds UNIQUEMENT en JSON, avec exactement ces clés : cycle_lu, niveau_lu.""",

    "suggerer_precisions_type": """{texte}

---

Ci-dessus, le référentiel officiel sur lequel t'appuyer pour rester dans le programme.

Tu es un concepteur pédagogique.
Pour le type d'activité « {label} » enseigné au niveau « {niveau} », propose 3 à 6 PRÉCISIONS : des déclinaisons concrètes de ce type, réellement adaptées à ce niveau (ni trop enfantines, ni trop avancées).

Rends UNIQUEMENT des libellés courts (2 à 4 mots), en minuscules.""",
}


# Les textes d'AVANT, pour le downgrade. Recopies tels qu'ils etaient semes.
PROMPTS_AVANT = {
    "decoupe_amont": """Tu reçois le TEXTE BRUT d'un référentiel officiel, extrait d'un PDF. Tu ne connais rien de ce document à l'avance : tu le comprends en le lisant.

Texte brut :
{texte}

Ta mission : DÉCOUPER ce document et ne garder QUE ses vraies UNITÉS DE CONTENU. Une unité de contenu = un élément concret, décrit pour lui-même avec sa propre description, que l'utilisateur exploitera directement (par exemple une activité, une fiche, une compétence…) — tu déduis leur nature en lisant, on ne te souffle aucun critère.

Ne retiens QUE ces unités. Le texte qui ENTOURE les unités n'est PAS une unité, tu l'écartes entièrement :
- la page de titre, les avertissements et mentions (ex. « DOCUMENT DE TRAVAIL ») ;
- l'introduction, le mode d'emploi, les explications générales de cadrage ;
- les en-têtes de partie ou de domaine qui ne font qu'annoncer une section (ex. « DOMAINE 1 - Parler et réfléchir ») ;
- les listes de Sources, d'attribution ou de références ;
- tout RENVOI ou pointeur vers une unité décrite ailleurs (une ligne « voir … » ou marquée « (renvoi) ») : ne garde jamais un pointeur qui répète une unité déjà présente ;
- tout élément SEULEMENT MENTIONNÉ dans une liste (par exemple une section « à valider », une énumération à puces) : une simple puce d'une ou deux lignes, sans description propre, n'est PAS une unité même si elle nomme une activité.

Repère qui tranche : une vraie unité a SA PROPRE description complète (de quoi la réaliser en la lisant : son matériel, ses objectifs, son déroulé…). Un titre de section, un texte de cadrage, un renvoi ou une simple puce de liste n'ont pas cette description — ils présentent, encadrent ou évoquent les unités, mais n'en sont pas : on les écarte.

Pour chaque unité RETENUE, rends UNIQUEMENT la LIGNE DE TITRE qui la commence, RECOPIÉE EXACTEMENT telle qu'elle apparaît dans le texte (mêmes mots, même casse, rien ajouté, rien enlevé). Tu ne réécris pas le contenu : la ligne de titre sert à retrouver la frontière dans le texte réel.

Format — JSON strict, rien autour :
{{
  "unites": [
    {{ "titre": "la ligne de titre exacte qui commence l'unité" }}
  ]
}}

Règles :
- Une entrée par unité, dans l'ORDRE du document.
- Recopie chaque titre À L'IDENTIQUE depuis le texte. N'invente aucun titre, n'en fusionne pas deux.
- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON.""",

    "detecter_matieres": """Tu lis un référentiel officiel et tu en dégages la liste des MATIÈRES (disciplines, domaines d'apprentissage) qu'il structure à ce niveau.

Texte du référentiel :
{texte}

Ta tâche :
- Repère les matières, disciplines ou domaines d'apprentissage que ce référentiel organise (ses grands champs).
- Donne le nom de chaque matière TEL QU'IL APPARAÎT DANS LE DOCUMENT : son orthographe, ses majuscules, ses accents. Ce document nomme SES matières ; il n'y a aucune liste extérieure à laquelle les ramener, et aucun nom à normaliser.
- Garde des noms courts et lisibles : le nom de la matière, pas une phrase ni un intitulé de chapitre.
- Ne sépare jamais un intitulé qui désigne UNE seule discipline, même si son nom est composé (par exemple « Prévention-santé-environnement » ou « Éducation physique et sportive » restent entières).
- Sépare en revanche un intitulé qui en énumère visiblement plusieurs (par exemple « Mathématiques et physique-chimie » donne deux matières), en gardant pour chacune le nom que le document lui donne.

Règle :
- "matieres" : la liste des noms de matières, sans doublon.
- N'invente aucune matière absente du document. Si aucune n'apparaît clairement, renvoie une liste vide.

Réponds UNIQUEMENT en JSON, avec exactement cette clé : matieres (un tableau de chaînes).""",

    "detecter_types_activite": """Tu lis un référentiel officiel et tu en dégages la liste des TYPES D'ACTIVITÉ (formats ou modalités d'activité pédagogique) qu'il met en œuvre à ce niveau.

Texte du référentiel :
{texte}

Ta tâche :
- Repère les types d'activité, formats ou modalités de travail que ce référentiel met réellement en œuvre (par exemple : atelier, mise en situation, travaux pratiques, projet, évaluation — selon ce qui apparaît réellement).
- Donne le nom de chaque type TEL QU'IL RESSORT DU DOCUMENT : ses mots, son orthographe. Ce document met en œuvre SES formats de travail ; il n'existe aucune liste extérieure à laquelle les ramener, et aucun libellé à normaliser.
- Garde des libellés courts et lisibles : le nom du type, pas une phrase ni un intitulé de chapitre.

Règle :
- "types" : la liste des libellés de types d'activité, sans doublon.
- N'invente aucun type absent du document. Si aucun n'apparaît clairement, renvoie une liste vide.

Réponds UNIQUEMENT en JSON, avec exactement cette clé : types (un tableau de chaînes).""",

    "verifier_couple": """Tu vérifies qu'un document officiel correspond bien au couple (cycle + niveau) déclaré.

Couple déclaré par l'administrateur :
- Cycle : {cycle}
- Niveau : {niveau}

Texte du document :
{texte}

Ta tâche :
- Lis à quel cycle et à quel niveau ce document s'adresse réellement.
- Dis s'il correspond au couple déclaré ci-dessus.

Règle :
- "correspond" = true si le document vise bien ce cycle et ce niveau (même si la formulation diffère), false sinon.
- "niveau_lu" : le cycle et le niveau que le document vise réellement, tels que tu les lis (une courte phrase).
- "raison" : pourquoi cela correspond ou non, en une phrase.

Réponds UNIQUEMENT en JSON, avec exactement ces clés : correspond, niveau_lu, raison.""",

    "detecter_couple": """Tu lis le début d'un référentiel officiel et tu identifies à quel CYCLE et à quel NIVEAU (diplôme, spécialité ou tranche d'âge) il s'adresse.

Cycles et niveaux déjà connus de l'application (un cycle par ligne, suivi de ses niveaux) :
{cycles_existants}

Texte du document :
{texte}

Ta tâche :
- Lis à quel cycle et à quel niveau ce document s'adresse réellement.
- Fais CORRESPONDRE ce que tu lis avec la liste ci-dessus :
  - Si le cycle visé correspond à un cycle de la liste, reprends EXACTEMENT son nom (même orthographe, mêmes majuscules).
  - Si le niveau visé correspond à un niveau de ce cycle dans la liste, reprends EXACTEMENT son nom.
  - Sinon, donne le nom tel qu'il ressort du document, court et lisible (le nom exact du diplôme ou du niveau, pas une phrase).

Règle :
- "cycle_lu" : le cycle visé par le document (nom de la liste si correspondance, sinon nom lu). Chaîne vide si le document ne permet pas de le dire.
- "niveau_lu" : le niveau, diplôme ou spécialité visé (nom de la liste si correspondance, sinon nom lu). Chaîne vide si le document ne permet pas de le dire.
- N'invente rien : la liste sert à faire correspondre, jamais à choisir un cycle que le document ne vise pas.

Réponds UNIQUEMENT en JSON, avec exactement ces clés : cycle_lu, niveau_lu.""",

    "suggerer_precisions_type": """Tu es un concepteur pédagogique.
Pour le type d'activité « {label} » enseigné au niveau « {niveau} », propose 3 à 6 PRÉCISIONS : des déclinaisons concrètes de ce type, réellement adaptées à ce niveau (ni trop enfantines, ni trop avancées).
Appuie-toi sur le référentiel officiel ci-dessous pour rester dans le programme :
{texte}

Rends UNIQUEMENT des libellés courts (2 à 4 mots), en minuscules.""",
}


def _ecrire(textes: dict) -> None:
    """Met a jour les lignes EXISTANTES de `settings`, sans jamais en creer.

    Une base qui n'a pas encore recu le semis des prompts n'en recevra pas ici : ce n'est pas le
    role de cette migration, et inventer une ligne masquerait l'absence du semis."""
    bind = op.get_bind()
    for cle, texte in textes.items():
        bind.execute(
            sa.text("UPDATE settings SET value = :v WHERE key = :k"),
            {"v": texte, "k": f"prompt_{cle}"},
        )


def upgrade() -> None:
    _ecrire(PROMPTS_MAJ)


def downgrade() -> None:
    _ecrire(PROMPTS_AVANT)
