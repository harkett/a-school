# Catalogue d'activités par matière.
#
# Les jeux d'activités EN DUR (Français, Histoire-Géo) et la matrice markdown
# (MATRICE_ACTIVITES_ASCHOOL.md → parse_markdown.py → generated_activities.py) ont été
# SUPPRIMÉS : le contenu doit provenir du référentiel via le RAG, jamais d'une liste figée.
# En attendant que le RAG fournisse les activités d'un couple, toute matière retombe sur le
# jeu GÉNÉRIQUE ci-dessous (cf. backend/routers/activites.py : .get(matiere, ACTIVITES_GENERIQUES)).
ACTIVITES_PAR_MATIERE = {}

# --- Jeu d'activités GÉNÉRIQUES — repli pour toute matière sans catalogue dédié.
# Prompts neutres (clés gen_*, ne nomment pas la matière) → justes pour toute matière.
# Sans ça, le prof resterait bloqué sur « Sélectionnez un type ». ---
ACTIVITES_GENERIQUES = {
    "Questions de compréhension": {"key": "gen_comprehension", "sous_types": [], "params": ["nb"]},
    "Questions de cours":         {"key": "gen_questions_cours", "sous_types": [], "params": ["nb"]},
    "Fiche de révision":          {"key": "gen_fiche_revision", "sous_types": [], "params": []},
}

# --- Index dérivé : activité → matière → données (calculé au démarrage) ---
def build_index(source: dict) -> dict:
    index = {}
    for matiere, activites in source.items():
        for nom, data in activites.items():
            index.setdefault(nom, {})[matiere] = data
    return index

ACTIVITES_PAR_ACTIVITE = build_index(ACTIVITES_PAR_MATIERE)
