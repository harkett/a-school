import { useEffect, useState } from 'react'

const ETOILES = r => '★'.repeat(r) + '☆'.repeat(5 - r)
const COULEUR = { 5: '#16a34a', 4: '#65a30d', 3: '#ca8a04', 2: '#ea580c', 1: '#dc2626' }

const STATUTS = [
  { id: 'nouveau',  label: 'Nouveau',   bg: '#dbeafe', color: '#1d4ed8' },
  { id: 'en_cours', label: 'En cours',  bg: '#ffedd5', color: '#c2410c' },
  { id: 'traite',   label: 'Traité',    bg: '#dcfce7', color: '#15803d' },
  { id: 'archive',  label: 'Archivé',   bg: '#f3f4f6', color: '#6b7280' },
]

function statutInfo(id) {
  return STATUTS.find(s => s.id === id) || STATUTS[0]
}

const TRANSITIONS = {
  nouveau:  ['en_cours'],
  en_cours: ['traite'],
  traite:   ['en_cours', 'archive'],
  archive:  ['traite'],
}

function labelTransition(current, target) {
  if (current === 'archive' && target === 'traite') return 'Désarchiver'
  if (target === 'archive') return 'Archiver'
  return statutInfo(target).label
}

const FILTRES_FB = ['tous', ...STATUTS.map(s => s.id)]
const FILTRES_LABELS = { tous: 'Tous', nouveau: 'Nouveau', en_cours: 'En cours', traite: 'Traité', archive: 'Archivé' }

export default function AdminFeedbacks() {
  const [items, setItems]   = useState(null)
  const [erreur, setErreur] = useState(null)
  const [onglet, setOnglet] = useState('notations')
  const [filtre, setFiltre] = useState('tous')

  useEffect(() => {
    fetch('/api/admin/feedbacks', { credentials: 'include' })
      .then(r => r.json())
      .then(setItems)
      .catch(() => setErreur('Impossible de charger les données.'))
  }, [])

  if (erreur) return <p className="text-red-600 text-sm">{erreur}</p>
  if (!items)  return <p className="text-gray-400 text-sm">Chargement…</p>

  const notations = items.filter(f => f.type === 'notation' && f.rating > 0)
  const feedbacks = items.filter(f => f.type !== 'notation')

  const feedbacksFiltres = filtre === 'tous'
    ? feedbacks
    : feedbacks.filter(f => (f.statut || 'nouveau') === filtre)

  async function changerStatut(id, statut) {
    await fetch(`/api/admin/feedbacks/${id}/statut`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ statut }),
    })
    setItems(prev => prev.map(f => f.id === id ? { ...f, statut } : f))
  }

  const moyenne = notations.length
    ? (notations.reduce((s, f) => s + f.rating, 0) / notations.length).toFixed(1)
    : '—'
  const csat = notations.length
    ? Math.round((notations.filter(f => f.rating >= 4).length / notations.length) * 100)
    : '—'

  const parNote = [5, 4, 3, 2, 1].map(n => ({
    note: n,
    count: notations.filter(f => f.rating === n).length,
  }))

  const tabStyle = active => ({
    padding: '7px 18px', borderRadius: 6, fontSize: 13, fontWeight: active ? 600 : 400,
    cursor: 'pointer', border: 'none',
    background: active ? 'var(--bleu)' : 'white',
    color: active ? 'white' : '#6b7280',
    boxShadow: active ? 'none' : 'inset 0 0 0 1px #e5e7eb',
  })

  const filtreStyle = active => ({
    padding: '4px 12px', fontSize: '12px', borderRadius: '4px', border: '1px solid',
    cursor: 'pointer', fontWeight: active ? 600 : 400,
    background: active ? '#1e40af' : '#fff',
    color: active ? '#fff' : '#6b7280',
    borderColor: active ? '#1e40af' : '#d1d5db',
  })

  return (
    <div className="flex flex-col gap-6">

      <h2 className="text-base font-semibold text-gray-800">Retours utilisateurs</h2>

      {/* Onglets */}
      <div className="flex gap-2">
        <button style={tabStyle(onglet === 'notations')} onClick={() => setOnglet('notations')}>
          Notations ({notations.length})
        </button>
        <button style={tabStyle(onglet === 'feedbacks')} onClick={() => setOnglet('feedbacks')}>
          Feedbacks ({feedbacks.length})
        </button>
      </div>

      {/* ── NOTATIONS ── */}
      {onglet === 'notations' && (
        <>
          {notations.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400 text-sm">
              Aucune notation reçue pour le moment.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
                  <div className="text-2xl font-bold" style={{ color: 'var(--bleu)' }}>{notations.length}</div>
                  <div className="text-xs text-gray-400 mt-1">Notations reçues</div>
                </div>
                <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
                  <div className="text-2xl font-bold" style={{ color: '#ca8a04' }}>{moyenne}<span className="text-sm font-normal text-gray-400">/5</span></div>
                  <div className="text-xs text-gray-400 mt-1">Note moyenne</div>
                </div>
                <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
                  <div className="text-2xl font-bold" style={{ color: '#16a34a' }}>{csat}<span className="text-sm font-normal text-gray-400">%</span></div>
                  <div className="text-xs text-gray-400 mt-1">CSAT (4-5 ★)</div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <p className="text-xs font-medium text-gray-500 mb-3">Répartition des notes</p>
                <div className="flex flex-col gap-2">
                  {parNote.map(({ note, count }) => {
                    const pct = notations.length ? Math.round((count / notations.length) * 100) : 0
                    return (
                      <div key={note} className="flex items-center gap-3">
                        <span className="text-xs w-6 text-right text-gray-500">{note}★</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-2">
                          <div className="h-2 rounded-full transition-all" style={{ width: `${pct}%`, background: COULEUR[note] }} />
                        </div>
                        <span className="text-xs text-gray-400 w-8">{count}</span>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="flex flex-col gap-3">
                {notations.map(f => (
                  <div key={f.id} className="bg-white rounded-xl border border-gray-200 p-5">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <span style={{ color: COULEUR[f.rating], fontSize: 18 }}>{ETOILES(f.rating)}</span>
                      <div className="text-right flex-shrink-0">
                        <div className="text-xs text-gray-400">{f.date}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{f.email}</div>
                      </div>
                    </div>
                    {f.message && f.message !== '—' && (
                      <p className="text-sm text-gray-700 leading-relaxed">{f.message}</p>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}

      {/* ── FEEDBACKS ── */}
      {onglet === 'feedbacks' && (
        <>
          {/* Filtres statut */}
          <div className="flex items-center gap-2 flex-wrap">
            {FILTRES_FB.map(f => (
              <button
                key={f}
                onClick={() => setFiltre(f)}
                title={`Filtrer : ${FILTRES_LABELS[f]}`}
                style={filtreStyle(filtre === f)}
              >
                {FILTRES_LABELS[f]}
                {f !== 'tous' && (
                  <span style={{ marginLeft: 6, opacity: 0.7 }}>
                    ({feedbacks.filter(fb => (fb.statut || 'nouveau') === f).length})
                  </span>
                )}
              </button>
            ))}
            {filtre !== 'tous' && (
              <span className="text-xs text-gray-400 ml-1">
                {feedbacksFiltres.length} / {feedbacks.length}
              </span>
            )}
          </div>

          {feedbacksFiltres.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400 text-sm">
              Aucun feedback dans cette catégorie.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {feedbacksFiltres.map(f => {
                const st = statutInfo(f.statut || 'nouveau')
                return (
                  <div key={f.id} className="bg-white rounded-xl border border-gray-200 p-5">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        {f.category && (
                          <span className="text-xs rounded px-2 py-0.5" style={{ background: '#eff6ff', color: '#1d4ed8' }}>
                            {f.category}
                          </span>
                        )}
                        <span className="text-xs rounded px-2 py-0.5 font-medium" style={{ background: st.bg, color: st.color }}>
                          {st.label}
                        </span>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <div className="text-xs text-gray-400">{f.date}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{f.email}</div>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed mb-3">{f.message}</p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400">Changer le statut :</span>
                      {(TRANSITIONS[f.statut || 'nouveau'] || []).map(targetId => {
                        const s = statutInfo(targetId)
                        const label = labelTransition(f.statut || 'nouveau', targetId)
                        return (
                          <button
                            key={targetId}
                            onClick={() => changerStatut(f.id, targetId)}
                            title={label}
                            style={{
                              padding: '2px 10px', fontSize: '11px', borderRadius: '4px',
                              border: `1px solid ${s.color}`, cursor: 'pointer',
                              background: '#fff', color: s.color,
                            }}
                          >
                            {label}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}

    </div>
  )
}
