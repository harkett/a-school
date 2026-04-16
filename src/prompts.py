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
}


SUFFIXE_CORRECTION = """

---
**IMPORTANT : après chaque question ou activité, ajoute une proposition de réponse-type.**
Format attendu :
> ✏️ *Réponse attendue :* [réponse rédigée, adaptable par le professeur]

Ces réponses doivent être claires, précises, et directement utilisables comme base de correction.
"""


def build_prompt(activite: str, texte: str, avec_correction: bool = False, **kwargs) -> str:
    template = PROMPTS[activite]
    prompt = template.format(texte=texte, **kwargs)
    if avec_correction:
        prompt += SUFFIXE_CORRECTION
    return prompt
