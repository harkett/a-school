import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

export default function AdminProgrammes() {
  const [data, setData]     = useState(null)   // { cycles, matieres, paires }
  const [msg, setMsg]       = useState(null)
  const [erreur, setErreur] = useState(null)
  const [selectedCycleId, setSelectedCycleId] = useState(null)  // id du cycle ouvert à droite

  function flash(text, isErr = false) {
    if (isErr) setErreur(text); else setMsg(text)
    setTimeout(() => { setMsg(null); setErreur(null) }, 3500)
  }

  useEffect(() => {
    fetch('/api/admin/programmes', { credentials: 'include' })
      .then(r => r.json())
      .then(d => {
        setData(d)
        if (d.cycles && d.cycles.length) setSelectedCycleId(d.cycles[0].id)
      })
      .catch(() => flash('Impossible de charger les programmes.', true))
  }, [])

  function isActif(matiere_id, niveau_id) {
    const p = data.paires.find(p => p.matiere_id === matiere_id && p.niveau_id === niveau_id)
    return !!(p && p.actif)
  }

  // Bascule optimiste AVEC rollback : si le PATCH echoue, la case revient a l'etat reel.
  async function togglePaire(matiere_id, niveau_id, current) {
    const newActif = !current
    const prev = data
    setData(d => {
      const paires = [...d.paires]
      const i = paires.findIndex(p => p.matiere_id === matiere_id && p.niveau_id === niveau_id)
      if (i >= 0) paires[i] = { ...paires[i], actif: newActif }
      else paires.push({ matiere_id, niveau_id, actif: newActif })
      return { ...d, paires }
    })
    try {
      const r = await fetchWithTimeout('/api/admin/programmes/paire', {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ matiere_id, niveau_id, actif: newActif }),
      }, TIMEOUT_STD)
      if (!r.ok) throw new Error()
    } catch {
      setData(prev)  // rollback : la case revient a son etat reel
      flash('Échec de l’enregistrement — la case est revenue à son état réel.', true)
    }
  }

  if (!data) return <p className="text-gray-400 text-sm">Chargement…</p>

  const selected = data.cycles.find(c => c.id === selectedCycleId) || null

  function ouvrirCycle(id) {
    setSelectedCycleId(id)
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-base font-semibold text-gray-800">Programmes</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Choisissez un cycle à gauche : son détail s’ouvre à droite. Cochez les paires matière × niveau — décocher <strong>désactive</strong> (l’historique reste intact).
        </p>
      </div>

      {msg && <div style={{ padding: '8px 12px', background: '#dcfce7', color: '#166534', borderRadius: 6, fontSize: 12 }}>{msg}</div>}
      {erreur && <div style={{ padding: '8px 12px', background: '#fee2e2', color: '#991b1b', borderRadius: 6, fontSize: 12 }}>{erreur}</div>}

      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>

        {/* ── Colonne gauche : liste verticale des cycles ── */}
        <div style={{ width: 220, flexShrink: 0 }}>
          <div className="bg-white rounded-lg border border-gray-200" style={{ overflow: 'hidden' }}>
            {data.cycles.map(cycle => {
              const active = cycle.id === selectedCycleId
              return (
                <button
                  key={cycle.id}
                  onClick={() => ouvrirCycle(cycle.id)}
                  title={`Ouvrir « ${cycle.nom} »`}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left',
                    padding: '10px 14px', fontSize: 13, cursor: 'pointer',
                    border: 'none', borderBottom: '1px solid #f1f5f9',
                    borderLeft: active ? '3px solid #A63045' : '3px solid transparent',
                    background: active ? '#fdf2f4' : 'white',
                    color: active ? '#A63045' : '#374151',
                    fontWeight: active ? 600 : 400,
                  }}
                >
                  {cycle.nom}
                  <span style={{ display: 'block', fontSize: 10, marginTop: 2, color: active ? '#A63045' : '#9ca3af' }}>
                    {cycle.niveaux.length} niveau{cycle.niveaux.length > 1 ? 'x' : ''}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* ── Colonne droite : détail du cycle sélectionné ── */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selected ? (
            <p className="text-sm text-gray-400">Sélectionnez un cycle à gauche.</p>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">

              {/* En-tête : nom du cycle */}
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ fontSize: 14, fontWeight: 700, color: '#1a3a6e' }}>{selected.nom}</span>
              </div>

              {selected.niveaux.length === 0 ? (
                <div style={{ padding: '16px', fontSize: 12, color: '#94a3b8' }}>
                  Aucun niveau dans ce cycle.
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left', padding: '8px 12px', color: '#64748b', fontWeight: 600, borderBottom: '1px solid #f1f5f9', position: 'sticky', left: 0, background: '#fff' }}>Matière</th>
                        {selected.niveaux.map(n => (
                          <th key={n.id} style={{ padding: '8px 10px', color: '#1e293b', fontWeight: 600, borderBottom: '1px solid #f1f5f9', textAlign: 'center', whiteSpace: 'nowrap' }}>{n.nom}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.matieres.map(m => (
                        <tr key={m.id} style={{ opacity: m.actif ? 1 : 0.45 }}>
                          <td style={{ padding: '7px 12px', color: '#374151', borderBottom: '1px solid #f8fafc', whiteSpace: 'nowrap', position: 'sticky', left: 0, background: '#fff' }}>
                            {m.nom}{!m.actif && <span style={{ marginLeft: 6, fontSize: 10, color: '#94a3b8' }}>(inactive)</span>}
                          </td>
                          {selected.niveaux.map(n => {
                            const actif = isActif(m.id, n.id)
                            return (
                              <td key={n.id} style={{ textAlign: 'center', padding: '6px', borderBottom: '1px solid #f8fafc' }}>
                                <input
                                  type="checkbox"
                                  checked={actif}
                                  disabled={!m.actif}
                                  onChange={() => togglePaire(m.id, n.id, actif)}
                                  title={m.actif
                                    ? `${m.nom} en ${n.nom} : ${actif ? 'enseigné (décocher pour retirer)' : 'non enseigné (cocher pour ajouter)'}`
                                    : `${m.nom} est inactive (édition en T3)`}
                                  style={{ cursor: m.actif ? 'pointer' : 'not-allowed', width: 15, height: 15 }}
                                />
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
          )}
        </div>
      </div>
    </div>
  )
}
