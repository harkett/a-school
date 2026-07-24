import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

export default function AdminProgrammes() {
  const [data, setData]     = useState(null)   // { cycles, matieres, paires }
  const [msg, setMsg]       = useState(null)
  const [erreur, setErreur] = useState(null)
  const [selectedCycleId, setSelectedCycleId] = useState(null)  // id du cycle ouvert à droite
  // Création de cycle / niveau — la SEULE place de l'admin où l'on crée ces entrées
  // (le dépôt de référentiel ne propose que l'existant, en cascade cycle → niveau).
  const [newCycleNom, setNewCycleNom]   = useState('')
  const [newNiveauNom, setNewNiveauNom] = useState('')
  const [ajoutBusy, setAjoutBusy]       = useState(false)

  function flash(text, isErr = false) {
    if (isErr) setErreur(text); else setMsg(text)
    setTimeout(() => { setMsg(null); setErreur(null) }, 3500)
  }

  // (Re)lecture de l'arbre complet en base (get, zéro copie). `garderSelection` = après un ajout,
  // on reste sur le cycle courant (ou on ouvre celui qu'on vient de créer via `ouvrirId`).
  function recharger(ouvrirId = null) {
    return fetch('/api/admin/programmes', { credentials: 'include' })
      .then(r => r.json())
      .then(d => {
        setData(d)
        if (ouvrirId) setSelectedCycleId(ouvrirId)
        else if (!selectedCycleId && d.cycles && d.cycles.length) setSelectedCycleId(d.cycles[0].id)
      })
      .catch(() => flash('Impossible de charger les programmes.', true))
  }

  useEffect(() => { recharger() }, [])  // eslint-disable-line react-hooks/exhaustive-deps

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

  // CREATE encadré (backend : nom requis + unicité) : POST puis relecture de l'arbre en base.
  async function creerCycle() {
    const nom = newCycleNom.trim()
    if (!nom) { flash('Indiquez le nom du cycle.', true); return }
    setAjoutBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/cycles', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nom }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { flash(d.detail || 'Création du cycle impossible.', true); return }
      setNewCycleNom('')
      await recharger(d.id)   // le nouveau cycle s'ouvre à droite
      flash(`Cycle « ${d.nom} » créé.`)
    } catch { flash('Création du cycle impossible (réseau).', true) }
    finally { setAjoutBusy(false) }
  }

  async function creerNiveau() {
    const nom = newNiveauNom.trim()
    if (!nom) { flash('Indiquez le nom du niveau.', true); return }
    if (!selectedCycleId) return
    setAjoutBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/niveaux', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: selectedCycleId, nom }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { flash(d.detail || 'Création du niveau impossible.', true); return }
      setNewNiveauNom('')
      await recharger(selectedCycleId)
      flash(`Niveau « ${d.nom} » créé.`)
    } catch { flash('Création du niveau impossible (réseau).', true) }
    finally { setAjoutBusy(false) }
  }

  if (!data) return <p className="text-gray-400 text-sm">Chargement…</p>

  const selected = data.cycles.find(c => c.id === selectedCycleId) || null

  function ouvrirCycle(id) {
    setSelectedCycleId(id)
  }

  const champAjout = { flex: 1, minWidth: 0, border: '1px solid #d1d5db', borderRadius: 6, padding: '6px 8px', fontSize: 12 }
  const btnAjout = { whiteSpace: 'nowrap', fontSize: 12, fontWeight: 600, padding: '6px 10px', borderRadius: 6,
    border: '1px solid #cbd5e1', background: '#f8fafc', color: '#334155', cursor: ajoutBusy ? 'wait' : 'pointer' }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-base font-semibold text-gray-800">Programmes</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Choisissez un cycle à gauche : son détail s’ouvre à droite. Cochez les paires matière × niveau — décocher <strong>désactive</strong> (l’historique reste intact). Les boutons « + Cycle » et « + Niveau » sont la seule place où l’on crée un cycle ou un niveau.
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
            {/* + Cycle : CREATE encadré (le backend refuse un nom vide ou déjà pris). */}
            <div style={{ display: 'flex', gap: 6, padding: '10px 10px', borderTop: '1px solid #f1f5f9', background: '#f8fafc' }}>
              <input style={champAjout} value={newCycleNom} disabled={ajoutBusy}
                placeholder="Nom du cycle…" title="Nom du nouveau cycle (ex. CAP)"
                onChange={e => setNewCycleNom(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') creerCycle() }} />
              <button type="button" style={btnAjout} onClick={creerCycle} disabled={ajoutBusy}
                title="Créer ce cycle (il apparaît dans la liste et s’ouvre à droite)">+ Cycle</button>
            </div>
          </div>
        </div>

        {/* ── Colonne droite : détail du cycle sélectionné ── */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selected ? (
            <p className="text-sm text-gray-400">Sélectionnez un cycle à gauche.</p>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">

              {/* En-tête : nom du cycle + ajout d'un niveau dans CE cycle */}
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #f1f5f9',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 14, fontWeight: 700, color: '#1a3a6e' }}>{selected.nom}</span>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center', minWidth: 220, flex: '0 1 320px' }}>
                  <input style={champAjout} value={newNiveauNom} disabled={ajoutBusy}
                    placeholder={`Nom du niveau dans « ${selected.nom} »…`}
                    title="Nom du nouveau niveau de ce cycle (ex. CAP Cuisine)"
                    onChange={e => setNewNiveauNom(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') creerNiveau() }} />
                  <button type="button" style={btnAjout} onClick={creerNiveau} disabled={ajoutBusy}
                    title="Créer ce niveau dans le cycle ouvert">+ Niveau</button>
                </div>
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
