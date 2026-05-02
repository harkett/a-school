import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

export default function AdminSessions() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading]   = useState(true)
  const [forcing, setForcing]   = useState(null)
  const navigate = useNavigate()

  const load = useCallback(() => {
    fetch('/api/admin/sessions', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        return r.json()
      })
      .then(data => { if (data) setSessions(data) })
      .finally(() => setLoading(false))
  }, [navigate])

  useEffect(() => {
    load()
    const id = setInterval(load, 30000)
    return () => clearInterval(id)
  }, [load])

  async function forceLogout(id, email) {
    if (!confirm(`Déconnecter ${email} ?`)) return
    setForcing(id)
    await fetch(`/api/admin/force-logout/${id}`, { method: 'POST', credentials: 'include' })
    setForcing(null)
    load()
  }

  const online  = sessions.filter(s => s.is_online).length
  const offline = sessions.filter(s => !s.is_online).length

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">
          Sessions actives
          <span className="ml-2 text-xs font-normal text-gray-400">
            ({sessions.length} session{sessions.length !== 1 ? 's' : ''} — refresh auto 30s)
          </span>
        </h2>
        <div className="flex gap-2">
          <span style={{ padding: '3px 10px', borderRadius: 99, fontSize: 12, background: '#dcfce7', color: '#15803d', fontWeight: 600 }}>
            ● {online} en ligne
          </span>
          <span style={{ padding: '3px 10px', borderRadius: 99, fontSize: 12, background: '#f1f5f9', color: '#94a3b8' }}>
            ○ {offline} inactif{offline !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {sessions.length === 0 ? (
        <p className="text-sm text-gray-400">Aucune session active — les sessions apparaissent dès qu'un prof se connecte.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-4 py-3 font-medium">Statut</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Navigateur / OS</th>
                <th className="px-4 py-3 font-medium">IP</th>
                <th className="px-4 py-3 font-medium">Connexion</th>
                <th className="px-4 py-3 font-medium">Vu à</th>
                <th className="px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sessions.map(s => (
                <tr key={s.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: 5,
                      fontSize: 12, fontWeight: 600,
                      color: s.is_online ? '#15803d' : '#94a3b8',
                    }}>
                      {s.is_online ? '●' : '○'} {s.is_online ? 'En ligne' : 'Inactif'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-800">{s.email}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    <div>{s.browser}</div>
                    <div className="text-gray-400">{s.os} · {s.device}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{s.ip}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">{s.login_at}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">{s.last_seen}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => forceLogout(s.id, s.email)}
                      disabled={forcing === s.id}
                      title={`Déconnecter ${s.email} immédiatement`}
                      style={{
                        padding: '3px 10px', fontSize: 11, borderRadius: 4,
                        border: '1px solid #fca5a5', cursor: 'pointer',
                        background: forcing === s.id ? '#f1f5f9' : '#fff',
                        color: forcing === s.id ? '#94a3b8' : '#dc2626',
                      }}
                    >
                      {forcing === s.id ? '…' : 'Déconnecter'}
                    </button>
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
