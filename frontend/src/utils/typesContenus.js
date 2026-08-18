// Identité visuelle des TYPES du monde neuf « Mes contenus » : un type = une couleur
// d'accent + une icône, répétées en PETITES TOUCHES (icône du titre, pastille compteur,
// liseré de sélection, point du menu) — jamais en fond de page. UNE seule place pour la
// palette : les pages listes ET le menu la lisent ici (zéro copie).
// Le trio complet posé sur GO utilisateur le 30/07 : séquence violet, séance vert émeraude,
// activité ambre.
export const TYPES_CONTENUS = {
  sequence: { accent: '#7c3aed', fond: '#f5f3ff', bord: '#ddd6fe' },
  seance:   { accent: '#0f766e', fond: '#f0fdfa', bord: '#99f6e4' },
  activite: { accent: '#b45309', fond: '#fffbeb', bord: '#fde68a' },
  // La grille d'évaluation (17/08/2026) : bleu ardoise. Elle n'appartient pas au trio
  // « Mes contenus » — c'est une évaluation, pas un contenu de cours — mais elle se range,
  // se liste et s'ouvre comme eux, et sa page a besoin de la même identité. Sans ligne ici,
  // elle restait grise : la seule des quatre listes à ne pas porter de couleur.
  grille:   { accent: '#475569', fond: '#f8fafc', bord: '#cbd5e1' },
}
