// La couleur d'un type d'ambiguïté — l'écran l'affiche, et la sortie mise en forme la reprend
// telle quelle. Deux rendus, une seule palette.
//
// Elle vivait dans AmbiguitesResultat.jsx, qui l'exportait à côté de son composant. Ce mélange
// coûtait le rechargement à chaud du fichier (règle `react-refresh/only-export-components`) : une
// couleur retouchée rechargeait la page entière au lieu du seul composant. Même rangement que
// `axesConsigne.js`, qui porte la palette des consignes.
export const TYPE_COLOR = {
  'Consigne vague':                  { bg: '#fef3c7', text: '#92400e', border: '#fde68a' },
  'Vocabulaire technique non défini': { bg: '#f3e8ff', text: '#6b21a8', border: '#d8b4fe' },
  'Double sens':                     { bg: '#fce7f3', text: '#9d174d', border: '#f9a8d4' },
  'Critères de réussite absents':    { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' },
  'Référence implicite':             { bg: '#e0f2fe', text: '#075985', border: '#7dd3fc' },
  'Consigne trop longue':            { bg: '#f0fdf4', text: '#166534', border: '#86efac' },
}

export const DEFAULT_COLOR = { bg: '#f1f5f9', text: '#334155', border: '#cbd5e1' }
