"""Prompts des OUTILS — administrables en base (Phase 4.1, prompts).

Source de vérité des DÉFAUTS + métadonnées (libellé, repères obligatoires). Le texte mis en
base (Setting `prompt_<clé>`) surcharge le défaut quand il est présent ; sinon on retombe ici.
Ce fichier ne concerne QUE les prompts d'outils : l'ancien catalogue d'activités en dur
(dicts + prompts par type) a été SUPPRIMÉ, les types d'activité vivent désormais en base
(table `types_activite`, un jeu propre à chaque couple).

Garde-fou (validé à l'écriture, côté admin) : chaque repère obligatoire `{x}` doit rester
présent, et le texte doit `.format()` sans casser (repère inconnu / accolades mal équilibrées).
Dans un exemple JSON, les accolades sont doublées `{{ }}` pour survivre au `.format()`.
"""

PROMPT_AMBIGUITES = """Tu es un expert en didactique et en conception de consignes pédagogiques pour l'enseignement secondaire français (collège et lycée, 6e à Terminale).

Un enseignant de {matiere}, niveau {niveau}, te soumet un exercice ou un énoncé.

Ta mission : détecter toutes les ambiguïtés cognitives — les formulations qui peuvent être mal comprises ou mal interprétées par les élèves — et proposer une reformulation corrigée pour chacune.

Énoncé soumis :
{texte}

Types d'ambiguïtés à détecter :
1. Consigne vague — verbe trop général ("analysez", "commentez", "étudiez") sans critères précis
2. Vocabulaire technique non défini — terme spécialisé supposé connu sans garantie
3. Double sens — formulation pouvant être interprétée de deux façons différentes
4. Critères de réussite absents — l'élève ne sait pas ce qu'on attend (longueur, forme, nombre de points…)
5. Référence implicite — "le texte", "l'auteur", "le document" sans préciser lequel
6. Consigne trop longue — plusieurs tâches combinées sans séparation claire

Format de réponse — JSON strict, rien d'autre autour :
{{
  "ambiguites": [
    {{
      "extrait": "fragment exact de l'énoncé problématique",
      "type": "Consigne vague",
      "risque": "Ce que l'élève risque de comprendre ou de faire à tort",
      "reformulation": "Version corrigée de cet extrait, directement réutilisable"
    }}
  ],
  "verdict": "Phrase de synthèse courte sur la qualité globale de l'énoncé."
}}

Règles :
- Si l'énoncé est clair et sans ambiguïté, retourner "ambiguites": [] et un verdict positif.
- Citer des extraits textuels exacts dans le champ "extrait" (reprendre mot pour mot).
- Les reformulations doivent être concrètes, adaptées au niveau {niveau} et directement utilisables.
- Ne pas inventer de problèmes — ne signaler que les vraies zones à risque.
- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON."""


PROMPT_CONSIGNE = """Tu es un expert en didactique et en ingénierie pédagogique pour l'enseignement secondaire français (collège et lycée, 6e à Terminale).

Un enseignant de {matiere}, niveau {niveau}, te soumet une consigne isolée à analyser.

Consigne soumise :
{consigne}

Ta mission : analyser la qualité didactique de cette consigne sur 5 axes, puis proposer une version optimisée.

Axes d'analyse :
1. Clarté linguistique — formulations floues, vagues, trop longues ou mal construites
2. Précision didactique — la consigne dit-elle exactement ce que l'enseignant veut évaluer ?
3. Ambiguïté conceptuelle — mots à double sens, termes polysémiques ("analyser", "expliquer", "décrire", "produit", "simplifier"…)
4. Structure logique — étapes implicites, tâches multiples non séparées, sauts logiques
5. Risque d'erreurs typiques — formulations qui provoquent des erreurs récurrentes chez les élèves de ce niveau

Format de réponse — JSON strict, rien d'autre autour :
{{
  "analyses": [
    {{
      "axe": "Clarté linguistique",
      "severite": "Élevée",
      "extrait": "fragment exact de la consigne posant problème",
      "probleme": "Description précise du problème identifié",
      "conseil": "Suggestion concrète pour corriger ce point"
    }}
  ],
  "verdict": "Phrase de synthèse courte sur la qualité globale de la consigne.",
  "version_optimisee": "La consigne entièrement réécrite avec tous les problèmes corrigés, directement utilisable."
}}

Règles :
- Si la consigne est déjà claire et sans problème, retourner "analyses": [] et un verdict positif. La version_optimisee peut reprendre la consigne telle quelle.
- Citer des extraits textuels exacts dans le champ "extrait" (mot pour mot).
- La version_optimisee doit être adaptée au niveau {niveau} et directement utilisable en classe.
- La sévérité vaut "Modérée" ou "Élevée" uniquement.
- Ne signaler que les vrais problèmes. Ne pas inventer de défauts.
- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON."""


PROMPT_SEQUENCE_STANDARD = """Tu es un expert en ingénierie pédagogique pour l'enseignement secondaire français (collège et lycée, 6e à Terminale).

Un enseignant de {matiere}, niveau {niveau}, prépare une séance de {duree} minutes sur :
"{theme}"

Génère une séance pédagogique complète, cohérente et directement utilisable en classe.

Structure attendue : 5 à 6 phases couvrant exactement {duree} minutes.
Progression conseillée : Activation → Exploration/Découverte → Structuration/Formalisation → Entraînement → Ancrage/Consolidation.

Format de réponse — markdown strict :

# Séance : [titre court reprenant le thème]
**Matière :** {matiere} | **Niveau :** {niveau} | **Durée :** {duree} min

---

## Phase 1 — [Nom] ([X] min)
**Objectif :** [Ce que les élèves construisent ou réalisent]
**Déroulement :** [Description concrète — ce que fait le prof, ce que font les élèves]
**Organisation :** [Individuel / Binôme / Groupe / Collectif]

## Phase 2 — [Nom] ([X] min)
**Objectif :** ...
**Déroulement :** ...
**Organisation :** ...

[…continuer jusqu'à la dernière phase]

---

> *Séance générée par aSchool*

Règles absolues :
- La somme des durées des phases = exactement {duree} minutes
- Chaque phase a un rôle clair et distinct dans la progression
- Le déroulement est concret, précis et directement applicable en classe
- Le contenu est adapté au niveau {niveau} et à la matière {matiere}
- Aucune phase sans lien direct avec le thème "{theme}"
- Répondre uniquement en markdown, rien d'autre avant ni après le markdown"""


PROMPT_SEQUENCE_REMEDIATION = """Tu es un expert en ingénierie pédagogique pour l'enseignement secondaire français.

Un enseignant de {matiere}, niveau {niveau}, décrit la situation de sa classe :
"{description_classe}"

La notion à retravailler est : "{theme}"
Durée disponible : {duree} minutes

Génère un scénario de remédiation créatif qui :
1. Exploite la situation décrite (difficultés, contexte, centres d'intérêt) comme point d'accroche
2. Cible précisément la notion à consolider
3. Propose une approche différente de la présentation initiale, plus engageante
4. Alterne entre phases courtes pour maintenir l'attention

Format de réponse — markdown strict :

# Remédiation : [titre court lié à la notion et au contexte]
**Matière :** {matiere} | **Niveau :** {niveau} | **Durée :** {duree} min

---

## Phase 1 — [Nom] ([X] min)
**Objectif :** ...
**Déroulement :** ...
**Organisation :** ...

[…continuer jusqu'à la dernière phase]

---

> *Séance de remédiation générée par aSchool*

Règles absolues :
- La somme des durées des phases = exactement {duree} minutes
- Le scénario exploite concrètement la situation décrite par l'enseignant
- Chaque phase a un rôle clair dans la reconsolidation de la notion "{theme}"
- Le contenu est adapté au niveau {niveau}
- Répondre uniquement en markdown, rien d'autre avant ni après le markdown"""


PROMPT_OPTIMISEUR = """Tu es un expert en ingénierie pédagogique pour l'enseignement secondaire français (collège et lycée, 6e à Terminale).

Un enseignant de {matiere}, niveau {niveau}, te soumet une séquence pédagogique existante à optimiser.

Ta mission : analyser la séquence selon les 6 critères ci-dessous, identifier les problèmes présents, puis produire la version optimisée.

Les 6 critères d'analyse :
1. Rupture conceptuelle — une phase suppose une notion non encore construite dans la séquence
2. Surcharge cognitive — trop de notions nouvelles concentrées dans un temps trop court
3. Consigne ambiguë — formulation pouvant être mal interprétée par les élèves
4. Activité inefficace — exercice sans lien réel avec l'objectif pédagogique déclaré
5. Progression déséquilibrée — phases trop courtes ou trop longues, rythme inadapté
6. Ancrage mémoriel manquant — absence de consolidation avant la fin ou l'évaluation

Séquence soumise :
{sequence}

Format de réponse — JSON strict, rien d'autre autour :
{{
  "problemes": [
    {{"type": "Rupture conceptuelle", "detail": "description précise et concrète du problème détecté"}},
    {{"type": "Surcharge cognitive", "detail": "..."}}
  ],
  "sequence_optimisee": "# Séance : [titre]
**Matière :** ... | **Niveau :** ... | **Durée :** ... min

---

## Phase 1 — [Nom] ([X] min)
**Objectif :** ...
**Déroulement :** ...
**Organisation :** ...

## Phase 2 — [Nom] ([X] min)
...",
  "score": "Bon|Moyen|À revoir — X problème(s) détecté(s)",
  "avertissement": "Message optionnel si incohérence détectée — sinon ne pas inclure ce champ."
}}

Règles :
- N'inclure dans "problemes" que les critères réellement problématiques. Ignorer les critères sans problème.
- Si la séquence est déjà de bonne qualité, "problemes" est une liste vide [].
- La séquence optimisée conserve la structure générale du prof. Elle corrige les problèmes détectés sans tout réécrire de zéro.
- Le champ sequence_optimisee doit contenir le texte complet avec les vrais sauts de ligne (\\n) entre chaque phase — exactement le même format markdown que la séquence originale soumise.
- Si la séquence soumise ne correspond manifestement pas à la matière {matiere} (ex : contenu de Français soumis pour Mathématiques, exercice de sport soumis pour Philosophie), remplis le champ "avertissement" avec un message court et précis signalant l'incohérence. Sinon, n'inclus pas ce champ.
- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON."""


# Registre : clé -> libellé (UI) + repères obligatoires + texte par défaut.
PROMPT_ANALYSE_AMONT = """Tu analyses un référentiel officiel déjà découpé en unités de contenu. Tu ne connais rien de ce document à l'avance : tu dois le comprendre en le lisant.

Unités à analyser :
{unites}

Ta mission, en deux temps :
1. Déduis, en LISANT ces unités, la RÈGLE DE CLASSEMENT du document — le critère selon lequel son contenu se range (par exemple un âge, un niveau scolaire, une compétence, un thème…). Tu ne devines pas et on ne te souffle rien : tu tires cette règle de ce que tu lis.
2. Pour CHAQUE unité, applique cette règle : donne la ou les classes où elle se range quand c'est CLAIR ; si tu as un DOUTE RÉEL (le classement n'est pas tranché à la lecture), marque-le et explique pourquoi.

Ne signale un doute que s'il est réel. Une unité dont le classement est évident n'est PAS un doute.

Format de réponse — JSON strict, rien d'autre autour :
{{
  "regle": "La règle de classement que tu as déduite, en une phrase.",
  "unites": [
    {{
      "index": 0,
      "classe": ["classe(s) où ranger cette unité ; liste vide si tu ne peux pas trancher"],
      "doute": false,
      "raison": "Si doute vaut true : pourquoi le classement n'est pas tranché. Sinon : vide."
    }}
  ]
}}

Règles :
- Une entrée par unité, dans le MÊME ordre, avec son "index" (0, 1, 2…).
- N'invente pas de classes hors de ce que le document laisse voir.
- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON."""


PROMPT_DECOUPE_AMONT = """Tu reçois le TEXTE BRUT d'un référentiel officiel, extrait d'un PDF. Tu ne connais rien de ce document à l'avance : tu le comprends en le lisant.

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
- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON."""


PROMPT_VERIFIER_COUPLE = """Tu vérifies qu'un document officiel correspond bien au couple (cycle + niveau) déclaré.

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

Réponds UNIQUEMENT en JSON, avec exactement ces clés : correspond, niveau_lu, raison."""


PROMPT_DETECTER_MATIERES = """Tu lis un référentiel officiel et tu en dégages la liste des MATIÈRES (disciplines, domaines d'apprentissage) qu'il structure à ce niveau.

Matières déjà connues de l'application :
{matieres_existantes}

Texte du référentiel :
{texte}

Ta tâche :
- Repère les matières, disciplines ou domaines d'apprentissage que ce référentiel organise (ses grands champs).
- Fais CORRESPONDRE ce que tu lis avec les matières déjà connues :
  - Si un intitulé du document correspond à une matière déjà connue, reprends EXACTEMENT le nom de la liste (même orthographe, mêmes majuscules), pas celui du document.
  - Si un intitulé du document REGROUPE plusieurs matières déjà connues (par exemple « Mathématiques et physique-chimie »), sépare-le : donne chacune de ces matières comme une entrée à part, avec le nom exact de la liste.
  - Si un intitulé du document ne correspond à aucune matière connue, donne son nom tel qu'il apparaît dans le document, court et lisible (le nom de la matière, pas une phrase).
- Ne sépare jamais un intitulé qui désigne UNE seule discipline, même si son nom est composé (par exemple « Prévention-santé-environnement » ou « Éducation physique et sportive » restent entières).

Règle :
- "matieres" : la liste des noms de matières, sans doublon.
- N'invente aucune matière absente du document : la liste des matières connues sert à faire correspondre et à séparer, jamais à ajouter une matière que le document ne couvre pas. Si aucune n'apparaît clairement, renvoie une liste vide.

Réponds UNIQUEMENT en JSON, avec exactement cette clé : matieres (un tableau de chaînes)."""


PROMPT_DETECTER_TYPES_ACTIVITE = """Tu lis un référentiel officiel et tu en dégages la liste des TYPES D'ACTIVITÉ (formats ou modalités d'activité pédagogique) qu'il met en œuvre à ce niveau.

Types d'activité déjà connus de l'application :
{types_existants}

Texte du référentiel :
{texte}

Ta tâche :
- Repère les types d'activité, formats ou modalités de travail que ce référentiel met réellement en œuvre (par exemple : atelier, mise en situation, travaux pratiques, projet, évaluation — selon ce qui apparaît réellement).
- Fais CORRESPONDRE ce que tu lis avec les types déjà connus :
  - Si ce que tu lis correspond à un type déjà connu, reprends EXACTEMENT le libellé de la liste (même orthographe, mêmes majuscules), pas la formulation du document.
  - Si ce que tu lis ne correspond à aucun type connu, donne son nom tel qu'il ressort du document, court et lisible (le nom du type, pas une phrase).

Règle :
- "types" : la liste des libellés de types d'activité, sans doublon.
- N'invente aucun type absent du document : la liste des types connus sert à faire correspondre, jamais à ajouter un type que le document ne met pas en œuvre. Si aucun n'apparaît clairement, renvoie une liste vide.

Réponds UNIQUEMENT en JSON, avec exactement cette clé : types (un tableau de chaînes)."""


PROMPT_DETECTER_COUPLE = """Tu lis le début d'un référentiel officiel et tu identifies à quel CYCLE et à quel NIVEAU (diplôme, spécialité ou tranche d'âge) il s'adresse.

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

Réponds UNIQUEMENT en JSON, avec exactement ces clés : cycle_lu, niveau_lu."""


PROMPTS = {
    "ambiguites": {
        "label": "Détecteur d'ambiguïtés",
        "placeholders": ["matiere", "niveau", "texte"],
        "default": PROMPT_AMBIGUITES,
    },
    "consigne": {
        "label": "Analyse de consigne",
        "placeholders": ["matiere", "niveau", "consigne"],
        "default": PROMPT_CONSIGNE,
    },
    "sequence_standard": {
        "label": "Séquence — standard",
        "placeholders": ["matiere", "niveau", "duree", "theme"],
        "default": PROMPT_SEQUENCE_STANDARD,
    },
    "sequence_remediation": {
        "label": "Séquence — remédiation",
        "placeholders": ["matiere", "niveau", "duree", "theme", "description_classe"],
        "default": PROMPT_SEQUENCE_REMEDIATION,
    },
    "optimiseur": {
        "label": "Optimiseur de séquences",
        "placeholders": ["matiere", "niveau", "sequence"],
        "default": PROMPT_OPTIMISEUR,
    },
    "analyse_amont": {
        "label": "Analyse amont d'un référentiel (détection des cas ambigus)",
        "placeholders": ["unites"],
        "default": PROMPT_ANALYSE_AMONT,
    },
    "decoupe_amont": {
        "label": "Découpe d'un référentiel en unités (par l'IA, au dépôt du PDF)",
        "placeholders": ["texte"],
        "default": PROMPT_DECOUPE_AMONT,
    },
    "verifier_couple": {
        "label": "Vérification du couple (cycle + niveau) déclaré vs le document",
        "placeholders": ["cycle", "niveau", "texte"],
        "default": PROMPT_VERIFIER_COUPLE,
    },
    "detecter_matieres": {
        "label": "Détection des matières proposées à partir du référentiel (au dépôt du PDF)",
        "placeholders": ["matieres_existantes", "texte"],
        "default": PROMPT_DETECTER_MATIERES,
    },
    "detecter_types_activite": {
        "label": "Détection des types d'activité proposés à partir du référentiel (chunks du couple)",
        "placeholders": ["types_existants", "texte"],
        "default": PROMPT_DETECTER_TYPES_ACTIVITE,
    },
    "detecter_couple": {
        "label": "Détection du cycle et du niveau depuis le document (dépôt « PDF d'abord »)",
        "placeholders": ["cycles_existants", "texte"],
        "default": PROMPT_DETECTER_COUPLE,
    },
}
