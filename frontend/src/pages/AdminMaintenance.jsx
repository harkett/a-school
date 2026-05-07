import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

const LABELS = {
  tokens_email_expires:    { label: 'Tokens email expirés',              detail: 'Liens de vérification et reset MDP périmés.',                  color: '#d97706' },
  tokens_refresh_old:      { label: 'Refresh tokens périmés / révoqués', detail: 'Tokens de session expirés ou révoqués.',                        color: '#d97706' },
  sessions_inactives:      { label: 'Sessions fermées',                  detail: 'Sessions déconnectées (manuellement ou par expiration).',       color: '#64748b' },
  users_non_verifies_30j:  { label: 'Comptes non vérifiés +30 jours',    detail: 'Inscriptions abandonnées sans clic sur le lien email.',         color: '#dc2626' },
  connexion_logs_90j:      { label: 'Logs connexion +90 jours',          detail: 'Historique des connexions antérieur à 3 mois.',                 color: '#64748b' },
  failed_logins_30j:       { label: 'Tentatives échouées +30 jours',     detail: 'Tentatives de connexion antérieures à 1 mois.',                 color: '#64748b' },
  audit_logs_180j:         { label: 'Audit trail +180 jours',            detail: 'Actions admin antérieures à 6 mois.',                          color: '#64748b' },
}

function ProgressBar({ value, max, color }) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0
  return (
    <div style={{ background: '#f1f5f9', borderRadius: 4, height: 6, overflow: 'hidden' }}>
      <div style={{ width: `${pct}%`, height: '100%', background: color || '#3b82f6', borderRadius: 4, transition: 'width 0.4s' }} />
    </div>
  )
}

export default function AdminMaintenance() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [purging, setPurging] = useState(null)
  const [results, setResults] = useState({})
  const navigate = useNavigate()

  const load = useCallback(() => {
    setLoading(true)
    fetch('/api/admin/maintenance/stats', { credentials: 'include' })
      .then(r => { if (r.status === 401) { navigate('/admin/login'); return null } return r.json() })
      .then(d => { if (d) setData(d) })
      .finally(() => setLoading(false))
  }, [navigate])

  useEffect(() => { load() }, [load])

  async function purge(category) {
    if (!window.confirm(`Purger "${LABELS[category]?.label}" ?\n\nCette action est irréversible.`)) return
    setPurging(category)
    try {
      const res = await fetch(`/api/admin/maintenance/purge/${category}`, { method: 'POST', credentials: 'include' })
      const json = await res.json()
      setResults(r => ({ ...r, [category]: json.purged }))
      load()
    } finally { setPurging(null) }
  }

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>
  if (!data)   return null

  const totalRecords = Object.values(data.tables).reduce((s, v) => s + v, 0)
  const totalOrphans = Object.values(data.orphans).reduce((s, v) => s + v, 0)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* En-tête */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h2 className="text-sm font-semibold text-gray-700">Maintenance base de données</h2>
          <p className="text-xs text-gray-400 mt-0.5">Fichier SQLite · {data.db_size_mb} Mo · {totalRecords.toLocaleString('fr')} enregistrements au total</p>
        </div>
        <button onClick={load}
          style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'white', border: '1px solid #d1d5db', borderRadius: 7, padding: '6px 14px', fontSize: 12, color: '#374151', cursor: 'pointer' }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
          Actualiser
        </button>
      </div>

      {/* Contenu tables */}
      <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f1f5f9' }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', margin: 0 }}>Contenu des tables</h3>
          <p style={{ fontSize: 11, color: '#94a3b8', margin: '2px 0 0' }}>Nombre d'enregistrements par table</p>
        </div>
        <div style={{ padding: '8px 0' }}>
          {Object.entries(data.tables).map(([name, count]) => (
            <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 20px' }}>
              <span style={{ fontSize: 12, color: '#374151', width: 200, flexShrink: 0 }}>{name}</span>
              <div style={{ flex: 1 }}>
                <ProgressBar value={count} max={totalRecords} color="#3b82f6" />
              </div>
              <span style={{ fontSize: 12, fontWeight: 600, color: count > 0 ? '#1e293b' : '#d1d5db', width: 60, textAlign: 'right', flexShrink: 0 }}>
                {count.toLocaleString('fr')}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Données orphelines */}
      <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', margin: 0 }}>Données à nettoyer</h3>
            <p style={{ fontSize: 11, color: '#94a3b8', margin: '2px 0 0' }}>
              {totalOrphans > 0
                ? <><span style={{ color: '#d97706', fontWeight: 600 }}>{totalOrphans.toLocaleString('fr')} enregistrement{totalOrphans > 1 ? 's' : ''}</span> pouvant être supprimés</>
                : <span style={{ color: '#15803d', fontWeight: 600 }}>Base propre — rien à purger</span>
              }
            </p>
          </div>
        </div>

        <div style={{ padding: '8px 0' }}>
          {Object.entries(data.orphans).map(([key, count]) => {
            const meta   = LABELS[key] || { label: key, detail: '', color: '#64748b' }
            const result = results[key]
            const isEmpty = count === 0
            return (
              <div key={key} style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: '10px 20px',
                borderBottom: '1px solid #f8fafc',
                opacity: isEmpty ? 0.5 : 1,
              }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 500, color: '#1e293b' }}>{meta.label}</div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 1 }}>{meta.detail}</div>
                </div>
                <span style={{
                  fontSize: 13, fontWeight: 700,
                  color: isEmpty ? '#d1d5db' : meta.color,
                  width: 60, textAlign: 'right', flexShrink: 0,
                }}>
                  {count.toLocaleString('fr')}
                </span>
                {result !== undefined && (
                  <span style={{ fontSize: 11, color: '#15803d', fontWeight: 600, flexShrink: 0 }}>
                    ✓ {result} purgé{result > 1 ? 's' : ''}
                  </span>
                )}
                <button
                  onClick={() => purge(key)}
                  disabled={isEmpty || purging === key}
                  title={isEmpty ? 'Rien à purger' : `Supprimer les ${count} enregistrement(s)`}
                  style={{
                    background: isEmpty ? '#f8fafc' : '#fef2f2',
                    color: isEmpty ? '#d1d5db' : '#dc2626',
                    border: `1px solid ${isEmpty ? '#e2e8f0' : '#fecaca'}`,
                    borderRadius: 6, padding: '4px 12px', fontSize: 11, fontWeight: 500,
                    cursor: isEmpty ? 'not-allowed' : 'pointer',
                    flexShrink: 0,
                    opacity: purging === key ? 0.6 : 1,
                  }}>
                  {purging === key ? 'Purge…' : 'Purger'}
                </button>
              </div>
            )
          })}
        </div>

        {totalOrphans === 0 && (
          <div style={{ padding: '20px', textAlign: 'center', color: '#15803d', fontSize: 13 }}>
            Base de données propre.
          </div>
        )}
      </div>

    </div>
  )
}
