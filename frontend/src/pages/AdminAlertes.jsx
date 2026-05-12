import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

const LEVEL_STYLE = {
  critical: { bg: '#fee2e2', color: '#dc2626', label: 'Critique' },
  warning:  { bg: '#ffedd5', color: '#d97706', label: 'Attention' },
  info:     { bg: '#dbeafe', color: '#1d4ed8', label: 'Info' },
}

export default function AdminAlertes() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  function load() {
    fetch('/api/admin/alerts', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        return r.json()
      })
      .then(data => { if (data) setAlerts(data) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function markRead(id) {
    await fetchWithTimeout(`/api/admin/alerts/${id}/read`, { method: 'POST', credentials: 'include' }, TIMEOUT_STD)
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a))
  }

  const nonLues = alerts.filter(a => !a.is_read).length

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">
          Alertes système
          {nonLues > 0 && (
            <span style={{ marginLeft: 8, padding: '2px 8px', borderRadius: 99, fontSize: 11, background: '#fee2e2', color: '#dc2626', fontWeight: 700 }}>
              {nonLues} non lue{nonLues > 1 ? 's' : ''}
            </span>
          )}
        </h2>
        <span className="text-xs text-gray-400">Vérification automatique toutes les 5 min</span>
      </div>

      {alerts.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>✓</div>
          <p className="text-sm">Aucune alerte — tout va bien.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {alerts.map(a => {
            const s = LEVEL_STYLE[a.level] || LEVEL_STYLE.info
            return (
              <div
                key={a.id}
                style={{
                  background: 'white',
                  border: `1px solid ${a.is_read ? '#e2e8f0' : s.bg}`,
                  borderLeft: `4px solid ${a.is_read ? '#e2e8f0' : s.color}`,
                  borderRadius: 8,
                  padding: '14px 18px',
                  opacity: a.is_read ? 0.6 : 1,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 14,
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700, background: s.bg, color: s.color }}>
                      {s.label}
                    </span>
                    <span className="text-xs text-gray-400">{a.date}</span>
                  </div>
                  <p style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', margin: 0 }}>{a.title}</p>
                  <p style={{ fontSize: 12, color: '#64748b', margin: '3px 0 0' }}>{a.message}</p>
                </div>
                {!a.is_read && (
                  <button
                    onClick={() => markRead(a.id)}
                    title="Marquer comme lu"
                    style={{
                      padding: '4px 12px', fontSize: 11, borderRadius: 4,
                      border: '1px solid #e2e8f0', cursor: 'pointer',
                      background: 'white', color: '#64748b', flexShrink: 0,
                    }}
                  >
                    Lu
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
