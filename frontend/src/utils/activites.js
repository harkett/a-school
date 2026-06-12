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

// Regroupe les activités par couple (matière + niveau) pour l'onglet « Toutes mes activités ».
// Ordre : couple courant épinglé en tête, « Non classé » (matière/niveau vide) en dernier,
// le reste par ordre alphabétique. Fonction pure → testée dans activites.test.js.
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
  return Object.values(groupes).sort((x, y) => {
    if (x.key === currentKey) return -1            // couple courant épinglé en haut
    if (y.key === currentKey) return 1
    const xNon = !x.matiere && !x.niveau
    const yNon = !y.matiere && !y.niveau
    if (xNon !== yNon) return xNon ? 1 : -1         // « Non classé » en dernier
    return x.label.localeCompare(y.label, 'fr')     // sinon alphabétique
  })
}
