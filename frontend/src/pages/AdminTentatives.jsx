import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function AdminTentatives() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/failed-attempts', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        return r.json()
      })
      .then(data => { if (data) setRows(data) })
      .finally(() => setLoading(false))
  }, [navigate])

  const bloquees = rows.filter(r => r.blocked).length

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">
          Tentatives de connexion échouées
          {bloquees > 0 && (
            <span style={{ marginLeft: 8, padding: '2px 8px', borderRadius: 99, fontSize: 11, background: '#fee2e2', color: '#dc2626', fontWeight: 700 }}>
              {bloquees} bloquée{bloquees > 1 ? 's' : ''}
            </span>
          )}
        </h2>
        <span className="text-xs text-gray-400">{rows.length} entrée{rows.length !== 1 ? 's' : ''} — 200 dernières</span>
      </div>

      {rows.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>✓</div>
          <p className="text-sm">Aucune tentative échouée enregistrée.</p>
        </div>
      ) : (
        <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Date</th>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }}>IP</th>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Identifiant tenté</th>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Statut</th>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }}>User-Agent</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr
                  key={r.id}
                  style={{ borderBottom: i < rows.length - 1 ? '1px solid #f1f5f9' : 'none', background: r.blocked ? '#fff5f5' : 'white' }}
                >
                  <td style={{ padding: '10px 16px', color: '#475569', whiteSpace: 'nowrap' }}>{r.date}</td>
                  <td style={{ padding: '10px 16px', fontFamily: 'monospace', color: '#1e293b' }}>{r.ip}</td>
                  <td style={{ padding: '10px 16px', color: '#1e293b' }}>{r.username}</td>
                  <td style={{ padding: '10px 16px' }}>
                    {r.blocked ? (
                      <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700, background: '#fee2e2', color: '#dc2626' }}>Bloquée</span>
                    ) : (
                      <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, background: '#fff7ed', color: '#d97706' }}>Échouée</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: 11, maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                    title={r.user_agent}>
                    {r.user_agent}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
