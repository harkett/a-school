import { useState, useEffect } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from './api.js'

// Source UNIQUE des matières, dérivées de la base via /api/matieres
// (jointure matieres⋈matiere_niveaux). Remplace les listes « MATIERES »
// autrefois copiées en dur dans 8 écrans (P5.10).
//
// Renvoie des NOMS (« Français »), car c'est le nom qui est stocké dans le
// profil et comparé côté backend, jamais la clé.
//
// `chargement` permet d'afficher un état d'attente (select désactivé, libellé
// « Chargement… ») au lieu d'un flash de liste vide le temps du fetch.
export function useMatieres() {
  const [matieres, setMatieres]     = useState([])
  const [chargement, setChargement] = useState(true)

  useEffect(() => {
    let actif = true
    setChargement(true)
    fetchWithTimeout(
      '/api/matieres',
      { credentials: 'include' },
      TIMEOUT_STD,
    )
      .then(r => (r.ok ? r.json() : []))
      .then(rows => { if (actif) setMatieres(rows.map(m => m.nom)) })
      .catch(() => { if (actif) setMatieres([]) })
      .finally(() => { if (actif) setChargement(false) })
    return () => { actif = false }
  }, [])

  return { matieres, chargement }
}
