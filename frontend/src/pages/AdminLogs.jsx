import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const FILTRES = [
  { id: 'tous',         label: 'Tous' },
  { id: 'signup',       label: 'Inscriptions' },
  { id: 'login',        label: 'Connexions' },
]

export default function AdminLogs() {
  const [logs, setLogs]       = useState([])
  const [loading, setLoading] = useState(true)
  const [filtre, setFiltre]   = useState('tous')
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

  const logsFiltres = filtre === 'tous' ? logs : logs.filter(l => l.action === filtre)

  return (
    <div>
      <div className="flex items-center justify-between mb-4 gap-4 flex-wrap">
        <h2 className="text-sm font-semibold text-gray-700">
          Historique des connexions
          <span className="ml-2 text-xs font-normal text-gray-400">({logsFiltres.length} / {logs.length} entrées)</span>
        </h2>
        <div className="flex gap-1">
          {FILTRES.map(f => (
            <button
              key={f.id}
              onClick={() => setFiltre(f.id)}
              title={`Afficher : ${f.label}`}
              style={{
                padding: '4px 12px',
                fontSize: '12px',
                borderRadius: '4px',
                border: '1px solid',
                cursor: 'pointer',
                fontWeight: filtre === f.id ? 600 : 400,
                background: filtre === f.id ? '#1e40af' : '#fff',
                color: filtre === f.id ? '#fff' : '#6b7280',
                borderColor: filtre === f.id ? '#1e40af' : '#d1d5db',
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {logsFiltres.length === 0 ? (
        <p className="text-sm text-gray-400">Aucune entrée.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Matière</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logsFiltres.map(l => (
                <tr key={l.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{l.date}</td>
                  <td className="px-4 py-3 text-gray-800">{l.email}</td>
                  <td className="px-4 py-3 text-gray-600">{l.subject}</td>
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
