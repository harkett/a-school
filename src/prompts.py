PROMPTS = {

    # ── 1. QUESTIONS DE COMPRÉHENSION ──────────────────────────────────────────
    "comprehension": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type de questions : {sous_type}.

Types possibles :
- "simples (repérage)" : questions factuelles, réponse dans le texte
- "inférence" : l'élève doit déduire à partir d'indices
- "interprétation" : l'élève donne son avis argumenté
- "personnages" : focalisées sur les personnages
- "décor / contexte" : lieu, époque, atmosphère
- "émotions / intentions" : ce que ressentent ou veulent les personnages
- "mélange" : panacher les types ci-dessus

Formule des questions progressives (du plus simple au plus complexe).
Si QCM, propose 4 choix avec la bonne réponse indiquée.

Texte :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    # ── 2. PISTES DE LECTURE ────────────────────────────────────────────────────
    "pistes": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, propose {nb} pistes de lecture pour des élèves de {niveau}.
Angle : {sous_type}.

Angles possibles :
- "thématique" : misère, injustice, enfance, travail...
- "narrateur" : qui raconte, comment, pourquoi
- "réalisme" : procédés réalistes, ancrage dans le réel
- "point de vue" : focalisation interne/externe/omnisciente
- "registre" : pathétique, dramatique, ironique...

Chaque piste = un titre d'axe + 2-3 lignes d'explication exploitable en classe.

Texte :
---
{texte}
---
""",

    # ── 3. RÉSUMÉS ──────────────────────────────────────────────────────────────
    "resume": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, rédige un résumé pour des élèves de {niveau}.
Type de résumé : {sous_type}.

Types possibles :
- "court (5 lignes)" : résumé condensé, essentiel uniquement
- "structuré (début/milieu/fin)" : résumé en 3 parties clairement identifiées
- "pour l'oral" : formulé pour être lu à voix haute, phrases courtes et claires

Texte :
---
{texte}
---
""",

    # ── 4. ANALYSE DE TEXTE ─────────────────────────────────────────────────────
    "analyse": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, réalise une analyse pour des élèves de {niveau}.
Type d'analyse : {sous_type}.

Types possibles :
- "thème principal" : identifier et justifier le thème dominant
- "champs lexicaux" : repérer et nommer les champs lexicaux avec exemples
- "procédés d'écriture" : figures de style, syntaxe, rythme, avec effets
- "passage difficile" : reformuler et expliquer un passage complexe

Sois précis, cite des exemples du texte, formule des explications accessibles au niveau {niveau}.

Texte :
---
{texte}
---
""",

    # ── 5. EXERCICES DE RÉÉCRITURE ──────────────────────────────────────────────
    "reecriture": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, crée un exercice de réécriture pour des élèves de {niveau}.
Transformation demandée : {sous_type}.

Transformations possibles :
- "style direct vers style indirect"
- "passé simple vers présent"
- "présent vers passé simple"
- "présent vers conditionnel présent"
- "1ère personne du singulier vers 1ère personne du pluriel"
- "3ème personne du singulier vers 1ère personne du pluriel"
- "changement de point de vue"
- "simplifier le vocabulaire"
- "enrichir le texte"

Fournis :
1. Une consigne claire pour l'élève
2. Le passage à transformer (extrait du texte)
3. Un exemple de correction

Texte :
---
{texte}
---
""",

    # ── 6. ÉTUDE DE VOCABULAIRE ─────────────────────────────────────────────────
    "vocabulaire": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, crée un exercice de vocabulaire pour des élèves de {niveau}.
Type d'exercice : {sous_type}.

Types possibles :
- "mots difficiles + définitions" : liste les mots complexes avec définition adaptée au niveau
- "synonymes / antonymes" : propose des synonymes et antonymes pour des mots clés du texte
- "exercices à trous" : phrase du texte avec un mot à retrouver parmi 3 propositions
- "reformulation" : reformuler des phrases du texte avec d'autres mots

Texte :
---
{texte}
---
""",

    # ── 7. PRODUCTION D'ÉCRIT ───────────────────────────────────────────────────
    "production_ecrit": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, crée un sujet de production écrite pour des élèves de {niveau}.
Type de production : {sous_type}.

Types possibles :
- "paragraphe argumenté" : sujet avec consigne de rédaction d'un paragraphe structuré
- "continuer le texte" : consigne pour écrire la suite du passage
- "décrire un personnage" : consigne de portrait physique et moral
- "imaginer la suite d'une scène" : consigne créative avec contraintes narratives
- "texte poétique" : écriture d'un poème inspiré du texte (forme libre ou contrainte)

Fournis :
1. Le sujet complet avec consigne précise
2. Les critères de réussite (ce qui sera évalué)
3. Des pistes pour aider les élèves en difficulté

Texte :
---
{texte}
---
""",

    # ── 8. QUESTIONS POUR L'ORAL ────────────────────────────────────────────────
    "oral": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, génère {nb} questions pour l'oral pour des élèves de {niveau}.
Type d'oral : {sous_type}.

Types possibles :
- "débat" : questions ouvertes qui suscitent des avis différents
- "exposé" : questions structurantes pour préparer une présentation
- "échange en classe" : questions courtes pour lancer la discussion

Formule des questions claires, adaptées à la prise de parole en classe.

Texte :
---
{texte}
---
""",

    # ── 9. FICHE PÉDAGOGIQUE ────────────────────────────────────────────────────
    "fiche_pedagogique": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, génère une fiche pédagogique rapide pour une séance de {niveau}.

La fiche doit contenir :
1. **Objectifs de séance** (2-3 objectifs précis)
2. **Notions à retenir** (vocabulaire, notions littéraires, points de langue)
3. **Points de vigilance** (difficultés fréquentes des élèves sur ce type de texte)
4. **Activités possibles** (séquencement suggéré : mise en route → activités → bilan)

Texte :
---
{texte}
---
""",

    # ── 10. EXERCICES DE GRAMMAIRE ──────────────────────────────────────────────
    "grammaire": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, crée un exercice de grammaire pour des élèves de {niveau}.
Type d'exercice : {sous_type}.

Types possibles :
- "temps verbaux" : identifier et justifier les temps utilisés dans le texte
- "types de phrases" : repérer et classer les types et formes de phrases
- "transformer des phrases" : passer d'une forme à une autre (active/passive, etc.)
- "accords" : exercice sur les accords du GN, du verbe, du participe passé

Fournis :
1. La consigne de l'exercice
2. Les phrases ou passages extraits du texte à travailler
3. Le corrigé complet

Texte :
---
{texte}
---
""",
    # ── 11. RECHERCHE DE SÉQUENCES ─────────────────────────────────────────────
    "recherche_sequences": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, propose des idées de séquences pédagogiques pour des élèves de {niveau}.

Pour chaque séquence proposée, indique :
1. **Titre de la séquence**
2. **Objet d'étude** (ex. : le roman réaliste, la poésie, l'argumentation...)
3. **Problématique** (question directrice)
4. **Textes supports possibles** (en lien avec le texte fourni)
5. **Compétences travaillées**

Propose 3 à 5 idées de séquences adaptées au niveau {niveau}.

Texte :
---
{texte}
---
""",

    # ── 12. SÉQUENCE DÉTAILLÉE ─────────────────────────────────────────────────
    "sequence_detaillee": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, construis une séquence pédagogique complète et détaillée pour des élèves de {niveau}.

La séquence doit contenir :
1. **Titre et objet d'étude**
2. **Problématique**
3. **Objectifs** (savoirs, savoir-faire, compétences)
4. **Déroulé séance par séance** (6 à 8 séances) :
   - Titre de la séance
   - Durée (1h ou 2h)
   - Support utilisé
   - Activités élèves
   - Objectif de la séance
5. **Évaluation finale** (type et critères)

Texte support :
---
{texte}
---
""",

    # ── 13. QUESTIONNAIRE SUR UN ROMAN ────────────────────────────────────────
    "questionnaire_roman": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous (extrait ou résumé d'un roman), génère un questionnaire de lecture pour des élèves de {niveau}.

Le questionnaire doit comporter :
1. **Questions sur l'intrigue** (5 questions — repérage des faits)
2. **Questions sur les personnages** (3 questions — portrait, évolution, relations)
3. **Questions sur les thèmes** (2 questions — sens, portée du roman)
4. **Question de réaction personnelle** (1 question — ressenti, avis argumenté)

Chaque question doit être claire et adaptée au niveau {niveau}.

Texte :
---
{texte}
---
""",

    # ── 14. ÉVALUATION DE GRAMMAIRE ───────────────────────────────────────────
    "evaluation_grammaire": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, crée une évaluation de grammaire complète pour des élèves de {niveau}.

L'évaluation doit contenir :
1. **Exercice 1 — Identification** : repérer et classer des éléments grammaticaux dans le texte
2. **Exercice 2 — Transformation** : modifier des phrases selon une consigne précise
3. **Exercice 3 — Conjugaison** : conjuguer des verbes extraits du texte à d'autres temps
4. **Exercice 4 — Analyse** : analyser grammaticalement une phrase du texte

Fournis le corrigé complet après chaque exercice.
Barème suggéré pour une évaluation sur 20 points.

Texte :
---
{texte}
---
""",

    # ── 15. ÉVALUATION D'ORTHOGRAPHE ──────────────────────────────────────────
    "evaluation_orthographe": """Tu es un professeur de français expérimenté.
À partir du texte ci-dessous, crée une évaluation d'orthographe pour des élèves de {niveau}.

L'évaluation doit contenir :
1. **Dictée préparée** : un passage du texte adapté à dicter (8-10 lignes), avec liste des points de vigilance
2. **Exercice d'accords** : phrases à compléter (accords GN, participes passés, verbes)
3. **Exercice homophones** : phrases avec homophones à choisir (a/à, son/sont, etc.)
4. **Exercice de mémorisation** : 10 mots difficiles du texte à orthographier correctement

Fournis le corrigé complet.
Barème suggéré pour une évaluation sur 20 points.

Texte :
---
{texte}
---
""",
}


PROMPTS_HISTGEO = {

    "hg_comprehension": """Tu es un professeur d'histoire-géographie expérimenté.
À partir du document ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type de questions : {sous_type}.

Types possibles :
- "identification" : qui, quoi, quand, où — repérage direct dans le document
- "contexte" : replacer le document dans son contexte historique ou géographique
- "analyse" : dégager les idées principales, l'intention de l'auteur
- "mise en relation" : lier le document à d'autres connaissances du cours
- "mélange" : combiner les types ci-dessus

Formule des questions progressives. Adapte le vocabulaire au niveau {niveau}.

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "hg_analyse_source": """Tu es un professeur d'histoire-géographie expérimenté.
À partir du document ci-dessous, rédige une analyse de source complète pour des élèves de {niveau}.

L'analyse doit suivre cette structure :
1. **Présentation du document** : nature, auteur, date, destinataire, contexte de production
2. **Idées principales** : résumé structuré en 3-4 points
3. **Intérêt historique / géographique** : apport du document pour comprendre la période ou le territoire
4. **Limites et précautions** : ce que le document ne dit pas, biais éventuels

Document :
---
{texte}
---
""",

    "hg_questions_cours": """Tu es un professeur d'histoire-géographie expérimenté.
À partir du contenu de cours ci-dessous, génère {nb} questions de cours pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "connaissances" : questions factuelles sur les dates, acteurs, lieux clés
- "définitions" : demander de définir des notions importantes
- "explication" : expliquer un mécanisme, une cause, une conséquence
- "mélange" : combiner les types

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "hg_frise": """Tu es un professeur d'histoire-géographie expérimenté.
À partir du texte ci-dessous, construis une frise chronologique pédagogique pour des élèves de {niveau}.

La frise doit contenir :
1. **Les dates clés** à placer (minimum 8, maximum 15)
2. **Un événement court** associé à chaque date (1 ligne)
3. **Les périodes** à délimiter (ex. : Antiquité, Moyen Âge...)
4. **Une consigne élève** : comment compléter ou utiliser la frise en classe

Texte :
---
{texte}
---
""",

    "hg_paragraphe": """Tu es un professeur d'histoire-géographie expérimenté.
À partir du document ou cours ci-dessous, crée un sujet de paragraphe argumenté pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "réponse organisée" : paragraphe structuré avec introduction, développement, conclusion
- "SEUL" : méthode Situation / Explication / Utilisation / Lien
- "bilan de séquence" : synthèse des notions essentielles de la séquence

Fournis :
1. Le sujet complet avec la question posée
2. Les critères de réussite
3. Un plan détaillé attendu (titres de parties + arguments)

Texte :
---
{texte}
---
""",

    "hg_fiche_revision": """Tu es un professeur d'histoire-géographie expérimenté.
À partir du cours ci-dessous, génère une fiche de révision structurée pour des élèves de {niveau}.

La fiche doit contenir :
1. **Titre et thème** du chapitre
2. **Dates et repères clés** (tableau dates / événements)
3. **Acteurs importants** (nom + rôle en 1 ligne)
4. **Notions et définitions** à retenir
5. **Cartes mentales / mots-clés** pour mémoriser
6. **Questions type bac / brevet** pour s'entraîner (3 questions)

Cours :
---
{texte}
---
""",

    # ── 7. COMPOSITION / DISSERTATION ─────────────────────────────────────────
    "hg_composition": """Tu es un professeur d'histoire-géographie expérimenté.
À partir du sujet ou document ci-dessous, aide des élèves de {niveau} à construire une composition.
Type d'aide demandée : {sous_type}.

Types possibles :
- "introduction seule" : accroche + contextualisation + problématique + annonce du plan
- "plan détaillé" : 2 ou 3 parties avec sous-parties titrées et arguments clés
- "développement complet" : composition rédigée intégralement avec introduction et conclusion
- "plan avec transitions" : plan détaillé + phrases de transition entre chaque partie

Adapte le niveau de langue et la complexité au niveau {niveau}.
Pour le lycée (2nde, 1ère, Terminale) : respecte les exigences du bac (problématique, 3 parties, conclusion).
Pour le collège (3e) : structure simplifiée en 2 parties, vocabulaire accessible.

Sujet / Document :
---
{texte}
---
""",

    # ── 8. LECTURE DE CARTE / CROQUIS ─────────────────────────────────────────
    "hg_carte": """Tu es un professeur d'histoire-géographie expérimenté.
À partir de la description ou légende de carte ci-dessous, crée une activité de lecture de carte pour des élèves de {niveau}.
Type d'activité : {sous_type}.

Types possibles :
- "décrire et expliquer une carte" : guide méthodologique + questions progressives sur la carte
- "questions sur un croquis" : questions de compréhension du croquis avec éléments de légende à identifier
- "légende à compléter" : liste des figurés à placer dans la bonne catégorie de légende

Fournis :
1. Une méthode de lecture claire adaptée au niveau {niveau}
2. Les questions ou exercices
3. Les éléments de correction

Description / Légende de la carte :
---
{texte}
---
""",

    # ── 9. ÉTUDE D'UN DOCUMENT ICONOGRAPHIQUE ────────────────────────────────
    "hg_iconographie": """Tu es un professeur d'histoire-géographie expérimenté.
À partir de la description du document iconographique ci-dessous, construis une étude complète pour des élèves de {niveau}.
Type de document : {sous_type}.

Types possibles :
- "affiche de propagande" : contexte politique, messages explicites et implicites, procédés rhétoriques
- "dessin de presse" : auteur, journal, contexte, symboles, message, point de vue
- "photographie historique" : date, lieu, sujet, contexte, ce que montre / ne montre pas l'image
- "œuvre d'art" : nature, auteur, époque, description, interprétation historique

L'étude doit contenir :
1. **Présentation du document** (nature, auteur, date, contexte)
2. **Description** (ce qu'on voit — plan, personnages, symboles, couleurs, texte)
3. **Interprétation** (message, intention, mise en relation avec le cours)
4. **Limites** (ce que le document ne montre pas, biais)
5. **Questions élèves** (3 questions progressives avec correction)

Description du document :
---
{texte}
---
""",

    # ── 10. EXERCICE DE REPÈRES ───────────────────────────────────────────────
    "hg_reperes": """Tu es un professeur d'histoire-géographie expérimenté.
À partir du cours ou document ci-dessous, crée un exercice de repères pour des élèves de {niveau}.
Type d'exercice : {sous_type}.
Nombre d'items : {nb}.

Types possibles :
- "QCM de repères" : questions à choix multiples sur des dates, lieux ou acteurs clés
- "définir des notions clés" : liste de notions à définir en 2-3 lignes
- "placer des événements sur une frise" : liste d'événements à ordonner chronologiquement avec leur date
- "situer des lieux" : liste de lieux à associer à leur description géographique ou historique

Fournis :
1. L'exercice complet ({nb} items)
2. Le corrigé détaillé

Cours / Document :
---
{texte}
---
""",

    # ── 11. MISE EN RELATION DE DOCUMENTS ────────────────────────────────────
    "hg_mise_en_relation": """Tu es un professeur d'histoire-géographie expérimenté.
À partir des documents ci-dessous, construis un exercice de mise en relation pour des élèves de {niveau}.
Approche : {sous_type}.

Types possibles :
- "confronter deux sources" : comparer l'origine, le point de vue et les informations de deux documents
- "dégager complémentarité / contradiction" : identifier ce que les documents partagent ou se contredisent
- "synthèse de documents" : rédiger un paragraphe de synthèse croisant les apports des documents

Fournis :
1. Une consigne claire pour l'élève
2. Les questions guidantes (3 à 5 questions)
3. Un exemple de réponse rédigée attendue

Documents :
---
{texte}
---
""",

    # ── 12. PRÉPARATION À L'ORAL ──────────────────────────────────────────────
    "hg_oral": """Tu es un professeur d'histoire-géographie expérimenté.
À partir du sujet ou document ci-dessous, génère {nb} questions pour préparer une activité orale avec des élèves de {niveau}.
Type d'oral : {sous_type}.

Types possibles :
- "exposé" : questions structurantes pour préparer une présentation organisée (introduction, développement, conclusion)
- "débat" : questions ouvertes qui suscitent des prises de position argumentées
- "Grand Oral Terminale" : questions type Grand Oral bac, avec conseils de formulation et de posture
- "échange en classe" : questions courtes pour lancer une discussion collective

Formule des questions claires, progressives, adaptées à la prise de parole en classe de {niveau}.

Sujet / Document :
---
{texte}
---
""",
}


# ── Helpers fiches (appelés au chargement du module) ──────────────────────

def _fiche_revision(matiere: str) -> str:
    return f"""Tu es un professeur de {matiere} expérimenté.
À partir du cours ci-dessous, génère une fiche de révision structurée pour des élèves de {{niveau}}.

La fiche doit contenir :
1. **Titre et thème** du chapitre
2. **Notions et définitions** à retenir
3. **Points de méthode** essentiels
4. **Tableau ou schéma de synthèse** si pertinent
5. **Questions d'entraînement** (3 questions type bac / brevet)

Cours :
---
{{texte}}
---
"""


def _fiche_pedagogique(matiere: str) -> str:
    return f"""Tu es un professeur de {matiere} expérimenté.
À partir du document ci-dessous, génère une fiche pédagogique pour une séance de {{niveau}}.

La fiche doit contenir :
1. **Objectifs de séance** (2-3 objectifs précis)
2. **Notions à retenir** (concepts clés, vocabulaire, points de méthode)
3. **Points de vigilance** (difficultés fréquentes sur ce type de contenu)
4. **Activités suggérées** (mise en route → activités → bilan)

Document :
---
{{texte}}
---
"""


PROMPTS_AUTRES = {

    # ══════════════════════════════════════════════════════════════════════
    # PHILOSOPHIE
    # ══════════════════════════════════════════════════════════════════════

    "philo_comprehension": """Tu es un professeur de philosophie expérimenté.
À partir du texte ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type de questions : {sous_type}.

Types possibles :
- "Compréhension d'un concept" : identifier et expliquer un concept philosophique dans le texte
- "Compréhension d'un argument" : repérer la structure logique d'un argument (prémisses, conclusion)
- "Compréhension d'un texte philosophique" : dégager les idées principales et la thèse
- "Identification d'une thèse" : formuler en une phrase la position défendue par l'auteur

Formule des questions progressives. Adapte le vocabulaire au niveau {niveau}.

Texte :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "philo_questions_support": """Tu es un professeur de philosophie expérimenté.
À partir du support ci-dessous, génère {nb} questions pour des élèves de {niveau}.
Type de support : {sous_type}.

Types possibles :
- "Texte philosophique" : questions sur la thèse, les arguments, le vocabulaire
- "Extrait d'œuvre" : questions sur le contexte, l'auteur, la portée philosophique
- "Document historique" : mise en contexte philosophique et historique
- "Article contemporain" : liens avec les grandes questions philosophiques actuelles

Texte :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "philo_questions_cours": """Tu es un professeur de philosophie expérimenté.
À partir du contenu de cours ci-dessous, génère {nb} questions de cours pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Définir un concept" : donner la définition précise d'une notion philosophique
- "Expliquer une thèse" : reformuler et justifier la position d'un auteur
- "Identifier un auteur / courant" : associer une idée à son auteur ou courant de pensée
- "Mélange" : combiner les types ci-dessus

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "philo_analyse_contenu": """Tu es un professeur de philosophie expérimenté.
À partir du texte ci-dessous, réalise une analyse pour des élèves de {niveau}.
Type d'analyse : {sous_type}.

Types possibles :
- "Analyse d'un argument" : identifier prémisses, conclusion, forme logique
- "Analyse d'un texte d'auteur" : thèse, plan, procédés argumentatifs
- "Analyse de thèse / antithèse" : repérer la tension dialectique du texte
- "Analyse d'une démonstration" : suivre la progression logique du raisonnement

Sois précis, cite des passages, formule des explications adaptées au niveau {niveau}.

Texte :
---
{texte}
---
""",

    "philo_analyse_source": """Tu es un professeur de philosophie expérimenté.
À partir du texte ci-dessous, rédige une analyse de source complète pour des élèves de {niveau}.
Approche : {sous_type}.

Types possibles :
- "Analyse d'un texte philosophique" : auteur, époque, thèse, arguments, portée
- "Déconstruction d'un argument" : identifier les failles, les présupposés, les limites
- "Mise en contexte historique" : replacer la pensée dans son époque et ses débats

L'analyse doit contenir :
1. **Présentation** (auteur, œuvre, contexte)
2. **Thèse principale** (en une phrase)
3. **Structure de l'argumentation** (3-4 points)
4. **Notions philosophiques mobilisées**
5. **Portée et limites** de la pensée

Texte :
---
{texte}
---
""",

    "philo_pistes_de_lecture_in": """Tu es un professeur de philosophie expérimenté.
À partir du texte ci-dessous, propose des pistes de lecture pour des élèves de {niveau}.
Angle : {sous_type}.

Angles possibles :
- "Thématique centrale" : identifier le grand thème philosophique du texte
- "Contradiction interne" : repérer les tensions ou paradoxes dans l'argumentation
- "Lien avec d'autres auteurs" : mettre en dialogue avec d'autres philosophes
- "Actualité du texte" : montrer la pertinence contemporaine de la problématique

Chaque piste = un titre + 2-3 lignes exploitables en classe.

Texte :
---
{texte}
---
""",

    "philo_résumés_synthèses": """Tu es un professeur de philosophie expérimenté.
À partir du texte ci-dessous, réalise un travail de synthèse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Résumé d'un texte" : reformuler fidèlement la pensée de l'auteur en 10-15 lignes
- "Synthèse d'une doctrine" : présenter de façon ordonnée les grandes thèses d'un auteur
- "Synthèse d'un courant de pensée" : caractériser un mouvement philosophique et ses représentants
- "Reformulation d'un argument" : réécrire un argument complexe en langage accessible

Texte :
---
{texte}
---
""",

    "philo_étude_de_vocabulaire": """Tu es un professeur de philosophie expérimenté.
À partir du texte ci-dessous, crée un exercice de vocabulaire philosophique pour des élèves de {niveau}.
Type d'exercice : {sous_type}.

Types possibles :
- "Définir un concept philosophique" : liste de notions à définir avec exemples et contre-exemples
- "Distinguer deux notions" : paires de notions proches à différencier précisément
- "Champ lexical d'un texte" : repérer et regrouper le vocabulaire philosophique du texte
- "Notion et contre-exemple" : pour chaque notion, trouver un exemple et un contre-exemple

Texte :
---
{texte}
---
""",

    "philo_production_réponse_s": """Tu es un professeur de philosophie expérimenté.
À partir du texte ci-dessous, crée un sujet de production écrite pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Rédaction d'une réflexion" : sujet ouvert invitant à penser par soi-même à partir du texte
- "Justification d'une position" : défendre ou critiquer la thèse de l'auteur
- "Explication d'un concept" : rédiger une explication claire d'une notion philosophique

Fournis :
1. Le sujet complet avec consigne précise
2. Les critères de réussite
3. Un plan possible pour les élèves en difficulté

Texte :
---
{texte}
---
""",

    "philo_paragraphe_argumenté": """Tu es un professeur de philosophie expérimenté.
À partir du texte ci-dessous, crée un sujet de paragraphe argumenté pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Thèse + argument + exemple" : rédiger un paragraphe structuré en 3 temps
- "Objection + réponse" : formuler une objection à la thèse puis y répondre
- "Synthèse partielle" : bilan d'un moment de réflexion, transition vers l'étape suivante

Fournis :
1. Le sujet avec la consigne
2. La méthode attendue
3. Un exemple de réponse rédigée

Texte :
---
{texte}
---
""",

    "philo_dissertation": """Tu es un professeur de philosophie expérimenté.
À partir du sujet ou document ci-dessous, aide des élèves de {niveau} à construire une dissertation philosophique.
Type d'aide : {sous_type}.

Types possibles :
- "Introduction seule" : accroche + définition des termes + problématique + annonce du plan
- "Plan détaillé" : 3 parties avec sous-parties, arguments et exemples pour chaque
- "Développement complet" : dissertation rédigée intégralement avec introduction et conclusion
- "Plan avec transitions" : plan détaillé + phrases de transition entre chaque partie

Respecte la méthode de la dissertation philosophique au lycée :
- Problématisation rigoureuse (ne pas répondre d'emblée)
- 3 parties dialectiques (thèse / antithèse / synthèse) ou 2 parties bien construites
- Références aux auteurs et œuvres au programme

Sujet / Document :
---
{texte}
---
""",

    "philo_étude_iconographique": """Tu es un professeur de philosophie expérimenté.
À partir de la description du document ci-dessous, construis une étude pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Analyse d'une œuvre d'art philosophique" : liens entre l'œuvre et les idées qu'elle illustre
- "Analyse d'une image symbolique" : déchiffrer les symboles, allégories, métaphores visuelles
- "Rapport texte / image" : mettre en relation un texte philosophique et une représentation visuelle

L'étude doit contenir :
1. **Description** du document
2. **Interprétation philosophique** (concepts mobilisés)
3. **Questions élèves** (3 questions progressives avec correction)

Description du document :
---
{texte}
---
""",

    "philo_mise_en_relation": """Tu es un professeur de philosophie expérimenté.
À partir des textes ci-dessous, construis un exercice de mise en relation pour des élèves de {niveau}.
Approche : {sous_type}.

Types possibles :
- "Deux textes philosophiques" : comparer les thèses, les méthodes, les conclusions
- "Texte + contexte historique" : éclairer un texte par son époque et ses enjeux
- "Thèse + contre-thèse" : confronter deux positions opposées, dégager les enjeux du débat

Fournis :
1. La consigne pour l'élève
2. Les questions guidantes (3 à 5)
3. Un exemple de réponse attendue

Textes :
---
{texte}
---
""",

    "philo_oral": """Tu es un professeur de philosophie expérimenté.
À partir du sujet ou document ci-dessous, génère {nb} questions pour préparer une activité orale avec des élèves de {niveau}.
Type d'oral : {sous_type}.

Types possibles :
- "Exposé philosophique" : questions structurantes pour présenter une problématique
- "Débat argumenté" : questions ouvertes suscitant des prises de position philosophiques
- "Grand Oral Terminale" : questions type Grand Oral bac avec conseils de formulation

Formule des questions progressives, adaptées à la prise de parole en classe de {niveau}.

Sujet / Document :
---
{texte}
---
""",

    "philo_fiche_revision": _fiche_revision("philosophie"),
    "philo_fiche_pedagogique": _fiche_pedagogique("philosophie"),

    "philo_recherche_sequences": """Tu es un professeur de philosophie expérimenté.
À partir du texte ci-dessous, propose des idées de séquences pédagogiques pour des élèves de {niveau}.

Pour chaque séquence proposée, indique :
1. **Titre de la séquence** et notion du programme
2. **Problématique** (question directrice)
3. **Textes supports possibles** (auteurs, œuvres en lien)
4. **Compétences travaillées** (analyser, argumenter, disserter...)
5. **Évaluation finale suggérée**

Propose 3 à 5 idées de séquences adaptées au niveau {niveau}.

Texte :
---
{texte}
---
""",

    "philo_sequence_detaillee": """Tu es un professeur de philosophie expérimenté.
À partir du texte ci-dessous, construis une séquence pédagogique complète pour des élèves de {niveau}.

La séquence doit contenir :
1. **Titre, notion du programme et problématique**
2. **Objectifs** (savoirs, savoir-faire, compétences)
3. **Déroulé séance par séance** (6 à 8 séances) :
   - Titre et durée
   - Support utilisé
   - Activités élèves
   - Objectif de la séance
4. **Évaluation finale** (dissertation ou explication de texte — type et critères)

Texte support :
---
{texte}
---
""",

    # ══════════════════════════════════════════════════════════════════════
    # MATHÉMATIQUES
    # ══════════════════════════════════════════════════════════════════════

    "maths_comprehension": """Tu es un professeur de mathématiques expérimenté.
À partir du document ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Identification des données utiles" : repérer les informations pertinentes dans l'énoncé
- "Reformulation de l'énoncé" : réécrire le problème avec ses propres mots
- "Détection des contraintes" : identifier les conditions et limites du problème
- "Reconnaissance du type de problème" : identifier la notion mathématique mobilisée
- "Identification des unités / grandeurs" : repérer et vérifier la cohérence des unités
- "Lecture de schéma / graphique" : lire et interpréter une représentation visuelle

Formule des questions progressives. Adapte le vocabulaire au niveau {niveau}.

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "maths_questions_support": """Tu es un professeur de mathématiques expérimenté.
À partir du support ci-dessous, génère {nb} questions pour des élèves de {niveau}.
Type de support : {sous_type}.

Types possibles :
- "Lecture de tableau" : lire, extraire et interpréter des données tabulaires
- "Lecture de graphique" : lire les axes, les valeurs remarquables, la tendance
- "Analyse d'un schéma géométrique" : identifier les éléments et les relations
- "Analyse d'un énoncé complexe" : décomposer un problème à plusieurs étapes

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "maths_questions_cours": """Tu es un professeur de mathématiques expérimenté.
À partir du contenu ci-dessous, génère {nb} questions de cours pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Rappel d'une définition" : donner la définition précise d'un objet mathématique
- "Rappel d'une propriété / théorème" : énoncer et illustrer une propriété
- "Explication d'une méthode" : décrire pas à pas une technique de résolution
- "Mélange" : combiner les types ci-dessus

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "maths_analyse_contenu": """Tu es un professeur de mathématiques expérimenté.
À partir du document ci-dessous, réalise une analyse pour des élèves de {niveau}.
Type d'analyse : {sous_type}.

Types possibles :
- "Analyse d'un raisonnement" : vérifier la validité logique, identifier les étapes
- "Analyse d'un algorithme simple" : suivre l'exécution, identifier les variables et les sorties
- "Analyse d'une figure" : identifier les éléments géométriques, les relations, les propriétés

Document :
---
{texte}
---
""",

    "maths_étude_de_vocabulaire": """Tu es un professeur de mathématiques expérimenté.
À partir du document ci-dessous, crée un exercice de vocabulaire mathématique pour des élèves de {niveau}.
Type d'exercice : {sous_type}.

Types possibles :
- "Définir un terme mathématique" : liste de termes à définir avec exemples
- "Distinguer deux notions" : paires de notions proches à différencier (ex : diamètre/rayon)
- "Vocabulaire de géométrie" : termes géométriques à identifier dans une figure
- "Vocabulaire de statistiques" : termes statistiques à définir et illustrer

Document :
---
{texte}
---
""",

    "maths_logique": """Tu es un professeur de mathématiques expérimenté.
À partir du document ci-dessous, crée un exercice de logique mathématique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Implication et réciproque" : énoncer la réciproque, tester si elle est vraie
- "Raisonnement par l'absurde" : construire ou compléter une preuve par l'absurde
- "Contre-exemple" : trouver un contre-exemple à une propriété fausse
- "Logique propositionnelle" : tables de vérité, connecteurs logiques (ET, OU, NON)

Fournis :
1. L'exercice complet avec consigne
2. Le corrigé détaillé

Document :
---
{texte}
---
""",

    "maths_évaluation_de_logiqu": """Tu es un professeur de mathématiques expérimenté.
À partir du document ci-dessous, crée une évaluation de logique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Vrai / faux avec justification" : affirmations à valider ou infirmer avec démonstration
- "QCM raisonné" : questions à choix multiples avec justification obligatoire
- "Démonstration à compléter" : preuve lacunaire à compléter en justifiant chaque étape

Fournis l'évaluation complète avec corrigé. Barème suggéré sur 20 points.

Document :
---
{texte}
---
""",

    "maths_résumés_synthèses": """Tu es un professeur de mathématiques expérimenté.
À partir du cours ci-dessous, rédige une synthèse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Synthèse d'une méthode" : fiche méthode pas à pas, illustrée d'un exemple résolu
- "Résumé d'un théorème" : énoncé + conditions + exemple d'application + cas particuliers

Cours :
---
{texte}
---
""",

    "maths_production_réponse_s": """Tu es un professeur de mathématiques expérimenté.
À partir du document ci-dessous, crée un sujet de production pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Justification d'un raisonnement" : l'élève rédige une preuve complète et justifiée
- "Explication d'une méthode" : l'élève explique comment résoudre un type de problème

Fournis la consigne, les critères de réussite et un exemple de réponse.

Document :
---
{texte}
---
""",

    "maths_paragraphe_argumenté": """Tu es un professeur de mathématiques expérimenté.
À partir du document ci-dessous, crée un exercice de rédaction mathématique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Justification d'une démarche" : expliquer les choix de résolution étape par étape
- "Explication d'un résultat" : interpréter le résultat dans le contexte du problème
- "Raisonnement rédigé" : rédiger une démonstration complète en français et en symboles

Document :
---
{texte}
---
""",

    "maths_lecture_de_schéma_di": """Tu es un professeur de mathématiques expérimenté.
À partir du document ci-dessous, crée une activité de lecture de représentation graphique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Lecture d'un graphique de fonction" : lire les valeurs, identifier les variations, les extrema
- "Lecture d'un tableau statistique" : extraire des indicateurs (moyenne, médiane, étendue)
- "Analyse d'une figure géométrique" : identifier propriétés, angles, longueurs, symétries
- "Diagramme de probabilités" : lire un arbre, un tableau à double entrée, calculer des probabilités

Fournis les questions et le corrigé complet.

Document :
---
{texte}
---
""",

    "maths_mise_en_relation": """Tu es un professeur de mathématiques expérimenté.
À partir du document ci-dessous, crée un exercice de mise en relation pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Modèle ↔ données" : relier une situation concrète à son modèle mathématique
- "Algébrique ↔ graphique" : passer de l'expression algébrique à la représentation graphique

Document :
---
{texte}
---
""",

    "maths_oral": """Tu es un professeur de mathématiques expérimenté.
À partir du document ci-dessous, génère {nb} questions pour préparer une activité orale pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Présentation d'une démonstration" : l'élève présente et justifie une preuve à l'oral
- "Exposé d'une méthode" : l'élève explique une technique de résolution avec exemple

Document :
---
{texte}
---
""",

    "maths_fiche_revision": _fiche_revision("mathématiques"),
    "maths_fiche_pedagogique": _fiche_pedagogique("mathématiques"),

    # ══════════════════════════════════════════════════════════════════════
    # NSI
    # ══════════════════════════════════════════════════════════════════════

    "nsi_comprehension": """Tu es un professeur de NSI (Numérique et Sciences Informatiques) expérimenté.
À partir du document ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Lecture de code" : identifier ce que fait un programme, ligne par ligne
- "Compréhension d'algorithme" : dégager l'objectif, les entrées, les sorties d'un algorithme
- "Lecture de diagramme" : interpréter un diagramme de flux ou de séquence
- "Identification des variables" : repérer le rôle et le type de chaque variable

Formule des questions progressives. Adapte la complexité au niveau {niveau}.

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "nsi_questions_support": """Tu es un professeur de NSI expérimenté.
À partir du support ci-dessous, génère {nb} questions pour des élèves de {niveau}.
Type de support : {sous_type}.

Types possibles :
- "Lecture de code Python" : comprendre, annoter, prédire la sortie
- "Lecture de pseudo-code" : traduire en français, identifier la logique
- "Analyse d'un algorithme écrit" : évaluer la complexité, identifier les cas limites
- "Lecture d'un diagramme" : interpréter un diagramme UML, de flux ou un arbre

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "nsi_questions_cours": """Tu es un professeur de NSI expérimenté.
À partir du contenu ci-dessous, génère {nb} questions de cours pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Définir un concept informatique" : définir précisément un terme technique
- "Expliquer le fonctionnement d'un système" : décrire un mécanisme informatique
- "Identifier une structure de données" : reconnaître et justifier le choix d'une structure
- "Mélange" : combiner les types ci-dessus

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "nsi_analyse_contenu": """Tu es un professeur de NSI expérimenté.
À partir du code ou document ci-dessous, réalise une analyse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Analyse d'un programme" : objectif, entrées/sorties, structure générale, points clés
- "Analyse d'une fonction" : signature, paramètres, valeur de retour, effets de bord
- "Analyse d'une boucle / condition" : condition de terminaison, cas limites, invariants

Document :
---
{texte}
---
""",

    "nsi_analyse_source": """Tu es un professeur de NSI expérimenté.
À partir du code source ci-dessous, rédige une analyse complète pour des élèves de {niveau}.
Approche : {sous_type}.

Types possibles :
- "Analyse de code source" : structure, fonctions, algorithmes utilisés, qualité du code
- "Analyse de pseudo-code" : traduction en Python, évaluation de la logique
- "Analyse de structure de données" : choix de la structure, avantages, limites, complexité

L'analyse doit contenir :
1. **Description générale** du code / document
2. **Points clés** à retenir (3-5 points)
3. **Questions élèves** (3 questions avec correction)

Document :
---
{texte}
---
""",

    "nsi_étude_de_vocabulaire": """Tu es un professeur de NSI expérimenté.
À partir du document ci-dessous, crée un exercice de vocabulaire informatique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Vocabulaire algorithmique" : définir itération, récursivité, complexité, tri...
- "Vocabulaire réseau" : protocoles, adresses IP, routage, DNS, HTTP...
- "Vocabulaire base de données" : table, requête SQL, clé primaire, jointure...
- "Vocabulaire systèmes" : processus, mémoire, système de fichiers, OS...

Document :
---
{texte}
---
""",

    "nsi_logique": """Tu es un professeur de NSI expérimenté.
À partir du document ci-dessous, crée un exercice de logique informatique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Tables de vérité" : compléter ou construire des tables de vérité (ET, OU, NON, XOR)
- "Algèbre de Boole" : simplifier des expressions booléennes
- "Déduction algorithmique" : prédire la sortie d'un algorithme pour des entrées données
- "Correction d'erreur de logique" : identifier et corriger un bug logique dans un code

Fournis l'exercice complet avec corrigé détaillé.

Document :
---
{texte}
---
""",

    "nsi_évaluation_de_logiqu": """Tu es un professeur de NSI expérimenté.
À partir du document ci-dessous, crée une évaluation de logique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "QCM de logique" : questions à choix multiples sur la logique booléenne et algorithmique
- "Vrai / faux raisonné" : affirmations à valider avec justification
- "Trace d'exécution" : suivre pas à pas l'exécution d'un programme, noter les valeurs des variables

Fournis l'évaluation complète avec corrigé. Barème suggéré sur 20 points.

Document :
---
{texte}
---
""",

    "nsi_résumés_synthèses": """Tu es un professeur de NSI expérimenté.
À partir du cours ci-dessous, rédige une synthèse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Résumé d'un algorithme" : description claire, complexité, cas d'usage, exemple
- "Synthèse d'une architecture" : composants, rôles, interactions, schéma explicatif

Cours :
---
{texte}
---
""",

    "nsi_production_réponse_s": """Tu es un professeur de NSI expérimenté.
À partir du document ci-dessous, crée un sujet de production pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Rédaction d'un algorithme" : écrire un algorithme en pseudo-code ou en Python
- "Explication d'un code" : rédiger un commentaire structuré expliquant le fonctionnement d'un programme

Fournis la consigne, les critères de réussite et un exemple de réponse.

Document :
---
{texte}
---
""",

    "nsi_paragraphe_argumenté": """Tu es un professeur de NSI expérimenté.
À partir du document ci-dessous, crée un sujet de rédaction argumentée pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Justification d'un choix algorithmique" : défendre le choix d'un algorithme face à une alternative
- "Explication d'un concept technique" : expliquer un mécanisme informatique à un non-spécialiste
- "Argumentation sur une architecture" : justifier les choix d'architecture d'un système

Document :
---
{texte}
---
""",

    "nsi_schema": """Tu es un professeur de NSI expérimenté.
À partir du document ci-dessous, crée une activité de lecture de diagramme pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Diagramme de flux" : lire le déroulement, identifier les conditions, les boucles
- "Diagramme de séquence UML" : identifier les acteurs, les messages, les interactions
- "Schéma réseau" : identifier les composants (routeur, switch, serveur), les connexions
- "Arbre de décision" : lire les branches, associer des conditions aux nœuds

Fournis les questions et le corrigé complet.

Document :
---
{texte}
---
""",

    "nsi_mise_en_relation": """Tu es un professeur de NSI expérimenté.
À partir du document ci-dessous, crée un exercice de mise en relation pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Code ↔ diagramme" : passer d'un code à son diagramme de flux (ou inversement)
- "Problème ↔ algorithme" : relier un énoncé de problème à l'algorithme qui le résout

Document :
---
{texte}
---
""",

    "nsi_oral": """Tu es un professeur de NSI expérimenté.
À partir du document ci-dessous, génère {nb} questions pour préparer une activité orale pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Présentation d'un projet" : structure d'un exposé de projet informatique (contexte, conception, résultats)
- "Exposé technique" : présenter un concept informatique de façon claire et structurée

Document :
---
{texte}
---
""",

    "nsi_fiche_revision": _fiche_revision("NSI"),
    "nsi_fiche_pedagogique": _fiche_pedagogique("NSI"),

    # ══════════════════════════════════════════════════════════════════════
    # PHYSIQUE-CHIMIE
    # ══════════════════════════════════════════════════════════════════════

    "pc_comprehension": """Tu es un professeur de physique-chimie expérimenté.
À partir du document ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Compréhension d'un montage" : identifier les composants, les connexions, l'objectif
- "Compréhension d'un protocole" : dégager les étapes, les précautions, les mesures
- "Lecture d'un graphique" : lire les axes, interpréter la courbe, dégager une loi

Formule des questions progressives. Adapte le vocabulaire au niveau {niveau}.

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "pc_questions_support": """Tu es un professeur de physique-chimie expérimenté.
À partir du support ci-dessous, génère {nb} questions pour des élèves de {niveau}.
Type de support : {sous_type}.

Types possibles :
- "Lecture d'un graphique expérimental" : axes, unités, allure, valeurs remarquables
- "Analyse d'un tableau de mesures" : extraire des valeurs, calculer des grandeurs dérivées
- "Lecture d'un schéma de montage" : identifier les éléments et leurs rôles
- "Analyse d'un spectre" : identifier les raies, les longueurs d'onde, les transitions

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "pc_questions_cours": """Tu es un professeur de physique-chimie expérimenté.
À partir du contenu ci-dessous, génère {nb} questions de cours pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Rappel d'une loi / formule" : énoncer et expliquer une loi physique ou chimique
- "Définir une grandeur physique" : définition, unité, ordre de grandeur
- "Expliquer un phénomène" : décrire et interpréter un phénomène physique ou chimique
- "Mélange" : combiner les types ci-dessus

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "pc_analyse_contenu": """Tu es un professeur de physique-chimie expérimenté.
À partir du document ci-dessous, réalise une analyse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Analyse d'un modèle" : hypothèses, domaine de validité, prédictions, limites
- "Analyse d'une expérience" : protocole, résultats attendus, sources d'erreurs, conclusion

Document :
---
{texte}
---
""",

    "pc_analyse_source": """Tu es un professeur de physique-chimie expérimenté.
À partir du document ci-dessous, rédige une analyse de source pour des élèves de {niveau}.
Approche : {sous_type}.

Types possibles :
- "Analyse d'un protocole expérimental" : objectif, matériel, étapes, précautions, résultats attendus
- "Analyse d'un article scientifique" : hypothèse, méthode, résultats, conclusion, portée
- "Interprétation de données expérimentales" : traitement, représentation, loi dégagée, incertitudes

L'analyse doit contenir :
1. **Présentation** du document
2. **Points clés** (3-5)
3. **Questions élèves** (3 questions avec correction)

Document :
---
{texte}
---
""",

    "pc_étude_de_vocabulaire": """Tu es un professeur de physique-chimie expérimenté.
À partir du document ci-dessous, crée un exercice de vocabulaire pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Définir une grandeur physique" : nom, symbole, unité SI, formule de définition
- "Distinguer deux concepts" : différencier des notions proches (ex : masse/poids)
- "Vocabulaire de chimie" : atome, molécule, liaison, réaction, oxydoréduction...
- "Vocabulaire d'optique / électricité" : termes spécifiques à définir et illustrer

Document :
---
{texte}
---
""",

    "pc_résumés_synthèses": """Tu es un professeur de physique-chimie expérimenté.
À partir du cours ci-dessous, rédige une synthèse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Synthèse d'un protocole" : fiche protocole pas à pas avec précautions et schéma
- "Résumé d'un modèle" : hypothèses, formules clés, domaine d'application, exemple

Cours :
---
{texte}
---
""",

    "pc_production_réponse_s": """Tu es un professeur de physique-chimie expérimenté.
À partir du document ci-dessous, crée un sujet de production pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Justification d'un résultat" : l'élève rédige une conclusion scientifique à partir de données
- "Analyse d'erreur" : l'élève identifie et commente les sources d'incertitude d'une mesure

Fournis la consigne, les critères et un exemple de réponse.

Document :
---
{texte}
---
""",

    "pc_paragraphe_argumenté": """Tu es un professeur de physique-chimie expérimenté.
À partir du document ci-dessous, crée un sujet de rédaction scientifique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Justification d'un résultat expérimental" : relier les résultats à la théorie avec argumentation
- "Explication d'un phénomène physique" : décrire et interpréter un phénomène de façon rédigée
- "Conclusion rédigée d'une expérience" : bilan expérimental en 3-4 phrases structurées

Document :
---
{texte}
---
""",

    "pc_lecture_de_schéma_di": """Tu es un professeur de physique-chimie expérimenté.
À partir du document ci-dessous, crée une activité de lecture de schéma pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Schéma de montage électrique" : identifier composants, tensions, intensités
- "Diagramme énergie-temps" : lire les transferts d'énergie, identifier les phases
- "Graphique de décroissance radioactive" : lire la demi-vie, calculer une activité
- "Schéma de circuit" : tracer ou annoter un circuit électrique

Fournis les questions et le corrigé complet.

Document :
---
{texte}
---
""",

    "pc_mise_en_relation": """Tu es un professeur de physique-chimie expérimenté.
À partir du document ci-dessous, crée un exercice de mise en relation pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Modèle ↔ expérience" : confronter les prédictions d'un modèle aux données expérimentales
- "Données ↔ loi physique" : retrouver la loi à partir de données (proportionnalité, puissance...)

Document :
---
{texte}
---
""",

    "pc_oral": """Tu es un professeur de physique-chimie expérimenté.
À partir du document ci-dessous, génère {nb} questions pour préparer une activité orale pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Présentation d'une expérience" : structure d'un exposé de TP (contexte, protocole, résultats, conclusion)
- "Exposé scientifique" : présenter un phénomène physique ou chimique de façon claire

Document :
---
{texte}
---
""",

    "pc_fiche_revision": _fiche_revision("physique-chimie"),
    "pc_fiche_pedagogique": _fiche_pedagogique("physique-chimie"),

    # ══════════════════════════════════════════════════════════════════════
    # SVT
    # ══════════════════════════════════════════════════════════════════════

    "svt_comprehension": """Tu es un professeur de SVT (Sciences de la Vie et de la Terre) expérimenté.
À partir du document ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Lecture d'un schéma" : identifier les structures biologiques représentées et leurs rôles
- "Compréhension d'un protocole" : dégager les étapes, les précautions, les mesures
- "Lecture d'un graphique" : lire les axes, interpréter les variations, dégager une tendance

Formule des questions progressives. Adapte le vocabulaire au niveau {niveau}.

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "svt_questions_support": """Tu es un professeur de SVT expérimenté.
À partir du support ci-dessous, génère {nb} questions pour des élèves de {niveau}.
Type de support : {sous_type}.

Types possibles :
- "Lecture d'un schéma biologique" : identifier structures, fonctions, relations
- "Analyse d'un tableau de données" : extraire, comparer, calculer des valeurs
- "Lecture d'un graphique expérimental" : axes, unités, allure, valeurs remarquables
- "Analyse d'une image de microscopie" : identifier les structures cellulaires visibles

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "svt_questions_cours": """Tu es un professeur de SVT expérimenté.
À partir du contenu ci-dessous, génère {nb} questions de cours pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Rappel d'un mécanisme biologique" : décrire les étapes d'un processus (respiration, photosynthèse...)
- "Définir un terme scientifique" : définition précise d'un mot du vocabulaire SVT
- "Expliquer une fonction" : relier structure et fonction (rôle d'un organe, d'une cellule...)
- "Mélange" : combiner les types ci-dessus

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "svt_analyse_contenu": """Tu es un professeur de SVT expérimenté.
À partir du document ci-dessous, réalise une analyse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Analyse d'un mécanisme" : décrire les étapes, les acteurs, les régulations
- "Analyse d'une expérience" : protocole, résultats attendus, conclusion, limites

Document :
---
{texte}
---
""",

    "svt_analyse_source": """Tu es un professeur de SVT expérimenté.
À partir du document ci-dessous, rédige une analyse de source pour des élèves de {niveau}.
Approche : {sous_type}.

Types possibles :
- "Analyse d'un protocole expérimental" : objectif, matériel, étapes, précautions, résultats attendus
- "Analyse de résultats expérimentaux" : traitement des données, interprétation, conclusion
- "Analyse d'un document scientifique" : hypothèse, méthode, résultats, portée, limites

L'analyse doit contenir :
1. **Présentation** du document
2. **Points clés** (3-5)
3. **Questions élèves** (3 questions avec correction)

Document :
---
{texte}
---
""",

    "svt_étude_de_vocabulaire": """Tu es un professeur de SVT expérimenté.
À partir du document ci-dessous, crée un exercice de vocabulaire scientifique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Définir un terme biologique" : définition précise avec exemple
- "Distinguer deux notions" : différencier des concepts proches (ex : ADN/ARN, mitose/méiose)
- "Vocabulaire de génétique" : gène, allèle, génotype, phénotype, mutation...
- "Vocabulaire de physiologie" : homéostasie, métabolisme, régulation, stimulus...

Document :
---
{texte}
---
""",

    "svt_résumés_synthèses": """Tu es un professeur de SVT expérimenté.
À partir du cours ci-dessous, rédige une synthèse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Synthèse d'un mécanisme" : description ordonnée des étapes clés avec schéma bilan possible

Cours :
---
{texte}
---
""",

    "svt_production_réponse_s": """Tu es un professeur de SVT expérimenté.
À partir du document ci-dessous, crée un sujet de production pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Explication d'un phénomène" : l'élève rédige une explication scientifique structurée

Fournis la consigne, les critères et un exemple de réponse.

Document :
---
{texte}
---
""",

    "svt_paragraphe_argumenté": """Tu es un professeur de SVT expérimenté.
À partir du document ci-dessous, crée un sujet de rédaction scientifique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Bilan d'expérience rédigé" : conclusions tirées de résultats expérimentaux en 3-4 phrases
- "Explication d'un mécanisme" : décrire un processus biologique de façon rédigée et structurée
- "Réponse à une problématique scientifique" : répondre à une question en s'appuyant sur des documents

Document :
---
{texte}
---
""",

    "svt_lecture_de_schéma_di": """Tu es un professeur de SVT expérimenté.
À partir du document ci-dessous, crée une activité de lecture de schéma pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Schéma du corps humain" : légender, annoter, expliquer les relations entre organes
- "Schéma d'un mécanisme cellulaire" : identifier les structures, décrire les échanges
- "Graphique d'évolution" : lire les tendances, identifier les phases, expliquer les variations
- "Diagramme écologique" : lire une pyramide des âges, un réseau trophique, un diagramme climatique

Fournis les questions et le corrigé complet.

Document :
---
{texte}
---
""",

    "svt_mise_en_relation": """Tu es un professeur de SVT expérimenté.
À partir des documents ci-dessous, crée un exercice de mise en relation pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Documents ↔ mécanisme" : relier les informations des documents pour expliquer un mécanisme biologique

Document :
---
{texte}
---
""",

    "svt_oral": """Tu es un professeur de SVT expérimenté.
À partir du document ci-dessous, génère {nb} questions pour préparer une activité orale pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Présentation d'une expérience" : structure d'un exposé scientifique (contexte, protocole, résultats, conclusion)
- "Exposé scientifique" : présenter un phénomène biologique ou géologique de façon claire

Document :
---
{texte}
---
""",

    "svt_fiche_revision": _fiche_revision("SVT"),
    "svt_fiche_pedagogique": _fiche_pedagogique("SVT"),

    # ══════════════════════════════════════════════════════════════════════
    # TECHNOLOGIE
    # ══════════════════════════════════════════════════════════════════════

    "techno_comprehension": """Tu es un professeur de technologie expérimenté.
À partir du document ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Lecture d'un schéma technique" : identifier les composants, les liaisons, les flux
- "Compréhension d'un système" : identifier la fonction d'usage, les entrées/sorties, les contraintes

Formule des questions progressives. Adapte le vocabulaire au niveau {niveau}.

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "techno_questions_support": """Tu es un professeur de technologie expérimenté.
À partir du support ci-dessous, génère {nb} questions pour des élèves de {niveau}.
Type de support : {sous_type}.

Types possibles :
- "Lecture d'un schéma technique" : identifier les composants et leurs fonctions
- "Analyse d'un cahier des charges" : identifier les fonctions de service, les contraintes
- "Lecture d'un diagramme de flux" : suivre le flux d'énergie ou de matière
- "Analyse d'un plan" : lire les cotes, identifier les vues, reconnaître les formes

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "techno_questions_cours": """Tu es un professeur de technologie expérimenté.
À partir du contenu ci-dessous, génère {nb} questions de cours pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Rappel d'un principe technique" : énoncer et expliquer un principe de fonctionnement
- "Définir un composant" : nom, rôle, symbole, exemples d'utilisation
- "Expliquer une fonction d'usage" : à quoi sert l'objet, quel besoin il satisfait
- "Mélange" : combiner les types ci-dessus

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "techno_analyse_contenu": """Tu es un professeur de technologie expérimenté.
À partir du document ci-dessous, réalise une analyse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Analyse fonctionnelle" : fonctions principales, fonctions contraintes, diagramme FAST
- "Analyse structurelle" : identification des sous-ensembles, des liaisons, des matériaux

Document :
---
{texte}
---
""",

    "techno_analyse_source": """Tu es un professeur de technologie expérimenté.
À partir du document ci-dessous, rédige une analyse pour des élèves de {niveau}.
Approche : {sous_type}.

Types possibles :
- "Analyse d'un cahier des charges" : fonctions de service, critères, niveaux, flexibilité
- "Analyse d'une solution technique existante" : avantages, inconvénients, domaine d'usage
- "Analyse d'un prototype" : conformité au cahier des charges, points forts, améliorations

Document :
---
{texte}
---
""",

    "techno_étude_de_vocabulaire": """Tu es un professeur de technologie expérimenté.
À partir du document ci-dessous, crée un exercice de vocabulaire technique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Vocabulaire mécanique" : liaison, guidage, transmission, assemblage...
- "Vocabulaire électronique" : capteur, actionneur, microcontrôleur, signal...
- "Vocabulaire informatique industrielle" : programme, variable, boucle, condition...
- "Définir une fonction technique" : relier une fonction à son nom technique et à un exemple

Document :
---
{texte}
---
""",

    "techno_résumés_synthèses": """Tu es un professeur de technologie expérimenté.
À partir du cours ci-dessous, rédige une synthèse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Synthèse d'un fonctionnement" : description ordonnée du fonctionnement d'un système technique

Cours :
---
{texte}
---
""",

    "techno_production_réponse_s": """Tu es un professeur de technologie expérimenté.
À partir du document ci-dessous, crée un sujet de production pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Justification d'un choix technique" : l'élève argumente le choix d'une solution face à un cahier des charges

Fournis la consigne, les critères et un exemple de réponse.

Document :
---
{texte}
---
""",

    "techno_paragraphe_argumenté": """Tu es un professeur de technologie expérimenté.
À partir du document ci-dessous, crée un sujet de rédaction technique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Justification d'un choix de matériau" : comparer des matériaux selon des critères techniques
- "Justification d'une solution technique" : argumenter en faveur d'une solution face à des alternatives
- "Argumentation face à un cahier des charges" : montrer que la solution répond aux exigences

Document :
---
{texte}
---
""",

    "techno_lecture_de_schéma_di": """Tu es un professeur de technologie expérimenté.
À partir du document ci-dessous, crée une activité de lecture de schéma pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Schéma cinématique" : identifier les liaisons, les mouvements, les degrés de liberté
- "Diagramme FAST" : identifier les fonctions de service, les fonctions techniques
- "Schéma de flux d'énergie" : suivre la chaîne d'énergie (source → distribution → conversion → action)
- "Plan de pièce" : lire les vues, les cotes, les tolérances

Fournis les questions et le corrigé complet.

Document :
---
{texte}
---
""",

    "techno_mise_en_relation": """Tu es un professeur de technologie expérimenté.
À partir du document ci-dessous, crée un exercice de mise en relation pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Besoin ↔ solution" : relier un besoin du cahier des charges à la solution technique adoptée

Document :
---
{texte}
---
""",

    "techno_oral": """Tu es un professeur de technologie expérimenté.
À partir du document ci-dessous, génère {nb} questions pour préparer une activité orale pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Présentation d'un projet technique" : structure de l'exposé (contexte, conception, réalisation, bilan)
- "Soutenance de dossier" : présenter un dossier technique devant un jury

Document :
---
{texte}
---
""",

    "techno_fiche_revision": _fiche_revision("technologie"),
    "techno_fiche_pedagogique": _fiche_pedagogique("technologie"),

    # ══════════════════════════════════════════════════════════════════════
    # SES
    # ══════════════════════════════════════════════════════════════════════

    "ses_comprehension": """Tu es un professeur de SES (Sciences Économiques et Sociales) expérimenté.
À partir du document ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Lecture d'un graphique économique" : axes, unités, tendances, valeurs remarquables
- "Lecture d'un tableau statistique" : extraire des données, calculer des variations, comparer
- "Compréhension d'un mécanisme économique" : identifier les acteurs, les relations de causalité

Formule des questions progressives. Adapte le vocabulaire au niveau {niveau}.

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "ses_questions_support": """Tu es un professeur de SES expérimenté.
À partir du support ci-dessous, génère {nb} questions pour des élèves de {niveau}.
Type de support : {sous_type}.

Types possibles :
- "Lecture d'un graphique statistique" : lire, interpréter, nuancer
- "Analyse d'un tableau de données INSEE" : extraire, comparer, calculer des évolutions
- "Lecture d'un article de presse économique" : idée principale, arguments, nuances
- "Analyse d'un document institutionnel" : nature, auteur, contexte, message principal

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "ses_questions_cours": """Tu es un professeur de SES expérimenté.
À partir du contenu ci-dessous, génère {nb} questions de cours pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Rappel d'un mécanisme économique" : décrire les relations de causalité (offre/demande, prix...)
- "Définir un concept" : définition précise avec exemple et illustration statistique
- "Identifier un acteur économique" : rôle, comportement, interactions avec d'autres acteurs
- "Mélange" : combiner les types ci-dessus

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "ses_analyse_contenu": """Tu es un professeur de SES expérimenté.
À partir du document ci-dessous, réalise une analyse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Analyse d'un document scientifique" : hypothèse, méthode, résultats, portée, limites
- "Analyse d'un modèle économique" : hypothèses, mécanismes, prédictions, critiques

Document :
---
{texte}
---
""",

    "ses_analyse_source": """Tu es un professeur de SES expérimenté.
À partir du document ci-dessous, rédige une analyse de source pour des élèves de {niveau}.
Approche : {sous_type}.

Types possibles :
- "Analyse d'un article scientifique en économie" : hypothèse, méthode, résultats, portée
- "Analyse d'une étude statistique" : échantillon, méthode, résultats, limites
- "Analyse d'un rapport institutionnel" : commanditaire, objectif, conclusions, nuances

L'analyse doit contenir :
1. **Présentation** du document (nature, auteur, date)
2. **Idées principales** (3-4 points)
3. **Intérêt et limites** pour comprendre la réalité économique et sociale
4. **Questions élèves** (3 questions avec correction)

Document :
---
{texte}
---
""",

    "ses_étude_de_vocabulaire": """Tu es un professeur de SES expérimenté.
À partir du document ci-dessous, crée un exercice de vocabulaire économique et social pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Définir un concept économique" : définition précise avec exemple chiffré ou illustration
- "Distinguer deux notions" : différencier des concepts proches (ex : croissance/développement)
- "Vocabulaire de sociologie" : socialisation, stratification, mobilité sociale, capital...
- "Vocabulaire de politique économique" : politique budgétaire, monétaire, fiscale...

Document :
---
{texte}
---
""",

    "ses_résumés_synthèses": """Tu es un professeur de SES expérimenté.
À partir du cours ci-dessous, rédige une synthèse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Synthèse d'un chapitre" : récapituler les notions clés, les mécanismes, les données chiffrées
- "Résumé d'un mécanisme" : décrire en 10 lignes un enchaînement de causes et d'effets

Cours :
---
{texte}
---
""",

    "ses_production_réponse_s": """Tu es un professeur de SES expérimenté.
À partir du document ci-dessous, crée un sujet de production pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Rédaction d'un paragraphe argumenté" : thèse + argument + illustration statistique + conclusion
- "Réponse construite à une question" : réponse structurée en 2-3 parties, avec données à l'appui

Fournis la consigne, les critères et un exemple de réponse.

Document :
---
{texte}
---
""",

    "ses_paragraphe_argumenté": """Tu es un professeur de SES expérimenté.
À partir du document ci-dessous, crée un sujet de paragraphe argumenté pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Thèse + argument + illustration statistique" : structure en 3 temps avec donnée chiffrée obligatoire
- "Réponse construite en SES" : thèse, mécanisme, nuance — avec auteur ou donnée à l'appui
- "Bilan de mécanisme" : synthèse rédigée d'un enchaînement économique ou social

Document :
---
{texte}
---
""",

    "ses_dissertation": """Tu es un professeur de SES expérimenté.
À partir du sujet ou document ci-dessous, aide des élèves de {niveau} à construire une dissertation de SES.
Type d'aide : {sous_type}.

Types possibles :
- "Introduction seule" : accroche + définitions + problématique + annonce du plan
- "Plan détaillé" : 2 ou 3 parties avec sous-parties, arguments et données chiffrées
- "Développement complet" : dissertation rédigée intégralement
- "Plan avec transitions" : plan détaillé + phrases de liaison entre les parties

Respecte la méthode de la dissertation de SES au lycée :
- Utiliser des données chiffrées et des auteurs (économistes, sociologues)
- Structurer l'argumentation (thèse, antithèse, synthèse)
- Distinguer niveaux micro et macroéconomique si pertinent

Sujet / Document :
---
{texte}
---
""",

    "ses_mise_en_relation": """Tu es un professeur de SES expérimenté.
À partir des documents ci-dessous, crée un exercice de mise en relation pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Données ↔ mécanisme" : relier des données statistiques à un mécanisme économique ou social
- "Modèle ↔ situation réelle" : confronter les prédictions d'un modèle à des données réelles

Document :
---
{texte}
---
""",

    "ses_oral": """Tu es un professeur de SES expérimenté.
À partir du sujet ou document ci-dessous, génère {nb} questions pour préparer une activité orale pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Exposé économique" : questions structurantes pour présenter une problématique économique
- "Débat argumenté" : questions ouvertes suscitant des prises de position argumentées
- "Grand Oral Terminale" : questions type Grand Oral bac avec conseils de formulation

Document :
---
{texte}
---
""",

    "ses_fiche_revision": _fiche_revision("SES"),
    "ses_fiche_pedagogique": _fiche_pedagogique("SES"),

    # ══════════════════════════════════════════════════════════════════════
    # LANGUES VIVANTES
    # ══════════════════════════════════════════════════════════════════════

    "lv_comprehension": """Tu es un professeur de {langue} expérimenté.
À partir du document ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Compréhension écrite" : repérage d'informations, idée générale, détails importants
- "Compréhension orale" : questions adaptées à un document audio ou vidéo (décrit dans le texte)
- "Compréhension lexicale" : sens des mots en contexte, champ lexical, registre

Formule des questions progressives. Adapte le niveau linguistique à la classe {niveau}.

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "lv_questions_support": """Tu es un professeur de {langue} expérimenté.
À partir du support ci-dessous, génère {nb} questions pour des élèves de {niveau}.
Type de support : {sous_type}.

Types possibles :
- "Texte en langue étrangère" : compréhension, vocabulaire, structure, intention de l'auteur
- "Document audio / vidéo" : questions sur le contenu, les locuteurs, le contexte
- "Article de presse" : idée principale, arguments, nuances, points de vue
- "Document iconographique" : description, interprétation, mise en relation avec un thème culturel

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "lv_questions_cours": """Tu es un professeur de {langue} expérimenté.
À partir du contenu ci-dessous, génère {nb} questions de cours pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Règle grammaticale" : énoncer et illustrer une règle de grammaire
- "Fait culturel et civilisationnel" : rappeler un fait historique, culturel ou social de la langue cible
- "Vocabulaire thématique" : questions sur un champ lexical du cours
- "Mélange" : combiner les types ci-dessus

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "lv_analyse_contenu": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, réalise une analyse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Analyse d'un texte court" : structure, idées principales, registre, intention
- "Analyse d'un dialogue" : rôles, relations entre locuteurs, enjeux de l'échange
- "Analyse d'intentions (registre, ton, point de vue)" : identifier le registre, le ton, la visée

Document :
---
{texte}
---
""",

    "lv_pistes_de_lecture_in": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, propose des pistes de lecture pour des élèves de {niveau}.
Angle : {sous_type}.

Angles possibles :
- "Thématique culturelle" : relier le texte à un grand thème culturel de la langue cible
- "Point de vue de l'auteur" : identifier la position, les intentions, les biais de l'auteur
- "Implicite culturel" : repérer ce qui est sous-entendu, propre à la culture de la langue cible
- "Registre et ton" : analyser le niveau de langue, le ton (humoristique, critique, nostalgique...)

Chaque piste = un titre + 2-3 lignes exploitables en classe.

Texte :
---
{texte}
---
""",

    "lv_étude_de_vocabulaire": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, crée un exercice de vocabulaire pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Vocabulaire thématique" : liste de mots clés du texte à définir et mémoriser
- "Faux amis" : repérer et expliquer les faux amis présents dans le texte
- "Expressions idiomatiques" : identifier et expliquer les expressions figées
- "Collocations" : associations de mots fréquentes (verbe + nom, adjectif + nom...)

Texte :
---
{texte}
---
""",

    "lv_exercices_de_réécrit": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, crée un exercice de transformation pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Transformation de phrases (affirmatif ↔ négatif, actif ↔ passif, direct ↔ indirect)" : transformer des phrases selon la consigne
- "Reformulation avec contrainte (temps, modalité, pronom, connecteur)" : réécrire en changeant un élément grammatical
- "Correction d'erreurs dans un texte court" : identifier et corriger les fautes dans un passage

Fournis :
1. La consigne claire pour l'élève
2. Les phrases ou le passage à transformer (extrait du texte)
3. Le corrigé complet

Texte :
---
{texte}
---
""",

    "lv_grammaire": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, crée un exercice de grammaire pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Conjugaison (temps, aspects, modes)" : identifier et justifier les temps, conjuguer à d'autres temps
- "Accord (genre, nombre, personne)" : exercices sur les accords dans les groupes nominaux et verbaux
- "Ordre des mots / structure de phrase" : remettre dans l'ordre, compléter une structure
- "Utilisation des temps (présent, prétérit, present perfect…)" : choisir le bon temps selon le contexte

Fournis la consigne, les exercices extraits du texte, et le corrigé complet.

Texte :
---
{texte}
---
""",

    "lv_eval_grammaire": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, crée une évaluation de grammaire pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "QCM grammatical" : choisir la bonne forme parmi 3 ou 4 propositions
- "Texte à trous" : compléter un texte avec les formes grammaticales correctes
- "Correction d'erreurs" : repérer et corriger les erreurs grammaticales dans un texte
- "Transformation de phrases" : appliquer une règle grammaticale à des phrases extraites

Fournis l'évaluation complète avec corrigé. Barème suggéré sur 20 points.

Texte :
---
{texte}
---
""",

    "lv_eval_ortho": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, crée une évaluation d'orthographe pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Orthographe lexicale (mots fréquents)" : liste de mots courants à orthographier correctement
- "Orthographe grammaticale (accords de base)" : accords en genre, nombre, personne
- "Ponctuation et majuscules" : utilisation correcte de la ponctuation et des majuscules en langue étrangère

Fournis l'évaluation complète avec corrigé. Barème suggéré sur 20 points.

Texte :
---
{texte}
---
""",

    "lv_résumés_synthèses": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, crée un exercice de synthèse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Résumé d'un texte" : résumer fidèlement le contenu en langue étrangère (limite de mots précisée)
- "Reformulation dans la même langue" : reformuler des passages complexes avec des mots plus simples
- "Reformulation simplifiée" : réécrire le texte pour un niveau plus accessible

Texte :
---
{texte}
---
""",

    "lv_production_réponse_s": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, crée un sujet de production pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Production écrite (message, récit, description, argumentation simple)" : sujet avec consigne, longueur, critères
- "Production orale (présentation, interaction, jeu de rôle)" : consigne pour une activité orale

Fournis :
1. Le sujet complet avec consigne
2. Les critères de réussite
3. Des pistes pour les élèves en difficulté

Texte :
---
{texte}
---
""",

    "lv_paragraphe_argumenté": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, crée un sujet de paragraphe argumenté pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Opinion personnelle structurée" : exprimer et défendre un point de vue avec arguments
- "Pour / contre" : lister les arguments favorables et défavorables à une position
- "Synthèse d'un document" : résumer et commenter le contenu d'un document en langue étrangère
- "Réponse à une question ouverte" : répondre de façon développée à une question de compréhension

Document :
---
{texte}
---
""",

    "lv_étude_iconographique": """Tu es un professeur de {langue} expérimenté.
À partir de la description du document ci-dessous, construis une étude iconographique pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Analyse d'une publicité" : contexte culturel, message, techniques rhétoriques, vocabulaire visuel
- "Analyse d'une affiche culturelle" : contexte, message, références culturelles, rapport texte/image
- "Analyse d'une image de presse" : situation, personnages, message, point de vue

L'étude doit contenir :
1. **Guide de description** en langue étrangère
2. **Interprétation** (contexte culturel, message)
3. **Questions élèves** (3 questions progressives avec correction)

Description du document :
---
{texte}
---
""",

    "lv_mise_en_relation": """Tu es un professeur de {langue} expérimenté.
À partir des documents ci-dessous, crée un exercice de mise en relation pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Deux documents sur la même thématique" : comparer les points de vue, les registres, les approches
- "Points de vue opposés" : identifier et formuler les positions contradictoires
- "Document + témoignage" : croiser un document et un récit personnel sur le même sujet

Document :
---
{texte}
---
""",

    "lv_oral": """Tu es un professeur de {langue} expérimenté.
À partir du document ci-dessous, génère {nb} questions pour préparer une activité orale pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Exposé thématique" : présenter un sujet culturel de façon structurée en langue étrangère
- "Jeu de rôle" : questions pour préparer une interaction simulée (achat, entretien, débat...)
- "Compréhension orale commentée" : questions pour guider l'écoute et le commentaire d'un document audio

Document :
---
{texte}
---
""",

    "lv_fiche_revision": _fiche_revision("langues vivantes"),
    "lv_fiche_pedagogique": _fiche_pedagogique("langues vivantes"),

    "lv_recherche_sequences": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, propose des idées de séquences pédagogiques pour des élèves de {niveau}.

Pour chaque séquence proposée, indique :
1. **Titre de la séquence** et axe thématique / culturel
2. **Problématique** (question directrice)
3. **Supports possibles** (textes, vidéos, chansons, images en lien)
4. **Compétences travaillées** (CO, CE, PO, PE, médiation)
5. **Évaluation finale suggérée**

Propose 3 à 5 idées de séquences adaptées au niveau {niveau}.

Texte :
---
{texte}
---
""",

    "lv_sequence_detaillee": """Tu es un professeur de {langue} expérimenté.
À partir du texte ci-dessous, construis une séquence pédagogique complète pour des élèves de {niveau}.

La séquence doit contenir :
1. **Titre, axe thématique et problématique**
2. **Objectifs** (langagiers, culturels, méthodologiques)
3. **Déroulé séance par séance** (6 à 8 séances) :
   - Titre et durée
   - Support utilisé
   - Activités élèves (CO, CE, PO, PE)
   - Objectif de la séance
4. **Évaluation finale** (type, critères, barème)

Texte support :
---
{texte}
---
""",

    # ══════════════════════════════════════════════════════════════════════
    # ARTS
    # ══════════════════════════════════════════════════════════════════════

    "arts_comprehension": """Tu es un professeur d'arts (arts plastiques, histoire des arts, éducation musicale) expérimenté.
À partir du document ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Compréhension d'une œuvre" : identifier le sujet, les techniques, les éléments visuels ou sonores
- "Compréhension d'une intention artistique" : dégager le propos de l'artiste, ses choix formels

Formule des questions progressives. Adapte le vocabulaire au niveau {niveau}.

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "arts_questions_support": """Tu es un professeur d'arts expérimenté.
À partir du support ci-dessous, génère {nb} questions pour des élèves de {niveau}.
Type de support : {sous_type}.

Types possibles :
- "Analyse d'une œuvre plastique" : composition, couleurs, matières, procédés, format
- "Analyse d'une photographie" : cadrage, lumière, sujet, point de vue, intention
- "Analyse d'un extrait musical" : tempo, dynamique, instrumentation, structure, émotion
- "Analyse d'une mise en scène" : espace, corps, lumière, son, intention dramaturgique

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "arts_analyse_contenu": """Tu es un professeur d'arts expérimenté.
À partir du document ci-dessous, réalise une analyse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Analyse d'une œuvre" : description formelle + interprétation + mise en contexte
- "Analyse d'un procédé visuel" : identifier et nommer une technique, un effet, un choix formel

Sois précis, cite des éléments visibles ou audibles, adapte le vocabulaire au niveau {niveau}.

Document :
---
{texte}
---
""",

    "arts_pistes_de_lecture_in": """Tu es un professeur d'arts expérimenté.
À partir du document ci-dessous, propose des pistes d'interprétation pour des élèves de {niveau}.
Angle : {sous_type}.

Angles possibles :
- "Intention artistique" : que cherche l'artiste à exprimer, provoquer, questionner ?
- "Mouvement et courant artistique" : situer l'œuvre dans un courant, identifier ses caractéristiques
- "Symbolique / allégorie" : décoder les symboles, les métaphores visuelles ou sonores
- "Rapport à l'époque" : montrer comment l'œuvre reflète ou répond à son contexte historique

Chaque piste = un titre + 2-3 lignes exploitables en classe.

Document :
---
{texte}
---
""",

    "arts_résumés_synthèses": """Tu es un professeur d'arts expérimenté.
À partir du document ci-dessous, rédige une synthèse pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Résumé d'une démarche artistique" : décrire en 10-15 lignes la démarche, les choix, l'évolution d'un artiste

Document :
---
{texte}
---
""",

    "arts_production_réponse_s": """Tu es un professeur d'arts expérimenté.
À partir du document ci-dessous, crée un sujet de production pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Analyse critique" : l'élève rédige une analyse argumentée et personnelle d'une œuvre
- "Justification d'un choix artistique" : l'élève défend les choix formels d'une création personnelle

Fournis la consigne, les critères de réussite et un exemple de réponse.

Document :
---
{texte}
---
""",

    "arts_mise_en_relation": """Tu es un professeur d'arts expérimenté.
À partir des documents ci-dessous, crée un exercice de mise en relation pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Deux œuvres d'une même période" : comparer les styles, les techniques, les intentions
- "Deux artistes en dialogue" : identifier des influences, des résonances, des contrastes
- "Œuvre + contexte historique" : montrer comment l'histoire éclaire l'œuvre (et inversement)

Document :
---
{texte}
---
""",

    "arts_oral": """Tu es un professeur d'arts expérimenté.
À partir du document ci-dessous, génère {nb} questions pour préparer une activité orale pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Présentation d'une œuvre" : structure d'un exposé (description, analyse, interprétation, contexte)
- "Analyse comparative" : comparer deux œuvres à l'oral de façon structurée
- "Commentaire d'une démarche artistique" : présenter et défendre une démarche de création

Document :
---
{texte}
---
""",

    "arts_fiche_revision": _fiche_revision("arts"),
    "arts_fiche_pedagogique": _fiche_pedagogique("arts"),

    # ══════════════════════════════════════════════════════════════════════
    # EPS
    # ══════════════════════════════════════════════════════════════════════

    "eps_comprehension": """Tu es un professeur d'EPS (Éducation Physique et Sportive) expérimenté.
À partir du document ci-dessous, génère {nb} questions de compréhension pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Compréhension d'une règle" : identifier et expliquer une règle de jeu ou de sécurité
- "Compréhension d'une stratégie" : analyser un schéma tactique, identifier les principes d'action
- "Compréhension d'un dispositif" : comprendre l'organisation d'un atelier, d'une situation d'apprentissage

Formule des questions progressives. Adapte le vocabulaire au niveau {niveau}.

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "eps_questions_cours": """Tu es un professeur d'EPS expérimenté.
À partir du contenu ci-dessous, génère {nb} questions de cours pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Sécurité" : règles de sécurité, gestes à risque, conduites à tenir en cas d'accident
- "Principes tactiques" : principes d'attaque, de défense, de jeu collectif

Document :
---
{texte}
---
Réponds uniquement avec les questions numérotées.
""",

    "eps_oral": """Tu es un professeur d'EPS expérimenté.
À partir du document ci-dessous, génère {nb} questions pour préparer une activité orale pour des élèves de {niveau}.
Type : {sous_type}.

Types possibles :
- "Analyse d'une performance" : décrire, analyser et évaluer une performance sportive

Document :
---
{texte}
---
""",

    "eps_fiche_revision": _fiche_revision("EPS"),
    "eps_fiche_pedagogique": _fiche_pedagogique("EPS"),
}


SUFFIXE_CORRECTION = """

---
**IMPORTANT : après chaque question ou activité, ajoute une proposition de réponse-type.**
Format attendu :
> ✏️ *Réponse attendue :* [réponse rédigée, adaptable par le professeur]

Ces réponses doivent être claires, précises, et directement utilisables comme base de correction.
"""


def _build_few_shot_prefix(exemples: list[str]) -> str:
    lines = [
        "Voici des exemples de la façon dont ce professeur formule ses activités. "
        "Adapte ton style en conséquence.\n",
    ]
    for i, ex in enumerate(exemples, 1):
        lines.append(f"--- Exemple {i} ---\n{ex}\n")
    lines.append("--- Génère maintenant dans le même style ---\n\n")
    return "\n".join(lines)


def build_prompt(
    activite: str,
    texte: str,
    avec_correction: bool = False,
    exemples: list[str] | None = None,
    **kwargs,
) -> str:
    all_prompts = {**PROMPTS, **PROMPTS_HISTGEO, **PROMPTS_AUTRES}
    template = all_prompts[activite]
    prompt = template.format(texte=texte, **kwargs)
    if exemples:
        prompt = _build_few_shot_prefix(exemples) + prompt
    if avec_correction:
        prompt += SUFFIXE_CORRECTION
    return prompt
