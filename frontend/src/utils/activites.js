// Sauvegarde d'une activité dans « Mes activités ».
//
// Contrairement à l'ancien appel fire-and-forget (`.catch(() => {})` qui avalait tout),
// cette fonction LÈVE en cas d'échec — réseau (fetch rejette) OU statut HTTP non-ok —
// pour que l'appelant puisse prévenir le prof. Supprime la perte silencieuse d'activités
// (audit 15/05, Phase 2.1 du plan de reprise). Payload = contrat de POST /api/mes-activites.
export async function sauvegarderActivite(payload) {
  const res = await fetch('/api/mes-activites', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// Clé d'un couple matière+niveau (vide -> chaîne vide, jamais de collision avec un vrai couple).
export function coupleKey(matiere, niveau) {
  return `${matiere || ''}|||${niveau || ''}`
}

// Comparateur : plus récent d'abord, les activités sans date (created_at null) en dernier.
export function parDateDesc(a, b) {
  const ta = a.created_at ? Date.parse(a.created_at) : -Infinity
  const tb = b.created_at ? Date.parse(b.created_at) : -Infinity
  return tb - ta
}

// Regroupe les activités par couple (matière + niveau) pour l'onglet « Toutes mes activités ».
// Ordre des sections : couple courant épinglé en tête, « Non classé » (matière/niveau vide) en
// dernier, le reste alphabétique. Dans chaque section : tri par date décroissante.
// Fonction pure → testée dans activites.test.js.
export function grouperParCouple(activites, currentKey = null) {
  const groupes = {}
  for (const a of activites) {
    const k = coupleKey(a.matiere, a.niveau)
    if (!groupes[k]) {
      const label = (!a.matiere && !a.niveau)
        ? 'Non classé'
        : [a.matiere, a.niveau].filter(Boolean).join(' — ')
      groupes[k] = { key: k, matiere: a.matiere || null, niveau: a.niveau || null, label, items: [] }
    }
    groupes[k].items.push(a)
  }
  const sections = Object.values(groupes)
  sections.forEach(g => g.items.sort(parDateDesc))   // plus récent en haut dans chaque section
  return sections.sort((x, y) => {
    if (x.key === currentKey) return -1            // couple courant épinglé en haut
    if (y.key === currentKey) return 1
    const xNon = !x.matiere && !x.niveau
    const yNon = !y.matiere && !y.niveau
    if (xNon !== yNon) return xNon ? 1 : -1         // « Non classé » en dernier
    return x.label.localeCompare(y.label, 'fr')     // sinon alphabétique
  })
}

// Libellé daté d'une activité. Récent → relatif ; au-delà de 7 jours → date complète.
// Renvoie { court, complet } ; court = à afficher, complet = pour l'infobulle (title=).
// `now` injectable pour les tests. created_at null/illisible → libellés vides.
export function formatDateActivite(iso, now = new Date()) {
  if (!iso) return { court: '', complet: '', recent: false }
  const d = new Date(iso)
  if (isNaN(d.getTime())) return { court: '', complet: '', recent: false }
  const complet = d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
  // Différence en jours CALENDAIRES (minuit→minuit) pour que « hier » soit exact.
  const jourD = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const jourN = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const diff = Math.round((jourN - jourD) / 86400000)
  let court, recent
  if (diff <= 0)       { court = "aujourd'hui";        recent = true }
  else if (diff === 1) { court = 'hier';               recent = true }
  else if (diff <= 7)  { court = `il y a ${diff} jours`; recent = true }
  else                 { court = `le ${complet}`;      recent = false }  // >7 j → date complète, jamais « il y a 247 jours »
  return { court, complet, recent }
}

// Couleur stable d'un couple matière+niveau (hash déterministe → palette fixe).
// Même couple = toujours la même couleur. La pastille est un COMPLÉMENT du texte, jamais seule.
const PALETTE_COUPLE = [
  '#2563eb', '#16a34a', '#db2777', '#d97706', '#7c3aed', '#0891b2',
  '#dc2626', '#4d7c0f', '#9333ea', '#0d9488', '#c2410c', '#475569',
]
export function couleurCouple(key) {
  let h = 0
  for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) >>> 0
  return PALETTE_COUPLE[h % PALETTE_COUPLE.length]
}
