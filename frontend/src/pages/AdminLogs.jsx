import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const FILTRES = [
  { id: 'tous',        label: 'Tous' },
  { id: 'signup',      label: 'Inscriptions' },
  { id: 'login',       label: 'Connexions' },
  { id: 'admin_login', label: 'Admin' },
]

export default function AdminLogs() {
  const [logs, setLogs]       = useState([])
  const [loading, setLoading] = useState(true)
  const [filtre, setFiltre]   = useState('tous')
  const [filterIp, setFilterIp]     = useState('')
  const [filterEmail, setFilterEmail] = useState('')
  const [sortDir, setSortDir]       = useState('desc')
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

  const logsFiltres = logs
    .filter(l => filtre === 'tous' || l.action === filtre)
    .filter(l => !filterIp    || (l.ip    || '').includes(filterIp))
    .filter(l => !filterEmail || (l.email || '').toLowerCase().includes(filterEmail.toLowerCase()))
    .sort((a, b) => sortDir === 'desc'
      ? b.date.localeCompare(a.date)
      : a.date.localeCompare(b.date)
    )

  return (
    <div>
      <div className="flex items-center justify-between mb-3 gap-4 flex-wrap">
        <h2 className="text-sm font-semibold text-gray-700">
          Historique des connexions
          <span className="ml-2 text-xs font-normal text-gray-400">({logsFiltres.length} / {logs.length} entrées)</span>
        </h2>
        <div className="flex gap-1 flex-wrap">
          {FILTRES.map(f => (
            <button key={f.id} onClick={() => setFiltre(f.id)} title={`Afficher : ${f.label}`}
              style={{ padding: '4px 12px', fontSize: '12px', borderRadius: '4px', border: '1px solid', cursor: 'pointer',
                fontWeight: filtre === f.id ? 600 : 400, background: filtre === f.id ? '#1e40af' : '#fff',
                color: filtre === f.id ? '#fff' : '#6b7280', borderColor: filtre === f.id ? '#1e40af' : '#d1d5db' }}>
              {f.label}
            </button>
          ))}
          <button onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')} title="Inverser l'ordre par date"
            style={{ padding: '4px 12px', fontSize: '12px', borderRadius: '4px', border: '1px solid #d1d5db', cursor: 'pointer', background: '#fff', color: '#6b7280' }}>
            Date {sortDir === 'desc' ? '↓' : '↑'}
          </button>
        </div>
      </div>
      <div className="flex gap-2 mb-3 flex-wrap">
        <input type="text" placeholder="Filtrer par email…" value={filterEmail} onChange={e => setFilterEmail(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm flex-1 min-w-32" />
        <input type="text" placeholder="Filtrer par IP…" value={filterIp} onChange={e => setFilterIp(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm" style={{ width: 140 }} />
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
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                    {new Date(l.date).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="px-4 py-3 text-gray-800">{l.email}</td>
                  <td className="px-4 py-3 text-gray-600">{l.subject}</td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
                      style={
                        l.action === 'signup'
                          ? { background: '#dcfce7', color: '#15803d' }
                          : l.action === 'admin_login'
                          ? { background: '#ffedd5', color: '#c2410c' }
                          : { background: '#dbeafe', color: '#1d4ed8' }
                      }
                    >
                      {l.action === 'signup' ? 'Inscription' : l.action === 'admin_login' ? 'Admin' : 'Connexion'}
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
