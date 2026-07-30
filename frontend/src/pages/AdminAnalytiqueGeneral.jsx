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

  // Monde NEUF uniquement (décision 30/07) : les sections « Outils avancés » (Séquence /
  // Optimiseur, démolis) et « Communauté » (partages ancien monde) ont disparu.
  const { activites } = data

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>

      <div>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: '#1e293b', margin: 0 }}>Vue générale</h1>
        <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
          Synthèse de l'ensemble de la plateforme aSchool.
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

    </div>
  )
}
