import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

// Fenêtre MAÎTRE-DÉTAIL sur la table `types_activite` (get direct à chaque ouverture).
//  • GAUCHE  = navigation : bouton « + Nouveau » puis la liste des types (clic = sélection).
//  • DROITE  = la fiche du type choisi (ou le formulaire de création si « + Nouveau »).
// Opérations (règle 4, contrôle côté base) :
//  • CREATE — POST …/catalogue : refus du doublon par LIBELLÉ (renvoyé `deja_present`) → on le dit et on
//    sélectionne l'existant plutôt que d'en refaire un.
//  • DELETE — DELETE …/{id} : le back refuse si le type est encore utilisé ; le front GRISE la poubelle.
// Le PROMPT n'est PAS ici (il vit sur le lien referentiel_types_activite, propre au couple). Les précisions
// et paramètres (tables `type_precisions` / `type_parametres`) seront branchés dans le panneau à l'étape 2.
// Petit badge d'ORIGINE du type (colonne `types_activite.origine`) — même esprit que le badge « défaut » :
// 'admin' = ajouté à la main, 'ia' = issu d'une suggestion IA. 'systeme' (pré-rempli) reste sans badge.
function BadgeOrigine({ texte, bg, fg }) {
  return (
    <span style={{ marginLeft: 6, padding: '1px 6px', borderRadius: 4, fontSize: 10, fontWeight: 600, background: bg, color: fg }}>
      {texte}
    </span>
  )
}

// Style d'une CARTOUCHE (carte blanche) et de son TITRE. Règle maison : tout titre de cartouche est
// PLUS GROS + EN GRAS (même geste partout).
const CARTE = { background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', padding: 20 }
const TITRE_CARTOUCHE = { fontSize: 18, fontWeight: 700, color: '#1e293b', margin: 0 }

export default function AdminTypesActivite() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState(null)   // id du type affiché à droite
  const [mode, setMode] = useState('none')             // 'none' | 'new' | 'view'
  const [newLabel, setNewLabel] = useState('')
  const [msg, setMsg] = useState(null)                 // message HUMAIN (règle 23) affiché dans le panneau
  const [busy, setBusy] = useState(false)
  const [precisions, setPrecisions] = useState(null)   // null = pas encore chargé ; [] = chargé, vide
  const [precLoading, setPrecLoading] = useState(false)
  const [newPrec, setNewPrec] = useState('')           // saisie du champ « Ajouter une précision »
  const [precBusy, setPrecBusy] = useState(false)
  const navigate = useNavigate()

  // get : (re)lit la table en base. Rappelé après chaque écriture — zéro copie, on relit toujours.
  function charger() {
    return fetch('/api/admin/activite-types', { credentials: 'include' })
      .then(r => { if (r.status === 401) { navigate('/admin/login'); return null } return r.json() })
      .then(data => { if (data) setRows(data.types || []) })
  }

  useEffect(() => { charger().finally(() => setLoading(false)) }, [navigate])  // eslint-disable-line react-hooks/exhaustive-deps

  // get des PRÉCISIONS d'un type (table `type_precisions`). Relu à chaque changement de type ET après
  // chaque écriture (ajout / suppression) — zéro copie, la cartouche reflète toujours la base.
  function chargerPrecisions(id) {
    setPrecLoading(true)
    return fetch(`/api/admin/activite-types/${id}/precisions`, { credentials: 'include' })
      .then(r => { if (r.status === 401) { navigate('/admin/login'); return null } return r.json() })
      .then(d => { if (d) setPrecisions(d.precisions || []) })
      .finally(() => setPrecLoading(false))
  }

  // Hors mode 'view' : rien à afficher, on vide.
  useEffect(() => {
    if (mode !== 'view' || selectedId == null) { setPrecisions(null); return }
    chargerPrecisions(selectedId)
  }, [mode, selectedId, navigate])  // eslint-disable-line react-hooks/exhaustive-deps

  const selected = rows.find(t => t.id === selectedId) || null

  function ouvrirType(t) {
    setSelectedId(t.id); setMode('view'); setMsg(null)
  }
  function ouvrirNouveau() {
    setSelectedId(null); setMode('new'); setNewLabel(''); setMsg(null)
  }

  // CREATE encadré : Valider = put. Le back refuse le doublon (deja_present) → message humain + on
  // sélectionne l'existant. Sinon on relit la table et on ouvre le type fraîchement créé.
  async function creer(e) {
    e.preventDefault()
    const label = newLabel.trim()
    if (!label) { setMsg({ type: 'err', texte: 'Indiquez un libellé pour le nouveau type.' }); return }
    setBusy(true); setMsg(null)
    try {
      const r = await fetch('/api/admin/referentiels/types-activite/catalogue', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label }),
      })
      if (r.status === 401) { navigate('/admin/login'); return }
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { setMsg({ type: 'err', texte: d.detail || 'Création impossible.' }); return }
      await charger()
      setSelectedId(d.id); setMode('view')
      setMsg(d.deja_present
        ? { type: 'info', texte: `Un type « ${d.label} » existait déjà — voici sa fiche.` }
        : null)
    } finally { setBusy(false) }
  }

  // DELETE encadré : seulement si supprimable, après confirmation. Puis on relit et on vide le panneau.
  async function supprimer(t) {
    if (!t.supprimable) return
    if (!window.confirm(`Supprimer définitivement le type « ${t.label} » ?\nCette action est irréversible.`)) return
    setBusy(true)
    try {
      const r = await fetch(`/api/admin/activite-types/${t.id}`, { method: 'DELETE', credentials: 'include' })
      if (r.status === 401) { navigate('/admin/login'); return }
      if (!r.ok) {
        const d = await r.json().catch(() => ({}))
        setMsg({ type: 'err', texte: d.detail || 'Suppression impossible.' })
        await charger()   // resynchronise l'état réel (ex. quelqu'un l'a utilisé entre-temps)
        return
      }
      await charger()
      setSelectedId(null); setMode('none'); setMsg(null)
    } finally { setBusy(false) }
  }

  // CREATE encadré (précision) : Ajouter = put (POST). Le back refuse le doublon (deja_present) → message
  // humain. Sinon on vide le champ et on relit la liste (get) — jamais de recopie côté front.
  async function ajouterPrecision(e) {
    e.preventDefault()
    const libelle = newPrec.trim()
    if (!libelle) { setMsg({ type: 'err', texte: 'Indiquez un libellé pour la précision.' }); return }
    if (selectedId == null) return
    setPrecBusy(true); setMsg(null)
    try {
      const r = await fetch(`/api/admin/activite-types/${selectedId}/precisions`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ libelle }),
      })
      if (r.status === 401) { navigate('/admin/login'); return }
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { setMsg({ type: 'err', texte: d.detail || 'Ajout impossible.' }); return }
      setNewPrec('')
      if (d.deja_present) setMsg({ type: 'info', texte: `La précision « ${d.libelle} » existe déjà pour ce type.` })
      await chargerPrecisions(selectedId)
    } finally { setPrecBusy(false) }
  }

  // DELETE encadré (précision) : après confirmation, puis on relit la liste. Aucune contrainte de grisage
  // (rien ne référence une précision par clé étrangère).
  async function supprimerPrecision(p) {
    if (selectedId == null) return
    if (!window.confirm(`Supprimer la précision « ${p.libelle} » ?\nCette action est irréversible.`)) return
    setPrecBusy(true); setMsg(null)
    try {
      const r = await fetch(`/api/admin/activite-types/${selectedId}/precisions/${p.id}`, { method: 'DELETE', credentials: 'include' })
      if (r.status === 401) { navigate('/admin/login'); return }
      if (!r.ok) {
        const d = await r.json().catch(() => ({}))
        setMsg({ type: 'err', texte: d.detail || 'Suppression impossible.' })
      }
      await chargerPrecisions(selectedId)
    } finally { setPrecBusy(false) }
  }

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">Types d'activité</h2>
        <span className="text-xs text-gray-400">{rows.length} type{rows.length > 1 ? 's' : ''}</span>
      </div>

      <p className="text-xs text-gray-500 mb-3" style={{ maxWidth: 720, lineHeight: 1.5 }}>
        Catalogue global des types d'activité (table <code>types_activite</code>), lu en base. Créez un type
        avec <b>+ Nouveau</b> ; cliquez un type pour sa fiche. Créer un type ne l'active nulle part : il devient
        réel pour un couple seulement quand un référentiel le coche.
      </p>

      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        {/* ─── GAUCHE : navigation ─── */}
        <div style={{ width: 280, flexShrink: 0 }}>
          <button
            onClick={ouvrirNouveau}
            style={{
              width: '100%', marginBottom: 10, height: 42, borderRadius: 8, cursor: 'pointer',
              border: '1px solid #334155', background: mode === 'new' ? '#334155' : '#0f172a', color: 'white',
              fontWeight: 600, fontSize: 13,
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}
          >
            <span aria-hidden="true" style={{ fontSize: 22, lineHeight: 0, fontWeight: 400 }}>＋</span>
            Nouveau type
          </button>

          <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
            {rows.length === 0 ? (
              <p className="text-sm" style={{ padding: '16px', color: '#94a3b8', textAlign: 'center' }}>Aucun type.</p>
            ) : rows.map((t, i) => {
              const actif = t.id === selectedId && mode === 'view'
              return (
                <button
                  key={t.id}
                  onClick={() => ouvrirType(t)}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left', cursor: 'pointer',
                    padding: '10px 14px', fontSize: 13,
                    border: 'none', borderBottom: i < rows.length - 1 ? '1px solid #f1f5f9' : 'none',
                    borderLeft: '3px solid ' + (actif ? '#2563eb' : 'transparent'),
                    background: actif ? '#eff6ff' : 'white',
                    color: '#1e293b', fontWeight: actif ? 600 : 500,
                  }}
                >
                  {t.label}
                  {t.is_default && <span style={{ marginLeft: 6, fontSize: 10, color: '#0891b2' }}>défaut</span>}
                  {t.origine === 'admin' && <BadgeOrigine texte="admin" bg="#e0e7ff" fg="#4338ca" />}
                  {t.origine === 'ia' && <BadgeOrigine texte="IA" bg="#f3e8ff" fg="#7e22ce" />}
                  {!t.actif && <span style={{ marginLeft: 6, fontSize: 10, color: '#94a3b8' }}>inactif</span>}
                </button>
              )
            })}
          </div>
        </div>

        {/* ─── DROITE : détail / création — PILE DE CARTOUCHES ─── */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {msg && (
            <div style={{
              padding: '8px 12px', borderRadius: 8, fontSize: 12.5,
              background: msg.type === 'err' ? '#fef2f2' : '#eff6ff',
              color: msg.type === 'err' ? '#dc2626' : '#1d4ed8',
              border: '1px solid ' + (msg.type === 'err' ? '#fecaca' : '#bfdbfe'),
            }}>{msg.texte}</div>
          )}

          {mode === 'new' ? (
            <div style={CARTE}>
              <form onSubmit={creer}>
                <h3 style={TITRE_CARTOUCHE}>Nouveau type d'activité</h3>
                <label className="text-xs text-gray-500" style={{ display: 'block', margin: '14px 0 6px' }}>Libellé</label>
                <input
                  autoFocus value={newLabel} onChange={e => setNewLabel(e.target.value)}
                  placeholder="ex. Débat argumenté"
                  style={{ width: '100%', height: 38, padding: '0 12px', fontSize: 13, borderRadius: 8, border: '1px solid #cbd5e1', boxSizing: 'border-box' }}
                />
                <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
                  <button type="submit" disabled={busy}
                    style={{ height: 36, padding: '0 18px', borderRadius: 8, border: 'none', background: '#2563eb', color: 'white', fontWeight: 600, fontSize: 13, cursor: busy ? 'default' : 'pointer', opacity: busy ? 0.6 : 1 }}
                  >Créer</button>
                  <button type="button" onClick={() => { setMode('none'); setMsg(null) }}
                    style={{ height: 36, padding: '0 18px', borderRadius: 8, border: '1px solid #e2e8f0', background: 'white', color: '#64748b', fontWeight: 600, fontSize: 13, cursor: 'pointer' }}
                  >Annuler</button>
                </div>
              </form>
            </div>
          ) : mode === 'view' && selected ? (
            <>
              {/* Cartouche 1 — la fiche du type (titre = libellé, gros + gras) */}
              <div style={CARTE}>
                <div className="flex items-center justify-between" style={{ marginBottom: 16 }}>
                  <h3 style={TITRE_CARTOUCHE}>{selected.label}</h3>
                  <button
                    onClick={() => supprimer(selected)}
                    disabled={!selected.supprimable || busy}
                    title={selected.supprimable
                      ? `Supprimer le type « ${selected.label} »`
                      : `Utilisé par ${selected.usage} activité(s)/jalon(s) — suppression impossible`}
                    style={{
                      height: 32, padding: '0 12px', borderRadius: 8, fontSize: 12.5, fontWeight: 600,
                      border: '1px solid ' + (selected.supprimable ? '#fecaca' : '#e2e8f0'),
                      background: selected.supprimable ? '#fef2f2' : '#f8fafc',
                      color: selected.supprimable ? '#dc2626' : '#cbd5e1',
                      cursor: selected.supprimable && !busy ? 'pointer' : 'not-allowed',
                    }}
                  >🗑 Supprimer</button>
                </div>

                <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', columnGap: 16, rowGap: 10, fontSize: 13, alignItems: 'center' }}>
                  <dt style={{ color: '#94a3b8' }}>id</dt>
                  <dd style={{ fontFamily: 'monospace', color: '#64748b' }}>{selected.id}</dd>
                  <dt style={{ color: '#94a3b8' }}>Libellé</dt>
                  <dd style={{ fontWeight: 600, color: '#1e293b' }}>{selected.label}</dd>
                  <dt style={{ color: '#94a3b8' }}>Origine</dt>
                  <dd style={{ color: '#1e293b' }}>
                    {selected.origine === 'admin' ? 'admin (ajouté à la main)'
                      : selected.origine === 'ia' ? 'IA (suggestion)'
                      : 'système (pré-rempli)'}
                  </dd>
                  <dt style={{ color: '#94a3b8' }}>Type par défaut</dt>
                  <dd style={{ color: '#1e293b' }}>{selected.is_default ? 'oui' : 'non'}</dd>
                  <dt style={{ color: '#94a3b8' }}>Actif</dt>
                  <dd style={{ color: '#1e293b' }}>{selected.actif ? 'oui' : 'non'}</dd>
                  <dt style={{ color: '#94a3b8' }}>Ordre</dt>
                  <dd style={{ color: '#1e293b' }}>{selected.ordre}</dd>
                  <dt style={{ color: '#94a3b8' }}>Usage</dt>
                  <dd style={{ color: '#1e293b' }}>{selected.usage} activité(s)/jalon(s)</dd>
                </dl>
              </div>

              {/* Cartouche 2 — Précisions (get direct dans `type_precisions`, lecture seule à l'étape A) */}
              <div style={CARTE}>
                <h3 style={TITRE_CARTOUCHE}>Précisions</h3>
                {precLoading ? (
                  <p className="text-sm" style={{ marginTop: 12, color: '#94a3b8' }}>Chargement…</p>
                ) : precisions && precisions.length > 0 ? (
                  <ul style={{ marginTop: 12, listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {precisions.map(p => (
                      <li key={p.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: '8px 12px', borderRadius: 8, border: '1px solid #f1f5f9', background: '#f8fafc', fontSize: 13, color: '#1e293b' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                          <span style={{ fontWeight: 500 }}>{p.libelle}</span>
                          {p.source === 'admin' && <BadgeOrigine texte="admin" bg="#e0e7ff" fg="#4338ca" />}
                          {p.source === 'ia' && <BadgeOrigine texte="IA" bg="#f3e8ff" fg="#7e22ce" />}
                        </span>
                        <button
                          onClick={() => supprimerPrecision(p)} disabled={precBusy}
                          title={`Supprimer la précision « ${p.libelle} »`}
                          style={{ height: 26, width: 26, borderRadius: 6, border: '1px solid #fecaca', background: '#fef2f2', color: '#dc2626', cursor: precBusy ? 'default' : 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, flexShrink: 0 }}
                        >🗑</button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm" style={{ marginTop: 12, color: '#94a3b8' }}>Aucune précision pour ce type.</p>
                )}

                <form onSubmit={ajouterPrecision} style={{ marginTop: 14, display: 'flex', gap: 8 }}>
                  <input
                    value={newPrec} onChange={e => setNewPrec(e.target.value)}
                    placeholder="Ajouter une précision…"
                    style={{ flex: 1, minWidth: 0, height: 34, padding: '0 12px', fontSize: 13, borderRadius: 8, border: '1px solid #cbd5e1', boxSizing: 'border-box' }}
                  />
                  <button type="submit" disabled={precBusy}
                    style={{ height: 34, padding: '0 16px', borderRadius: 8, border: 'none', background: '#0f172a', color: 'white', fontWeight: 600, fontSize: 13, cursor: precBusy ? 'default' : 'pointer', opacity: precBusy ? 0.6 : 1, display: 'inline-flex', alignItems: 'center', gap: 6, flexShrink: 0 }}
                  >
                    <span aria-hidden="true" style={{ fontSize: 18, lineHeight: 0, fontWeight: 400 }}>＋</span>
                    Ajouter
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div style={CARTE}>
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#94a3b8' }}>
                <p className="text-sm">Sélectionnez un type à gauche, ou créez-en un avec <b>+ Nouveau</b>.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
