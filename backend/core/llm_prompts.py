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


# Prompts retirés (28/07, ménage) : PROMPT_VERIFIER_RESULTAT / PROMPT_CORRIGER_RESULTAT /
# PROMPT_AMELIORER_SIMPLIFIER / PROMPT_AMELIORER_ENRICHIR — les features Vérifier / Corriger /
# Améliorer ont été supprimées de l'écran (le contrôle qualité est intégré à la génération).


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


# ── Séance du monde « Mes contenus » — un prompt PAR MODE (les 4 pastilles de l'écran). ──
# Le squelette markdown (phases minutées) est commun ; les précisions optionnelles du formulaire
# (contexte, compétences, matériel, esquisse, contraintes) sont AJOUTÉES au prompt par le code,
# et le style de production est une COUCHE séparée (seance_style_*), comme le ton de l'activité.
_FORMAT_SEANCE = """Format de réponse — markdown strict :

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

PROMPT_SEANCE_STANDARD = """Tu es un expert en ingénierie pédagogique.

Un enseignant de {matiere}, niveau {niveau}, prépare une séance de {duree} minutes sur :
"{theme}"

Génère une séance pédagogique complète, cohérente et directement utilisable en classe.

Structure attendue : 5 à 6 phases couvrant exactement {duree} minutes.
Progression conseillée : Activation → Exploration/Découverte → Structuration/Formalisation → Entraînement → Ancrage/Consolidation.

""" + _FORMAT_SEANCE


PROMPT_SEANCE_REMEDIATION = """Tu es un expert en ingénierie pédagogique.

Un enseignant de {matiere}, niveau {niveau}, doit RETRAVAILLER une notion que sa classe n'a pas comprise lors d'une première présentation : "{theme}". Durée disponible : {duree} minutes.

Génère un scénario de remédiation qui :
1. Reprend la notion par une approche DIFFÉRENTE de la présentation initiale, plus engageante
2. Cible précisément les obstacles de compréhension les plus probables à ce niveau
3. Alterne des phases courtes pour maintenir l'attention
4. Se termine par une vérification concrète que la notion est cette fois acquise

""" + _FORMAT_SEANCE


PROMPT_SEANCE_APPROFONDISSEMENT = """Tu es un expert en ingénierie pédagogique.

Un enseignant de {matiere}, niveau {niveau}, veut ALLER PLUS LOIN sur un thème que sa classe maîtrise déjà : "{theme}". Durée disponible : {duree} minutes.

Génère une séance d'approfondissement qui :
1. Part des acquis (aucune redite de la découverte initiale) et les met au défi
2. Propose des situations plus riches ou plus complexes : transfert à un contexte nouveau, croisement de notions, analyse critique, production ambitieuse
3. Fait monter progressivement l'exigence au fil des phases
4. Garde chaque élève en réussite : un point d'appui est prévu pour ceux qui bloquent

""" + _FORMAT_SEANCE


PROMPT_SEANCE_AUTONOMIE = """Tu es un expert en ingénierie pédagogique.

Un enseignant de {matiere}, niveau {niveau}, prépare une séance en AUTONOMIE GUIDÉE de {duree} minutes sur : "{theme}". Les élèves travaillent SEULS : c'est la séance elle-même qui les guide, le professeur circule et n'intervient qu'en appui.

Génère une séance dont :
1. Chaque phase dit précisément ce que l'élève FAIT, seul, sans intervention du professeur
2. Les consignes sont autoportantes : lisibles et exécutables par l'élève sans explication orale
3. Chaque phase donne à l'élève un moyen de S'AUTO-VÉRIFIER avant de passer à la suivante
4. Un filet est prévu pour l'élève bloqué (indice, ressource, étape intermédiaire)

""" + _FORMAT_SEANCE


# « Propose-moi un thème » de l'écran Séance — la version séance de « Propose-moi une idée » :
# aSchool écrit le thème/objectif à la place du prof, ANCRÉ sur le programme officiel du niveau
# (extraits RAG). Le prof reste le patron : il relit, modifie, puis « Générer la séance ».
PROMPT_SEANCE_PROPOSER_THEME = """Tu aides un enseignant de {matiere}, niveau {niveau}, à choisir le sujet de sa prochaine séance.

Extraits du programme officiel de ce niveau :
{referentiel}

Propose UN thème de séance tiré de ces extraits : une à deux phrases qui décrivent le thème et l'objectif visé, prêtes à servir de point de départ. Concret, réalisable en une seule séance, adapté au niveau {niveau}.

Règles :
- Reste STRICTEMENT dans ce que couvrent les extraits — n'invente rien hors programme.
- Pas de titre, pas de commentaire, pas de liste : rends UNIQUEMENT le texte du thème (1 à 2 phrases)."""


PROMPT_SEANCE_PROPOSER_COMPETENCES = """Tu aides un enseignant de {matiere}, niveau {niveau}, à identifier les compétences que sa prochaine séance doit travailler.

Thème de la séance choisi par l'enseignant :
{theme}

Extraits du programme officiel de ce niveau :
{referentiel}

Propose de 3 à 5 compétences ou attendus du programme que cette séance peut travailler : des formulations courtes (une ligne chacune), directement tirées des extraits, en lien avec le thème donné et adaptées au niveau {niveau}.

Règles :
- Reste STRICTEMENT dans ce que couvrent les extraits — n'invente aucune compétence hors programme.
- Ne garde que ce qui a un vrai lien avec le thème : mieux vaut 3 compétences justes que 5 tirées par les cheveux.
- Une compétence par ligne, sans numérotation, sans puces, sans titre, sans commentaire : rends UNIQUEMENT les lignes de compétences."""


PROMPT_SEANCE_PROPOSER_MATERIEL = """Tu aides un enseignant de {matiere}, niveau {niveau}, à préparer une séance.

{seance}

Propose le MATÉRIEL nécessaire pour mener cette séance en classe.

Règles :
- Du matériel réaliste pour une salle de classe ordinaire — rien de coûteux ni d'exotique.
- Rends UNE SEULE ligne : une énumération courte séparée par des virgules (5 à 10 éléments maximum), sans phrase d'introduction, sans commentaire."""


PROMPT_SEANCE_PROPOSER_CONTRAINTES = """Tu aides un enseignant de {matiere}, niveau {niveau}, à préparer une séance.

{seance}

Propose des CONTRAINTES ou consignes spéciales utiles pour cette séance : les points de vigilance concrets qu'un enseignant expérimenté poserait (gestion du temps, organisation des groupes, différenciation, moments sensibles…).

Règles :
- Concret et réaliste, adapté au niveau {niveau} — pas de généralités creuses.
- Rends UNE SEULE ligne courte : une à trois consignes séparées par des points-virgules, sans phrase d'introduction, sans commentaire."""


PROMPT_SEANCE_PROPOSER_ESQUISSE = """Tu aides un enseignant de {matiere}, niveau {niveau}, à esquisser le déroulé de sa séance.

{seance}

Propose le contenu de la phase « {phase} » : ce que l'enseignant et les élèves y font, concrètement.

Règles :
- Concret, réalisable en classe, adapté au niveau {niveau}.
- Cohérent avec les autres phases déjà esquissées quand il y en a — tu complètes un déroulé, tu ne repars pas de zéro.
- Rends 1 à 3 phrases courtes, sans titre, sans liste, sans commentaire : UNIQUEMENT le contenu de la phase."""


# Style de production de la séance — couche ajoutée au prompt selon la pastille choisie
# (facultative : aucune pastille = aucune couche), même mécanique que le ton de l'activité.
PROMPT_SEANCE_STYLE_CLASSIQUE = """STYLE DE PRODUCTION — CLASSIQUE

Rédige la séance dans une présentation sobre et traditionnelle, telle qu'on la trouve dans un classeur de préparation : intitulés neutres, formulations posées, aucun effet de style. N'ajoute aucun commentaire sur le style employé : rends uniquement la séance."""

PROMPT_SEANCE_STYLE_LUDIQUE = """STYLE DE PRODUCTION — LUDIQUE

Donne à la séance une approche par le JEU : chaque phase s'appuie sur une mécanique ludique adaptée au niveau (défi, énigme, jeu de rôle, points, coopération…), sans jamais perdre l'objectif d'apprentissage ni le sérieux du contenu. N'ajoute aucun commentaire sur le style employé : rends uniquement la séance."""

PROMPT_SEANCE_STYLE_STRUCTURE = """STYLE DE PRODUCTION — STRUCTURÉ

Rends la séance au découpage TRÈS NET : chaque phase strictement minutée, objectifs et déroulement en listes à puces courtes, transitions explicites entre phases, matériel rappelé phase par phase. N'ajoute aucun commentaire sur le style employé : rends uniquement la séance."""

PROMPT_SEANCE_STYLE_CONCIS = """STYLE DE PRODUCTION — TRÈS CONCIS

Va à l'essentiel : phrases très courtes, format télégraphique lisible en un coup d'œil, aucune phrase superflue — la séance doit tenir sur une page sans rien perdre d'indispensable. N'ajoute aucun commentaire sur le style employé : rends uniquement la séance."""


# ---------------------------------------------------------------------------
# SÉQUENCE du monde « Mes contenus » (playlist : séquence ⊃ séances ⊃ activités).
# Famille NEUVE. Elle a coexisté un temps avec `sequence_standard` / `sequence_remediation`,
# restes de l'ANCIEN outil démoli le 30/07 (qui, malgré leur nom, généraient une SÉANCE) —
# retirés le 02/08, faute d'appelant. Le préfixe `sequence` ne dit donc rien à lui seul : les
# trois prompts ci-dessous, eux, sont bel et bien appelés (backend/contenu/mes_contenus.py).
# Le plan généré n'est jamais un texte stocké : chaque ligne devient une vraie ligne
# `seances` (rattachée, ordonnée).
# ---------------------------------------------------------------------------

PROMPT_SEQUENCE_GENERER_PLAN = """Tu es un expert en ingénierie pédagogique.

Un enseignant de {matiere}, niveau {niveau}, construit une séquence pédagogique — une suite ordonnée de séances qui mène sa classe vers un objectif, quelle que soit sa durée (quelques séances comme un projet au long cours).

Objectif général de la séquence :
"{objectif}"

Construis le PLAN de cette séquence : la liste ordonnée des séances qui y mènent.

Règles :
- Chaque ligne = UNE séance : son titre, concret et autoporteur (on doit comprendre ce que la séance travaille en lisant son seul titre).
- L'ordre des lignes = l'ordre des séances : une progression logique, de la première à la dernière.
- Le NOMBRE de séances découle de l'objectif et des précisions de l'enseignant — pas de remplissage, pas de séance artificielle.
- Adapté au niveau {niveau}.
- Rends UNIQUEMENT les lignes de titres : une séance par ligne, sans numérotation, sans puces, sans titre de section, sans commentaire."""


PROMPT_SEQUENCE_PROPOSER_OBJECTIF = """Tu aides un enseignant de {matiere}, niveau {niveau}, à formuler l'objectif général de sa prochaine séquence — une suite ordonnée de séances vers un même but.

Extraits du programme officiel de ce niveau :
{referentiel}

Propose UN objectif de séquence tiré de ces extraits : une à deux phrases qui décrivent le but à atteindre au fil des séances, prêtes à servir de point de départ. Assez ample pour porter plusieurs séances, adapté au niveau {niveau}.

Règles :
- Reste STRICTEMENT dans ce que couvrent les extraits — n'invente rien hors programme.
- Pas de titre, pas de commentaire, pas de liste : rends UNIQUEMENT le texte de l'objectif (1 à 2 phrases)."""


PROMPT_SEQUENCE_PROPOSER_COMPETENCES = """Tu aides un enseignant de {matiere}, niveau {niveau}, à identifier les compétences que sa prochaine séquence doit travailler.

Objectif général de la séquence choisi par l'enseignant :
{objectif}

Extraits du programme officiel de ce niveau :
{referentiel}

Propose de 3 à 6 compétences ou attendus du programme que cette séquence peut travailler au fil de ses séances : des formulations courtes (une ligne chacune), directement tirées des extraits, en lien avec l'objectif donné et adaptées au niveau {niveau}.

Règles :
- Reste STRICTEMENT dans ce que couvrent les extraits — n'invente aucune compétence hors programme.
- Ne garde que ce qui a un vrai lien avec l'objectif : mieux vaut 3 compétences justes que 6 tirées par les cheveux.
- Une compétence par ligne, sans numérotation, sans puces, sans titre, sans commentaire : rends UNIQUEMENT les lignes de compétences."""


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


# -----------------------------------------------------------------------------
# PROMPTS EN MODE « replace » — ils DECRIVENT un autre prompt, ils ne sont pas
# formates. Leur texte contient des accolades qui doivent SURVIVRE (le repere
# {texte} que le prompt produit devra porter, un exemple JSON a imposer) : les
# passer a `.format()` leve. Ils sont donc consommes par `str.replace`, et le
# registre le DIT (cle « mode »), pour que la validation d'ecriture le sache.
# -----------------------------------------------------------------------------

PROMPT_META_DECOUPE = """Tu prepares le decoupage d'un referentiel officiel pour un logiciel pedagogique.

On te donne le TEXTE BRUT d'un referentiel (extrait d'un PDF) :
---
{document}
---

Ta mission : REDIGER un PROMPT de decoupe sur mesure pour CE document precis. Ce prompt sera ensuite donne a une IA pour qu'elle decoupe le document en ne gardant QUE ses vraies unites de contenu (les elements concrets et decrits que l'utilisateur exploitera : activites, fiches, competences... selon ce que contient ce document), et en ecartant tout le texte qui les entoure (page de titre, avertissements, introduction, mode d'emploi, en-tetes de partie ou de section, notes, renvois, listes de simples mentions, sources et attribution).

Le prompt que tu rediges DOIT :
- etre adapte a la structure reelle de CE document : nomme les reperes concrets que tu observes (comment une vraie unite de contenu se presente ici ; ce qui n'est que du texte d'entourage) ;
- demander, pour chaque unite retenue, UNIQUEMENT sa ligne de titre recopiee exactement telle qu'elle apparait dans le texte ;
- contenir le marqueur {texte} a l'endroit ou le texte brut du document sera insere ;
- imposer une sortie JSON stricte : {"unites":[{"titre":"..."}]} et rien d'autre autour.

Reponds UNIQUEMENT par le texte du prompt de decoupe, sans aucun commentaire autour."""


# Méta-prompt des MATIÈRES — même geste que PROMPT_META_DECOUPE, mais pour la liste des matières.
# Il ne cherche AUCUNE matière : il fait écrire, par l'IA, le prompt qui les cherchera. Ce prompt
# généré est rangé sur le CYCLE : il doit donc valoir pour TOUS les référentiels de ce cycle (tous
# les BTS sont bâtis pareil, tous les programmes de collège aussi), pas seulement pour l'exemplaire
# qui a servi de modèle. C'est ce qui remplace le prompt unique, écrit d'avance pour tout le monde,
# qui rendait une liste incomplète sur les documents structurés.
PROMPT_META_MATIERES = """Tu prépares la lecture des MATIÈRES d'un référentiel officiel pour un logiciel pédagogique.

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
- contenir le marqueur {texte} à l'endroit où le texte du document sera inséré ;
- imposer une sortie JSON stricte : {"matieres":["...","..."]} et rien d'autre autour.

Réponds UNIQUEMENT par le texte du prompt, sans aucun commentaire autour."""


PROMPT_VERIF_DECOUPE = """Tu es un relecteur exigeant. On te donne un PROMPT DE DÉCOUPE destiné à découper un référentiel en unités. Vérifie qu'il respecte STRICTEMENT ce contrat :

1. TITRES VERBATIM (priorité absolue) : le prompt doit exiger que chaque unité renvoie sa LIGNE DE TITRE EXACTEMENT telle qu'elle apparaît dans le document, mot pour mot, jamais reformulée ni résumée. C'est vital : le code retrouve ensuite chaque titre dans le texte réel pour trancher ; un titre paraphrasé fait perdre la frontière.
2. FORMAT JSON EXACT : le prompt doit imposer la sortie {"unites":[{"titre":"..."}]} — une clé "unites" contenant une liste d'objets à clé "titre", et rien d'autre.
3. PAS DE CONTENU : le prompt ne doit PAS demander le contenu, le déroulé ni le détail des unités. Le code reconstitue le contenu lui-même en tranchant le texte réel ; un contenu demandé à l'IA est du gaspillage de tokens (et serait jeté).
4. EXCLUSIONS : le prompt doit écarter ce qui n'est pas une unité (page de titre, introduction, avertissements, en-têtes de partie ou de section, notes, renvois, sources, attributions).

Si le prompt viole un ou plusieurs de ces points, RENVOIE une version CORRIGÉE du prompt qui les respecte tous. S'il les respecte déjà, renvoie-le INCHANGÉ.

Ne renvoie QUE le prompt (corrigé ou inchangé), sans commentaire, sans explication, sans balise de code.

PROMPT À VÉRIFIER :
{prompt}"""


PROMPT_GABARIT_TYPE = """Tu es un enseignant expérimenté.
Conçois une activité du type « {label} » adaptée à des élèves de {niveau}.

Pars de l'idée du professeur ci-dessous — garde son intention et son style, c'est elle qui mène :
{texte}

Appuie-toi sur le programme officiel ci-dessous pour cadrer et enrichir l'activité, sans t'en écarter :
{referentiel}

Rends une activité claire et directement exploitable (objectif, consigne, déroulé)."""

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


PROMPT_REFERENTIEL_FUSION = """Tu reçois les documents officiels fournis pour un même niveau scolaire. Tu en tires UN SEUL référentiel de travail, complet et sans redite.

Couple visé :
- Cycle : {cycle}
- Niveau : {niveau}

Documents fournis :
{documents}

Ta tâche :
- Retiens ce qui vaut pour CE niveau : les matières enseignées, et pour chacune ce que l'élève doit savoir et savoir faire.
- Un même contenu revient souvent d'un document à l'autre (un programme et son bulletin officiel disent la même chose) : ne l'écris QU'UNE FOIS, dans sa formulation la plus complète.
- Quand deux documents se contredisent, garde ce qui vaut pour le niveau visé et ignore l'autre. N'explique pas ton choix dans le texte.
- Écarte ce qui n'est pas du programme : préambules administratifs, sommaires, références d'arrêtés, mentions légales, pagination, remerciements.
- N'ajoute RIEN qui ne soit pas dans les documents. Tu résumes et tu ordonnes, tu n'inventes pas.

Forme attendue :
- Une matière par section, introduite par une ligne « ## » suivie du nom de la matière tel que les documents le nomment.
- Sous chaque matière, des lignes courtes commençant par « - », une idée par ligne.
- Pas d'introduction, pas de conclusion, pas de commentaire sur ton travail : le texte du référentiel, et rien d'autre.
- {consigne_taille}

Réponds uniquement par ce texte."""


PROMPT_DETECTER_MATIERES = """Tu lis un référentiel officiel et tu en dégages la liste des MATIÈRES (disciplines, domaines d'apprentissage) qu'il structure à ce niveau.

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

Réponds UNIQUEMENT en JSON, avec exactement cette clé : matieres (un tableau de chaînes)."""


# Bouton « générer les précisions » de l'écran admin des types d'activité. Ce texte était ÉCRIT
# EN DUR dans backend/rag/analyse_amont.py (f-string, ligne 490) : le seul vrai prompt du projet
# que l'admin ne pouvait ni lire, ni corriger, ni même savoir qu'il existait — alors que ses
# trois voisines du même fichier passaient déjà par le registre.
# Repris ICI MOT POUR MOT, retours à la ligne compris : la seule différence est que les valeurs
# interpolées deviennent des repères. On ne profite pas d'un déménagement pour réécrire un texte
# qui marche — sinon un changement de comportement voyage sous couvert de rangement.
PROMPT_SUGGERER_PRECISIONS_TYPE = """Tu es un concepteur pédagogique.
Pour le type d'activité « {label} » enseigné au niveau « {niveau} », propose 3 à 6 PRÉCISIONS : des déclinaisons concrètes de ce type, réellement adaptées à ce niveau (ni trop enfantines, ni trop avancées).
Appuie-toi sur le référentiel officiel ci-dessous pour rester dans le programme :
{texte}

Rends UNIQUEMENT des libellés courts (2 à 4 mots), en minuscules."""


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


PROMPT_CORRECTION = """Ajoute ensuite, après l'activité, une section « Correction » : le corrigé complet et ordonné de chaque question ou exercice de l'activité — la réponse attendue, avec une courte explication quand elle éclaire — directement utilisable par le professeur.
Ne corrige que ce que l'activité demande : n'ajoute aucun nouvel exercice, aucune variante."""


# Contrôle qualité INTÉGRÉ à la génération (ajouté en dernière couche du prompt, comme le corrigé).
# Remplace l'ancienne cartouche « Vérifier » : au lieu de demander au prof de contrôler après coup
# (ce qui affichait notre propre doute), le modèle s'auto-relit et corrige AVANT de rendre. Un seul
# appel, aucun surcoût de latence. Les 5 axes de l'ancien Vérifier, retournés en exigences.
PROMPT_CONTROLE_QUALITE = """CONTRÔLE QUALITÉ — À APPLIQUER AVANT DE RENDRE

Avant de considérer l'activité comme terminée, relis-la et vérifie qu'elle respecte TOUS les points ci-dessous. Corrige silencieusement le moindre écart, puis rends UNIQUEMENT l'activité finale.

1. Fidélité à la demande — l'activité correspond exactement au type d'activité demandé, au niveau visé et à l'intention du texte source ; rien hors sujet, rien d'oublié.
2. Corrigé juste — si l'activité comporte un corrigé, chaque question ou exercice y a sa réponse, correcte et complète, sans décalage de numérotation ni oubli.
3. Conformité au format — la forme respecte réellement le type demandé (un QCM reste un QCM, une dictée reste une dictée, etc.).
4. Consignes sans flou — aucune consigne ambiguë, vague ou à double sens ; une seule tâche claire à la fois ; critères de réussite explicites ; vocabulaire adapté au niveau et défini quand un mot difficile est indispensable.
5. Mise en forme propre — titre clair, numérotation cohérente, structure lisible et régulière.

Ne laisse apparaître aucune trace de cette vérification (pas de commentaire, pas de « j'ai vérifié », pas de liste de contrôle) : le professeur ne doit voir que l'activité, prête à l'emploi."""


# TON de rédaction — couche de style ajoutée au prompt selon le bouton de génération cliqué
# (« Générer — ton académique » / « Générer — ton opérationnel »). Deux registres SEULEMENT, pas de
# défaut : le prof choisit au clic. Placée avant le contrôle qualité pour qu'il relise dans le bon ton.
PROMPT_TON_ACADEMIQUE = """TON DE RÉDACTION — ACADÉMIQUE

Rédige toute l'activité (titre, consignes, énoncés, et le corrigé s'il y en a un) dans un registre ACADÉMIQUE : formel et institutionnel, à la manière des documents et programmes officiels. Phrases construites et complètes, vocabulaire soutenu et précis, tournures impersonnelles. Reste rigoureux et exact, et garde un niveau réellement adapté aux élèves visés. N'ajoute aucun commentaire sur le ton employé : rends uniquement l'activité."""

PROMPT_TON_OPERATIONNEL = """TON DE RÉDACTION — OPÉRATIONNEL

Rédige toute l'activité (titre, consignes, énoncés, et le corrigé s'il y en a un) dans un registre OPÉRATIONNEL : clair, net et direct, à la manière d'un professeur qui parle à sa classe. Phrases courtes, consignes directes (verbe d'action en tête), vocabulaire simple et concret. Va droit à l'essentiel sans appauvrir le contenu ni sauter d'étape. N'ajoute aucun commentaire sur le ton employé : rends uniquement l'activité."""


# Few-shot « aSchool vous reconnaît » : couche ajoutée à la génération quand ce prof a déjà
# produit assez d'activités DU MÊME TYPE pour le MÊME couple (seuil `few_shot_seuil`, en base).
# Les exemples montrent SA manière ; ils ne doivent jamais déteindre sur le contenu demandé,
# d'où la consigne explicite de ne rien recopier.
PROMPT_FEW_SHOT = """LA MANIÈRE DE CE PROFESSEUR

Voici des activités que ce professeur a déjà produites et gardées. Elles montrent SA façon de faire : ton employé, formulation des consignes, longueur des énoncés, mise en page, niveau de langue, habitudes de présentation.

{exemples}

Inspire-toi de ces exemples pour la MANIÈRE, jamais pour le CONTENU. L'activité à produire porte sur le texte source donné plus haut, et sur lui seul : ne reprends aucune question, aucun énoncé, aucun extrait de ces exemples. N'ajoute aucun commentaire sur ces exemples : rends uniquement l'activité demandée."""


# ── Les trois textes qui vivaient HORS du registre (étape 9 lot C) ────────────────────────
# `build_exemple_referentiel_prompt` et `build_proposer_idee_prompt` (llm/prompts.py) étaient
# deux fonctions Python qui assemblaient leur prompt en f-string : deux boutons visibles du prof
# — « Document d'exemple » et « Propose-moi une idée » — pilotés par un texte que l'admin ne
# pouvait ni lire ni corriger, alors qu'il corrige les autres. Ils entrent au registre, donc en
# base, donc dans l'écran d'administration des prompts.
# La MISE EN FORME des extraits (l'entête « [Référentiel …, p.N] ») reste du code : ce n'est pas
# de la consigne rédigée, c'est l'assemblage de ce que le RAG a ramené.

PROMPT_EXEMPLE_REFERENTIEL = """Tu es enseignant·e en {matiere} pour le niveau « {niveau} ».

À partir des EXTRAITS du référentiel officiel ci-dessous, rédige un TEXTE SOURCE court et concret (énoncé, situation professionnelle, document de travail) directement exploitable comme point de départ d'une activité pour ce niveau.
Contraintes : reste dans le périmètre du référentiel ; ne recopie PAS la liste de compétences ; produis un vrai contenu (contexte, données, consigne), pas un sommaire.

## Extraits du référentiel officiel — {matiere}, {niveau}

{referentiel}

## Texte source à rédiger
"""


# {quoi} = le type d'activité choisi, avec sa précision s'il y en a une (« Compréhension écrite
# (précision : sur un texte documentaire) »). Composé côté serveur parce qu'il est CONDITIONNEL :
# un gabarit ne sait pas dire « seulement si le prof a rempli ce champ ».
PROMPT_PROPOSER_IDEE = """Tu es enseignant·e pour le niveau « {niveau} ».

Un professeur a choisi le type d'activité {quoi} et cherche une idée de départ.
À partir des EXTRAITS du référentiel officiel ci-dessous, propose UNE idée d'activité pour ce type d'activité, écrite comme la demande que le professeur taperait lui-même : 2 à 4 phrases concrètes (thème, support ou matériel, intention pédagogique), à la première personne ou à l'infinitif.
Présentation : commence par UNE première ligne « Objet : » suivie d'un titre très court (3 à 8 mots) pour retrouver l'activité facilement, puis une ligne vide, puis la demande aérée en 2 ou 3 petits paragraphes séparés par une ligne vide — d'abord le matériel ou le support, puis le déroulement, puis l'objectif pédagogique.
Contraintes : reste dans le périmètre du référentiel ; ne rédige PAS l'activité complète ; AUCUN titre, AUCUNE liste, AUCUNE autre mise en forme que ces lignes vides — uniquement le texte de la demande.

## Extraits du référentiel officiel — {niveau}

{referentiel}

## Idée d'activité à proposer
"""


# L'intitulé sous lequel le cahier des charges de l'établissement est ajouté à un prompt de
# génération. Une seule ligne, mais elle porte une DÉCISION pédagogique : la priorité entre les
# règles de l'école et le programme officiel. Elle n'a rien à faire dans une constante Python.
PROMPT_ENTETE_CAHIER = """Cahier des charges de l'établissement (à respecter par-dessus le programme officiel) :"""


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


# Registre des prompts administrables. `categorie` dit À QUI sert le texte, et donc sous quelle
# sous-option de l'écran admin « Prompts » il se range :
#   - "prof"   : ce que l'enseignant déclenche (séances, séquences, propositions, tons, corrections) ;
#   - "admin"  : le traitement d'un référentiel au dépôt du PDF (découpe, analyse, détections) ;
#   - "autres" : le filet — ce qui n'entre dans aucune des deux. AUCUN prompt n'y est rangé
#     aujourd'hui, et c'est voulu. Il a contenu les trois restes de l'ancien monde démoli le
#     30/07 (sequence_standard, sequence_remediation, optimiseur), que plus aucun `get_prompt`
#     ne demandait ; la décision, alors mise de côté, a été prise le 02/08 : retirés du
#     registre et de la base (migration b6d1f4a8c2e7). La catégorie reste ouverte pour le
#     prochain texte qui ne saurait pas où se ranger — l'écran « Prompts — Autres » affiche
#     simplement une liste vide tant qu'il n'y en a pas.
# C'est de la même nature que `label` et `placeholders` — donc ici, pas en base : aucune migration.
#
# `mode` dit COMMENT le texte est consommé, et donc comment il se VALIDE (cf. `valider_prompt`) :
#   - "format" (défaut, absent = celui-ci) : le prompt est passé à `str.format(**valeurs)`. Ses
#     accolades sont donc du code : chaque repère obligatoire doit être là, et le texte entier
#     doit se formater sans lever. Un exemple JSON s'y écrit avec des accolades DOUBLÉES.
#   - "replace" : le prompt est consommé par `str.replace("{repère}", valeur)`. Ses autres
#     accolades sont du TEXTE, et doivent survivre intactes — c'est même leur raison d'être :
#     ces prompts-là DÉCRIVENT un autre prompt (« ton prompt devra contenir {texte} », « impose
#     la sortie {"unites":[…]} »). Les passer à `.format()` lève, mesuré : `KeyError: 'texte'`
#     et `KeyError: '"unites"'` sur leur texte réel. On vérifie donc la PRÉSENCE des repères, et
#     on n'appelle jamais `.format()`.
# Sans ce champ, les trois prompts en mode replace ne pouvaient pas entrer au registre — et
# `prompt_verif_decoupe` restait lu à chaque découpe sans qu'AUCUNE route ne permette de le
# corriger (trouvé le 01/08/2026, réparé le 02/08).
PROMPTS = {
    "ambiguites": {
        "label": "Détecteur d'ambiguïtés",
        "placeholders": ["matiere", "niveau", "texte"],
        "categorie": "prof",
        "default": PROMPT_AMBIGUITES,
    },
    "consigne": {
        "label": "Analyse de consigne",
        "placeholders": ["matiere", "niveau", "consigne"],
        "categorie": "prof",
        "default": PROMPT_CONSIGNE,
    },
    "seance_standard": {
        "label": "Séance (Mes contenus) — mode standard",
        "placeholders": ["matiere", "niveau", "duree", "theme"],
        "categorie": "prof",
        "default": PROMPT_SEANCE_STANDARD,
    },
    "seance_remediation": {
        "label": "Séance (Mes contenus) — mode remédiation",
        "placeholders": ["matiere", "niveau", "duree", "theme"],
        "categorie": "prof",
        "default": PROMPT_SEANCE_REMEDIATION,
    },
    "seance_approfondissement": {
        "label": "Séance (Mes contenus) — mode approfondissement",
        "placeholders": ["matiere", "niveau", "duree", "theme"],
        "categorie": "prof",
        "default": PROMPT_SEANCE_APPROFONDISSEMENT,
    },
    "seance_autonomie": {
        "label": "Séance (Mes contenus) — mode autonomie guidée",
        "placeholders": ["matiere", "niveau", "duree", "theme"],
        "categorie": "prof",
        "default": PROMPT_SEANCE_AUTONOMIE,
    },
    "seance_proposer_theme": {
        "label": "Séance (Mes contenus) — « Propose-moi un thème » (zone Texte de départ)",
        "placeholders": ["matiere", "niveau", "referentiel"],
        "categorie": "prof",
        "default": PROMPT_SEANCE_PROPOSER_THEME,
    },
    "seance_proposer_competences": {
        "label": "Séance (Mes contenus) — « Propose-moi des compétences » (cartouche Contenu pédagogique)",
        "placeholders": ["matiere", "niveau", "theme", "referentiel"],
        "categorie": "prof",
        "default": PROMPT_SEANCE_PROPOSER_COMPETENCES,
    },
    "seance_proposer_materiel": {
        "label": "Séance (Mes contenus) — « Propose-moi du matériel nécessaire » (cartouche Contenu pédagogique)",
        "placeholders": ["matiere", "niveau", "seance"],
        "categorie": "prof",
        "default": PROMPT_SEANCE_PROPOSER_MATERIEL,
    },
    "seance_proposer_contraintes": {
        "label": "Séance (Mes contenus) — « Propose-moi des contraintes spéciales » (cartouche Contenu pédagogique)",
        "placeholders": ["matiere", "niveau", "seance"],
        "categorie": "prof",
        "default": PROMPT_SEANCE_PROPOSER_CONTRAINTES,
    },
    "seance_proposer_esquisse": {
        "label": "Séance (Mes contenus) — « Propose-moi cette phase » (esquisse A/B/C du Déroulé souhaité)",
        "placeholders": ["matiere", "niveau", "seance", "phase"],
        "categorie": "prof",
        "default": PROMPT_SEANCE_PROPOSER_ESQUISSE,
    },
    "seance_style_classique": {
        "label": "Séance (Mes contenus) — style de production classique",
        "placeholders": [],
        "categorie": "prof",
        "default": PROMPT_SEANCE_STYLE_CLASSIQUE,
    },
    "seance_style_ludique": {
        "label": "Séance (Mes contenus) — style de production ludique",
        "placeholders": [],
        "categorie": "prof",
        "default": PROMPT_SEANCE_STYLE_LUDIQUE,
    },
    "seance_style_structure": {
        "label": "Séance (Mes contenus) — style de production structuré",
        "placeholders": [],
        "categorie": "prof",
        "default": PROMPT_SEANCE_STYLE_STRUCTURE,
    },
    "seance_style_concis": {
        "label": "Séance (Mes contenus) — style de production très concis",
        "placeholders": [],
        "categorie": "prof",
        "default": PROMPT_SEANCE_STYLE_CONCIS,
    },
    "sequence_generer_plan": {
        "label": "Séquence (Mes contenus) — génération du PLAN (une ligne = une séance)",
        "placeholders": ["matiere", "niveau", "objectif"],
        "categorie": "prof",
        "default": PROMPT_SEQUENCE_GENERER_PLAN,
    },
    "sequence_proposer_objectif": {
        "label": "Séquence (Mes contenus) — « Propose-moi un objectif » (zone Objectif général)",
        "placeholders": ["matiere", "niveau", "referentiel"],
        "categorie": "prof",
        "default": PROMPT_SEQUENCE_PROPOSER_OBJECTIF,
    },
    "sequence_proposer_competences": {
        "label": "Séquence (Mes contenus) — « Propose-moi des compétences » (cartouche Précisions)",
        "placeholders": ["matiere", "niveau", "objectif", "referentiel"],
        "categorie": "prof",
        "default": PROMPT_SEQUENCE_PROPOSER_COMPETENCES,
    },
    "analyse_amont": {
        "label": "Analyse amont d'un référentiel (détection des cas ambigus)",
        "placeholders": ["unites"],
        "categorie": "admin",
        "default": PROMPT_ANALYSE_AMONT,
    },
    "decoupe_amont": {
        "label": "Découpe d'un référentiel en unités (par l'IA, au dépôt du PDF)",
        "placeholders": ["texte"],
        "categorie": "admin",
        "default": PROMPT_DECOUPE_AMONT,
    },
    # ── Les trois prompts en mode « replace » (cf. l'en-tête du registre) ──────────────
    "meta_decoupe": {
        "label": "Découpe — méta-prompt : l'IA RÉDIGE le prompt de découpe du document",
        "placeholders": ["document"],
        "categorie": "admin",
        "mode": "replace",
        "default": PROMPT_META_DECOUPE,
    },
    "meta_matieres": {
        "label": "Matières — méta-prompt : l'IA RÉDIGE le prompt qui lira les matières du cycle",
        "placeholders": ["document"],
        "categorie": "admin",
        # replace, comme meta_decoupe : le prompt RÉDIGÉ doit contenir {texte} intact — un
        # `.format()` global le consommerait avec {document}.
        "mode": "replace",
        "default": PROMPT_META_MATIERES,
    },
    "verif_decoupe": {
        "label": "Découpe — méta-prompt de critique : l'IA RELIT le prompt qu'elle vient d'écrire",
        "placeholders": ["prompt"],
        "categorie": "admin",
        "mode": "replace",
        "default": PROMPT_VERIF_DECOUPE,
    },
    "gabarit_type": {
        "label": "Gabarit du prompt d'un type d'activité (posé au coche d'un type)",
        # {label} et {niveau} sont remplis ICI (au coche) ; {texte} et {referentiel} doivent
        # RESTER INTACTS — c'est la génération du prof qui les remplira. D'où le mode replace :
        # un `.format()` global consommerait aussi les deux derniers.
        "placeholders": ["label", "niveau", "texte", "referentiel"],
        "categorie": "admin",
        "mode": "replace",
        "default": PROMPT_GABARIT_TYPE,
    },
    "verifier_couple": {
        "label": "Vérification du couple (cycle + niveau) déclaré vs le document",
        "placeholders": ["cycle", "niveau", "texte"],
        "categorie": "admin",
        "default": PROMPT_VERIFIER_COUPLE,
    },
    "referentiel_fusion": {
        "label": "Fusion des documents d'un couple en un seul référentiel (bouton « Fusionner »)",
        # {documents} : les textes fournis, séparés et titrés par le serveur.
        # {consigne_taille} : la longueur visée, calculée depuis le plafond de pages EN BASE —
        # elle n'est pas écrite dans le prompt, sinon changer le plafond ne changerait rien.
        "placeholders": ["cycle", "niveau", "documents", "consigne_taille"],
        "categorie": "admin",
        "default": PROMPT_REFERENTIEL_FUSION,
    },
    "detecter_matieres": {
        "label": "Détection des matières proposées à partir du référentiel (au dépôt du PDF)",
        # {matieres_existantes} RETIRÉ : il n'y a plus de catalogue commun auquel comparer le
        # document. Chaque référentiel nomme SES matières — l'IA ne reçoit donc que le texte.
        "placeholders": ["texte"],
        "categorie": "admin",
        "default": PROMPT_DETECTER_MATIERES,
    },
    "detecter_types_activite": {
        "label": "Détection des types d'activité proposés à partir du référentiel (chunks du couple)",
        "placeholders": ["types_existants", "texte"],
        "categorie": "admin",
        "default": PROMPT_DETECTER_TYPES_ACTIVITE,
    },
    "suggerer_precisions_type": {
        "label": "Suggestion des précisions d'un type d'activité pour un niveau (écran admin des types)",
        "placeholders": ["label", "niveau", "texte"],
        "categorie": "admin",
        "default": PROMPT_SUGGERER_PRECISIONS_TYPE,
    },
    "detecter_couple": {
        "label": "Détection du cycle et du niveau depuis le document (dépôt « PDF d'abord »)",
        "placeholders": ["cycles_existants", "texte"],
        "categorie": "admin",
        "default": PROMPT_DETECTER_COUPLE,
    },
    "correction": {
        "label": "Consigne du corrigé (case « Inclure une proposition de correction »)",
        "placeholders": [],
        "categorie": "prof",
        "default": PROMPT_CORRECTION,
    },
    "controle_qualite": {
        "label": "Contrôle qualité intégré à la génération (auto-relecture du modèle)",
        "placeholders": [],
        "categorie": "prof",
        "default": PROMPT_CONTROLE_QUALITE,
    },
    "ton_academique": {
        "label": "Ton de rédaction — académique (bouton « Générer — ton académique »)",
        "placeholders": [],
        "categorie": "prof",
        "default": PROMPT_TON_ACADEMIQUE,
    },
    "ton_operationnel": {
        "label": "Ton de rédaction — opérationnel (bouton « Générer — ton opérationnel »)",
        "placeholders": [],
        "categorie": "prof",
        "default": PROMPT_TON_OPERATIONNEL,
    },
    "few_shot": {
        "label": "Few-shot « aSchool vous reconnaît » (activités précédentes du prof en exemple)",
        "placeholders": ["exemples"],
        "categorie": "prof",
        "default": PROMPT_FEW_SHOT,
    },
    "exemple_referentiel": {
        "label": "Document d'exemple (texte source tiré du programme officiel)",
        "placeholders": ["matiere", "niveau", "referentiel"],
        "categorie": "prof",
        "default": PROMPT_EXEMPLE_REFERENTIEL,
    },
    "proposer_idee": {
        "label": "« Propose-moi une idée » (demande d'activité écrite à la place du prof)",
        "placeholders": ["quoi", "niveau", "referentiel"],
        "categorie": "prof",
        "default": PROMPT_PROPOSER_IDEE,
    },
    "entete_cahier": {
        "label": "Intitulé du cahier des charges de l'établissement (ajouté aux générations)",
        "placeholders": [],
        "categorie": "prof",
        "default": PROMPT_ENTETE_CAHIER,
    },
}
