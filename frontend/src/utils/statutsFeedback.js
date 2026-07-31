// La COULEUR de la pastille d'un statut de feedback, par code.
//
// Le libellé et l'explication du statut viennent de la BASE (table `feedback_statuts`,
// servie par /api/feedback/statuts) — ils ne sont écrits nulle part côté écran. La couleur,
// elle, est de l'affichage pur : elle vit ici, à UN seul endroit, parce que deux écrans la
// dessinent (« Mes retours » et l'Aide) et qu'ils doivent montrer la même.
//
// Un code inconnu prend le gris neutre : un statut ajouté en base s'affiche correctement
// (libellé et explication justes), simplement sans couleur dédiée tant qu'on ne lui en
// donne pas une ici.
const COULEURS = {
  nouveau:  { bg: '#dbeafe', color: '#1d4ed8' },
  en_cours: { bg: '#ffedd5', color: '#c2410c' },
  traite:   { bg: '#dcfce7', color: '#15803d' },
  archive:  { bg: '#f3f4f6', color: '#6b7280' },
}
const DEFAUT = { bg: '#f3f4f6', color: '#6b7280' }

export function couleurStatut(code) {
  return COULEURS[code] || DEFAUT
}
