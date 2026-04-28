# Généré automatiquement par parse_markdown.py
# Source  : MesMD/MATRICE_ACTIVITES_ASCHOOL.md
# ATTENTION : ne pas éditer manuellement.
#            Modifier le markdown et relancer : python parse_markdown.py

NOUVELLES_MATIERES = {
    "Philosophie": {
        "Questions de compréhension": {
            "key": "philo_comprehension",
            "sous_types": ["Compréhension d'un concept", "Compréhension d'un argument", "Compréhension d'un texte philosophique", "Identification d'une thèse"],
            "params": ["nb", "sous_type"],
        },
        "Questions sur un support": {
            "key": "philo_questions_support",
            "sous_types": ["Texte philosophique", "Extrait d'œuvre", "Document historique", "Article contemporain"],
            "params": ["nb", "sous_type"],
        },
        "Questions de cours": {
            "key": "philo_questions_cours",
            "sous_types": ["Définir un concept", "Expliquer une thèse", "Identifier un auteur / courant", "Mélange"],
            "params": ["nb", "sous_type"],
        },
        "Analyse de contenu": {
            "key": "philo_analyse_contenu",
            "sous_types": ["Analyse d'un argument", "Analyse d'un texte d'auteur", "Analyse de thèse / antithèse", "Analyse d'une démonstration"],
            "params": ["sous_type"],
        },
        "Analyse de source": {
            "key": "philo_analyse_source",
            "sous_types": ["Analyse d'un texte philosophique", "Déconstruction d'un argument", "Mise en contexte historique"],
            "params": ["sous_type"],
        },
        "Pistes de lecture - interprétation": {
            "key": "philo_pistes_de_lecture_in",
            "sous_types": ["Thématique centrale", "Contradiction interne", "Lien avec d'autres auteurs", "Actualité du texte"],
            "params": ["sous_type"],
        },
        "Résumés - synthèses": {
            "key": "philo_résumés_synthèses",
            "sous_types": ["Résumé d'un texte", "Synthèse d'une doctrine", "Synthèse d'un courant de pensée", "Reformulation d'un argument"],
            "params": ["sous_type"],
        },
        "Étude de vocabulaire - notions clés": {
            "key": "philo_étude_de_vocabulaire",
            "sous_types": ["Définir un concept philosophique", "Distinguer deux notions", "Champ lexical d'un texte", "Notion et contre‑exemple"],
            "params": ["sous_type"],
        },
        "Production - réponse structurée": {
            "key": "philo_production_réponse_s",
            "sous_types": ["Rédaction d'une réflexion", "Justification d'une position", "Explication d'un concept"],
            "params": ["sous_type"],
        },
        "Paragraphe argumenté - justification": {
            "key": "philo_paragraphe_argumenté",
            "sous_types": ["Thèse + argument + exemple", "Objection + réponse", "Synthèse partielle"],
            "params": ["sous_type"],
        },
        "Dissertation": {
            "key": "philo_dissertation",
            "sous_types": ["Introduction seule", "Plan détaillé", "Développement complet", "Plan avec transitions"],
            "params": ["sous_type"],
        },
        "Étude iconographique - visuelle": {
            "key": "philo_étude_iconographique",
            "sous_types": ["Analyse d'une œuvre d'art philosophique", "Analyse d'une image symbolique", "Rapport texte / image"],
            "params": ["sous_type"],
        },
        "Mise en relation de supports": {
            "key": "philo_mise_en_relation",
            "sous_types": ["Deux textes philosophiques", "Texte + contexte historique", "Thèse + contre‑thèse"],
            "params": ["sous_type"],
        },
        "Préparation à l'oral": {
            "key": "philo_oral",
            "sous_types": ["Exposé philosophique", "Débat argumenté", "Grand Oral Terminale"],
            "params": ["nb", "sous_type"],
        },
        "Fiche de révision": {
            "key": "philo_fiche_revision",
            "sous_types": [],
            "params": [],
        },
        "Fiche pédagogique": {
            "key": "philo_fiche_pedagogique",
            "sous_types": [],
            "params": [],
        },
        "Recherche de séquences": {
            "key": "philo_recherche_sequences",
            "sous_types": [],
            "params": [],
        },
        "Séquence détaillée": {
            "key": "philo_sequence_detaillee",
            "sous_types": [],
            "params": [],
        },
    },
    "Mathématiques": {
        "Questions de compréhension": {
            "key": "maths_comprehension",
            "sous_types": ["Identification des données utiles", "Reformulation de l'énoncé", "Détection des contraintes", "Reconnaissance du type de problème", "Identification des unités / grandeurs", "Lecture de schéma / graphique"],
            "params": ["nb", "sous_type"],
        },
        "Questions sur un support": {
            "key": "maths_questions_support",
            "sous_types": ["Lecture de tableau", "Lecture de graphique", "Analyse d'un schéma géométrique", "Analyse d'un énoncé complexe"],
            "params": ["nb", "sous_type"],
        },
        "Questions de cours": {
            "key": "maths_questions_cours",
            "sous_types": ["Rappel d'une définition", "Rappel d'une propriété / théorème", "Explication d'une méthode", "Mélange"],
            "params": ["nb", "sous_type"],
        },
        "Analyse de contenu": {
            "key": "maths_analyse_contenu",
            "sous_types": ["Analyse d'un raisonnement", "Analyse d'un algorithme simple", "Analyse d'une figure"],
            "params": ["sous_type"],
        },
        "Étude de vocabulaire - notions clés": {
            "key": "maths_étude_de_vocabulaire",
            "sous_types": ["Définir un terme mathématique", "Distinguer deux notions", "Vocabulaire de géométrie", "Vocabulaire de statistiques"],
            "params": ["sous_type"],
        },
        "Exercices de logique": {
            "key": "maths_logique",
            "sous_types": ["Implication et réciproque", "Raisonnement par l'absurde", "Contre‑exemple", "Logique propositionnelle"],
            "params": ["sous_type"],
        },
        "Évaluation de logique": {
            "key": "maths_évaluation_de_logiqu",
            "sous_types": ["Vrai / faux avec justification", "QCM raisonné", "Démonstration à compléter"],
            "params": ["sous_type"],
        },
        "Résumés - synthèses": {
            "key": "maths_résumés_synthèses",
            "sous_types": ["Synthèse d'une méthode", "Résumé d'un théorème"],
            "params": ["sous_type"],
        },
        "Production - réponse structurée": {
            "key": "maths_production_réponse_s",
            "sous_types": ["Justification d'un raisonnement", "Explication d'une méthode"],
            "params": ["sous_type"],
        },
        "Paragraphe argumenté - justification": {
            "key": "maths_paragraphe_argumenté",
            "sous_types": ["Justification d'une démarche", "Explication d'un résultat", "Raisonnement rédigé"],
            "params": ["sous_type"],
        },
        "Lecture de schéma - diagramme": {
            "key": "maths_lecture_de_schéma_di",
            "sous_types": ["Lecture d'un graphique de fonction", "Lecture d'un tableau statistique", "Analyse d'une figure géométrique", "Diagramme de probabilités"],
            "params": ["sous_type"],
        },
        "Mise en relation": {
            "key": "maths_mise_en_relation",
            "sous_types": ["Modèle ↔ données", "Algébrique ↔ graphique"],
            "params": ["sous_type"],
        },
        "Préparation à l'oral": {
            "key": "maths_oral",
            "sous_types": ["Présentation d'une démonstration", "Exposé d'une méthode"],
            "params": ["nb", "sous_type"],
        },
        "Fiche de révision": {
            "key": "maths_fiche_revision",
            "sous_types": [],
            "params": [],
        },
        "Fiche pédagogique": {
            "key": "maths_fiche_pedagogique",
            "sous_types": [],
            "params": [],
        },
    },
    "NSI": {
        "Questions de compréhension": {
            "key": "nsi_comprehension",
            "sous_types": ["Lecture de code", "Compréhension d'algorithme", "Lecture de diagramme", "Identification des variables"],
            "params": ["nb", "sous_type"],
        },
        "Questions sur un support": {
            "key": "nsi_questions_support",
            "sous_types": ["Lecture de code Python", "Lecture de pseudo‑code", "Analyse d'un algorithme écrit", "Lecture d'un diagramme"],
            "params": ["nb", "sous_type"],
        },
        "Questions de cours": {
            "key": "nsi_questions_cours",
            "sous_types": ["Définir un concept informatique", "Expliquer le fonctionnement d'un système", "Identifier une structure de données", "Mélange"],
            "params": ["nb", "sous_type"],
        },
        "Analyse de contenu": {
            "key": "nsi_analyse_contenu",
            "sous_types": ["Analyse d'un programme", "Analyse d'une fonction", "Analyse d'une boucle / condition"],
            "params": ["sous_type"],
        },
        "Analyse de source": {
            "key": "nsi_analyse_source",
            "sous_types": ["Analyse de code source", "Analyse de pseudo‑code", "Analyse de structure de données"],
            "params": ["sous_type"],
        },
        "Étude de vocabulaire - notions clés": {
            "key": "nsi_étude_de_vocabulaire",
            "sous_types": ["Vocabulaire algorithmique", "Vocabulaire réseau", "Vocabulaire base de données", "Vocabulaire systèmes"],
            "params": ["sous_type"],
        },
        "Exercices de logique": {
            "key": "nsi_logique",
            "sous_types": ["Tables de vérité", "Algèbre de Boole", "Déduction algorithmique", "Correction d'erreur de logique"],
            "params": ["sous_type"],
        },
        "Évaluation de logique": {
            "key": "nsi_évaluation_de_logiqu",
            "sous_types": ["QCM de logique", "Vrai / faux raisonné", "Trace d'exécution"],
            "params": ["sous_type"],
        },
        "Résumés - synthèses": {
            "key": "nsi_résumés_synthèses",
            "sous_types": ["Résumé d'un algorithme", "Synthèse d'une architecture"],
            "params": ["sous_type"],
        },
        "Production - réponse structurée": {
            "key": "nsi_production_réponse_s",
            "sous_types": ["Rédaction d'un algorithme", "Explication d'un code"],
            "params": ["sous_type"],
        },
        "Paragraphe argumenté - justification": {
            "key": "nsi_paragraphe_argumenté",
            "sous_types": ["Justification d'un choix algorithmique", "Explication d'un concept technique", "Argumentation sur une architecture"],
            "params": ["sous_type"],
        },
        "Lecture de diagramme": {
            "key": "nsi_schema",
            "sous_types": ["Diagramme de flux", "Diagramme de séquence UML", "Schéma réseau", "Arbre de décision"],
            "params": ["sous_type"],
        },
        "Mise en relation": {
            "key": "nsi_mise_en_relation",
            "sous_types": ["Code ↔ diagramme", "Problème ↔ algorithme"],
            "params": ["sous_type"],
        },
        "Préparation à l'oral": {
            "key": "nsi_oral",
            "sous_types": ["Présentation d'un projet", "Exposé technique"],
            "params": ["nb", "sous_type"],
        },
        "Fiche de révision": {
            "key": "nsi_fiche_revision",
            "sous_types": [],
            "params": [],
        },
        "Fiche pédagogique": {
            "key": "nsi_fiche_pedagogique",
            "sous_types": [],
            "params": [],
        },
    },
    "Physique-Chimie": {
        "Questions de compréhension": {
            "key": "pc_comprehension",
            "sous_types": ["Compréhension d'un montage", "Compréhension d'un protocole", "Lecture d'un graphique"],
            "params": ["nb", "sous_type"],
        },
        "Questions sur un support": {
            "key": "pc_questions_support",
            "sous_types": ["Lecture d'un graphique expérimental", "Analyse d'un tableau de mesures", "Lecture d'un schéma de montage", "Analyse d'un spectre"],
            "params": ["nb", "sous_type"],
        },
        "Questions de cours": {
            "key": "pc_questions_cours",
            "sous_types": ["Rappel d'une loi / formule", "Définir une grandeur physique", "Expliquer un phénomène", "Mélange"],
            "params": ["nb", "sous_type"],
        },
        "Analyse de contenu": {
            "key": "pc_analyse_contenu",
            "sous_types": ["Analyse d'un modèle", "Analyse d'une expérience"],
            "params": ["sous_type"],
        },
        "Analyse de source": {
            "key": "pc_analyse_source",
            "sous_types": ["Analyse d'un protocole expérimental", "Analyse d'un article scientifique", "Interprétation de données expérimentales"],
            "params": ["sous_type"],
        },
        "Étude de vocabulaire - notions clés": {
            "key": "pc_étude_de_vocabulaire",
            "sous_types": ["Définir une grandeur physique", "Distinguer deux concepts", "Vocabulaire de chimie", "Vocabulaire d'optique / électricité"],
            "params": ["sous_type"],
        },
        "Résumés - synthèses": {
            "key": "pc_résumés_synthèses",
            "sous_types": ["Synthèse d'un protocole", "Résumé d'un modèle"],
            "params": ["sous_type"],
        },
        "Production - réponse structurée": {
            "key": "pc_production_réponse_s",
            "sous_types": ["Justification d'un résultat", "Analyse d'erreur"],
            "params": ["sous_type"],
        },
        "Paragraphe argumenté - justification": {
            "key": "pc_paragraphe_argumenté",
            "sous_types": ["Justification d'un résultat expérimental", "Explication d'un phénomène physique", "Conclusion rédigée d'une expérience"],
            "params": ["sous_type"],
        },
        "Lecture de schéma - diagramme": {
            "key": "pc_lecture_de_schéma_di",
            "sous_types": ["Schéma de montage électrique", "Diagramme énergie‑temps", "Graphique de décroissance radioactive", "Schéma de circuit"],
            "params": ["sous_type"],
        },
        "Mise en relation": {
            "key": "pc_mise_en_relation",
            "sous_types": ["Modèle ↔ expérience", "Données ↔ loi physique"],
            "params": ["sous_type"],
        },
        "Préparation à l'oral": {
            "key": "pc_oral",
            "sous_types": ["Présentation d'une expérience", "Exposé scientifique"],
            "params": ["nb", "sous_type"],
        },
        "Fiche de révision": {
            "key": "pc_fiche_revision",
            "sous_types": [],
            "params": [],
        },
        "Fiche pédagogique": {
            "key": "pc_fiche_pedagogique",
            "sous_types": [],
            "params": [],
        },
    },
    "SVT": {
        "Questions de compréhension": {
            "key": "svt_comprehension",
            "sous_types": ["Lecture d'un schéma", "Compréhension d'un protocole", "Lecture d'un graphique"],
            "params": ["nb", "sous_type"],
        },
        "Questions sur un support": {
            "key": "svt_questions_support",
            "sous_types": ["Lecture d'un schéma biologique", "Analyse d'un tableau de données", "Lecture d'un graphique expérimental", "Analyse d'une image de microscopie"],
            "params": ["nb", "sous_type"],
        },
        "Questions de cours": {
            "key": "svt_questions_cours",
            "sous_types": ["Rappel d'un mécanisme biologique", "Définir un terme scientifique", "Expliquer une fonction", "Mélange"],
            "params": ["nb", "sous_type"],
        },
        "Analyse de contenu": {
            "key": "svt_analyse_contenu",
            "sous_types": ["Analyse d'un mécanisme", "Analyse d'une expérience"],
            "params": ["sous_type"],
        },
        "Analyse de source": {
            "key": "svt_analyse_source",
            "sous_types": ["Analyse d'un protocole expérimental", "Analyse de résultats expérimentaux", "Analyse d'un document scientifique"],
            "params": ["sous_type"],
        },
        "Étude de vocabulaire - notions clés": {
            "key": "svt_étude_de_vocabulaire",
            "sous_types": ["Définir un terme biologique", "Distinguer deux notions", "Vocabulaire de génétique", "Vocabulaire de physiologie"],
            "params": ["sous_type"],
        },
        "Résumés - synthèses": {
            "key": "svt_résumés_synthèses",
            "sous_types": ["Synthèse d'un mécanisme"],
            "params": ["sous_type"],
        },
        "Production - réponse structurée": {
            "key": "svt_production_réponse_s",
            "sous_types": ["Explication d'un phénomène"],
            "params": ["sous_type"],
        },
        "Paragraphe argumenté - justification": {
            "key": "svt_paragraphe_argumenté",
            "sous_types": ["Bilan d'expérience rédigé", "Explication d'un mécanisme", "Réponse à une problématique scientifique"],
            "params": ["sous_type"],
        },
        "Lecture de schéma - diagramme": {
            "key": "svt_lecture_de_schéma_di",
            "sous_types": ["Schéma du corps humain", "Schéma d'un mécanisme cellulaire", "Graphique d'évolution", "Diagramme écologique"],
            "params": ["sous_type"],
        },
        "Mise en relation": {
            "key": "svt_mise_en_relation",
            "sous_types": ["Documents ↔ mécanisme"],
            "params": ["sous_type"],
        },
        "Préparation à l'oral": {
            "key": "svt_oral",
            "sous_types": ["Présentation d'une expérience", "Exposé scientifique"],
            "params": ["nb", "sous_type"],
        },
        "Fiche de révision": {
            "key": "svt_fiche_revision",
            "sous_types": [],
            "params": [],
        },
        "Fiche pédagogique": {
            "key": "svt_fiche_pedagogique",
            "sous_types": [],
            "params": [],
        },
    },
    "Technologie": {
        "Questions de compréhension": {
            "key": "techno_comprehension",
            "sous_types": ["Lecture d'un schéma technique", "Compréhension d'un système"],
            "params": ["nb", "sous_type"],
        },
        "Questions sur un support": {
            "key": "techno_questions_support",
            "sous_types": ["Lecture d'un schéma technique", "Analyse d'un cahier des charges", "Lecture d'un diagramme de flux", "Analyse d'un plan"],
            "params": ["nb", "sous_type"],
        },
        "Questions de cours": {
            "key": "techno_questions_cours",
            "sous_types": ["Rappel d'un principe technique", "Définir un composant", "Expliquer une fonction d'usage", "Mélange"],
            "params": ["nb", "sous_type"],
        },
        "Analyse de contenu": {
            "key": "techno_analyse_contenu",
            "sous_types": ["Analyse fonctionnelle", "Analyse structurelle"],
            "params": ["sous_type"],
        },
        "Analyse de source": {
            "key": "techno_analyse_source",
            "sous_types": ["Analyse d'un cahier des charges", "Analyse d'une solution technique existante", "Analyse d'un prototype"],
            "params": ["sous_type"],
        },
        "Étude de vocabulaire - notions clés": {
            "key": "techno_étude_de_vocabulaire",
            "sous_types": ["Vocabulaire mécanique", "Vocabulaire électronique", "Vocabulaire informatique industrielle", "Définir une fonction technique"],
            "params": ["sous_type"],
        },
        "Résumés - synthèses": {
            "key": "techno_résumés_synthèses",
            "sous_types": ["Synthèse d'un fonctionnement"],
            "params": ["sous_type"],
        },
        "Production - réponse structurée": {
            "key": "techno_production_réponse_s",
            "sous_types": ["Justification d'un choix technique"],
            "params": ["sous_type"],
        },
        "Paragraphe argumenté - justification": {
            "key": "techno_paragraphe_argumenté",
            "sous_types": ["Justification d'un choix de matériau", "Justification d'une solution technique", "Argumentation face à un cahier des charges"],
            "params": ["sous_type"],
        },
        "Lecture de schéma - diagramme": {
            "key": "techno_lecture_de_schéma_di",
            "sous_types": ["Schéma cinématique", "Diagramme FAST", "Schéma de flux d'énergie", "Plan de pièce"],
            "params": ["sous_type"],
        },
        "Mise en relation": {
            "key": "techno_mise_en_relation",
            "sous_types": ["Besoin ↔ solution"],
            "params": ["sous_type"],
        },
        "Préparation à l'oral": {
            "key": "techno_oral",
            "sous_types": ["Présentation d'un projet technique", "Soutenance de dossier"],
            "params": ["nb", "sous_type"],
        },
        "Fiche de révision": {
            "key": "techno_fiche_revision",
            "sous_types": [],
            "params": [],
        },
        "Fiche pédagogique": {
            "key": "techno_fiche_pedagogique",
            "sous_types": [],
            "params": [],
        },
    },
    "SES": {
        "Questions de compréhension": {
            "key": "ses_comprehension",
            "sous_types": ["Lecture d'un graphique économique", "Lecture d'un tableau statistique", "Compréhension d'un mécanisme économique"],
            "params": ["nb", "sous_type"],
        },
        "Questions sur un support": {
            "key": "ses_questions_support",
            "sous_types": ["Lecture d'un graphique statistique", "Analyse d'un tableau de données INSEE", "Lecture d'un article de presse économique", "Analyse d'un document institutionnel"],
            "params": ["nb", "sous_type"],
        },
        "Questions de cours": {
            "key": "ses_questions_cours",
            "sous_types": ["Rappel d'un mécanisme économique", "Définir un concept", "Identifier un acteur économique", "Mélange"],
            "params": ["nb", "sous_type"],
        },
        "Analyse de contenu": {
            "key": "ses_analyse_contenu",
            "sous_types": ["Analyse d'un document scientifique", "Analyse d'un modèle économique"],
            "params": ["sous_type"],
        },
        "Analyse de source": {
            "key": "ses_analyse_source",
            "sous_types": ["Analyse d'un article scientifique en économie", "Analyse d'une étude statistique", "Analyse d'un rapport institutionnel"],
            "params": ["sous_type"],
        },
        "Étude de vocabulaire - notions clés": {
            "key": "ses_étude_de_vocabulaire",
            "sous_types": ["Définir un concept économique", "Distinguer deux notions", "Vocabulaire de sociologie", "Vocabulaire de politique économique"],
            "params": ["sous_type"],
        },
        "Résumés - synthèses": {
            "key": "ses_résumés_synthèses",
            "sous_types": ["Synthèse d'un chapitre", "Résumé d'un mécanisme"],
            "params": ["sous_type"],
        },
        "Production - réponse structurée": {
            "key": "ses_production_réponse_s",
            "sous_types": ["Rédaction d'un paragraphe argumenté", "Réponse construite à une question"],
            "params": ["sous_type"],
        },
        "Paragraphe argumenté - justification": {
            "key": "ses_paragraphe_argumenté",
            "sous_types": ["Thèse + argument + illustration statistique", "Réponse construite en SES", "Bilan de mécanisme"],
            "params": ["sous_type"],
        },
        "Dissertation": {
            "key": "ses_dissertation",
            "sous_types": ["Introduction seule", "Plan détaillé", "Développement complet", "Plan avec transitions"],
            "params": ["sous_type"],
        },
        "Mise en relation": {
            "key": "ses_mise_en_relation",
            "sous_types": ["Données ↔ mécanisme", "Modèle ↔ situation réelle"],
            "params": ["sous_type"],
        },
        "Préparation à l'oral": {
            "key": "ses_oral",
            "sous_types": ["Exposé économique", "Débat argumenté", "Grand Oral Terminale"],
            "params": ["nb", "sous_type"],
        },
        "Fiche de révision": {
            "key": "ses_fiche_revision",
            "sous_types": [],
            "params": [],
        },
        "Fiche pédagogique": {
            "key": "ses_fiche_pedagogique",
            "sous_types": [],
            "params": [],
        },
    },
    "Langues Vivantes (LV)": {
        "Questions de compréhension": {
            "key": "lv_comprehension",
            "sous_types": ["Compréhension écrite", "Compréhension orale", "Compréhension lexicale"],
            "params": ["nb", "sous_type"],
        },
        "Questions sur un support": {
            "key": "lv_questions_support",
            "sous_types": ["Texte en langue étrangère", "Document audio / vidéo", "Article de presse", "Document iconographique"],
            "params": ["nb", "sous_type"],
        },
        "Questions de cours": {
            "key": "lv_questions_cours",
            "sous_types": ["Règle grammaticale", "Fait culturel et civilisationnel", "Vocabulaire thématique", "Mélange"],
            "params": ["nb", "sous_type"],
        },
        "Analyse de contenu": {
            "key": "lv_analyse_contenu",
            "sous_types": ["Analyse d'un texte court", "Analyse d'un dialogue", "Analyse d'intentions (registre, ton, point de vue)"],
            "params": ["sous_type"],
        },
        "Pistes de lecture - interprétation": {
            "key": "lv_pistes_de_lecture_in",
            "sous_types": ["Thématique culturelle", "Point de vue de l'auteur", "Implicite culturel", "Registre et ton"],
            "params": ["sous_type"],
        },
        "Étude de vocabulaire - notions clés": {
            "key": "lv_étude_de_vocabulaire",
            "sous_types": ["Vocabulaire thématique", "Faux amis", "Expressions idiomatiques", "Collocations"],
            "params": ["sous_type"],
        },
        "Exercices de réécriture - transformation": {
            "key": "lv_exercices_de_réécrit",
            "sous_types": ["Transformation de phrases (affirmatif ↔ négatif, actif ↔ passif, direct ↔ indirect)", "Reformulation avec contrainte (temps, modalité, pronom, connecteur)", "Correction d'erreurs dans un texte court"],
            "params": ["sous_type"],
        },
        "Exercices de grammaire": {
            "key": "lv_grammaire",
            "sous_types": ["Conjugaison (temps, aspects, modes)", "Accord (genre, nombre, personne)", "Ordre des mots / structure de phrase", "Utilisation des temps (présent, prétérit, present perfect…)"],
            "params": ["sous_type"],
        },
        "Évaluation de grammaire": {
            "key": "lv_eval_grammaire",
            "sous_types": ["QCM grammatical", "Texte à trous", "Correction d'erreurs", "Transformation de phrases"],
            "params": ["sous_type"],
        },
        "Évaluation d'orthographe": {
            "key": "lv_eval_ortho",
            "sous_types": ["Orthographe lexicale (mots fréquents)", "Orthographe grammaticale (accords de base)", "Ponctuation et majuscules"],
            "params": ["sous_type"],
        },
        "Résumés - synthèses": {
            "key": "lv_résumés_synthèses",
            "sous_types": ["Résumé d'un texte", "Reformulation dans la même langue", "Reformulation simplifiée"],
            "params": ["sous_type"],
        },
        "Production - réponse structurée": {
            "key": "lv_production_réponse_s",
            "sous_types": ["Production écrite (message, récit, description, argumentation simple)", "Production orale (présentation, interaction, jeu de rôle)"],
            "params": ["sous_type"],
        },
        "Paragraphe argumenté - justification": {
            "key": "lv_paragraphe_argumenté",
            "sous_types": ["Opinion personnelle structurée", "Pour / contre", "Synthèse d'un document", "Réponse à une question ouverte"],
            "params": ["sous_type"],
        },
        "Étude iconographique - visuelle": {
            "key": "lv_étude_iconographique",
            "sous_types": ["Analyse d'une publicité", "Analyse d'une affiche culturelle", "Analyse d'une image de presse"],
            "params": ["sous_type"],
        },
        "Mise en relation": {
            "key": "lv_mise_en_relation",
            "sous_types": ["Deux documents sur la même thématique", "Points de vue opposés", "Document + témoignage"],
            "params": ["sous_type"],
        },
        "Préparation à l'oral": {
            "key": "lv_oral",
            "sous_types": ["Exposé thématique", "Jeu de rôle", "Compréhension orale commentée"],
            "params": ["nb", "sous_type"],
        },
        "Fiche de révision": {
            "key": "lv_fiche_revision",
            "sous_types": [],
            "params": [],
        },
        "Fiche pédagogique": {
            "key": "lv_fiche_pedagogique",
            "sous_types": [],
            "params": [],
        },
        "Recherche de séquences": {
            "key": "lv_recherche_sequences",
            "sous_types": [],
            "params": [],
        },
        "Séquence détaillée": {
            "key": "lv_sequence_detaillee",
            "sous_types": [],
            "params": [],
        },
    },
    "Arts": {
        "Questions de compréhension": {
            "key": "arts_comprehension",
            "sous_types": ["Compréhension d'une œuvre", "Compréhension d'une intention artistique"],
            "params": ["nb", "sous_type"],
        },
        "Questions sur un support": {
            "key": "arts_questions_support",
            "sous_types": ["Analyse d'une œuvre plastique", "Analyse d'une photographie", "Analyse d'un extrait musical", "Analyse d'une mise en scène"],
            "params": ["nb", "sous_type"],
        },
        "Analyse de contenu": {
            "key": "arts_analyse_contenu",
            "sous_types": ["Analyse d'une œuvre", "Analyse d'un procédé visuel"],
            "params": ["sous_type"],
        },
        "Pistes de lecture - interprétation": {
            "key": "arts_pistes_de_lecture_in",
            "sous_types": ["Intention artistique", "Mouvement et courant artistique", "Symbolique / allégorie", "Rapport à l'époque"],
            "params": ["sous_type"],
        },
        "Résumés - synthèses": {
            "key": "arts_résumés_synthèses",
            "sous_types": ["Résumé d'une démarche artistique"],
            "params": ["sous_type"],
        },
        "Production - réponse structurée": {
            "key": "arts_production_réponse_s",
            "sous_types": ["Analyse critique", "Justification d'un choix artistique"],
            "params": ["sous_type"],
        },
        "Mise en relation": {
            "key": "arts_mise_en_relation",
            "sous_types": ["Deux œuvres d'une même période", "Deux artistes en dialogue", "Œuvre + contexte historique"],
            "params": ["sous_type"],
        },
        "Préparation à l'oral": {
            "key": "arts_oral",
            "sous_types": ["Présentation d'une œuvre", "Analyse comparative", "Commentaire d'une démarche artistique"],
            "params": ["nb", "sous_type"],
        },
        "Fiche de révision": {
            "key": "arts_fiche_revision",
            "sous_types": [],
            "params": [],
        },
        "Fiche pédagogique": {
            "key": "arts_fiche_pedagogique",
            "sous_types": [],
            "params": [],
        },
    },
    "EPS": {
        "Questions de compréhension": {
            "key": "eps_comprehension",
            "sous_types": ["Compréhension d'une règle", "Compréhension d'une stratégie", "Compréhension d'un dispositif"],
            "params": ["nb", "sous_type"],
        },
        "Questions de cours": {
            "key": "eps_questions_cours",
            "sous_types": ["Sécurité", "Principes tactiques"],
            "params": ["nb", "sous_type"],
        },
        "Préparation à l'oral": {
            "key": "eps_oral",
            "sous_types": ["Analyse d'une performance"],
            "params": ["nb", "sous_type"],
        },
        "Fiche de révision": {
            "key": "eps_fiche_revision",
            "sous_types": [],
            "params": [],
        },
        "Fiche pédagogique": {
            "key": "eps_fiche_pedagogique",
            "sous_types": [],
            "params": [],
        },
    },
}