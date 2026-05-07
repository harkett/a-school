import { useState, useEffect } from 'react'

const MATIERES = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']
const NIVEAUX  = ['6e', '5e', '4e', '3e', '2nde', '1ère', 'Terminale', 'Supérieur']

const IconShare = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
  </svg>
)

export default function MesActivites({ onCharger, sessionMatiere, sessionNiveau }) {
  const [activites, setActivites] = useState([])
  const [loading, setLoading]     = useState(true)
  const [hovered, setHovered]     = useState(null)
  const [toggling, setToggling]   = useState(null)
  const [matiere, setMatiere]     = useState(sessionMatiere || '')
  const [niveau,  setNiveau]      = useState(sessionNiveau  || '')

  useEffect(() => {
    fetch('/api/mes-activites', { credentials: 'include' })
      .then(r => r.json())
      .then(data => { setActivites(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  async function togglePartage(id, newValue) {
    setToggling(id)
    try {
      const res = await fetch(`/api/mes-activites/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ partagee: newValue }),
      })
      if (res.ok) {
        setActivites(prev => prev.map(a => a.id === id ? { ...a, partagee: newValue } : a))
      }
    } finally {
      setToggling(null)
    }
  }

  const filtered = activites.filter(a => {
    if (matiere && a.matiere !== matiere) return false
    if (niveau  && a.niveau  !== niveau)  return false
    return true
  })

  const labelFiltre = [matiere, niveau].filter(Boolean).join(', ') || 'Toutes les activités'

  return (
    <div className="flex flex-col gap-3 w-full">

      {/* En-tête + filtres */}
      <div className="flex flex-col gap-2">
        <div className="flex items-baseline gap-3">
          <h2 className="text-base font-semibold text-gray-800">Mes activités</h2>
          {!loading && (
            <span style={{ fontSize: 12, color: '#6b7280', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '1px 10px' }}>
              {filtered.length} activité{filtered.length > 1 ? 's' : ''}
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

      {!loading && activites.length > 0 && filtered.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune activité pour {labelFiltre}.</p>
          <p className="text-xs text-gray-400 mt-1">Modifiez les filtres pour voir d'autres activités.</p>
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          {filtered.map((a, i) => (
            <div
              key={a.id}
              onMouseEnter={() => setHovered(a.id)}
              onMouseLeave={() => setHovered(null)}
              style={{
                borderBottom: i < filtered.length - 1 ? '1px solid #e5e7eb' : 'none',
                background: hovered === a.id ? '#f3f4f6' : 'white',
                transition: 'background 0.15s',
              }}
            >
              <div className="flex items-center gap-3 px-5 py-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-gray-800 truncate">
                      {a.objet || a.activite_label}
                    </span>
                    {a.partagee && (
                      <span style={{ fontSize: 11, color: 'var(--bleu)', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 99, padding: '1px 8px', flexShrink: 0 }}>
                        Partagé
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
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => togglePartage(a.id, !a.partagee)}
                    disabled={toggling === a.id}
                    title={a.partagee ? 'Retirer de la bibliothèque partagée' : 'Partager cette activité avec vos collègues'}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 4,
                      background: 'none',
                      border: '1px solid',
                      borderColor: a.partagee ? 'var(--bleu)' : '#e5e7eb',
                      borderRadius: 6,
                      padding: '4px 8px',
                      cursor: toggling === a.id ? 'wait' : 'pointer',
                      color: a.partagee ? 'var(--bleu)' : '#9ca3af',
                      fontSize: 11,
                      fontWeight: a.partagee ? 500 : 400,
                      opacity: hovered === a.id || a.partagee ? 1 : 0.35,
                      transition: 'opacity 0.15s, color 0.15s, border-color 0.15s',
                    }}
                  >
                    <IconShare />
                    {a.partagee ? 'Partagé' : 'Partager'}
                  </button>

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
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
