// Libellés HUMAINS des écrans de l'appli prof — utilisés pour le contexte qu'un feedback
// emporte avec lui (« Depuis : écran Créer une activité · Français × 6e »). Une clé = la
// valeur `page` du routeur d'App.jsx.
const ECRANS = {
  'accueil':              'Accueil',
  'mes-contenus':         'Mes contenus',
  'seance':               'Séance (Mes contenus)',
  'activite':             'Activité (Mes contenus)',
  'ambiguites':           'Analyse des ambiguïtés',
  'consigne':             "Analyse d'une consigne",
  'equite':               'Équité',
  'eval-grilles':         "Mes grilles d'évaluation",
  'grille':               "Grille d'évaluation",
  'grille-nouvelle':      'Nouvelle grille',
  'bientot-disponible':   'Bientôt disponible',
  'mon-profil':           'Mon profil',
  'mes-feedbacks':        'Mes feedbacks',
  'mes-stats':            'Mes stats',
  'aide':                 "Centre d'aide",
  'apropos':              'À propos',
}

export function libelleEcran(page) {
  return ECRANS[page] || 'aSchool'
}
