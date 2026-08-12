// LES CINQ AXES sur lesquels une consigne est jugée — À UNE SEULE PLACE.
//
// Ils étaient écrits TROIS fois, dans trois endroits qui s'ignoraient : le prompt d'analyse (en
// base), les couleurs de l'écran, et la liste de l'onglet d'aide — avec des définitions qui
// avaient déjà divergé (« trop longues » d'un côté, « trop longues ou mal construites » de
// l'autre). Renommer un axe dans le prompt suffisait à faire tomber sa carte sur la couleur de
// repli, sans erreur nulle part, pendant que l'aide continuait d'annoncer l'ancien nom.
//
// Ce module est la source de l'ÉCRAN : les étiquettes de la colonne de gauche, les couleurs des
// cartes du rapport, la sortie HTML et le catalogue d'aide le lisent tous ici.
//
// LE PROMPT RESTE L'AUTRE SOURCE, et c'est assumé : il vit en base, l'admin le règle depuis
// Admin → IA → Prompts. Les `label` ci-dessous doivent donc rester le mot pour mot de ceux du
// prompt — c'est sur eux que le modèle étiquette ses réponses, et c'est par eux qu'une carte
// retrouve sa couleur. Le jour où les axes deviendront une table, ce module la lira.
//
// CE NE SONT PAS DES CASES À COCHER, contrairement aux types d'ambiguïté. Un type d'ambiguïté
// décoché retire des cartes du rapport, rien de plus. Un axe décoché produirait une « consigne
// optimisée » qui laisse passer un défaut connu, sans que le professeur le sache — les cinq axes
// sont les dimensions d'un même diagnostic, pas un filtre. Ils sont donc IMPOSÉS, et seulement
// affichés.

export const AXES_CONSIGNE = [
  {
    label: 'Clarté linguistique',
    description: 'formulations floues, vagues, trop longues ou mal construites',
    couleur: { bg: '#fef3c7', text: '#92400e', border: '#fde68a' },
  },
  {
    label: 'Précision didactique',
    description: "la consigne dit-elle exactement ce que l'enseignant veut évaluer ?",
    couleur: { bg: '#f3e8ff', text: '#6b21a8', border: '#d8b4fe' },
  },
  {
    label: 'Ambiguïté conceptuelle',
    description: 'mots à double sens, termes polysémiques (« analyser », « expliquer », « produit »…)',
    couleur: { bg: '#fce7f3', text: '#9d174d', border: '#f9a8d4' },
  },
  {
    label: 'Structure logique',
    description: 'étapes implicites, tâches multiples non séparées, sauts logiques',
    couleur: { bg: '#ffedd5', text: '#7c2d12', border: '#fdba74' },
  },
  {
    label: "Risque d'erreurs typiques",
    description: 'formulations qui provoquent des erreurs récurrentes chez les élèves de ce niveau',
    couleur: { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' },
  },
]

// Le gris de repli. Il ne devrait jamais servir : s'il apparaît à l'écran, c'est que le modèle a
// rendu un axe hors liste — donc que le prompt et ce module ont divergé.
export const AXE_DEFAUT = { bg: '#f1f5f9', text: '#334155', border: '#cbd5e1' }

// La couleur d'un axe rendu par le modèle. Étiquette inconnue → le gris de repli.
export function couleurAxe(label) {
  return (AXES_CONSIGNE.find(a => a.label === label) || {}).couleur || AXE_DEFAUT
}
