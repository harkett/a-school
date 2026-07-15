import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

// Lecture seule : affiche le contenu de la table `famille_couples` (les couples famille + niveau ;
// le cycle est dérivé du niveau, non stocké). Sert au contrôle de l'admin. Get direct à chaque
// ouverture — aucune donnée mise en cache côté écran.
export default function AdminFCAutorisees() {
  const [couples, setCouples] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/fc-autorisees', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        return r.json()
      })
      .then(data => { if (data) setCouples(data.couples || []) })
      .finally(() => setLoading(false))
  }, [navigate])

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  const th = { padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }
  const td = { padding: '10px 16px', color: '#1e293b' }

  return (
    <div>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">Famille-Couples</h2>
        <span className="text-xs text-gray-400">{couples.length} couple{couples.length > 1 ? 's' : ''}</span>
      </div>

      <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', borderRadius: 8, padding: '10px 14px', marginBottom: 12, fontSize: 12, lineHeight: 1.5 }}>
        (Cette liste n'est pas figée. Elle est aujourd'hui en lecture seule ; à l'avenir elle sera
        modifiable directement ici — bouton « Ajouter » et gestion complète des famille-couples,
        en respectant bien sûr les contraintes d'intégrité référentielle : un couple déjà utilisé
        ne pourra être ni modifié ni supprimé, seuls les couples non utilisés le seront.)
      </div>

      <p className="text-xs text-gray-500 mb-3" style={{ maxWidth: 720, lineHeight: 1.5 }}>
        Contenu de la table <code>famille_couples</code> — les <strong>famille-couples</strong>
        {' '}(quelle famille à quel niveau ; le cycle est dérivé du niveau, non stocké).
        {' '}Lecture seule, lu directement en base.
      </p>

      {couples.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
          <p className="text-sm">La table est vide.</p>
        </div>
      ) : (
        <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                <th style={th}>id</th>
                <th style={th}>Famille</th>
                <th style={th}>Cycle</th>
                <th style={th}>Niveau</th>
              </tr>
            </thead>
            <tbody>
              {couples.map((c, i) => (
                <tr key={c.id} style={{ borderBottom: i < couples.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                  <td style={{ ...td, color: '#94a3b8', fontFamily: 'monospace' }}>{c.id}</td>
                  <td style={{ ...td, fontWeight: 600 }}>{c.famille || <span style={{ color: '#cbd5e1' }}>famille_id {c.famille_id}</span>}</td>
                  <td style={td}>{c.cycle || <span style={{ color: '#cbd5e1' }}>—</span>}</td>
                  <td style={td}>{c.niveau || <span style={{ color: '#cbd5e1' }}>niveau_id {c.niveau_id}</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
