import { useQuery } from '@tanstack/react-query'
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
//
// La lecture est tenue par react-query : plusieurs écrans peuvent demander les matières
// en même temps, il n'y aura qu'UN appel — et pas un état d'attente posé à la main par écran.
export function useMatieres() {
  const { data: matieres = [], isPending: chargement } = useQuery({
    queryKey: ['matieres'],
    queryFn: async () => {
      try {
        const r = await fetchWithTimeout('/api/matieres', { credentials: 'include' }, TIMEOUT_STD)
        const rows = r.ok ? await r.json() : []
        return rows.map(m => m.nom)
      } catch {
        return []   // liste vide : l'écran n'invente aucune matière, il n'en propose aucune
      }
    },
  })

  return { matieres, chargement }
}
