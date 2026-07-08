// Page Référentiels — Étape 1 du chantier « Référentiel → matières + chunks ».
// L'admin déclare le couple (cycle + niveau), fournit le PDF officiel par LIEN ou
// par DÉPÔT, CONTRÔLE l'aperçu du document récupéré, puis valide : le système le
// range, en extrait le texte et enregistre sa provenance.
// Hors périmètre étape 1 : extraction des matières, chunks, recherche web automatique.
import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD, TIMEOUT_GROQ } from '../utils/api.js'
import { showError } from '../errorDialog.js'

// Construit les lignes de la table matières à partir de l'état du couple (endpoint /etat) :
// d'abord les matières DÉJÀ en base (cochée figée), puis les CANDIDATES proposées non encore
// en base (nouvelles, à cocher par l'admin). Les candidates viennent de matieres-candidates.json
// (préparé en DEV, rangé dans REFERENTIELS/<CYCLE>/<NIVEAU>/) — l'app ne les calcule jamais.
function construireLignesMatieres(etatObj) {
  const enBase = (etatObj?.matieres || []).map(m => ({ id: m.id, nom: m.nom, en_base: true, cochee: true }))
  const nomsEnBase = new Set(enBase.map(m => m.nom.toLowerCase()))
  const nouvelles = (etatObj?.candidates || [])
    .filter(nom => !nomsEnBase.has(nom.toLowerCase()))
    .map(nom => ({ id: null, nom, en_base: false, cochee: false }))
  return [...enBase, ...nouvelles]
}

export default function AdminReferentiels() {
  const [cycles, setCycles] = useState([])
  const [cycleId, setCycleId] = useState('')
  const [niveau, setNiveau] = useState('')
  const [mode, setMode] = useState('depot')       // 'depot' | 'lien'
  const [url, setUrl] = useState('')
  const [nomFichier, setNomFichier] = useState('')  // nom du PDF choisi (zone « Par dépôt »)
  const [source, setSource] = useState('')
  const [busy, setBusy] = useState(false)
  const [apercu, setApercu] = useState(null)      // { token, filename, pages, taille_ko, apercu }
  const [resultat, setResultat] = useState(null)  // { cycle, niveau, dossier, pages, caracteres_extraits, nom_fixe }
  // Table des matières du référentiel — INTERFACE seule ; le code (lecture des
  // candidats + enregistrement en base) sera branché à l'étape suivante.
  const [matieres, setMatieres] = useState([])
  const [nouvelleMatiere, setNouvelleMatiere] = useState('')
  const [editIndex, setEditIndex] = useState(-1)
  const [editNom, setEditNom] = useState('')
  const [bilanApercu, setBilanApercu] = useState('')
  // État du couple sélectionné : { existe_referentiel, referentiel:{fichier,source,date_doc}, matieres:[{id,nom}] }
  const [etat, setEtat] = useState(null)
  const [showPdf, setShowPdf] = useState(false)   // fenêtre de relecture du PDF déjà enregistré
  const [showParIa, setShowParIa] = useState(false)  // modale explicative « Par IA » (idée, pas encore branchée)

  useEffect(() => {
    fetchWithTimeout('/api/admin/programmes', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) setCycles(d.cycles || []) })
      .catch(() => {})
  }, [])

  // À la sélection d'un couple (cycle + niveau) : lire son état en base. Si un référentiel
  // est DÉJÀ enregistré (« déjà traité »), on affiche son nom réel + ses matières existantes
  // et on grise la zone de dépôt. Sinon, dépôt normal.
  useEffect(() => {
    if (!cycleId || !niveau) { setEtat(null); setMatieres([]); return }
    setApercu(null); setResultat(null); setBilanApercu(''); setShowPdf(false)
    let annule = false
    fetchWithTimeout(`/api/admin/referentiels/etat?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        if (annule) return
        setEtat(d)
        setMatieres(construireLignesMatieres(d))
      })
      .catch(() => { if (!annule) setEtat(null) })
    return () => { annule = true }
  }, [cycleId, niveau])

  async function recupererLien() {
    if (!url.trim()) { showError('Collez d’abord le lien du PDF.'); return }
    setBusy(true); setApercu(null); setResultat(null)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/preparer-lien', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      }, TIMEOUT_GROQ)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setApercu(d); setSource(url.trim()); setBilanApercu('')
    } catch (e) { showError(`Récupération impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  async function recupererDepot(file) {
    if (!file) return
    setNomFichier(file.name)
    setBusy(true); setApercu(null); setResultat(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const r = await fetchWithTimeout('/api/admin/referentiels/preparer-depot', {
        method: 'POST', credentials: 'include', body: form,
      }, TIMEOUT_GROQ)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setApercu(d); setSource('dépôt manuel'); setBilanApercu('')
    } catch (e) { showError(`Lecture du fichier impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  async function valider() {
    if (!cycleId) { showError('Choisissez d’abord le cycle.'); return }
    if (!niveau.trim()) { showError('Indiquez le niveau.'); return }
    if (!apercu) return
    setBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/valider', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: apercu.token, cycle_id: Number(cycleId), niveau: niveau.trim(), source, fichier_origine: apercu.filename }),
      }, TIMEOUT_GROQ)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setResultat(d); setApercu(null); setBilanApercu('')
      // La table matières reste alimentée par construireLignesMatieres (candidates du
      // référentiel + matières déjà en base), chargée à la sélection du couple.
    } catch (e) { showError(`Validation impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  const champ = { width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 10px', fontSize: 13 }
  const onglet = (actif) => ({
    fontSize: 12, padding: '6px 14px', borderRadius: 6, cursor: 'pointer',
    border: actif ? '1px solid #1F6EEB' : '1px solid #e2e8f0',
    background: actif ? '#eff6ff' : '#f8fafc', color: actif ? '#1d4ed8' : '#64748b', fontWeight: 600,
  })

  // ── Table des matières (INTERFACE) : interactions locales uniquement. Les actions
  //    qui touchent la base (enregistrer, retirer, renommer côté base) seront branchées
  //    à l'étape code ; ici « Récupérer » ne fait qu'un aperçu du bilan, sans écrire.
  function toggleCochee(i) {
    setMatieres(matieres.map((m, j) => (j === i && !m.en_base ? { ...m, cochee: !m.cochee } : m)))
  }
  function ajouterMain() {
    const nom = nouvelleMatiere.trim()
    if (!nom) return
    setMatieres([...matieres, { nom, en_base: false, cochee: true }])
    setNouvelleMatiere('')
  }
  async function rafraichirEtat() {
    const re = await fetchWithTimeout(`/api/admin/referentiels/etat?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
    if (re.ok) { const dd = await re.json(); setEtat(dd); setMatieres(construireLignesMatieres(dd)) }
  }
  function demarrerRenommage(i) { setEditIndex(i); setEditNom(matieres[i].nom) }
  async function validerRenommage() {
    const nom = editNom.trim()
    const i = editIndex
    setEditIndex(-1); setEditNom('')
    if (!nom || i < 0) return
    const ligne = matieres[i]
    if (nom === ligne.nom) return
    if (ligne.en_base && ligne.id) {
      // Renommage EN BASE (garde l'id) : effet GLOBAL → on prévient avant.
      if (!window.confirm(`Renommer « ${ligne.nom} » en « ${nom} » ?\n\nCette matière est partagée : le libellé changera PARTOUT où elle est utilisée (tous les niveaux).`)) return
      try {
        const r = await fetchWithTimeout('/api/admin/referentiels/matiere', {
          method: 'PATCH', credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ matiere_id: ligne.id, nouveau_nom: nom }),
        }, TIMEOUT_STD)
        const d = await r.json()
        if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
        await rafraichirEtat()
      } catch (e) { showError(`Renommage impossible.\n\n${e.message}`) }
    } else {
      // Matière pas encore en base : renommage LOCAL simple.
      setMatieres(ms => ms.map((m, j) => (j === i ? { ...m, nom } : m)))
    }
  }
  async function retirer(i) {
    const ligne = matieres[i]
    if (!ligne.en_base || !ligne.id) {
      setMatieres(ms => ms.filter((_, j) => j !== i))   // pas encore en base : retrait local
      return
    }
    if (!window.confirm(`Retirer « ${ligne.nom} » du niveau « ${niveau} » ?\n\nDésactivation réversible (l'historique est conservé, rien n'est supprimé).`)) return
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/retirer-matiere', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, matiere_id: ligne.id }),
      }, TIMEOUT_STD)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      if (d.profs > 0 || d.referentiels > 0) {
        showError(`« ${d.matiere} » a été retirée de ce niveau (réversible).\n\nÀ savoir : elle est encore utilisée par ${d.profs} prof(s) et ${d.referentiels} référentiel(s) de matière. Rien n'a été cassé (désactivation seulement).`)
      }
      await rafraichirEtat()
    } catch (e) { showError(`Retrait impossible.\n\n${e.message}`) }
  }
  async function recuperer() {
    // On envoie les matières qui doivent être en base = déjà en base + cochées (nouvelles).
    const aEnvoyer = matieres.filter(m => m.en_base || m.cochee).map(m => m.nom)
    if (!aEnvoyer.length) { setBilanApercu('Aucune matière cochée à enregistrer.'); return }
    setBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/matieres', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, matieres: aEnvoyer }),
      }, TIMEOUT_STD)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setBilanApercu(`Enregistré : ${d.nb_ajoutees} ajoutée(s), ${d.nb_deja} déjà en base.`)
      await rafraichirEtat()   // les nouvelles matières deviennent « déjà en base »
    } catch (e) { showError(`Enregistrement impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  const dejaTraite = !!(etat && etat.existe_referentiel)

  return (
    <div className="flex flex-col gap-6" style={{ maxWidth: 720 }}>
      <div>
        <h2 className="text-base font-semibold text-gray-800">Référentiels</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Fournissez le référentiel officiel (par lien ou en déposant le PDF), vérifiez que c’est le bon document, puis validez : le système le range et en extrait le texte.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Cycle</label>
            <select style={{ ...champ, background: '#fff' }} value={cycleId}
              onChange={e => { setCycleId(e.target.value); setNiveau('') }}>
              <option value="">— Choisissez —</option>
              {cycles.map(c => <option key={c.id} value={c.id}>{c.nom}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Niveau</label>
            <select style={{ ...champ, background: cycleId ? '#fff' : '#f3f4f6' }}
              value={niveau} disabled={!cycleId}
              onChange={e => setNiveau(e.target.value)}
              title={cycleId ? 'Choisissez le niveau de ce cycle' : 'Choisissez d’abord un cycle'}>
              <option value="">{cycleId ? '— Choisissez —' : '— Choisissez d’abord un cycle —'}</option>
              {(cycles.find(c => String(c.id) === String(cycleId))?.niveaux || [])
                .map(n => <option key={n.id} value={n.nom}>{n.nom}</option>)}
            </select>
          </div>
        </div>

        {dejaTraite ? (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Fichier PDF</label>
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
              <div style={{ flex: 1 }}>
                <input style={champ} value={etat.referentiel?.fichier || ''} readOnly
                  title="Nom du référentiel déjà enregistré pour ce couple" />
              </div>
              <button type="button" disabled
                title="Déjà traité — le remplacer sera un geste séparé (« Remplacer le référentiel »), à venir"
                style={{ background: '#e5e7eb', color: '#9ca3af', border: '1px solid #d1d5db', borderRadius: 6,
                  padding: '8px 14px', fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap',
                  cursor: 'not-allowed', pointerEvents: 'none' }}>
                Choisir le fichier
              </button>
            </div>
            <p style={{ fontSize: 12, color: '#166534', marginTop: 6 }}>
              Déjà téléchargé, déjà traité.{' '}
              <button type="button" onClick={() => setShowPdf(true)}
                title="Ouvrir le PDF du référentiel pour le relire"
                style={{ background: 'none', border: 'none', padding: 0, color: '#1d4ed8',
                  fontSize: 12, fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}>
                Voir le référentiel
              </button>
            </p>
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" title="Déposer le fichier PDF du référentiel" style={onglet(mode === 'depot')} onClick={() => setMode('depot')}>Par dépôt</button>
              <button type="button" title="Fournir le référentiel par un lien vers le PDF" style={onglet(mode === 'lien')} onClick={() => setMode('lien')}>Par lien</button>
              <button type="button"
                title="Laisser aSchool chercher le référentiel officiel sur le web — bientôt disponible (cliquez pour l’explication)"
                onClick={() => setShowParIa(true)}
                style={{ fontSize: 12, padding: '6px 14px', borderRadius: 6, cursor: 'pointer',
                  border: '1px dashed #cbd5e1', background: '#f8fafc', color: '#94a3b8', fontWeight: 600 }}>
                Par IA
              </button>
            </div>

            {mode === 'lien' ? (
              <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                <div style={{ flex: 1 }}>
                  <label className="block text-xs text-gray-500 mb-1">Lien du PDF</label>
                  <input style={champ} value={url} onChange={e => setUrl(e.target.value)}
                    placeholder="https://…/referentiel.pdf" />
                </div>
                <button type="button" className="btn-primary" title="Télécharger le PDF depuis ce lien pour vérification"
                  onClick={recupererLien} disabled={busy}>
                  {busy ? 'Récupération…' : 'Récupérer'}
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                <div style={{ flex: 1 }}>
                  <label className="block text-xs text-gray-500 mb-1">Fichier PDF</label>
                  <input style={champ} value={nomFichier} readOnly placeholder="Aucun fichier choisi" />
                </div>
                <input id="pdf-depot" type="file" accept="application/pdf,.pdf" style={{ display: 'none' }}
                  disabled={busy} onChange={e => recupererDepot(e.target.files[0])} />
                <label htmlFor="pdf-depot" className="btn-primary" title="Choisir le fichier PDF du référentiel à téléverser"
                  style={{ cursor: busy ? 'default' : 'pointer', opacity: busy ? 0.6 : 1 }}>
                  {busy ? 'Lecture…' : 'Choisir le fichier'}
                </label>
              </div>
            )}
          </>
        )}

        {/* POINT DE CONTRÔLE : l'admin VOIT le document récupéré et valide ou recommence. */}
        {apercu && (
          <div style={{ border: '1px solid #bfdbfe', background: '#f8fafc', borderRadius: 8, padding: 14 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', marginBottom: 6 }}>
              Document récupéré — vérifiez que c’est le bon
            </div>
            <div style={{ fontSize: 12, color: '#475569', marginBottom: 8 }}>
              {apercu.filename} · {apercu.pages} page(s) · {apercu.taille_ko} Ko
            </div>
            <pre style={{ fontSize: 11, color: '#334155', background: '#fff', border: '1px solid #e2e8f0',
              borderRadius: 6, padding: 10, maxHeight: 220, overflow: 'auto', whiteSpace: 'pre-wrap' }}>
              {apercu.apercu || '(aucun texte lisible sur la première page — PDF scanné ?)'}
            </pre>
            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              <button type="button" className="btn-primary" title="Confirmer que c’est le bon document : ranger, extraire le texte, enregistrer la provenance"
                onClick={valider} disabled={busy}>
                {busy ? 'Validation…' : 'Valider : c’est le bon document'}
              </button>
              <button type="button" className="btn-secondary" title="Ce n’est pas le bon document : recommencer avec un autre lien ou fichier"
                onClick={() => setApercu(null)} disabled={busy}>
                Recommencer
              </button>
            </div>
          </div>
        )}

        {resultat && (
          <div style={{ border: '1px solid #bbf7d0', background: '#f0fdf4', borderRadius: 8, padding: 14, fontSize: 12, color: '#166534' }}>
            Référentiel enregistré pour <strong>{resultat.niveau}</strong> ({resultat.cycle}).<br />
            Document d’origine : <strong>{resultat.fichier_origine}</strong> (conservé en base).<br />
            Rangé dans <code>REFERENTIELS/{resultat.dossier}/referentiel.pdf</code> · {resultat.pages} page(s) · {resultat.caracteres_extraits} caractères extraits.
          </div>
        )}

      </div>

      {(dejaTraite || resultat) && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          <div>
            <h2 className="text-base font-semibold text-gray-800">Matières de ce référentiel</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {dejaTraite
                ? 'Couple déjà traité : voici les matières déjà en base pour ce niveau. Tu peux les renommer, en retirer, ou en ajouter à la main (geste exceptionnel).'
                : 'Cochée = déjà en base (rien à faire). Décochée = nouvelle : cochez celles à ajouter. « Récupérer » enregistre en base les matières cochées et nouvelles.'}
            </p>
          </div>

          <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
            {matieres.map((m, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px',
                borderTop: i ? '1px solid #f1f5f9' : 'none', background: m.en_base ? '#f8fafc' : '#fff' }}>
                <input type="checkbox" checked={m.en_base || m.cochee} disabled={m.en_base}
                  title={m.en_base ? 'Déjà en base — pour l’enlever, utilisez « Retirer »' : 'Cocher pour ajouter cette matière'}
                  onChange={() => toggleCochee(i)} />
                {editIndex === i ? (
                  <input style={{ ...champ, flex: 1 }} value={editNom} autoFocus
                    onChange={e => setEditNom(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') validerRenommage(); if (e.key === 'Escape') { setEditIndex(-1); setEditNom('') } }}
                    onBlur={validerRenommage} title="Nouveau libellé de la matière" />
                ) : (
                  <span style={{ flex: 1, fontSize: 13, color: '#1e293b' }}>{m.nom}</span>
                )}
                <span style={{ fontSize: 11, fontWeight: 600, color: m.en_base ? '#16a34a' : '#2563eb' }}>
                  {m.en_base ? 'déjà en base' : 'nouvelle'}
                </span>
                <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px' }}
                  title="Renommer cette matière (garde le même identifiant)" onClick={() => demarrerRenommage(i)}>
                  Renommer
                </button>
                <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px' }}
                  title={m.en_base ? 'Retirer cette matière de ce niveau' : 'Retirer cette matière de la liste'}
                  onClick={() => retirer(i)}>
                  Retirer
                </button>
              </div>
            ))}
            {matieres.length === 0 && (
              <div style={{ padding: '10px', fontSize: 12, color: '#94a3b8' }}>
                Aucune matière à afficher pour l’instant.
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input style={{ ...champ, flex: 1 }} value={nouvelleMatiere}
              onChange={e => setNouvelleMatiere(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') ajouterMain() }}
              placeholder="Ajouter une matière à la main…" />
            <button type="button" className="btn-action" title="Ajouter cette matière à la liste"
              onClick={ajouterMain}>+ Ajouter</button>
          </div>

          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <button type="button" className="btn-primary" title="Enregistrer en base les matières cochées et nouvelles"
              onClick={recuperer} disabled={busy}>{busy ? 'Enregistrement…' : 'Récupérer'}</button>
            {bilanApercu && <span style={{ fontSize: 12, color: '#475569' }}>{bilanApercu}</span>}
          </div>
        </div>
      )}

      {/* Fenêtre de relecture : le PDF d'origine, repliable (clic dehors ou ×). */}
      {showPdf && dejaTraite && (
        <div onClick={() => setShowPdf(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                {etat.referentiel?.fichier || 'Référentiel'}
              </span>
              <button type="button" onClick={() => setShowPdf(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <iframe
              title="Référentiel PDF"
              src={`/api/admin/referentiels/pdf?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`}
              style={{ flex: 1, width: '100%', border: 'none' }} />
          </div>
        </div>
      )}

      {/* Modale explicative « Par IA » — l'idée est posée, la fonction n'est pas encore branchée. */}
      {showParIa && (
        <div onClick={() => setShowParIa(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 460, padding: '24px 24px 20px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#1e293b', marginBottom: 12 }}>
              « Par IA » — bientôt disponible
            </div>
            <div style={{ fontSize: 13, color: '#334155', lineHeight: 1.6 }}>
              <p style={{ marginBottom: 10 }}>
                Ce bouton laissera aSchool <strong>chercher lui-même, sur le web, le référentiel officiel</strong> de
                ce couple (cycle + niveau + matière). Il vous proposera le document trouvé, et
                <strong> c’est vous qui validez</strong>.
              </p>
              <p style={{ marginBottom: 10 }}>
                Un seul document officiel, jamais une liste. aSchool <strong>n’invente jamais un lien</strong> :
                s’il ne trouve pas la source officielle, il ne propose rien.
              </p>
              <p style={{ marginBottom: 0 }}>
                <strong>Pas encore actif :</strong> cette recherche demande une intelligence capable de naviguer
                sur le web, en préparation. En attendant, utilisez <strong>« Par dépôt »</strong> ou
                <strong> « Par lien »</strong>.
              </p>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 18 }}>
              <button type="button" className="btn-primary" title="Fermer cette explication"
                onClick={() => setShowParIa(false)}>
                J’ai compris
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
