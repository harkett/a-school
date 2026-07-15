import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

// Lecture seule : affiche le contenu de la table `cycles`. Get direct à chaque ouverture.
export default function AdminCycles() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/cycles', { credentials: 'include' })
      .then(r => { if (r.status === 401) { navigate('/admin/login'); return null } return r.json() })
      .then(data => { if (data) setRows(data.cycles || []) })
      .finally(() => setLoading(false))
  }, [navigate])

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  const th = { padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }
  const td = { padding: '10px 16px', color: '#1e293b' }

  return (
    <div>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">Cycles</h2>
        <span className="text-xs text-gray-400">{rows.length} cycle{rows.length > 1 ? 's' : ''}</span>
      </div>

      <p className="text-xs text-gray-500 mb-3" style={{ maxWidth: 720, lineHeight: 1.5 }}>
        Contenu de la table <code>cycles</code>, lu directement en base. Lecture seule.
      </p>

      {rows.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}><p className="text-sm">La table est vide.</p></div>
      ) : (
        <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                <th style={th}>id</th>
                <th style={th}>Nom</th>
                <th style={th}>Ordre</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c, i) => (
                <tr key={c.id} style={{ borderBottom: i < rows.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                  <td style={{ ...td, color: '#94a3b8', fontFamily: 'monospace' }}>{c.id}</td>
                  <td style={{ ...td, fontWeight: 600 }}>{c.nom}</td>
                  <td style={td}>{c.ordre}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
