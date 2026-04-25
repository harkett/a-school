import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function AdminLogs() {
  const [logs, setLogs]       = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/logs', { credentials: 'include' })
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
        Historique des connexions
        <span className="ml-2 text-xs font-normal text-gray-400">({logs.length} entrées)</span>
      </h2>

      {logs.length === 0 ? (
        <p className="text-sm text-gray-400">Aucune entrée.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map(l => (
                <tr key={l.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{l.date}</td>
                  <td className="px-4 py-3 text-gray-800">{l.email}</td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
                      style={
                        l.action === 'signup'
                          ? { background: '#dcfce7', color: '#15803d' }
                          : { background: '#dbeafe', color: '#1d4ed8' }
                      }
                    >
                      {l.action === 'signup' ? 'Inscription' : 'Connexion'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{l.ip || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
