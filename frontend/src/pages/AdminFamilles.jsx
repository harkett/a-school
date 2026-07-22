// Page Familles — menu latéral (« + Nouvelle famille » + liste des familles), panneau de droite =
// le builder mis au point dans le Labo (famille → cycles IA → matrice niveaux). Même principe d'écran
// que Référentiels : cliquer une entrée ouvre le panneau correspondant. Get/put, zéro copie (règle 4).
// Le Labo reste intact : on a COPIÉ son contenu ici, on ne l'a pas déplacé.
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchWithTimeout, TIMEOUT_STD, TIMEOUT_LONG } from '../utils/api.js'
import { showError } from '../errorDialog.js'

const btn = (bg, off = false) => ({
  height: 36, padding: '0 16px', borderRadius: 8, border: 'none',
  background: off ? '#e2e8f0' : bg, color: off ? '#94a3b8' : 'white',
  fontSize: 13, fontWeight: 600, cursor: off ? 'not-allowed' : 'pointer',
  display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
})
const champ = { padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: 13, background: 'white' }
const carte = { background: 'white', borderRadius: 12, border: '1px solid #e2e8f0', padding: 18, marginBottom: 16 }
const titre = { fontSize: 15, fontWeight: 700, color: '#1e293b', margin: '0 0 12px' }

export default function AdminFamilles() {
  const [familles, setFamilles] = useState([])       // [{id, nom, description, rejet}]
  const [vue, setVue] = useState('nouvelle')         // 'nouvelle' (création) | id d'une famille (builder)
  const [famNom, setFamNom] = useState('')           // saisie création famille
  const [famDesc, setFamDesc] = useState('')
  const [busy, setBusy] = useState(false)
  // Édition de la description d'une famille existante (crayon)
  const [editDesc, setEditDesc] = useState(false)
  const [brouillonDesc, setBrouillonDesc] = useState('')
  // Builder cycles/niveaux (copié du Labo) — opère sur la famille active (vue = son id)
  const [suggBusy, setSuggBusy] = useState(false)
  const [suggestions, setSuggestions] = useState([])         // [{nom, cycle_id, existant}]
  const [niveauxParCycle, setNiveauxParCycle] = useState({}) // { cycle_id: [{nom, niveau_id, existant, lie}] }
  const [nouvNivParCycle, setNouvNivParCycle] = useState({}) // { cycle_id: texte }
  const navigate = useNavigate()

  const familleActiveId = vue !== 'nouvelle' ? vue : null
  const familleActive = familles.find(f => String(f.id) === String(vue))

  function chargerFamilles() {
    return fetchWithTimeout('/api/admin/familles', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => { if (r.status === 401) { navigate('/admin/login'); return null } return r.ok ? r.json() : null })
      .then(d => { if (d) setFamilles(d.familles || []) })
      .catch(() => {})
  }
  useEffect(() => { chargerFamilles() }, [])   // eslint-disable-line react-hooks/exhaustive-deps

  // Changement d'entrée dans le menu : on repart propre, puis on LIT le détail de la famille (get).
  useEffect(() => {
    setNouvNivParCycle({}); setEditDesc(false); setBrouillonDesc('')
    if (vue !== 'nouvelle') { chargerMatrice(vue) }
    else { setSuggestions([]); setNiveauxParCycle({}) }
  }, [vue])   // eslint-disable-line react-hooks/exhaustive-deps

  // Détail (GET) de la famille : ses cycles + niveaux DÉJÀ reliés, affichés d'emblée (avant toute IA).
  async function chargerMatrice(fid) {
    setSuggestions([]); setNiveauxParCycle({})
    try {
      const r = await fetchWithTimeout(`/api/admin/familles/${fid}/matrice`, { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) return
      const d = await r.json()
      const cyc = d.cycles || []
      setSuggestions(cyc.map(c => ({ nom: c.nom, cycle_id: c.cycle_id, existant: true })))
      const map = {}
      for (const c of cyc) map[c.cycle_id] = (c.niveaux || []).map(n => ({ nom: n.nom, niveau_id: n.niveau_id, existant: true, lie: n.lie }))
      setNiveauxParCycle(map)
    } catch { /* réseau : on garde l'affichage courant */ }
  }

  // ── Création d'une famille (create encadré : nom unique, description requise). ──
  async function creerFamille() {
    const nom = famNom.trim(), description = famDesc.trim()
    if (!nom || !description) { showError('Nom et description de la famille sont requis.'); return }
    setBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/familles', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nom, description }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Création impossible (${r.status}).`); return }
      setFamNom(''); setFamDesc('')
      await chargerFamilles()
      setVue(String(d.id))   // on bascule sur le builder de la famille créée
    } catch { showError('Création de la famille impossible.') }
    finally { setBusy(false) }
  }

  // ── Édition de la description (update encadré : jamais le nom). Valider = put, Annuler = rien. ──
  function ouvrirEditionDesc() { setEditDesc(true); setBrouillonDesc(familleActive?.description || '') }
  function annulerEditionDesc() { setEditDesc(false); setBrouillonDesc('') }
  async function validerDescription() {
    const description = brouillonDesc.trim()
    if (!description) { showError('La description ne peut pas être vide.'); return }
    setBusy(true)
    try {
      const r = await fetchWithTimeout(`/api/admin/familles/${familleActiveId}/description`, {
        method: 'PUT', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Enregistrement impossible (${r.status}).`); return }
      await chargerFamilles()
      setEditDesc(false); setBrouillonDesc('')
    } catch { showError('Enregistrement impossible.') }
    finally { setBusy(false) }
  }

  // ── Builder cycles/niveaux (copié du Labo), opère sur familleActiveId ──
  async function proposerCycles() {
    if (!familleActiveId) return
    setSuggBusy(true)
    try {
      const r = await fetchWithTimeout(`/api/admin/familles/${familleActiveId}/suggerer-cycles`,
        { method: 'POST', credentials: 'include' }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Suggestion impossible (${r.status}).`); return }
      const props = d.propositions || []
      // Fusion : on GARDE l'existant déjà affiché (get) + on AJOUTE les cycles proposés absents.
      setSuggestions(prev => {
        const vusId = new Set(prev.filter(s => s.cycle_id != null).map(s => String(s.cycle_id)))
        const vusNom = new Set(prev.filter(s => s.cycle_id == null).map(s => s.nom.toLowerCase()))
        const res = [...prev]
        for (const p of props) {
          const deja = p.cycle_id != null ? vusId.has(String(p.cycle_id)) : vusNom.has(p.nom.toLowerCase())
          if (!deja) {
            res.push(p)
            if (p.cycle_id != null) vusId.add(String(p.cycle_id)); else vusNom.add(p.nom.toLowerCase())
          }
        }
        return res
      })
      // Fusion des niveaux : pour chaque cycle existant proposé, on ajoute ses niveaux proposés absents.
      for (const p of props) {
        if (p.existant && p.cycle_id != null) {
          const propNiv = await proposerNiveauxCycle(p.cycle_id)
          setNiveauxParCycle(prev => {
            const cur = prev[p.cycle_id] || []
            const vusId = new Set(cur.filter(n => n.niveau_id != null).map(n => String(n.niveau_id)))
            const vusNom = new Set(cur.filter(n => n.niveau_id == null).map(n => n.nom.toLowerCase()))
            const merged = [...cur]
            for (const n of propNiv) {
              const deja = n.niveau_id != null ? vusId.has(String(n.niveau_id)) : vusNom.has(n.nom.toLowerCase())
              if (!deja) {
                merged.push(n)
                if (n.niveau_id != null) vusId.add(String(n.niveau_id)); else vusNom.add(n.nom.toLowerCase())
              }
            }
            return { ...prev, [p.cycle_id]: merged }
          })
        }
      }
    } catch { showError('Suggestion des cycles impossible.') }
    finally { setSuggBusy(false) }
  }

  async function proposerNiveauxCycle(cycleId) {
    try {
      const r = await fetchWithTimeout(`/api/admin/familles/${familleActiveId}/cycles/${cycleId}/suggerer-niveaux`,
        { method: 'POST', credentials: 'include' }, TIMEOUT_LONG)
      if (!r.ok) return []
      const d = await r.json()
      return d.propositions || []
    } catch { return [] }
  }

  async function basculerNiveauMatrice(cycleId, niveauId, lieActuel) {
    if (!familleActiveId) return
    const actif = !lieActuel
    const poser = (val) => setNiveauxParCycle(prev => ({ ...prev,
      [cycleId]: (prev[cycleId] || []).map(n => (n.niveau_id === niveauId ? { ...n, lie: val } : n)) }))
    poser(actif)
    try {
      const r = await fetchWithTimeout('/api/admin/familles/couple', {
        method: 'PUT', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ famille_id: Number(familleActiveId), niveau_id: niveauId, actif }),
      }, TIMEOUT_STD)
      if (!r.ok) { const e = await r.json().catch(() => ({})); showError(e.detail || `Enregistrement impossible (${r.status}).`); poser(lieActuel) }
    } catch { showError('Enregistrement impossible.'); poser(lieActuel) }
  }

  async function ajouterCycleSuggere(nom) {
    setBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/cycles', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nom }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Ajout du cycle impossible (${r.status}).`); return }
      setSuggestions(prev => prev.map(s => (s.nom === nom ? { ...s, existant: true, cycle_id: d.id } : s)))
      const niv = await proposerNiveauxCycle(d.id)
      setNiveauxParCycle(prev => ({ ...prev, [d.id]: niv }))
    } catch { showError('Ajout du cycle impossible.') }
    finally { setBusy(false) }
  }

  async function creerNiveauPropose(cycleId, nom) {
    setBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/niveaux', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), nom }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Ajout du niveau impossible (${r.status}).`); return }
      setNiveauxParCycle(prev => ({ ...prev,
        [cycleId]: (prev[cycleId] || []).map(n => (n.nom === nom && !n.existant ? { ...n, existant: true, niveau_id: d.id } : n)) }))
    } catch { showError('Ajout du niveau impossible.') }
    finally { setBusy(false) }
  }

  async function ajouterNiveauManuel(cycleId) {
    const nom = (nouvNivParCycle[cycleId] || '').trim()
    if (!nom) return
    setBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/niveaux', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), nom }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Ajout du niveau impossible (${r.status}).`); return }
      setNiveauxParCycle(prev => ({ ...prev,
        [cycleId]: [...(prev[cycleId] || []), { nom: d.nom, niveau_id: d.id, existant: true, lie: false }] }))
      setNouvNivParCycle(prev => ({ ...prev, [cycleId]: '' }))
    } catch { showError('Ajout du niveau impossible.') }
    finally { setBusy(false) }
  }

  return (
    <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>

      {/* Menu latéral : « + Nouvelle famille » en haut (sélectionné par défaut), puis la liste des familles. */}
      <aside style={{ width: 240, flexShrink: 0, background: '#fff', border: '1px solid #e2e8f0',
        borderRadius: 12, overflow: 'hidden', position: 'sticky', top: 0, alignSelf: 'flex-start' }}>
        <div style={{ padding: '10px 12px', borderBottom: '1px solid #e2e8f0', fontSize: 12,
          fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Familles ({familles.length})
        </div>
        <button type="button" onClick={() => setVue('nouvelle')}
          title="Créer une nouvelle famille"
          style={{ display: 'block', width: '100%', textAlign: 'left', padding: '10px 12px',
            border: 'none', borderBottom: '1px solid #e2e8f0', cursor: 'pointer', fontSize: 13, fontWeight: 700,
            background: vue === 'nouvelle' ? '#16a34a' : '#f0fdf4', color: vue === 'nouvelle' ? '#fff' : '#166534' }}>
          + Nouvelle famille
        </button>
        {familles.length === 0 ? (
          <div style={{ padding: 12, fontSize: 12, color: '#94a3b8' }}>Aucune famille.</div>
        ) : familles.map(f => {
          const actif = String(vue) === String(f.id)
          return (
            <button key={f.id} type="button" onClick={() => setVue(String(f.id))}
              title={f.description || f.nom}
              style={{ display: 'block', width: '100%', textAlign: 'left', padding: '9px 12px',
                border: 'none', borderBottom: '1px solid #f1f5f9', cursor: 'pointer', fontSize: 13,
                background: actif ? '#eff6ff' : '#fff', color: actif ? '#1d4ed8' : '#1e293b',
                fontWeight: actif ? 600 : 400 }}>
              {f.nom}
              {f.rejet && <span title="Famille de rejet" style={{ marginLeft: 6, fontSize: 10, color: '#dc2626' }}>rejet</span>}
            </button>
          )
        })}
      </aside>

      {/* Panneau de droite : création OU builder de la famille sélectionnée. */}
      <div style={{ flex: 1 }}>

        {vue === 'nouvelle' ? (
          <div style={carte}>
            <h3 style={titre}>Nouvelle famille</h3>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <input value={famNom} onChange={e => setFamNom(e.target.value)} placeholder="Nom (ex. Enseignement Agricole)"
                style={{ ...champ, flex: '1 1 220px' }} />
              <input value={famDesc} onChange={e => setFamDesc(e.target.value)} placeholder="Description"
                style={{ ...champ, flex: '1 1 260px' }} />
              <button onClick={creerFamille} disabled={busy || !famNom.trim() || !famDesc.trim()}
                style={btn('#16a34a', busy || !famNom.trim() || !famDesc.trim())}
                title="Créer cette famille en base"><span aria-hidden="true">＋</span> Créer</button>
            </div>
            <p className="text-xs text-gray-400" style={{ marginTop: 10, lineHeight: 1.5 }}>
              Une fois créée, on enchaîne : proposition des cycles par l'IA, puis matrice cycles × niveaux à cocher.
            </p>
          </div>
        ) : familleActive ? (<>

          {/* Cartouche 1 — la famille : nom (jamais modifié) + description (éditable au crayon). */}
          <div style={carte}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
              <h3 style={{ ...titre, margin: 0 }}>{familleActive.nom}</h3>
              {!editDesc && (
                <button type="button" onClick={ouvrirEditionDesc} title="Modifier la description"
                  style={{ padding: '4px 8px', borderRadius: 6, border: '1px solid #e2e8f0', background: 'white', color: '#475569', fontSize: 13, cursor: 'pointer' }}>
                  ✏️
                </button>
              )}
            </div>
            {editDesc ? (
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <textarea value={brouillonDesc} onChange={e => setBrouillonDesc(e.target.value)} rows={3} autoFocus disabled={busy}
                  style={{ width: '100%', padding: '8px 10px', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: 13, resize: 'vertical', fontFamily: 'inherit' }} />
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" onClick={validerDescription} disabled={busy}
                    style={btn('#2563eb', busy)} title="Enregistrer la description en base">
                    {busy ? '…' : '✓ Valider'}
                  </button>
                  <button type="button" onClick={annulerEditionDesc} disabled={busy}
                    title="Annuler — aucune écriture"
                    style={{ ...btn('#fff', false), background: 'white', color: '#dc2626', border: '1px solid #fca5a5' }}>
                    ✕ Annuler
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ marginTop: 10, padding: '10px 12px', background: '#f0fdf4', border: '1px solid #bbf7d0',
                borderRadius: 8, fontSize: 13, color: '#334155', lineHeight: 1.5 }}>
                {familleActive.description}
              </div>
            )}
          </div>

          {/* Cartouche 2 — cycles & niveaux (builder copié du Labo). */}
          <div style={carte}>
            <h3 style={titre}>Cycles de la famille « {familleActive.nom} »</h3>

            <div style={{ marginBottom: 14 }}>
              <button onClick={proposerCycles} disabled={suggBusy}
                style={{ ...btn('#7c3aed', suggBusy), cursor: suggBusy ? 'wait' : 'pointer' }}
                title="L'IA propose les cycles sur lesquels s'appuie cette famille">
                <span aria-hidden="true">🤖</span> {suggBusy ? 'Analyse…' : 'Proposer les cycles (IA)'}
              </button>
            </div>

            {suggestions.length === 0 ? (
              <p className="text-sm" style={{ color: '#94a3b8' }}>
                Clique « Proposer les cycles (IA) » pour afficher les cycles et leurs niveaux.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {suggestions.map((s, i) => {
                  const niveaux = s.existant && s.cycle_id != null ? (niveauxParCycle[s.cycle_id] || []) : []
                  return (
                    <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 14, padding: '10px 0',
                      borderBottom: i < suggestions.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                      <div style={{ flex: '0 0 190px', paddingTop: 5 }}>
                        {s.existant ? (
                          <span style={{ fontWeight: 700, color: '#166534', fontSize: 14 }}>{s.nom}</span>
                        ) : (
                          <button type="button" onClick={() => ajouterCycleSuggere(s.nom)} disabled={busy}
                            title="Cycle absent de la base — cliquer pour l'ajouter"
                            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13,
                              padding: '4px 10px', borderRadius: 8, border: '1px dashed #cbd5e1',
                              cursor: busy ? 'wait' : 'pointer', background: '#f8fafc', color: '#475569', fontWeight: 600 }}>
                            <span aria-hidden="true">＋</span> {s.nom} <span style={{ fontSize: 10, color: '#94a3b8' }}>à créer</span>
                          </button>
                        )}
                      </div>
                      <div style={{ flex: 1, display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
                        {!s.existant ? (
                          <span className="text-xs" style={{ color: '#cbd5e1', paddingTop: 6 }}>— ajoute le cycle pour voir ses niveaux</span>
                        ) : (<>
                          {niveaux.length === 0 && (
                            <span className="text-xs" style={{ color: '#cbd5e1' }}>aucun niveau pertinent proposé</span>
                          )}
                          {niveaux.map((n, j) => n.existant ? (
                            <label key={`n${j}`} title={n.lie ? 'Relié — décocher pour délier' : 'Cocher pour relier à la famille'}
                              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer',
                                padding: '4px 10px', borderRadius: 999,
                                border: '1px solid ' + (n.lie ? '#bbf7d0' : '#e2e8f0'),
                                background: n.lie ? '#dcfce7' : '#f8fafc', color: n.lie ? '#166534' : '#475569',
                                fontWeight: n.lie ? 700 : 500 }}>
                              <input type="checkbox" checked={n.lie}
                                onChange={() => basculerNiveauMatrice(s.cycle_id, n.niveau_id, n.lie)}
                                style={{ width: 15, height: 15 }} />
                              {n.nom}
                            </label>
                          ) : (
                            <button key={`n${j}`} type="button" onClick={() => creerNiveauPropose(s.cycle_id, n.nom)} disabled={busy}
                              title="Niveau absent de la base — cliquer pour le créer"
                              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13,
                                padding: '4px 10px', borderRadius: 999, border: '1px dashed #cbd5e1',
                                cursor: busy ? 'wait' : 'pointer', background: '#f8fafc', color: '#475569', fontWeight: 500 }}>
                              <span aria-hidden="true">＋</span> {n.nom} <span style={{ fontSize: 10, color: '#94a3b8' }}>à créer</span>
                            </button>
                          ))}
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                            <input value={nouvNivParCycle[s.cycle_id] || ''}
                              onChange={e => setNouvNivParCycle(prev => ({ ...prev, [s.cycle_id]: e.target.value }))}
                              onKeyDown={e => { if (e.key === 'Enter') ajouterNiveauManuel(s.cycle_id) }}
                              placeholder="+ niveau" style={{ ...champ, padding: '4px 8px', width: 130, fontSize: 12 }} />
                            <button type="button" onClick={() => ajouterNiveauManuel(s.cycle_id)}
                              disabled={busy || !(nouvNivParCycle[s.cycle_id] || '').trim()}
                              title="Ajouter ce niveau au cycle en base"
                              style={{ padding: '5px 9px', borderRadius: 8, border: 'none', fontSize: 13, fontWeight: 700,
                                cursor: (busy || !(nouvNivParCycle[s.cycle_id] || '').trim()) ? 'not-allowed' : 'pointer',
                                background: (busy || !(nouvNivParCycle[s.cycle_id] || '').trim()) ? '#e2e8f0' : '#16a34a',
                                color: (busy || !(nouvNivParCycle[s.cycle_id] || '').trim()) ? '#94a3b8' : 'white' }}>
                              ＋
                            </button>
                          </span>
                        </>)}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </>) : (
          <div style={carte}><p className="text-sm" style={{ color: '#94a3b8' }}>Famille introuvable.</p></div>
        )}
      </div>
    </div>
  )
}
