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


SUFFIXE_CORRECTION = """

---
**IMPORTANT : après chaque question ou activité, ajoute une proposition de réponse-type.**
Format attendu :
> ✏️ *Réponse attendue :* [réponse rédigée, adaptable par le professeur]

Ces réponses doivent être claires, précises, et directement utilisables comme base de correction.
"""


def build_prompt(activite: str, texte: str, avec_correction: bool = False, **kwargs) -> str:
    all_prompts = {**PROMPTS, **PROMPTS_HISTGEO}
    template = all_prompts[activite]
    prompt = template.format(texte=texte, **kwargs)
    if avec_correction:
        prompt += SUFFIXE_CORRECTION
    return prompt
