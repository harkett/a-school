import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

export default function AdminProgrammes() {
  const [data, setData]     = useState(null)   // { cycles, matieres, paires }
  const [msg, setMsg]       = useState(null)
  const [erreur, setErreur] = useState(null)
  const [addCycle, setAddCycle] = useState(null)  // cycle.id en cours d'ajout
  const [addNom, setAddNom]     = useState('')

  function flash(text, isErr = false) {
    if (isErr) setErreur(text); else setMsg(text)
    setTimeout(() => { setMsg(null); setErreur(null) }, 3500)
  }

  useEffect(() => {
    fetch('/api/admin/programmes', { credentials: 'include' })
      .then(r => r.json())
      .then(setData)
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

  async function ajouterNiveau(cycle_id) {
    const nom = addNom.trim()
    if (!nom) return
    try {
      const r = await fetchWithTimeout('/api/admin/programmes/niveau', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id, nom }),
      }, TIMEOUT_STD)
      if (!r.ok) throw new Error(r.status === 409 ? 'Ce niveau existe déjà dans ce cycle.' : 'Création impossible.')
      const niv = await r.json()
      setData(d => ({
        ...d,
        cycles: d.cycles.map(c => c.id === cycle_id
          ? { ...c, niveaux: [...c.niveaux, { id: niv.id, nom: niv.nom, ordre: niv.ordre }] }
          : c),
      }))
      setAddCycle(null); setAddNom('')
      flash('Niveau ajouté.')
    } catch (e) {
      flash(e.message || 'Erreur.', true)
    }
  }

  if (!data) return <p className="text-gray-400 text-sm">Chargement…</p>

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-base font-semibold text-gray-800">Programmes</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Le programme officiel : cochez les paires matière × niveau. Décocher <strong>désactive</strong> (l’historique reste intact — rien n’est supprimé).
        </p>
      </div>

      {msg && <div style={{ padding: '8px 12px', background: '#dcfce7', color: '#166534', borderRadius: 6, fontSize: 12 }}>{msg}</div>}
      {erreur && <div style={{ padding: '8px 12px', background: '#fee2e2', color: '#991b1b', borderRadius: 6, fontSize: 12 }}>{erreur}</div>}

      {data.cycles.map(cycle => (
        <div key={cycle.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">

          <div style={{ padding: '12px 16px', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: '#1a3a6e' }}>{cycle.nom}</span>
            {addCycle === cycle.id ? (
              <div style={{ display: 'flex', gap: 6 }}>
                <input
                  autoFocus value={addNom}
                  onChange={e => setAddNom(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') ajouterNiveau(cycle.id)
                    if (e.key === 'Escape') { setAddCycle(null); setAddNom('') }
                  }}
                  placeholder="ex. BTS"
                  style={{ fontSize: 12, padding: '4px 8px', border: '1px solid #e2e8f0', borderRadius: 6, width: 110 }}
                />
                <button onClick={() => ajouterNiveau(cycle.id)} title="Créer ce niveau"
                  style={{ fontSize: 12, padding: '4px 10px', borderRadius: 6, border: 'none', background: '#1a3a6e', color: '#fff', cursor: 'pointer' }}>Ajouter</button>
                <button onClick={() => { setAddCycle(null); setAddNom('') }} title="Annuler"
                  style={{ fontSize: 14, padding: '4px 8px', borderRadius: 6, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#64748b', cursor: 'pointer', lineHeight: 1 }}>×</button>
              </div>
            ) : (
              <button onClick={() => { setAddCycle(cycle.id); setAddNom('') }}
                title="Ajouter un niveau à ce cycle (débloque Supérieur / Crèche, sans programme officiel)"
                style={{ fontSize: 12, padding: '4px 10px', borderRadius: 6, border: '1px solid #bfdbfe', background: '#eff6ff', color: '#1d4ed8', fontWeight: 600, cursor: 'pointer' }}>
                + Niveau
              </button>
            )}
          </div>

          {cycle.niveaux.length === 0 ? (
            <div style={{ padding: '16px', fontSize: 12, color: '#94a3b8' }}>
              Aucun niveau dans ce cycle — ajoutez-en un avec « + Niveau ».
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '8px 12px', color: '#64748b', fontWeight: 600, borderBottom: '1px solid #f1f5f9', position: 'sticky', left: 0, background: '#fff' }}>Matière</th>
                    {cycle.niveaux.map(n => (
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
                      {cycle.niveaux.map(n => {
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
      ))}
    </div>
  )
}
