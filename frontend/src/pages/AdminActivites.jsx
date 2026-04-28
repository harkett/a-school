import { useEffect, useState } from 'react'

const ABREV = {
  'Français':               'FR',
  'Histoire-Géographie':    'HG',
  'Philosophie':            'Philo',
  'Mathématiques':          'Maths',
  'SVT':                    'SVT',
  'Physique-Chimie':        'PC',
  'Technologie':            'Techno',
  'SES':                    'SES',
  'NSI':                    'NSI',
  'Langues Vivantes (LV)':  'LV',
  'Arts':                   'Arts',
  'EPS':                    'EPS',
}

export default function AdminActivites() {
  const [data, setData]         = useState(null)
  const [erreur, setErreur]     = useState(null)
  const [vue, setVue]           = useState('matiere')   // 'matiere' | 'matrice'
  const [ouvert, setOuvert]     = useState(null)

  useEffect(() => {
    fetch('/api/admin/activites', { credentials: 'include' })
      .then(r => r.json())
      .then(setData)
      .catch(() => setErreur('Impossible de charger les activités.'))
  }, [])

  if (erreur) return <p className="text-red-600 text-sm">{erreur}</p>
  if (!data)  return <p className="text-gray-400 text-sm">Chargement…</p>

  const { stats, matieres, par_matiere, matrice } = data

  return (
    <div className="flex flex-col gap-6">

      {/* Titre */}
      <div>
        <h2 className="text-base font-semibold text-gray-800">Activités pédagogiques</h2>
        <p className="text-xs text-gray-400 mt-0.5">Générées depuis MATRICE_ACTIVITES_ASCHOOL.md</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Matières',           val: stats.nb_matieres },
          { label: 'Activités uniques',  val: stats.nb_activites_uniques },
          { label: 'Entrées au total',   val: stats.nb_entrees },
        ].map(({ label, val }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold" style={{ color: 'var(--bleu)' }}>{val}</div>
            <div className="text-xs text-gray-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Onglets */}
      <div className="flex gap-2">
        {[
          { id: 'matiere', label: 'Par matière' },
          { id: 'matrice', label: 'Matrice globale' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setVue(tab.id)}
            className="px-4 py-1.5 rounded-lg text-xs font-medium transition-colors"
            style={
              vue === tab.id
                ? { background: 'var(--bleu)', color: 'white' }
                : { background: '#f1f5f9', color: '#6b7280' }
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Vue accordéon */}
      {vue === 'matiere' && (
        <div className="flex flex-col gap-2">
          {matieres.map(matiere => {
            const activites = par_matiere[matiere] || []
            const isOpen = ouvert === matiere
            return (
              <div key={matiere} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <button
                  onClick={() => setOuvert(isOpen ? null : matiere)}
                  className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-gray-800">{matiere}</span>
                    <span className="text-xs text-gray-400 bg-gray-100 rounded px-2 py-0.5">
                      {activites.length} activités
                    </span>
                  </div>
                  <span className="text-gray-400 text-xs">{isOpen ? '▲' : '▼'}</span>
                </button>

                {isOpen && (
                  <div className="border-t border-gray-100 px-5 py-4 flex flex-col gap-3">
                    {activites.map(act => (
                      <div key={act.key}>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-medium text-gray-700">{act.nom}</span>
                          {act.nb_sous_types === 0 && (
                            <span className="text-xs text-gray-300 italic">aucun sous-type</span>
                          )}
                        </div>
                        {act.sous_types.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {act.sous_types.map(st => (
                              <span
                                key={st}
                                className="text-xs rounded px-2 py-0.5"
                                style={{ background: '#eff6ff', color: '#1d4ed8' }}
                              >
                                {st}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Vue matrice */}
      {vue === 'matrice' && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left px-4 py-3 font-medium text-gray-500 bg-gray-50 min-w-[220px]">
                  Activité
                </th>
                {matieres.map(m => (
                  <th
                    key={m}
                    className="px-2 py-3 font-medium text-gray-500 bg-gray-50 text-center whitespace-nowrap"
                    title={m}
                  >
                    {ABREV[m] || m}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrice.map((row, i) => (
                <tr
                  key={row.activite}
                  className="border-b border-gray-100"
                  style={{ background: i % 2 === 0 ? 'white' : '#fafafa' }}
                >
                  <td className="px-4 py-2 text-gray-700 font-medium">{row.activite}</td>
                  {matieres.map(m => {
                    const ok = row.matieres.includes(m)
                    return (
                      <td key={m} className="px-2 py-2 text-center">
                        {ok
                          ? <span style={{ color: '#16a34a', fontWeight: 700 }}>✓</span>
                          : <span style={{ color: '#d1d5db' }}>—</span>
                        }
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
