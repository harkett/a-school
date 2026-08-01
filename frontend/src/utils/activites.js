// Logique pure partagée par les pages listes de Mes contenus (groupement par couple,
// dates, couleurs). sauvegarderActivite (POST /api/mes-activites) a été démolie le 30/07
// avec l'ancien monde — l'écriture vit dans les écrans Mes contenus (auto-save, règle 0).

// Clé d'un couple matière+niveau (vide -> chaîne vide, jamais de collision avec un vrai couple).
export function coupleKey(matiere, niveau) {
  return `${matiere || ''}|||${niveau || ''}`
}

// L'activité correspond-elle au profil courant (MÊME matière ET MÊME niveau) ?
// Sert à garder « Reprendre » : on ne regénère pas une activité d'un autre couple que
// le profil (on ne reprend pas du Français en étant prof de Réseaux) — on guide vers Mon profil.
export function correspondProfil(activite, matiere, niveau) {
  return !!activite && activite.matiere === matiere && activite.niveau === niveau
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
// Renvoie { court, complet, numerique, recent, heure } ; heure = HH:MM de la sauvegarde
// (created_at) ; numerique = JJ/MM/AAAA (ex. « 26/07/2026 »).
// `now` injectable pour les tests. created_at null/illisible → libellés vides.
export function formatDateActivite(iso, now = new Date()) {
  if (!iso) return { court: '', complet: '', numerique: '', recent: false, heure: '' }
  const d = new Date(iso)
  if (isNaN(d.getTime())) return { court: '', complet: '', numerique: '', recent: false, heure: '' }
  const complet = d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
  const numerique = d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })
  const heure = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
  // Différence en jours CALENDAIRES (minuit→minuit) pour que « hier » soit exact.
  const jourD = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const jourN = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const diff = Math.round((jourN - jourD) / 86400000)
  let court, recent
  if (diff <= 0)       { court = "aujourd'hui";        recent = true }
  else if (diff === 1) { court = 'hier';               recent = true }
  else if (diff <= 7)  { court = `il y a ${diff} jours`; recent = true }
  else                 { court = `le ${complet}`;      recent = false }  // >7 j → date complète, jamais « il y a 247 jours »
  return { court, complet, numerique, recent, heure }
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

// Champs du type d'activité remis à VIERGE : plus AUCUNE présélection (règle appli — tout
// combo démarre sur son placeholder gris « Choisissez… », le prof fait le choix). Avant, on
// reposait ici le 1er type de la matière et sa 1re précision : les deux combos arrivaient
// remplies et l'étape ① passait au vert sans que le prof ait rien choisi.
// Renvoie l'objet à fusionner dans `params`. (Venait de utils/activite.js, fusionné le 01/08 :
// deux fichiers voisins au nom quasi identique, rien ne disait lequel faisait quoi.)
export function typeVierge() {
  return {
    activite_type_id: null,   // identité du type = son id ; null = rien de choisi
    sous_type: null,
    nb: null,   // posé (à 5) par la carte Paramètres au choix du type, si son prompt le demande
    avec_correction: false,
  }
}
