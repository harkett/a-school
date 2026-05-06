import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

export default function AdminSessions() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading]   = useState(true)
  const [forcing, setForcing]   = useState(null)
  const [pending, setPending]   = useState(null) // { id, email }
  const [raison, setRaison]     = useState('')
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

  function startLogout(id, email) {
    setPending({ id, email })
    setRaison('')
  }

  async function confirmLogout() {
    setForcing(pending.id)
    await fetch(`/api/admin/force-logout/${pending.id}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raison }),
    })
    setPending(null)
    setRaison('')
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
                <th className="px-4 py-3 font-medium">Connexion</th>
                <th className="px-4 py-3 font-medium">Durée</th>
                <th className="px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sessions.map(s => (
                <tr key={s.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600, color: s.is_online ? '#15803d' : '#94a3b8' }}>
                      {s.is_online ? '●' : '○'} {s.is_online ? 'En ligne' : 'Inactif'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-800">{s.email}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    <div>{s.browser}</div>
                    <div className="text-gray-400">{s.os} · {s.device}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">{s.login_at}</td>
                  <td className="px-4 py-3 text-xs whitespace-nowrap font-medium" style={{ color: s.is_online ? '#15803d' : '#94a3b8' }}>{s.duree}</td>
                  <td className="px-4 py-3" style={{ minWidth: 220 }}>
                    {pending?.id === s.id ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <input
                          type="text"
                          placeholder="Raison (optionnel)"
                          value={raison}
                          onChange={e => setRaison(e.target.value)}
                          onKeyDown={e => e.key === 'Enter' && confirmLogout()}
                          autoFocus
                          style={{ fontSize: 11, border: '1px solid #fca5a5', borderRadius: 4, padding: '3px 8px', outline: 'none', width: '100%' }}
                        />
                        <div style={{ display: 'flex', gap: 4 }}>
                          <button
                            onClick={confirmLogout}
                            disabled={forcing === s.id}
                            title="Confirmer la déconnexion"
                            style={{ flex: 1, padding: '3px 8px', fontSize: 11, borderRadius: 4, border: 'none', cursor: 'pointer', background: '#dc2626', color: '#fff', fontWeight: 600 }}
                          >
                            {forcing === s.id ? '…' : 'Confirmer'}
                          </button>
                          <button
                            onClick={() => setPending(null)}
                            title="Annuler"
                            style={{ padding: '3px 8px', fontSize: 11, borderRadius: 4, border: '1px solid #e2e8f0', cursor: 'pointer', background: '#fff', color: '#64748b' }}
                          >
                            Annuler
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => startLogout(s.id, s.email)}
                        title={`Déconnecter ${s.email} immédiatement`}
                        style={{ padding: '3px 10px', fontSize: 11, borderRadius: 4, border: '1px solid #fca5a5', cursor: 'pointer', background: '#fff', color: '#dc2626' }}
                      >
                        Déconnecter
                      </button>
                    )}
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
