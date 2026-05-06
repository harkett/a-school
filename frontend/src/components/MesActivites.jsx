import { useState, useEffect } from 'react'

export default function MesActivites({ onCharger }) {
  const [activites, setActivites] = useState([])
  const [loading, setLoading] = useState(true)
  const [hovered, setHovered] = useState(null)

  useEffect(() => {
    fetch('/api/mes-activites', { credentials: 'include' })
      .then(r => r.json())
      .then(data => { setActivites(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div className="flex flex-col gap-3 w-full">
      <div className="flex items-baseline gap-3 mb-1">
        <h2 className="text-base font-semibold text-gray-800">Mes activités</h2>
        {!loading && activites.length > 0 && (
          <span style={{ fontSize: 12, color: '#6b7280', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '1px 10px' }}>
            {activites.length} activité{activites.length > 1 ? 's' : ''} sauvegardée{activites.length > 1 ? 's' : ''}
          </span>
        )}
      </div>

      {loading && (
        <p className="text-sm text-gray-400 py-4">Chargement…</p>
      )}

      {!loading && activites.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune activité sauvegardée.</p>
          <p className="text-xs text-gray-400 mt-1">Générez une activité depuis l'Accueil pour la retrouver ici.</p>
        </div>
      )}

      {!loading && activites.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          {activites.map((a, i) => (
            <div
              key={a.id}
              onMouseEnter={() => setHovered(a.id)}
              onMouseLeave={() => setHovered(null)}
              style={{
                borderBottom: i < activites.length - 1 ? '1px solid #e5e7eb' : 'none',
                background: hovered === a.id ? '#f3f4f6' : 'white',
                transition: 'background 0.15s',
              }}
            >
              <div className="flex items-center gap-4 px-5 py-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-gray-800">{a.activite_label}</span>
                    <span className="text-xs text-gray-500">{a.niveau}</span>
                    {a.sous_type && (
                      <span className="text-xs text-gray-400">· {a.sous_type}</span>
                    )}
                    {a.nb && (
                      <span className="text-xs text-gray-400">· {a.nb} questions</span>
                    )}
                    <span className="text-xs text-gray-400">
                      · {a.avec_correction ? 'Avec correction' : 'Sans correction'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1 truncate">{a.apercu}</p>
                </div>
                <button
                  onClick={() => onCharger(a)}
                  title="Charger cette activité dans le formulaire"
                  className="btn-primary shrink-0"
                  style={{ opacity: hovered === a.id ? 1 : 0, transition: 'opacity 0.15s' }}
                >
                  Charger
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
