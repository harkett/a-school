import { useEffect, useState } from 'react'

const ETOILES = r => '★'.repeat(r) + '☆'.repeat(5 - r)
const COULEUR = { 5: '#16a34a', 4: '#65a30d', 3: '#ca8a04', 2: '#ea580c', 1: '#dc2626' }

export default function AdminFeedbacks() {
  const [items, setItems]   = useState(null)
  const [erreur, setErreur] = useState(null)
  const [onglet, setOnglet] = useState('notations') // notations | feedbacks

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
              {/* Stats CSAT */}
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

              {/* Distribution */}
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

              {/* Liste */}
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
          {feedbacks.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400 text-sm">
              Aucun feedback reçu pour le moment.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {feedbacks.map(f => (
                <div key={f.id} className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <div className="flex items-center gap-3">
                      {f.category && (
                        <span className="text-xs rounded px-2 py-0.5" style={{ background: '#eff6ff', color: '#1d4ed8' }}>
                          {f.category}
                        </span>
                      )}
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-xs text-gray-400">{f.date}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{f.email}</div>
                    </div>
                  </div>
                  <p className="text-sm text-gray-700 leading-relaxed">{f.message}</p>
                </div>
              ))}
            </div>
          )}
        </>
      )}

    </div>
  )
}
