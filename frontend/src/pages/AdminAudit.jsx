import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const ACTION_STYLE = {
  FORCE_LOGOUT:    { bg: '#fee2e2', color: '#dc2626' },
  USER_DELETE:     { bg: '#fee2e2', color: '#dc2626' },
  SETTINGS_CHANGE: { bg: '#dbeafe', color: '#1d4ed8' },
}

export default function AdminAudit() {
  const [logs, setLogs]       = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/audit-log', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        return r.json()
      })
      .then(data => { if (data) setLogs(data) })
      .finally(() => setLoading(false))
  }, [navigate])

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-700 mb-4">
        Audit trail
        <span className="ml-2 text-xs font-normal text-gray-400">({logs.length} action{logs.length !== 1 ? 's' : ''})</span>
      </h2>

      {logs.length === 0 ? (
        <p className="text-sm text-gray-400">Aucune action enregistrée pour l'instant.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">Cible</th>
                <th className="px-4 py-3 font-medium">Détails</th>
                <th className="px-4 py-3 font-medium">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map(l => {
                const s = ACTION_STYLE[l.action] || { bg: '#f1f5f9', color: '#64748b' }
                return (
                  <tr key={l.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap text-xs">{l.date}</td>
                    <td className="px-4 py-3">
                      <span style={{
                        padding: '2px 8px', borderRadius: 4, fontSize: 11,
                        fontWeight: 600, background: s.bg, color: s.color,
                      }}>
                        {l.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-700 text-xs">{l.target_email}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{l.details}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{l.ip}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
