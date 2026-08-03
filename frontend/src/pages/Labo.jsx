// ── LABO — Ajout d'un référentiel · ÉTAPE 1 : fournir le document ─────────────────────────
// Bac à sable : on met la procédure au point isolément, avec les VRAIS appels sur la base
// réelle (aucune maquette, aucune donnée en dur), avant de l'intégrer dans Admin → Référentiels.
//
// L'ÉCRAN EST CELUI QUE L'ADMIN CONNAÎT. Disposition, onglets, libellés, styles : tout est
// recopié de pages/AdminReferentiels.jsx (colonne des catalogues + carte « Document PDF »).
// Ce qui est neuf dans ce chantier, c'est la plomberie et l'enchaînement des étapes — pas
// l'écran. Rien n'est redessiné, rien n'est « amélioré » au passage.
//
// Étape 1 — le premier geste de l'ajout, c'est le PDF. Deux portes, une à la fois (onglets),
// qui rendent la même chose ({token, filename, taille_ko, pages, apercu}) :
//   POST /api/admin/referentiels/preparer-depot  — le fichier (multipart, champ `file`)
//   POST /api/admin/referentiels/preparer-lien   — le lien ({"url": "…"})
import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD, TIMEOUT_LONG } from '../utils/api.js'
import { showError } from '../errorDialog.js'
import { demanderConfirmation } from '../confirmDialog.js'
import { Spinner } from '../components/icones.jsx'

// Pastille d'étape — recopiée telle quelle d'AdminReferentiels.jsx, où elle n'est pas exportée.
function Pastille({ etat, titre }) {
  const couleur = { vert: '#16a34a', rouge: '#dc2626', jaune: '#facc15' }[etat] || '#facc15'
  return (
    <span title={titre} style={{ display: 'inline-block', width: 11, height: 11, borderRadius: '50%',
      background: couleur, border: '1px solid rgba(0,0,0,0.12)', flexShrink: 0,
      verticalAlign: 'middle', marginRight: 8 }} />
  )
}

export default function Labo() {
  const [refsListe, setRefsListe] = useState([])   // colonne 2 : référentiels déposés (GET /liste)
  const [cycleId, setCycleId] = useState('')       // couple ouvert par la colonne (comme l'existant)
  // `niveauId` de l'écran existant n'est pas repris ici : il n'y sert qu'à `valider` et
  // `verifier-depot`, deux étapes que le labo n'a pas encore. Il reviendra avec elles.
  const [niveau, setNiveau] = useState('')
  const [mode, setMode] = useState('depot')        // 'depot' | 'lien'
  const [url, setUrl] = useState('')
  const [nomFichier, setNomFichier] = useState('') // nom du PDF choisi (zone « Par dépôt »)
  const [busy, setBusy] = useState(false)
  const [apercu, setApercu] = useState(null)       // la réponse du serveur au dépôt
  const [showPdf, setShowPdf] = useState(false)    // fenêtre de relecture du PDF en attente
  const [refCourant, setRefCourant] = useState(null)  // la ligne de la colonne actuellement ouverte
  const [supprBusy, setSupprBusy] = useState(false)
  const [blocages, setBlocages] = useState({ bloques: 0, a_informer: 0, profs: [] })

  // La liste des référentiels déposés, lue EN BASE (GET /liste). Aucune donnée recopiée.
  // Déclarée AVANT l'effet qui l'appelle (eslint react-hooks refuse l'ordre inverse).
  function chargerListe() {
    fetchWithTimeout('/api/admin/referentiels/liste', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) setRefsListe(d.referentiels || []) })
      .catch(() => {})
  }

  useEffect(() => { chargerListe() }, [])

  // Clic sur une ligne de la colonne : sélectionne le couple. La suite de l'écran (carte Couple,
  // matières, découpe) n'existe pas encore dans le labo — elle viendra étape par étape.
  // Qui est en attente sur ce niveau — lu EN BASE. Rend le bouton de déblocage visible tant
  // qu'il reste des lignes, et permet de relire la liste après coup.
  function chargerBlocages(r) {
    if (!r) { setBlocages({ bloques: 0, a_informer: 0, profs: [] }); return }
    const q = `cycle_id=${Number(r.cycle_id)}&niveau=${encodeURIComponent(r.niveau)}`
    fetchWithTimeout(`/api/admin/referentiels/blocages?${q}`, { credentials: 'include' }, TIMEOUT_STD)
      .then(x => (x.ok ? x.json() : null))
      .then(d => { if (d) setBlocages(d) })
      .catch(() => {})
  }

  function ouvrirRef(r) {
    setCycleId(String(r.cycle_id)); setNiveau(r.niveau); setRefCourant(r); chargerBlocages(r)
  }

  // « + Nouveau » : remet l'écran en création — aucun couple choisi, zone de dépôt vierge.
  function nouveau() {
    setCycleId(''); setNiveau(''); setRefCourant(null)
    setBlocages({ bloques: 0, a_informer: 0, profs: [] })
    setApercu(null); setNomFichier(''); setUrl('')
  }

  // Supprimer POUR DE BON le référentiel du couple ouvert — le geste qu'on fait quand l'Éducation
  // nationale publie une nouvelle version : on ne rafistole pas, on efface et on refait la
  // procédure depuis le début.
  //
  // DEUX boîtes, l'une après l'autre. La première ÉNUMÈRE ce qui part, avec les comptes LUS EN
  // BASE (get supprimer-bilan) — l'admin lit ce qu'il perd, il ne le devine pas. La seconde est le
  // garde-fou : maintenant qu'il a vu la liste, on redemande. C'est seulement là que ça part.
  async function supprimerReferentiel(r) {
    setSupprBusy(true)
    try {
      const q = `cycle_id=${Number(r.cycle_id)}&niveau=${encodeURIComponent(r.niveau)}`
      const rb = await fetchWithTimeout(`/api/admin/referentiels/supprimer-bilan?${q}`,
        { credentials: 'include' }, TIMEOUT_STD)
      const b = await rb.json().catch(() => ({}))
      if (!rb.ok) { showError(b.detail || `Lecture impossible (${rb.status}).`); return }
      if (!b.existe) { showError('Aucun référentiel à supprimer pour ce couple.'); return }

      const lignes = [
        `• ${b.matieres} matière(s)`,
        `• ${b.unites} unité(s) de découpe`,
        `• ${b.types} type(s) d’activité et leurs ${b.precisions} précision(s)`,
        `• le document PDF${b.fichier ? ` « ${b.fichier} »` : ''}${b.pdf ? '' : ' (déjà absent du disque)'}`,
      ].join('\n')
      // Les profs NOMMÉMENT, jamais un nombre : l'admin doit savoir qui il met en attente.
      const qui = (b.profs_liste || []).map(p =>
        `• ${[p.prenom, p.nom].filter(Boolean).join(' ') || '(sans nom)'} — ${p.email}${p.matiere ? ` — ${p.matiere}` : ''}`).join('\n')
      const alerte = b.profs > 0
        ? `\n\n${b.profs} professeur(s) travaillent sur ce référentiel :\n\n${qui}\n\n`
          + 'Ils seront mis en attente : ils ne pourront plus générer sur ce niveau, et ils recevront '
          + 'un message le leur expliquant. Leur matière sera rebranchée quand vous les débloquerez, '
          + 'après la nouvelle procédure.'
        : ''
      // Ce qui PART et ce qui RESTE, tous les deux : une liste de pertes sans son contrepoids
      // laisse croire qu'on efface plus que ça (le couple, les comptes). Chiffres lus en base.
      if (!await demanderConfirmation({
        titre: `Supprimer le référentiel « ${r.cycle} · ${r.niveau} » ?`,
        message: 'Action irréversible.\n\nSeront définitivement supprimés :\n\n'
          + `${lignes}\n\n`
          + 'Ne sont pas touchés : le cycle, le niveau, et les comptes des professeurs.\n\n'
          + 'Les matières et les unités se reconstruisent en refaisant la procédure avec le '
          + `nouveau document.${alerte}`,
        confirmLabel: 'Continuer',
      })) return

      if (!await demanderConfirmation({
        titre: 'Confirmer la suppression',
        message: `Êtes-vous sûr de vouloir supprimer le référentiel « ${r.cycle} · ${r.niveau} » ?`
          + (b.profs > 0 ? `\n\n${b.profs} professeur(s) seront mis en attente au même instant.` : '')
          + '\n\nCette action est définitive.',
        icone: 'interdit',
        confirmLabel: b.profs > 0 ? 'Supprimer et mettre en attente' : 'Supprimer définitivement',
        danger: true,
      })) return

      const rs = await fetchWithTimeout('/api/admin/referentiels/supprimer', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        // Le geste ASSUMÉ : c'est ce drapeau, posé seulement après les deux boîtes, qui autorise
        // le serveur à mettre les profs en attente. Sans lui, il refuse comme avant.
        body: JSON.stringify({ cycle_id: Number(r.cycle_id), niveau: r.niveau, bloquer_profs: b.profs > 0 }),
      }, TIMEOUT_LONG)
      const d = await rs.json().catch(() => ({}))
      if (!rs.ok) { showError(d.detail || `Suppression impossible (${rs.status}).`); return }
      nouveau()        // le couple ouvert n'existe plus : l'écran repart en création
      chargerListe()   // et la colonne se relit EN BASE (zéro copie)
      if (d.profs_bloques) {
        await demanderConfirmation({
          titre: 'Référentiel supprimé',
          message: `${d.profs_bloques} professeur(s) sont en attente et ont été prévenus.\n\n`
            + 'Déposez le nouveau document et menez la procédure jusqu’au découpage, puis revenez '
            + 'sur ce couple pour les débloquer.',
          boutonUnique: true, confirmLabel: 'J’ai compris',
        })
      }
    } catch (e) { showError(`Suppression impossible.\n\n${e.message}`) }
    finally { setSupprBusy(false) }
  }

  // Le déblocage — geste EXPLICITE, jamais déclenché par la fin de la découpe : l'admin seul sait
  // si la nouvelle procédure est vraiment en place. Le serveur rebranche chaque prof par le NOM de
  // sa matière ; on rend compte des deux issues, nommément.
  async function debloquer(r) {
    if (!await demanderConfirmation({
      titre: `Débloquer les professeurs de « ${r.cycle} · ${r.niveau} » ?`,
      message: `${blocages.bloques} professeur(s) en attente vont pouvoir générer de nouveau.\n\n`
        + 'Leur matière sera rebranchée sur le nouveau référentiel, par son nom. Celles que le '
        + 'nouveau document ne nomme plus ne peuvent pas être devinées : ces professeurs seront '
        + 'libérés et invités à rechoisir dans leur profil.',
      confirmLabel: 'Débloquer',
    })) return
    setSupprBusy(true)
    try {
      const rd = await fetchWithTimeout('/api/admin/referentiels/debloquer', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(r.cycle_id), niveau: r.niveau }),
      }, TIMEOUT_LONG)
      const d = await rd.json().catch(() => ({}))
      if (!rd.ok) { showError(d.detail || `Déblocage impossible (${rd.status}).`); return }
      const nom = p => `• ${[p.prenom, p.nom].filter(Boolean).join(' ') || '(sans nom)'} — ${p.email}`
      const perdus = d.non_rebranches || []
      await demanderConfirmation({
        titre: 'Professeurs débloqués',
        message: `${(d.rebranches || []).length} professeur(s) ont retrouvé leur matière.\n\n`
          + (perdus.length
            ? `${perdus.length} n’ont PAS pu être rebranchés — le nouveau document ne nomme plus `
              + `leur matière. Ils sont libérés et invités à rechoisir dans leur profil :\n\n`
              + perdus.map(nom).join('\n')
            : 'Aucun professeur laissé sans matière.'),
        icone: perdus.length ? 'interdit' : undefined,
        boutonUnique: true, confirmLabel: 'J’ai compris',
      })
      chargerBlocages(r)
    } catch (e) { showError(`Déblocage impossible.\n\n${e.message}`) }
    finally { setSupprBusy(false) }
  }

  // Après un dépôt réussi. Document INCONNU : le PDF s'ouvre directement, comme avant. Document
  // DÉJÀ CONNU : aucun message posé sur la page — une boîte de dialogue le dit (sens interdit
  // rouge), et le PDF ne s'ouvre QUE si l'admin clique « Voir le PDF ». Le dépôt, lui, a abouti
  // dans les deux cas : on prévient, on ne bloque pas.
  async function apresDepot(d) {
    setApercu(d)
    if (!d.deja) { setShowPdf(true); return }
    const message = d.deja.ou === 'attente'
      ? `Ce document est déjà en zone d’attente.\n\nIl y a été déposé le ${d.deja.depose_le.replace('T', ' à ')} sous le nom « ${d.deja.fichier} ».\n\nC’est le même fichier, quel que soit son nom : la comparaison porte sur son contenu.\n\nVotre dépôt a bien été enregistré — vous pouvez continuer.`
      : `Ce document est déjà le référentiel de ${d.deja.cycle} · ${d.deja.niveau}.${d.deja.fichier ? `\n\nIl y est enregistré sous le nom « ${d.deja.fichier} ».` : ''}\n\nC’est le même fichier, quel que soit son nom : la comparaison porte sur son contenu.\n\nVotre dépôt a bien été enregistré — vous pouvez continuer.`
    if (await demanderConfirmation({
      titre: 'Ce document est déjà connu',
      message,
      icone: 'interdit',
      cancelLabel: 'Fermer',
      confirmLabel: 'Voir le PDF',
    })) setShowPdf(true)
  }

  async function recupererLien() {
    if (!url.trim()) { showError('Collez d’abord le lien du PDF.'); return }
    setBusy(true); setApercu(null)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/preparer-lien', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      // Pas d'`await` ici : le dépôt est terminé (le bouton doit se dégriser tout de suite), et
      // la suite — fenêtre du PDF ou dialogue — attend l'admin, pas le serveur.
      apresDepot(d)
    } catch (e) { showError(`Récupération impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  async function recupererDepot(file) {
    if (!file) return
    setNomFichier(file.name)
    setBusy(true); setApercu(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const r = await fetchWithTimeout('/api/admin/referentiels/preparer-depot', {
        method: 'POST', credentials: 'include', body: form,
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      // Pas d'`await` ici : le dépôt est terminé (le bouton doit se dégriser tout de suite), et
      // la suite — fenêtre du PDF ou dialogue — attend l'admin, pas le serveur.
      apresDepot(d)
    } catch (e) { showError(`Lecture du fichier impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  const champ = { width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 10px', fontSize: 13 }
  const onglet = (actif) => ({
    fontSize: 12, padding: '6px 14px', borderRadius: 6, cursor: 'pointer',
    border: actif ? '1px solid #1F6EEB' : '1px solid #e2e8f0',
    background: actif ? '#eff6ff' : '#f8fafc', color: actif ? '#1d4ed8' : '#64748b', fontWeight: 600,
  })

  return (
    <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>

      {/* Colonne 2 — liste des référentiels déposés (get /liste). Clic = ouvre le couple à droite. */}
      <aside style={{ width: 240, flexShrink: 0, background: '#fff', border: '1px solid #e2e8f0',
        borderRadius: 12, overflow: 'hidden',
        position: 'sticky', top: 0, alignSelf: 'flex-start' }}>
        <div style={{ padding: '10px 12px', borderBottom: '1px solid #e2e8f0', fontSize: 12,
          fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Catalogues ({refsListe.length})
        </div>
        {/* « + Nouveau » en premier, couleur distincte, sélectionné par défaut (aucun référentiel ouvert). */}
        {(() => {
          const nouveauActif = !refsListe.some(r => String(r.cycle_id) === String(cycleId) && r.niveau === niveau)
          return (
            <button type="button" onClick={nouveau}
              title="Créer un nouveau référentiel (choisir un couple, déposer le PDF)"
              style={{ width: '100%', height: 42, cursor: 'pointer',
                border: '1px solid #334155', borderRadius: 8, fontWeight: 600, fontSize: 13,
                background: nouveauActif ? '#334155' : '#0f172a', color: '#fff',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
              <span aria-hidden="true" style={{ fontSize: 22, lineHeight: 0, fontWeight: 400 }}>＋</span>
              Nouveau
            </button>
          )
        })()}
        {refsListe.length === 0 ? (
          <div style={{ padding: 12, fontSize: 12, color: '#94a3b8' }}>Aucun référentiel déposé.</div>
        ) : refsListe.map(r => {
          const actif = String(cycleId) === String(r.cycle_id) && niveau === r.niveau
          return (
            <button key={r.id} type="button" onClick={() => ouvrirRef(r)}
              title={`${r.cycle} · ${r.niveau}`}
              style={{ display: 'block', width: '100%', textAlign: 'left', padding: '9px 12px',
                border: 'none', borderBottom: '1px solid #f1f5f9', cursor: 'pointer', fontSize: 13,
                background: actif ? '#eff6ff' : '#fff', color: actif ? '#1d4ed8' : '#1e293b',
                fontWeight: actif ? 600 : 400 }}>
              <Pastille etat={r.complet ? 'vert' : 'rouge'}
                titre={r.complet ? 'Procédure complète' : 'Procédure à terminer'} />
              {r.cycle} · {r.niveau}
              {r.forcage_motif && <span title="Validé en forçage" style={{ marginLeft: 6, color: '#b45309' }}>⚠</span>}
            </button>
          )
        })}
      </aside>

      {/* Colonne 3 — l'écran de travail du référentiel. */}
      <div className="flex flex-col gap-6" style={{ flex: 1, minWidth: 0 }}>
      <div>
        <h2 className="text-base font-semibold text-gray-800">Référentiels</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Fournissez le référentiel officiel (par lien ou en déposant le PDF), vérifiez que c’est le bon document, puis validez : le système le range et en extrait le texte.
        </p>
      </div>

      {/* Carte — le référentiel ouvert par la colonne. Elle ne porte pour l'instant que le geste
          de suppression ; le reste de la procédure viendra étape par étape. Bouton rouge repris
          tel quel de l'écran Référentiels. */}
      {refCourant && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center justify-between gap-4 flex-wrap">
          <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
            <Pastille etat={refCourant.complet ? 'vert' : 'rouge'}
              titre={refCourant.complet ? 'Procédure complète' : 'Procédure à terminer'} />
            {refCourant.cycle} · {refCourant.niveau}
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {/* Débloquer : visible tant qu'il reste des professeurs en attente sur ce niveau.
                Geste explicite — jamais déclenché par la fin de la découpe. */}
            {blocages.bloques > 0 && (
              <button type="button" onClick={() => debloquer(refCourant)} disabled={supprBusy}
                title={`Rendre la main aux ${blocages.bloques} professeur(s) en attente : leur matière est rebranchée sur ce référentiel, par son nom`}
                style={{ height: 30, display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
                  fontSize: 12, fontWeight: 700, padding: '0 12px', borderRadius: 6,
                  cursor: supprBusy ? 'not-allowed' : 'pointer',
                  background: supprBusy ? '#e2e8f0' : '#1F6EEB', color: supprBusy ? '#94a3b8' : '#fff',
                  border: 'none' }}>
                <span aria-hidden="true">🔓</span> Débloquer {blocages.bloques} professeur(s)
              </button>
            )}
            <button type="button" onClick={() => supprimerReferentiel(refCourant)} disabled={supprBusy}
              title="Supprimer définitivement ce référentiel (efface la fiche, ses matières, ses unités, ses types et le PDF)"
              style={{ height: 30, display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
                fontSize: 12, fontWeight: 700, padding: '0 12px', borderRadius: 6,
                cursor: supprBusy ? 'not-allowed' : 'pointer',
                background: '#fee2e2', color: '#dc2626', border: '1px solid #fecaca' }}>
              <span aria-hidden="true">⛔</span> Supprimer le référentiel
            </button>
          </div>
        </div>
      )}

      {/* Carte 0 — Document PDF : le dépôt vient EN PREMIER (« PDF d'abord »). */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
        <div>
          <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
            <Pastille etat={apercu ? 'vert' : 'rouge'} titre="Vert = un document PDF est en zone d'attente." />
            Document PDF
          </h2>
          <p className="text-sm text-gray-500" style={{ margin: 0 }}>
            Fournissez le référentiel officiel (dépôt ou lien), puis laissez l’IA détecter le cycle et le niveau — la carte Couple s’ouvre une fois le couple validé.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" title="Déposer le fichier PDF du référentiel" style={onglet(mode === 'depot')} onClick={() => setMode('depot')}>Par dépôt</button>
          <button type="button" title="Fournir le référentiel par un lien vers le PDF" style={onglet(mode === 'lien')} onClick={() => setMode('lien')}>Par lien</button>
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
              style={{ cursor: busy ? 'default' : 'pointer', opacity: busy ? 0.6 : 1, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              {busy ? <><Spinner /> Lecture…</> : 'Choisir le fichier'}
            </label>
          </div>
        )}
        {apercu && (
          <div style={{ fontSize: 12, color: '#475569' }}>
            Document en attente : <strong>{apercu.filename}</strong> · {apercu.pages} page(s) · {apercu.taille_ko} Ko{' '}
            <button type="button" onClick={() => setShowPdf(true)}
              title="Ouvrir le PDF déposé pour le relire"
              style={{ background: 'none', border: 'none', padding: 0, color: '#1d4ed8',
                fontSize: 12, fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}>
              Voir le PDF
            </button>
          </div>
        )}
      </div>
      </div>

      {/* Fenêtre de relecture : le PDF en attente, repliable (clic dehors ou ×). Patron recopié
          d'AdminReferentiels.jsx ; seule la source change — le document n'est pas encore rangé
          sous un couple, il est désigné par son jeton. */}
      {showPdf && apercu && (
        <div onClick={() => setShowPdf(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                {apercu.filename || 'Référentiel'}
              </span>
              <button type="button" onClick={() => setShowPdf(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <iframe
              title="Référentiel PDF"
              src={`/api/admin/referentiels/depot-pdf?token=${encodeURIComponent(apercu.token)}`}
              style={{ flex: 1, width: '100%', border: 'none' }} />
          </div>
        </div>
      )}
    </div>
  )
}
