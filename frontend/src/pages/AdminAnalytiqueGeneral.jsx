import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

function KpiCard({ label, value, sub, color, icon }) {
  return (
    <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 20px', flex: 1, minWidth: 130 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        {icon && <span style={{ color: color || '#64748b', opacity: 0.8 }}>{icon}</span>}
      </div>
      <div style={{ fontSize: 26, fontWeight: 700, color: color || '#1e293b', lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 12, color: '#475569', marginTop: 4 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div>
      <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
        {title}
      </div>
      {children}
    </div>
  )
}

export default function AdminAnalytiqueGeneral() {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/stats/general', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        return r.json()
      })
      .then(d => { if (d) setData(d) })
      .finally(() => setLoading(false))
  }, [navigate])

  if (loading) return <p style={{ color: '#94a3b8', padding: 32 }}>Chargement…</p>
  if (!data)   return <p style={{ color: '#ef4444', padding: 32 }}>Erreur de chargement.</p>

  const { activites, outils, communaute } = data
  const scores = outils.optimiseur.scores || {}
  const totalScores = Object.values(scores).reduce((s, n) => s + n, 0)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>

      <div>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: '#1e293b', margin: 0 }}>Vue générale</h1>
        <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
          Synthèse de l'ensemble de la plateforme A-SCHOOL.
        </p>
      </div>

      {/* Activités pédagogiques */}
      <Section title="Activités pédagogiques">
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <KpiCard
            label="Activités générées"
            value={activites.total}
            color="#A63045"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>}
          />
          <KpiCard
            label="Profs actifs"
            value={activites.nb_profs}
            color="#1e40af"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>}
          />
          <KpiCard
            label="Matière la plus active"
            value={activites.top_matiere}
            sub={`${activites.top_matiere_nb} activités`}
            color="#0369a1"
          />
          <KpiCard
            label="Type le plus utilisé"
            value={activites.top_type}
            sub={`×${activites.top_type_nb}`}
            color="#0369a1"
          />
        </div>
      </Section>

      {/* Outils avancés */}
      <Section title="Outils avancés">
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <KpiCard
            label="Séquences générées"
            value={outils.sequence.total}
            sub={`${outils.sequence.nb_profs} prof${outils.sequence.nb_profs > 1 ? 's' : ''}`}
            color="#7c3aed"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>}
          />
          <KpiCard
            label="Optimisations lancées"
            value={outils.optimiseur.total}
            sub={`${outils.optimiseur.nb_profs} prof${outils.optimiseur.nb_profs > 1 ? 's' : ''}`}
            color="#0891b2"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>}
          />
          {totalScores > 0 && (
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 20px', flex: 1, minWidth: 160 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#64748b', marginBottom: 10 }}>Scores Optimiseur</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {[['Bon', '#16a34a'], ['Moyen', '#ca8a04'], ['À revoir', '#dc2626']].map(([label, color]) => (
                  scores[label] ? (
                    <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 11, color: '#475569', width: 56 }}>{label}</span>
                      <div style={{ flex: 1, background: '#f1f5f9', borderRadius: 99, height: 6 }}>
                        <div style={{ width: `${Math.round(scores[label] / totalScores * 100)}%`, background: color, height: 6, borderRadius: 99 }} />
                      </div>
                      <span style={{ fontSize: 11, fontWeight: 700, color, minWidth: 20, textAlign: 'right' }}>{scores[label]}</span>
                    </div>
                  ) : null
                ))}
              </div>
            </div>
          )}
        </div>
      </Section>

      {/* Communauté */}
      <Section title="Communauté">
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <KpiCard
            label="Activités partagées"
            value={communaute.total_partages}
            color="#059669"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>}
          />
          <KpiCard
            label="Profs contributeurs"
            value={communaute.nb_contributeurs}
            color="#059669"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>}
          />
        </div>
      </Section>

    </div>
  )
}
