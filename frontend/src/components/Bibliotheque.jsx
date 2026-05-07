import { useState, useEffect } from 'react'

const MATIERES = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']
const NIVEAUX  = ['6e', '5e', '4e', '3e', '2nde', '1ère', 'Terminale', 'Supérieur']

export default function Bibliotheque({ onCharger, sessionMatiere, sessionNiveau }) {
  const [matiere, setMatiere] = useState(sessionMatiere || '')
  const [niveau,  setNiveau]  = useState('')
  const [activites, setActivites] = useState([])
  const [loading, setLoading]     = useState(true)
  const [hovered, setHovered]     = useState(null)

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams()
    if (matiere) params.set('matiere', matiere)
    if (niveau)  params.set('niveau',  niveau)
    fetch(`/api/bibliotheque?${params}`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => { setActivites(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [matiere, niveau])

  const labelFiltre = [matiere, niveau].filter(Boolean).join(', ') || 'Toutes les activités'

  return (
    <div className="flex flex-col gap-3 w-full">

      {/* En-tête + filtres */}
      <div className="flex flex-col gap-2">
        <div className="flex items-baseline gap-3">
          <h2 className="text-base font-semibold text-gray-800">Bibliothèque</h2>
          {!loading && (
            <span style={{ fontSize: 12, color: '#6b7280', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '1px 10px' }}>
              {activites.length} activité{activites.length > 1 ? 's' : ''}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span className="text-xs text-gray-500" style={{ fontWeight: 500 }}>
            Activités — <span style={{ color: '#1e293b' }}>{labelFiltre}</span>
          </span>
          <div style={{ display: 'flex', gap: 6, marginLeft: 'auto' }}>
            <select
              value={matiere}
              onChange={e => setMatiere(e.target.value)}
              title="Filtrer par matière"
              className="border border-gray-200 rounded px-2 py-1 text-xs bg-white text-gray-600"
            >
              <option value="">Toutes les matières</option>
              {MATIERES.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
            <select
              value={niveau}
              onChange={e => setNiveau(e.target.value)}
              title="Filtrer par niveau de classe"
              className="border border-gray-200 rounded px-2 py-1 text-xs bg-white text-gray-600"
            >
              <option value="">Tous les niveaux</option>
              {NIVEAUX.map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
        </div>

        <p className="text-xs text-gray-400">
          Activités partagées par vos collègues — cliquez "Utiliser" pour la charger comme point de départ.
        </p>
      </div>

      {loading && (
        <p className="text-sm text-gray-400 py-4">Chargement…</p>
      )}

      {!loading && activites.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">
            Aucune activité partagée{matiere || niveau ? ` pour ${labelFiltre}` : ''}.
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Depuis "Mes activités", cliquez sur "Partager" pour rendre une activité visible ici.
          </p>
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
                    <span className="text-sm font-semibold text-gray-800 truncate">
                      {a.objet ? a.objet.replace(/^\[Exemple\]\s*/, '') : a.activite_label}
                    </span>
                    {a.partagee_par === 'Équipe A-SCHOOL' && (
                      <span style={{ fontSize: 10, fontWeight: 600, color: '#7c3aed', background: '#f5f3ff', border: '1px solid #ddd6fe', borderRadius: 99, padding: '1px 7px', flexShrink: 0 }}>
                        Exemple
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 flex-wrap mt-0.5">
                    <span className="text-xs text-gray-400">{a.activite_label}</span>
                    <span className="text-xs text-gray-400">· {a.niveau}</span>
                    {a.sous_type && <span className="text-xs text-gray-400">· {a.sous_type}</span>}
                    {a.nb && <span className="text-xs text-gray-400">· {a.nb} questions</span>}
                    <span className="text-xs text-gray-400">
                      · {a.avec_correction ? 'Avec correction' : 'Sans correction'}
                    </span>
                  </div>
                  {!a.objet && (
                    <p className="text-xs text-gray-400 mt-0.5 truncate italic">{a.apercu}</p>
                  )}
                  <p className="text-xs mt-0.5" style={{ color: '#94a3b8' }}>
                    Partagé par <span style={{ color: '#64748b', fontWeight: 500 }}>{a.partagee_par}</span>
                    {a.matiere && <> · {a.matiere}</>}
                  </p>
                </div>
                <button
                  onClick={() => onCharger(a)}
                  title="Charger cette activité comme point de départ"
                  className="btn-primary shrink-0"
                  style={{ opacity: hovered === a.id ? 1 : 0, transition: 'opacity 0.15s' }}
                >
                  Utiliser
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
