// Logique pure de l'écran « Créer » — extraite du composant pour être testable
// sans harnais React (runner `node --test`).

// Vrai si la navigation vise l'écran « Créer une activité » : toute arrivée sur cette
// page doit repartir d'une activité VIERGE (le routeur `naviguer` s'appuie là-dessus).
export function estPageCreer(pageId) {
  return pageId === 'creer-activite'
}

// Champs du type d'activité remis au DÉFAUT de la matière (1er type de la liste renvoyée
// par /api/activites). Renvoie l'objet à fusionner dans `params`. Garde-fou : liste vide
// ou non-tableau → activite_key vide (pas de crash).
export function typeParDefaut(activites) {
  const premier = Array.isArray(activites) ? activites[0] : undefined
  return {
    activite_type_id: premier?.id ?? null,   // identité du type = son id
    sous_type: premier?.sous_types?.[0] || null,
    nb: premier?.params?.includes('nb') ? 5 : null,
    avec_correction: false,
  }
}
