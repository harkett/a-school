import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

// Assistant de PREMIÈRE MISE EN ROUTE (admin). Chaque pastille est un REFLET lu en direct
// dans la base (get, zéro copie) via /api/admin/mise-en-route/etat — jamais une case cochée
// à la main. Les boutons NE FONT QUE NAVIGUER vers l'écran où l'admin agit réellement.
export default function AdminMiseEnRoute() {
  const navigate = useNavigate()

  // L'état de la mise en route est UNE lecture en base : react-query la tient (première
  // lecture, panne, relecture), l'écran n'en garde aucune copie.
  const { data, isError: erreur, refetch } = useQuery({
    queryKey: ['admin', 'mise-en-route'],
    queryFn: async () => {
      const r = await fetchWithTimeout('/api/admin/mise-en-route/etat', { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) throw new Error('état de la mise en route illisible')
      return await r.json()
    },
  })

  if (erreur) return (
    <div style={{ fontSize: 13, color: '#64748b' }}>
      Impossible de lire l'état de la mise en route pour le moment.{' '}
      <button onClick={() => refetch()} style={lienStyle}>Réessayer</button>
    </div>
  )
  if (!data) return <div style={{ fontSize: 13, color: '#94a3b8' }}>Chargement…</div>

  const { complet, etapes } = data
  const restant = etapes.filter(e => !e.fait).length

  return (
    <div style={{ maxWidth: 780 }}>
      {/* Bandeau global — langage humain, jamais « tout est cassé » (règle 23) */}
      <div style={{
        borderRadius: 10, padding: '16px 18px', marginBottom: 20,
        background: complet ? '#f0fdf4' : '#eff6ff',
        border: `1px solid ${complet ? '#bbf7d0' : '#bfdbfe'}`,
      }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: '#1e293b', marginBottom: 4 }}>
          {complet ? 'Tout est prêt' : 'Mise en route d’aSchool'}
        </div>
        <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.6 }}>
          {complet
            ? 'aSchool est pleinement opérationnel : les profs travaillent avec l’ancrage complet au programme officiel.'
            : `Voici ce qui manque pour la pleine qualité — ${restant} étape${restant > 1 ? 's' : ''} restante${restant > 1 ? 's' : ''}. Les profs peuvent déjà générer des activités, mais sans ancrage au programme officiel tant que les référentiels ne sont pas prêts.`}
        </div>
      </div>

      {/* Les 8 étapes */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {etapes.map(e => (
          <div key={e.num} style={{
            display: 'flex', alignItems: 'flex-start', gap: 14,
            background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '14px 16px',
          }}>
            {/* Pastille : verte (fait) ou rouge (à faire) — lue en base */}
            <span style={{
              flexShrink: 0, marginTop: 1, width: 24, height: 24, borderRadius: '50%',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: e.fait ? '#16a34a' : '#fee2e2',
              color: e.fait ? '#fff' : '#dc2626', fontSize: 12, fontWeight: 700,
              border: e.fait ? 'none' : '1px solid #fecaca',
            }}>
              {e.fait
                ? <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                : e.num}
            </span>

            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#1e293b' }}>{e.titre}</div>
              {!e.fait && (
                <div style={{ fontSize: 13, color: '#64748b', lineHeight: 1.55, marginTop: 4 }}>{e.message}</div>
              )}
            </div>

            {!e.fait && e.ecran && (
              <button
                onClick={() => navigate(e.ecran)}
                className="btn-primary"
                style={{ flexShrink: 0, whiteSpace: 'nowrap' }}
                title={`Aller à l’écran pour : ${e.titre}`}
              >
                Aller à l'écran
              </button>
            )}
            {e.fait && (
              <span style={{ flexShrink: 0, fontSize: 12, fontWeight: 600, color: '#16a34a', marginTop: 4 }}>Fait</span>
            )}
          </div>
        ))}
      </div>

      <div style={{ marginTop: 16 }}>
        <button onClick={() => refetch()} style={lienStyle} title="Relire l'état en base">Rafraîchir l'état</button>
      </div>
    </div>
  )
}

const lienStyle = {
  background: 'none', border: 'none', color: '#1F6EEB',
  cursor: 'pointer', textDecoration: 'underline', fontSize: 13, padding: 0,
}
