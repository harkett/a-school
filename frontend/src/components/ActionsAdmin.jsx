import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

// L'ENCART « À TRAITER » — ce qui attend un geste de l'administrateur, en tête du tableau de
// bord (16/08/2026).
//
// LA SANTÉ DE LA PLATEFORME SE CONSULTE, UNE ACTION S'IMPOSE. D'où la place : juste sous le
// bandeau d'état, pleine largeur, avant tout le reste. Une alerte qu'il faut aller chercher en
// bas d'une colonne n'est pas une alerte — c'est ainsi que font Microsoft 365 et Google
// Workspace avec leur centre d'actions.
//
// L'ENCART N'EXISTE QUE S'IL Y A QUELQUE CHOSE. Pas de cartouche « Aucune action » en
// permanence : on apprend à ne plus le voir, et il occupe la place pour rien. Zéro action,
// zéro encart, la page respire.
//
// UNE SEULE SOURCE : `GET /api/admin/actions` (calculée dans `backend/systeme/actions_admin.py`).
// La pastille du menu compte la même chose — deux calculs séparés divergeraient.
//
// Chaque ligne S'EFFACE D'ELLE-MÊME quand le geste est fait : l'état se déduit de la base, rien
// ne se marque à la main, il n'y a donc rien à penser à décocher.
export const CLE_ACTIONS = ['admin', 'actions']

export function useActionsAdmin() {
  return useQuery({
    queryKey: CLE_ACTIONS,
    queryFn: async () => {
      const r = await fetchWithTimeout('/api/admin/actions', { credentials: 'include' }, TIMEOUT_STD)
      return r.ok ? await r.json() : { total: 0, actions: [], par_ecran: {} }
    },
    // Le tableau de bord n'est pas une salle de contrôle : une action attend, elle n'urge pas.
    staleTime: 60 * 1000,
  })
}

export default function ActionsAdmin() {
  const { data } = useActionsAdmin()
  const actions = data?.actions || []

  if (actions.length === 0) return null

  return (
    <div style={{
      background: '#fff', border: '1px solid #fde68a', borderLeft: '4px solid #f59e0b',
      borderRadius: 10, padding: '14px 18px 12px', marginBottom: 18,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{
          width: 8, height: 8, borderRadius: '50%', background: '#f59e0b', flexShrink: 0,
        }} />
        <span style={{
          fontSize: 13, fontWeight: 800, letterSpacing: '0.05em',
          textTransform: 'uppercase', color: '#92400e',
        }}>
          À traiter
        </span>
        <span style={{
          fontSize: 10.5, fontWeight: 800, padding: '1px 7px', borderRadius: 99,
          background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a',
        }}>
          {actions.length}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {actions.map(a => (
          // UNE LIGNE = UNE ACTION + UN LIEN. Elle dit ce qui est attendu, et ouvre l'écran où
          // le geste se fait : lire l'action et devoir chercher où agir, c'est deux travaux.
          <Link
            key={a.code}
            to={a.page}
            title="Ouvrir l’écran où faire ce geste"
            style={{
              display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap',
              padding: '9px 10px', borderRadius: 7, textDecoration: 'none',
              transition: 'background 0.12s',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = '#fffbeb' }}
            onMouseLeave={e => { e.currentTarget.style.background = 'transparent' }}
          >
            <span style={{ flex: '1 1 320px', minWidth: 0 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{a.titre}</span>
              {a.detail && (
                <span style={{ display: 'block', fontSize: 11.5, color: '#94a3b8', marginTop: 2, lineHeight: 1.45 }}>
                  {a.detail}
                </span>
              )}
            </span>
            <span style={{ fontSize: 12, fontWeight: 600, color: '#1F6EEB', flexShrink: 0 }}>
              Traiter →
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}
