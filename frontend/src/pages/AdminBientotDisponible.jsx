import { useQuery } from '@tanstack/react-query'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

// Écran « Tâches à faire → Bientôt disponible » (16/08/2026).
//
// CE QUE LE PROFESSEUR VOIT, VU D'ICI. Les six cartes de l'écran prof « Bientôt disponible »
// vivent en base (table `features_votables`) : jusqu'ici, l'administrateur ne pouvait les lire
// qu'en ouvrant l'application côté prof, et il n'avait de leur côté qu'un classement de votes
// perdu dans un onglet de Feedbacks. Cet écran-ci les montre telles qu'elles sont annoncées —
// le titre, le texte, la famille — avec ce qu'elles ont récolté.
//
// LECTURE SEULE, et c'est voulu : une promesse faite aux professeurs ne se réécrit pas d'un
// clic entre deux visites. Elle se change par migration, comme elle a été posée.
export default function AdminBientotDisponible() {
  const { data: features, isError } = useQuery({
    queryKey: ['admin', 'feature-votes'],
    queryFn: async () => {
      const r = await fetchWithTimeout('/api/admin/feature-votes', { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) throw new Error('Liste illisible')
      return await r.json()
    },
  })

  if (isError)  return <p className="text-red-600 text-sm">Impossible de charger les fonctionnalités annoncées.</p>
  if (!features) return <p className="text-gray-400 text-sm">Chargement…</p>

  // L'ordre d'affichage est celui du professeur (`ordre`), pas celui des votes : on lit ici la
  // page telle qu'elle se présente à lui. Le classement par popularité a déjà son écran.
  const liste = [...features].sort((a, b) => (a.ordre ?? 0) - (b.ordre ?? 0))
  const total = liste.reduce((s, f) => s + f.count, 0)
  const annoncees = liste.filter(f => f.actif).length

  return (
    <div className="flex flex-col gap-4">

      <div style={{
        background: '#eff6ff', border: '1px solid #bfdbfe', borderLeft: '4px solid #3b82f6',
        borderRadius: 8, padding: '12px 16px',
      }}>
        <div style={{ fontSize: 11, color: '#3b82f6', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
          Ce que le professeur voit
        </div>
        <div style={{ fontSize: 22, fontWeight: 800, color: '#1e3a8a', lineHeight: 1.2, marginTop: 2 }}>
          {annoncees} fonctionnalité{annoncees > 1 ? 's' : ''} annoncée{annoncees > 1 ? 's' : ''}
        </div>
        <div className="text-xs" style={{ color: '#64748b', marginTop: 4 }}>
          Écran prof « Bientôt disponible » · {total} vote{total > 1 ? 's' : ''} au total ·
          {' '}lecture seule, le texte se change par migration
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {liste.map(f => (
          <div key={f.key}
               className="bg-white rounded-xl border border-gray-200 px-5 py-4"
               style={{ opacity: f.actif ? 1 : 0.55 }}>
            <div className="flex items-start justify-between gap-3 mb-1" style={{ flexWrap: 'wrap' }}>
              <div className="flex items-center gap-2" style={{ minWidth: 0 }}>
                <span className="text-sm font-semibold text-gray-800">{f.label}</span>
                <span style={{
                  fontSize: 10.5, padding: '1px 8px', borderRadius: 5, whiteSpace: 'nowrap',
                  background: '#f1f5f9', color: '#64748b', border: '1px solid #e2e8f0',
                }}>
                  {f.categorie}
                </span>
                {/* Une carte retirée de l'écran prof garde ses votes : le dire, sinon le chiffre
                    d'à côté se lit comme un engouement actuel. */}
                {!f.actif && (
                  <span style={{
                    fontSize: 10.5, padding: '1px 8px', borderRadius: 5, whiteSpace: 'nowrap',
                    background: '#fef2f2', color: '#b91c1c', border: '1px solid #fecaca',
                  }}>
                    retirée de l’écran prof
                  </span>
                )}
              </div>
              <span className="text-sm font-bold" style={{ color: f.count > 0 ? '#A63045' : '#94a3b8', flexShrink: 0 }}>
                {f.count} vote{f.count !== 1 ? 's' : ''}
              </span>
            </div>
            <p className="text-xs text-gray-500" style={{ lineHeight: 1.55, margin: 0 }}>
              {f.description}
            </p>
          </div>
        ))}
      </div>

    </div>
  )
}
