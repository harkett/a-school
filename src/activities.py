ACTIVITES_PAR_MATIERE = {
    "Français": {
        "Questions de compréhension": {
            "key": "comprehension",
            "sous_types": ["simples (repérage)", "inférence", "interprétation", "personnages", "décor / contexte", "émotions / intentions", "mélange"],
            "params": ["nb", "sous_type"],
        },
        "Pistes de lecture": {
            "key": "pistes",
            "sous_types": ["thématique", "narrateur", "réalisme", "point de vue", "registre"],
            "params": ["nb", "sous_type"],
        },
        "Résumés": {
            "key": "resume",
            "sous_types": ["court (5 lignes)", "structuré (début/milieu/fin)", "pour l'oral"],
            "params": ["sous_type"],
        },
        "Analyse de texte": {
            "key": "analyse",
            "sous_types": ["thème principal", "champs lexicaux", "procédés d'écriture", "passage difficile"],
            "params": ["sous_type"],
        },
        "Exercices de réécriture": {
            "key": "reecriture",
            "sous_types": [
                "style direct vers style indirect",
                "passé simple vers présent",
                "présent vers passé simple",
                "présent vers conditionnel présent",
                "1ère personne du singulier vers 1ère personne du pluriel",
                "3ème personne du singulier vers 1ère personne du pluriel",
                "changement de point de vue",
                "simplifier le vocabulaire",
                "enrichir le texte",
            ],
            "params": ["sous_type"],
        },
        "Étude de vocabulaire": {
            "key": "vocabulaire",
            "sous_types": ["mots difficiles + définitions", "synonymes / antonymes", "exercices à trous", "reformulation"],
            "params": ["sous_type"],
        },
        "Production d'écrit": {
            "key": "production_ecrit",
            "sous_types": ["paragraphe argumenté", "continuer le texte", "décrire un personnage", "imaginer la suite d'une scène", "texte poétique"],
            "params": ["sous_type"],
        },
        "Questions pour l'oral": {
            "key": "oral",
            "sous_types": ["débat", "exposé", "échange en classe"],
            "params": ["nb", "sous_type"],
        },
        "Fiche pédagogique": {
            "key": "fiche_pedagogique",
            "sous_types": [],
            "params": [],
        },
        "Exercices de grammaire": {
            "key": "grammaire",
            "sous_types": ["temps verbaux", "types de phrases", "transformer des phrases", "accords"],
            "params": ["sous_type"],
        },
        "Recherche de séquences": {
            "key": "recherche_sequences",
            "sous_types": [],
            "params": [],
        },
        "Séquence détaillée": {
            "key": "sequence_detaillee",
            "sous_types": [],
            "params": [],
        },
        "Questionnaire sur un roman": {
            "key": "questionnaire_roman",
            "sous_types": [],
            "params": [],
        },
        "Évaluation de grammaire": {
            "key": "evaluation_grammaire",
            "sous_types": [],
            "params": [],
        },
        "Évaluation d'orthographe": {
            "key": "evaluation_orthographe",
            "sous_types": [],
            "params": [],
        },
    },
    "Histoire-Géographie": {
        "Questions sur un document": {
            "key": "hg_comprehension",
            "sous_types": ["identification", "contexte", "analyse", "mise en relation", "mélange"],
            "params": ["nb", "sous_type"],
        },
        "Analyse de source": {
            "key": "hg_analyse_source",
            "sous_types": [],
            "params": [],
        },
        "Questions de cours": {
            "key": "hg_questions_cours",
            "sous_types": ["connaissances", "définitions", "explication", "mélange"],
            "params": ["nb", "sous_type"],
        },
        "Frise chronologique": {
            "key": "hg_frise",
            "sous_types": [],
            "params": [],
        },
        "Paragraphe argumenté": {
            "key": "hg_paragraphe",
            "sous_types": ["réponse organisée", "SEUL", "bilan de séquence"],
            "params": ["sous_type"],
        },
        "Fiche de révision": {
            "key": "hg_fiche_revision",
            "sous_types": [],
            "params": [],
        },
        "Composition / Dissertation": {
            "key": "hg_composition",
            "sous_types": ["introduction seule", "plan détaillé", "développement complet", "plan avec transitions"],
            "params": ["sous_type"],
        },
        "Lecture de carte / Croquis": {
            "key": "hg_carte",
            "sous_types": ["décrire et expliquer une carte", "questions sur un croquis", "légende à compléter"],
            "params": ["sous_type"],
        },
        "Étude d'un document iconographique": {
            "key": "hg_iconographie",
            "sous_types": ["affiche de propagande", "dessin de presse", "photographie historique", "œuvre d'art"],
            "params": ["sous_type"],
        },
        "Exercice de repères": {
            "key": "hg_reperes",
            "sous_types": ["QCM de repères", "définir des notions clés", "placer des événements sur une frise", "situer des lieux"],
            "params": ["nb", "sous_type"],
        },
        "Mise en relation de documents": {
            "key": "hg_mise_en_relation",
            "sous_types": ["confronter deux sources", "dégager complémentarité / contradiction", "synthèse de documents"],
            "params": ["sous_type"],
        },
        "Préparation à l'oral": {
            "key": "hg_oral",
            "sous_types": ["exposé", "débat", "Grand Oral Terminale", "échange en classe"],
            "params": ["nb", "sous_type"],
        },
    },
}

# --- Matières générées automatiquement depuis le markdown ---
try:
    from src.generated_activities import NOUVELLES_MATIERES
except ImportError:
    from generated_activities import NOUVELLES_MATIERES

ACTIVITES_PAR_MATIERE.update(NOUVELLES_MATIERES)

# --- Index dérivé : activité → matière → données (calculé au démarrage) ---
def build_index(source: dict) -> dict:
    index = {}
    for matiere, activites in source.items():
        for nom, data in activites.items():
            index.setdefault(nom, {})[matiere] = data
    return index

ACTIVITES_PAR_ACTIVITE = build_index(ACTIVITES_PAR_MATIERE)
