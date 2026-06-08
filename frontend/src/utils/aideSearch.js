// Fonctions pures de la recherche dans la page Aide (item 41).
// Testées avec :  node --test src/utils/aideSearch.test.js   (depuis frontend/)
//
// Principe : on indexe une fois le texte réel de chaque rubrique (titre + nav +
// contenu JSX aplati), normalisé sans accents ni majuscules, puis on filtre en
// mode AND (tous les mots de la requête doivent être présents). Aucune duplication
// de contenu : extractText lit le JSX existant.

// Minuscule + suppression des accents → recherche tolérante.
// « Modèle », « modele », « MODÈLE » deviennent tous « modele ».
export function normalize(str) {
  return String(str ?? '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
}

// Extrait récursivement tout le texte d'un nœud React (JSX) en une chaîne plate.
// Gère : chaînes, nombres, tableaux, éléments (props.children), fragments.
// Ignore : null, undefined, booléens, fonctions.
export function extractText(node) {
  if (node == null || typeof node === 'boolean') return ''
  if (typeof node === 'string') return node
  if (typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(extractText).join(' ')
  if (typeof node === 'object' && node.props) return extractText(node.props.children)
  return ''
}

// Construit l'index : pour chaque rubrique, le texte affichable (plain) et sa
// version normalisée cherchable (haystack).
export function buildSearchIndex(sections) {
  return sections.map((s) => {
    const plain = `${s.titre || ''} ${s.nav || ''} ${extractText(s.contenu)}`.replace(/\s+/g, ' ').trim()
    return { ...s, plain, haystack: normalize(plain) }
  })
}

// Découpe une requête en mots normalisés (pour le filtre AND).
export function queryTerms(query) {
  return normalize(query).split(/\s+/).filter(Boolean)
}

// Filtre AND : une rubrique sort si elle contient TOUS les mots de la requête.
// Tri : les rubriques qui matchent par le titre/nav remontent avant celles qui
// ne matchent que par le contenu.
export function searchSections(index, query) {
  const terms = queryTerms(query)
  if (terms.length === 0) return []
  const titleHay = (item) => normalize(`${item.titre || ''} ${item.nav || ''}`)
  return index
    .filter((item) => terms.every((t) => item.haystack.includes(t)))
    .map((item) => {
      const th = titleHay(item)
      const score = terms.reduce((n, t) => n + (th.includes(t) ? 1 : 0), 0)
      return { item, score }
    })
    .sort((a, b) => b.score - a.score)
    .map((x) => x.item)
}

// Découpe un texte en segments { text, match } pour surligner les termes trouvés.
// Recherche insensible aux accents/majuscules (via normalize), surlignage sur le
// texte ORIGINAL. Hypothèse : normalize conserve la longueur (vrai pour le
// français usuel — un caractère accentué → un caractère de base). À défaut, le
// pire cas est un surlignage légèrement décalé, jamais un plantage.
export function highlightSegments(text, terms) {
  const src = String(text ?? '')
  const list = (terms || []).filter(Boolean)
  if (list.length === 0) return [{ text: src, match: false }]
  const norm = normalize(src)
  const ranges = []
  for (const t of list) {
    let from = 0
    let i
    while ((i = norm.indexOf(t, from)) !== -1) {
      ranges.push([i, i + t.length])
      from = i + t.length
    }
  }
  if (ranges.length === 0) return [{ text: src, match: false }]
  ranges.sort((a, b) => a[0] - b[0])
  const merged = []
  for (const r of ranges) {
    const last = merged[merged.length - 1]
    if (last && r[0] <= last[1]) last[1] = Math.max(last[1], r[1])
    else merged.push([r[0], r[1]])
  }
  const segments = []
  let pos = 0
  for (const [a, b] of merged) {
    if (a > pos) segments.push({ text: src.slice(pos, a), match: false })
    segments.push({ text: src.slice(a, b), match: true })
    pos = b
  }
  if (pos < src.length) segments.push({ text: src.slice(pos), match: false })
  return segments
}

// Extrait court du contenu autour du premier mot trouvé, pour la liste de résultats.
export function makeSnippet(plain, terms, radius = 70) {
  const src = String(plain ?? '')
  const list = (terms || []).filter(Boolean)
  const norm = normalize(src)
  let idx = -1
  for (const t of list) {
    const i = norm.indexOf(t)
    if (i !== -1 && (idx === -1 || i < idx)) idx = i
  }
  if (idx === -1) {
    return src.length > radius * 2 ? src.slice(0, radius * 2).trim() + '…' : src
  }
  const start = Math.max(0, idx - radius)
  const end = Math.min(src.length, idx + radius)
  return (start > 0 ? '…' : '') + src.slice(start, end).trim() + (end < src.length ? '…' : '')
}
