import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const SCORE_COLORS = { 'Bon': '#16a34a', 'Moyen': '#ca8a04', 'À revoir': '#dc2626' }
const SCORE_BG    = { 'Bon': '#dcfce7', 'Moyen': '#fef9c3', 'À revoir': '#fee2e2' }

function ToolCard({ title, icon, color, stats, children }) {
  return (
    <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 12, overflow: 'hidden', flex: 1, minWidth: 260 }}>
      <div style={{ padding: '16px 20px 14px', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ color }}>{icon}</span>
        <span style={{ fontSize: 14, fontWeight: 700, color: '#1e293b' }}>{title}</span>
      </div>
      <div style={{ padding: '16px 20px', display: 'flex', gap: 16, borderBottom: '1px solid #f1f5f9' }}>
        <div style={{ textAlign: 'center', flex: 1 }}>
          <div style={{ fontSize: 28, fontWeight: 700, color }}>{stats.total}</div>
          <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>Total</div>
        </div>
        <div style={{ width: 1, background: '#f1f5f9' }} />
        <div style={{ textAlign: 'center', flex: 1 }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#1e293b' }}>{stats.nb_profs}</div>
          <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>Profs</div>
        </div>
        <div style={{ width: 1, background: '#f1f5f9' }} />
        <div style={{ textAlign: 'center', flex: 1 }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#1e293b' }}>{stats.derniers_30j}</div>
          <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>30 derniers jours</div>
        </div>
      </div>
      {children && <div style={{ padding: '14px 20px' }}>{children}</div>}
    </div>
  )
}

export default function AdminAnalytiqueOutils() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/tool-usage', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        return r.json()
      })
      .then(d => { if (d) setData(d) })
      .finally(() => setLoading(false))
  }, [navigate])

  if (loading) return <p style={{ color: '#94a3b8', padding: 32 }}>Chargement…</p>
  if (!data)   return <p style={{ color: '#ef4444', padding: 32 }}>Erreur de chargement.</p>

  const { sequence, optimiseur } = data
  const scores = optimiseur.scores || {}
  const totalScores = Object.values(scores).reduce((s, n) => s + n, 0)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      <div>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: '#1e293b', margin: 0 }}>Outils avancés</h1>
        <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
          Utilisation de Séquence pédagogique et Optimiseur de séquences.
        </p>
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-start' }}>

        {/* Séquence */}
        <ToolCard
          title="Séquence pédagogique"
          color="#7c3aed"
          stats={sequence}
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="8" y1="6" x2="21" y2="6"/>
              <line x1="8" y1="12" x2="21" y2="12"/>
              <line x1="8" y1="18" x2="21" y2="18"/>
              <line x1="3" y1="6" x2="3.01" y2="6"/>
              <line x1="3" y1="12" x2="3.01" y2="12"/>
              <line x1="3" y1="18" x2="3.01" y2="18"/>
            </svg>
          }
        >
          {sequence.total === 0 && (
            <p style={{ fontSize: 12, color: '#94a3b8', margin: 0 }}>Aucune génération enregistrée pour le moment.</p>
          )}
        </ToolCard>

        {/* Optimiseur */}
        <ToolCard
          title="Optimiseur de séquences"
          color="#0891b2"
          stats={optimiseur}
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
            </svg>
          }
        >
          {totalScores === 0 ? (
            <p style={{ fontSize: 12, color: '#94a3b8', margin: 0 }}>Aucune analyse enregistrée pour le moment.</p>
          ) : (
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#64748b', marginBottom: 10 }}>
                Répartition des scores ({totalScores} analyses)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {['Bon', 'Moyen', 'À revoir'].map(label => {
                  const nb = scores[label] || 0
                  const pct = totalScores ? Math.round(nb / totalScores * 100) : 0
                  return (
                    <div key={label}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                        <span style={{
                          fontSize: 11, fontWeight: 600, padding: '1px 8px', borderRadius: 99,
                          background: SCORE_BG[label], color: SCORE_COLORS[label],
                        }}>
                          {label}
                        </span>
                        <span style={{ fontSize: 11, color: '#94a3b8' }}>{nb} ({pct}%)</span>
                      </div>
                      <div style={{ background: '#f1f5f9', borderRadius: 99, height: 6 }}>
                        <div style={{ width: `${pct}%`, background: SCORE_COLORS[label], height: 6, borderRadius: 99, transition: 'width 0.3s' }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </ToolCard>

      </div>
    </div>
  )
}
