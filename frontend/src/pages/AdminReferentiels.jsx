// Page Référentiels — Étape 1 du chantier « Référentiel → matières + chunks ».
// L'admin déclare le couple (cycle + niveau), fournit le PDF officiel par LIEN ou
// par DÉPÔT, CONTRÔLE l'aperçu du document récupéré, puis valide : le système le
// range, en extrait le texte et enregistre sa provenance.
// Hors périmètre étape 1 : extraction des matières, chunks, recherche web automatique.
import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD, TIMEOUT_LONG, MSG_TIMEOUT } from '../utils/api.js'
import { showError } from '../errorDialog.js'

// Sablier — indicateur d'attente pendant un appel IA lent (génération / découpe). Même motif
// que Consigne/Ambiguites : SVG animé via l'@keyframes `spin` global (index.css).
function Spinner() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}>
      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
    </svg>
  )
}

// Pastille d'étape — voyant vert/rouge/gris posé DANS le titre de la cartouche concernée.
// C'est un REFLET lu en base (get), jamais un statut recopié : la couleur est calculée à
// l'affichage à partir de l'état déjà chargé. vert = validé en base, rouge = pas encore,
// gris = non déterminé ici (ex. cas flous = appel IA à la demande).
function Pastille({ etat, titre }) {
  // vert = fait/validé · rouge = à faire · jaune canari = non vérifié (cas flous, ingéré).
  const couleur = { vert: '#16a34a', rouge: '#dc2626', jaune: '#facc15' }[etat] || '#facc15'
  return (
    <span title={titre} style={{ display: 'inline-block', width: 11, height: 11, borderRadius: '50%',
      background: couleur, border: '1px solid rgba(0,0,0,0.12)', flexShrink: 0,
      verticalAlign: 'middle', marginRight: 8 }} />
  )
}

// Construit les lignes de la table matières à partir de l'état du couple (endpoint /etat) :
// d'abord les matières DÉJÀ en base (cochée figée), puis les CANDIDATES proposées non encore
// en base (nouvelles, à cocher par l'admin). Les candidates viennent de la BASE
// (table matieres_candidates, une ligne par niveau) — l'app ne les calcule jamais.
function construireLignesMatieres(etatObj) {
  const enBase = (etatObj?.matieres || []).map(m => ({ id: m.id, nom: m.nom, en_base: true, cochee: true }))
  const nomsEnBase = new Set(enBase.map(m => m.nom.toLowerCase()))
  const nouvelles = (etatObj?.candidates || [])
    .filter(nom => !nomsEnBase.has(nom.toLowerCase()))
    .map(nom => ({ id: null, nom, en_base: false, cochee: false }))
  return [...enBase, ...nouvelles]
}

export default function AdminReferentiels() {
  const [couples, setCouples] = useState([])    // les 137 famille-couples (GET /admin/fc-autorisees)
  const [coupleId, setCoupleId] = useState('')  // id du couple choisi dans le menu unique
  const [refsListe, setRefsListe] = useState([])  // colonne 2 : référentiels déposés (GET /admin/referentiels/liste)
  const [cycleId, setCycleId] = useState('')    // dérivé du couple choisi (cycle_id de la ligne)
  const [niveau, setNiveau] = useState('')      // dérivé du couple choisi (nom du niveau)
  const [mode, setMode] = useState('depot')       // 'depot' | 'lien'
  const [url, setUrl] = useState('')
  const [nomFichier, setNomFichier] = useState('')  // nom du PDF choisi (zone « Par dépôt »)
  const [source, setSource] = useState('')
  const [busy, setBusy] = useState(false)
  const [apercu, setApercu] = useState(null)      // { token, filename, pages, taille_ko, apercu }
  const [resultat, setResultat] = useState(null)  // { cycle, niveau, dossier, pages, caracteres_extraits, nom_fixe }
  const [familleId, setFamilleId] = useState('')  // famille retenue pour le PDF en cours de dépôt
  const [detectFamille, setDetectFamille] = useState(false)  // classement IA en cours
  const [detection, setDetection] = useState(null)      // { scenario:'match', famille } | { scenario:'candidate', candidate }
  const [familleValidee, setFamilleValidee] = useState(false)  // l'admin a validé la famille → le bloc document apparaît
  const [cand, setCand] = useState(null)          // fiche candidate éditable (6 champs)
  const [familleBusy, setFamilleBusy] = useState(false)
  // Vérifications au dépôt (backend verifier-depot) : { couple:{correspond,niveau_lu,raison}, famille:{existe} }
  // 'loading' pendant l'appel, null au repos. Le document à valider ne s'affiche que si les deux passent.
  const [verif, setVerif] = useState(null)
  const [forcageMotif, setForcageMotif] = useState('')   // motif obligatoire si l'admin force malgré une alerte
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
  const [showSuppr, setShowSuppr] = useState(false)  // modale de confirmation de suppression du référentiel
  const [supprBusy, setSupprBusy] = useState(false)  // suppression en cours (bouton grisé)
  // Cas exceptionnel Matières → Prompt : interrupteur d'AFFICHAGE (navigation front, pas de la donnée
  // métier). Le bouton « Générer le prompt » de la carte Matières le passe à true → la cartouche Prompt
  // s'affiche. Remis à false à chaque changement de couple / « Nouveau ». La carte Prompt s'affiche aussi
  // toute seule si un prompt existe déjà en base (promptDecoupe non vide) — travail déjà fait.
  const [afficherPrompt, setAfficherPrompt] = useState(false)
  const [matieresOuvert, setMatieresOuvert] = useState(true)   // bloc Matières repliable (vue d'ensemble)
  // Prompt de découpe du couple — GÉNÉRÉ PAR L'IA, stocké en base, corrigé/validé par l'admin.
  const [promptDecoupe, setPromptDecoupe] = useState('')       // texte éditable du prompt
  const [promptValide, setPromptValide] = useState(false)      // garde-fou : découpe refusée tant que false
  const [decoupeValide, setDecoupeValide] = useState(false)    // étape FINALE : découpe validée → puce verte (lu via /prompt-decoupe)
  const [promptBusy, setPromptBusy] = useState('')             // 'generer' | 'regenerer' | 'valider' | 'decouper' | ''
  const [remarques, setRemarques] = useState('')              // remarques admin (français clair) pour régénérer le prompt
  const [decoupeUnites, setDecoupeUnites] = useState(null)     // résultat de la découpe : [{titre, taille}]
  const [promptOuvert, setPromptOuvert] = useState(true)

  useEffect(() => {
    fetchWithTimeout('/api/admin/fc-autorisees', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) setCouples(d.couples || []) })
      .catch(() => {})
    chargerListe()
  }, [])

  // Colonne 2 : la liste des référentiels déposés, lue EN BASE (GET /liste). Rechargée après chaque
  // validation (un nouveau référentiel apparaît). Aucune donnée recopiée : on relit la base.
  function chargerListe() {
    fetchWithTimeout('/api/admin/referentiels/liste', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) setRefsListe(d.referentiels || []) })
      .catch(() => {})
  }

  // Clic sur une ligne de la colonne 2 : sélectionne le couple (comme le menu déroulant) → l'écran
  // de droite charge ce référentiel via l'effet [cycleId, niveau]. On résout le couple dans `couples`
  // (par cycle_id + niveau) pour aussi refléter le choix dans le menu déroulant.
  function ouvrirRef(r) {
    const c = couples.find(x => String(x.cycle_id) === String(r.cycle_id) && x.niveau === r.niveau)
    if (c) { setCoupleId(String(c.id)); setCycleId(String(c.cycle_id)); setNiveau(c.niveau); setFamilleId(String(c.famille_id)) }
    else { setCoupleId(''); setCycleId(String(r.cycle_id)); setNiveau(r.niveau) }
  }

  // « + Nouveau » (colonne 2) : remet l'écran en création — aucun couple choisi, tout vide.
  function nouveau() {
    // resetSteps : remet TOUS les done à false via leur source (la table les calcule depuis ces valeurs).
    setCoupleId(''); setCycleId(''); setNiveau(''); setFamilleId('')  // → familleCouple.done = false
    setEtat(null)                                                     // → pdf / matieres / prompt / decoupe.done = false (tous lus depuis etat)
  }

  // Bouton FINAL « Valider le découpage » : l'admin accepte la découpe → put decoupe_valide=true en base.
  // C'est la dernière étape : on recharge la liste pour que la puce du menu passe au vert (get, zéro copie).
  async function validerDecoupe() {
    setPromptBusy('valider-decoupe')
    try {
      // On LANCE l'ingestion en tâche de fond (réponse immédiate) — l'écriture des chunks prend ~2 min,
      // trop long pour une requête HTTP. On surveille ensuite l'aboutissement via /decoupe/statut.
      const r = await fetchWithTimeout('/api/admin/referentiels/decoupe/valider', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || "Le lancement de la découpe a échoué."); setPromptBusy(''); return }
      surveillerDecoupe(Number(cycleId), niveau)
    } catch {
      showError("Le lancement de la découpe a échoué (réseau).")
      setPromptBusy('')
    }
  }

  // Surveille l'ingestion lancée en tâche de fond : poll /decoupe/statut toutes les 3 s jusqu'à
  // decoupe_valide (puce verte) ou erreur. Le bouton reste « Validation… » (promptBusy inchangé).
  // On fige le couple (c, nv) au lancement : un changement d'écran n'égare pas la surveillance.
  function surveillerDecoupe(c, nv) {
    const tick = async () => {
      try {
        const r = await fetchWithTimeout(
          `/api/admin/referentiels/decoupe/statut?cycle_id=${c}&niveau=${encodeURIComponent(nv)}`,
          { credentials: 'include' }, TIMEOUT_STD)
        const d = await r.json().catch(() => ({}))
        if (d.decoupe_valide) {   // aboutissement lu EN BASE
          if (Number(cycleId) === c && niveau === nv) { setDecoupeValide(true); setPromptBusy('') }
          chargerListe()          // la puce du menu passe au vert (relecture base)
          return
        }
        if (d.status === 'error') {
          showError(d.message ? `La découpe a échoué : ${d.message}` : "La découpe a échoué.")
          if (Number(cycleId) === c && niveau === nv) setPromptBusy('')
          return
        }
      } catch { /* réseau momentané : on retente au prochain tick */ }
      setTimeout(tick, 3000)
    }
    setTimeout(tick, 3000)
  }

  // Bouton « Supprimer le référentiel » (DELETE encadré). Le backend REFUSE (409) si le référentiel a
  // déjà servi (unités ingérées) : on relaie alors SON vrai message d'erreur. Sinon il efface la ligne
  // + le PDF (matières et couple intacts). Après coup on RELIT l'état en base + la liste (zéro copie) :
  // le référentiel disparaît, l'écran repasse en mode dépôt.
  async function supprimerReferentiel() {
    setSupprBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/supprimer', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || "La suppression du référentiel a échoué."); return }
      setShowSuppr(false)
      const re = await fetchWithTimeout(`/api/admin/referentiels/etat?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
        { credentials: 'include' }, TIMEOUT_STD)
      const dd = await re.json().catch(() => null)
      setEtat(dd); setMatieres(construireLignesMatieres(dd)); setResultat(null); setApercu(null)
      chargerListe()   // colonne 2 : le référentiel supprimé disparaît (relecture)
    } catch { showError("La suppression du référentiel a échoué (réseau).") }
    finally { setSupprBusy(false) }
  }


  // À la sélection d'un couple (cycle + niveau) : lire son état en base. Si un référentiel
  // est DÉJÀ enregistré (« déjà traité »), on affiche son nom réel + ses matières existantes
  // et on grise la zone de dépôt. Sinon, dépôt normal.
  useEffect(() => {
    if (!cycleId || !niveau) { setEtat(null); setMatieres([]); setAfficherPrompt(false); return }
    setApercu(null); setResultat(null); setBilanApercu(''); setShowPdf(false); setAfficherPrompt(false)
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
    // Prompt de découpe du couple (EN BASE) — généré par l'IA, corrigé/validé par l'admin.
    fetchWithTimeout(`/api/admin/referentiels/prompt-decoupe?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!annule) { setPromptDecoupe(d && d.prompt ? d.prompt : ''); setPromptValide(!!(d && d.valide)); setDecoupeValide(!!(d && d.decoupe_valide)); setDecoupeUnites(null) } })
      .catch(() => { if (!annule) { setPromptDecoupe(''); setPromptValide(false); setDecoupeValide(false) } })
    return () => { annule = true }
  }, [cycleId, niveau])


  // L'IA génère le prompt de découpe du document → rempli dans la zone éditable (non validé).
  async function genererPromptDecoupe() {
    setPromptBusy('generer')
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/prompt-decoupe/generer', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau }),
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || "La génération du prompt par l'IA a échoué."); return }
      setPromptDecoupe(d.prompt || ''); setPromptValide(false); setDecoupeUnites(null)
    } catch { showError("La génération du prompt a échoué (réseau).") }
    finally { setPromptBusy('') }
  }

  // L'IA régénère le prompt en tenant compte des remarques (français clair) → remplace la zone.
  // Répétable à volonté : l'admin relit, remet une remarque, régénère, jusqu'à ce que ça lui convienne.
  async function regenererPromptDecoupe() {
    if (!promptDecoupe.trim()) { showError('Générez d’abord un prompt, puis écrivez vos remarques.'); return }
    if (!remarques.trim()) { showError('Écrivez ce qui ne va pas dans le prompt (zone « Remarques »).'); return }
    setPromptBusy('regenerer')
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/prompt-decoupe/regenerer', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, prompt_actuel: promptDecoupe, remarques }),
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || "La régénération du prompt par l'IA a échoué."); return }
      setPromptDecoupe(d.prompt || ''); setPromptValide(false); setDecoupeUnites(null)
    } catch { showError("La régénération du prompt a échoué (réseau).") }
    finally { setPromptBusy('') }
  }

  // Enregistre le prompt (corrigé ou non) et le VALIDE → puis LANCE la découpe dans la foulée.
  // Un seul point d'arrêt : ma validation. Valider = enregistré + validé + découpe lancée.
  async function validerPromptDecoupe() {
    if (!promptDecoupe.trim()) { showError('Le prompt de découpe est vide.'); return }
    setPromptBusy('valider')
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/prompt-decoupe/valider', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, prompt: promptDecoupe }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || "La validation a échoué."); return }
      setPromptValide(true)   // la découpe est une ÉTAPE À PART (cartouche « Découpe » en dessous) — pas lancée ici
    } catch { showError("La validation a échoué (réseau)."); return }
    finally { setPromptBusy('') }
  }

  // Déclenche la découpe (lecture seule) avec le prompt validé → affiche les unités produites.
  async function declencherDecoupe() {
    setPromptBusy('decouper')
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/prompt-decoupe/decouper', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau }),
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || "La découpe a échoué."); return }
      setDecoupeUnites(d.unites || [])
    } catch (e) {
      showError(e?.message === MSG_TIMEOUT
        ? "La découpe a dépassé le délai de 45 secondes et a été interrompue (délai dépassé) — ce n'est pas une panne réseau."
        : "La découpe a échoué (réseau).")
    }
    finally { setPromptBusy('') }
  }

  async function recupererLien() {
    if (!url.trim()) { showError('Collez d’abord le lien du PDF.'); return }
    setBusy(true); setApercu(null); setResultat(null)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/preparer-lien', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      }, TIMEOUT_LONG)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setApercu(d); setSource(url.trim()); setBilanApercu(''); lancerDetectionFamille(d.token)
    } catch (e) { showError(`Récupération impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  // Dès qu'un PDF est récupéré : l'IA le classe. Deux issues : une famille existante (scénario
  // match) ou une famille candidate complète (scénario candidate). Tant que l'admin n'a pas tranché,
  // rien d'autre ne s'affiche.
  async function lancerDetectionFamille(token) {
    setFamilleId(''); setDetection(null); setFamilleValidee(false); setCand(null); setVerif(null); setForcageMotif(''); setDetectFamille(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/detecter-famille', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      }, TIMEOUT_LONG)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setDetection(d)
      if (d.scenario === 'candidate') setCand(d.candidate)
      // Match = famille connue → on enchaîne AUTOMATIQUEMENT les vérifications (aucun clic).
      if (d.scenario === 'match' && d.famille) { setFamilleId(String(d.famille.id)); setFamilleValidee(true) }
    } catch (e) { showError(`Analyse de la famille impossible.\n\n${e.message}`) }
    finally { setDetectFamille(false) }
  }

  // Scénario candidate : l'admin valide la fiche (éventuellement éditée) → création en base, puis on
  // repasse en scénario match avec la nouvelle famille (le PDF repart).
  async function validerFamilleCandidate() {
    if (!cand) return
    setFamilleBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/familles', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cand),
      }, TIMEOUT_STD)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setFamilleId(String(d.id)); setDetection({ scenario: 'match', famille: d }); setFamilleValidee(true)
    } catch (e) { showError(`Création de la famille impossible.\n\n${e.message}`) }
    finally { setFamilleBusy(false) }
  }

  // Dès que la famille est validée : vérifications au dépôt (couple par l'IA + famille↔couple).
  async function lancerVerifDepot() {
    const c = couples.find(x => String(x.id) === String(coupleId))
    if (!apercu?.token || !c || !familleId) return
    setVerif('loading')
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/verifier-depot', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: apercu.token, cycle_id: Number(cycleId), niveau_id: c.niveau_id, famille_id: Number(familleId) }),
      }, TIMEOUT_LONG)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setVerif(d)
    } catch (e) { setVerif(null); showError(`Vérification du dépôt impossible.\n\n${e.message}`) }
  }

  useEffect(() => {
    if (familleValidee && familleId) lancerVerifDepot()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [familleValidee, familleId])

  // Jeter : l'admin refuse le document (scénario candidate). On efface le PDF en attente, fin.
  async function jeterDocument() {
    if (apercu?.token) {
      try {
        await fetchWithTimeout('/api/admin/referentiels/abandonner', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: apercu.token }),
        }, TIMEOUT_STD)
      } catch { /* best-effort */ }
    }
    setApercu(null); setDetection(null); setCand(null); setFamilleValidee(false); setFamilleId(''); setVerif(null); setForcageMotif(''); setNomFichier('')
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
      }, TIMEOUT_LONG)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setApercu(d); setSource('dépôt manuel'); setBilanApercu(''); lancerDetectionFamille(d.token)
    } catch (e) { showError(`Lecture du fichier impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  async function valider(forcageArg = null) {
    if (!cycleId) { showError('Choisissez d’abord le cycle.'); return }
    if (!niveau.trim()) { showError('Indiquez le niveau.'); return }
    if (!apercu) return
    setBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/valider', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        // verif_couple : on transmet le verdict IA déjà en main à l'écran ({correspond, niveau_lu,
        // raison}) pour qu'il soit FIGÉ en base (avant, il était calculé puis jeté). null s'il manque.
        body: JSON.stringify({ token: apercu.token, cycle_id: Number(cycleId), niveau: niveau.trim(), famille_id: familleId ? Number(familleId) : null, source, fichier_origine: apercu.filename, forcage_motif: forcageArg, verif_couple: (verif && verif.couple) ? verif.couple : null }),
      }, TIMEOUT_LONG)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setResultat(d); setApercu(null); setVerif(null); setForcageMotif(''); setBilanApercu('')
      chargerListe()   // un nouveau référentiel vient d'apparaître → recharger la colonne 2
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
  // Libellé « Cycle · Niveau » du couple courant, lu dans la liste des couples (get, zéro copie).
  const coupleCourant = couples.find(c => String(c.id) === String(coupleId))
  const coupleLabel = coupleCourant ? `${coupleCourant.cycle} · ${coupleCourant.niveau}` : niveau

  // Les 5 cartouches = 5 étapes, ordre FIXE. `done` = REFLET lu en base (get, zéro copie), jamais un
  // booléen stocké en double : familleCouple = couple choisi ; pdf = référentiel enregistré ;
  // matieres = matières reliées ; prompt = prompt validé ; decoupe = découpage validé. Règle unique
  // d'affichage : une carte n'est visible que si TOUT ce qui la précède est fait (estVisible). Le
  // tableau ne change jamais ; « Nouveau » ne fait que revider l'état lu → les `done` repassent à false.
  const steps = [
    { id: 'familleCouple', done: !!(cycleId && niveau) },
    { id: 'pdf',           done: dejaTraite },   // = etat.existe_referentiel (une seule source : etat)
    { id: 'matieres',      done: !!(etat?.matieres?.length > 0) },
    { id: 'prompt',        done: !!etat?.prompt_decoupe_valide },   // lu depuis etat (get), comme matieres
    { id: 'decoupe',       done: !!etat?.decoupe_valide },          // lu depuis etat (get), comme matieres
  ]
  function estVisible(id) {
    const i = steps.findIndex(s => s.id === id)
    return steps.slice(0, i).every(s => s.done)   // visible si tout ce qui précède est validé
  }

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
              style={{ display: 'block', width: '100%', textAlign: 'left', padding: '10px 12px',
                border: 'none', borderBottom: '1px solid #e2e8f0', cursor: 'pointer', fontSize: 13, fontWeight: 700,
                background: nouveauActif ? '#16a34a' : '#f0fdf4', color: nouveauActif ? '#fff' : '#166534' }}>
              + Nouveau
            </button>
          )
        })()}
        {refsListe.length === 0 ? (
          <div style={{ padding: 12, fontSize: 12, color: '#94a3b8' }}>Aucun référentiel déposé.</div>
        ) : refsListe.map(r => {
          const actif = String(cycleId) === String(r.cycle_id) && niveau === r.niveau
          return (
            <button key={r.id} type="button" onClick={() => ouvrirRef(r)}
              title={`${r.famille || '—'} · ${r.cycle} · ${r.niveau}`}
              style={{ display: 'block', width: '100%', textAlign: 'left', padding: '9px 12px',
                border: 'none', borderBottom: '1px solid #f1f5f9', cursor: 'pointer', fontSize: 13,
                background: actif ? '#eff6ff' : '#fff', color: actif ? '#1d4ed8' : '#1e293b',
                fontWeight: actif ? 600 : 400 }}>
              {/* Puce de synthèse : verte = procédure complète (lue en base via /liste : matières +
                  prompt de découpe validé), rouge = à terminer. Reflet, jamais recopié. */}
              <Pastille etat={r.complet ? 'vert' : 'rouge'}
                titre={r.complet ? 'Procédure complète' : 'Procédure à terminer'} />
              {r.cycle} · {r.niveau}
              {r.forcage_motif && <span title="Validé en forçage" style={{ marginLeft: 6, color: '#b45309' }}>⚠</span>}
            </button>
          )
        })}
      </aside>

      {/* Colonne 3 — l'écran de travail du référentiel. */}
      <div className="flex flex-col gap-6" style={{ maxWidth: 720, flex: 1 }}>
      <div>
        <h2 className="text-base font-semibold text-gray-800">Référentiels</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Fournissez le référentiel officiel (par lien ou en déposant le PDF), vérifiez que c’est le bon document, puis validez : le système le range et en extrait le texte.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">

        <h2 className="text-base font-semibold text-gray-800">
          <Pastille etat={(cycleId && niveau) ? 'vert' : 'rouge'} titre="Vert = un couple est choisi." />
          Famille-Couple
        </h2>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Couple (famille · cycle · niveau)</label>
          <select style={{ ...champ, background: '#fff' }} value={coupleId}
            onChange={e => {
              const id = e.target.value
              setCoupleId(id)
              const c = couples.find(x => String(x.id) === String(id))
              if (c) { setCycleId(String(c.cycle_id)); setNiveau(c.niveau); setFamilleId(String(c.famille_id)) }
              else { setCycleId(''); setNiveau(''); setFamilleId('') }
            }}
            title="Choisissez le couple à traiter — la famille, le cycle et le niveau en découlent">
            <option value="">— Choisissez un couple —</option>
            {Object.entries(couples.reduce((groupes, c) => {
              (groupes[c.cycle] = groupes[c.cycle] || []).push(c)
              return groupes
            }, {})).map(([cycleNom, liste]) => (
              <optgroup key={cycleNom} label={cycleNom}>
                {liste.map(c => (
                  <option key={c.id} value={c.id}>{c.famille} · {c.niveau}</option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        {/* Récap lecture seule du couple choisi : le menu fermé masque le cycle (porté par
            l'optgroup), on le réaffiche ici en clair. Lu depuis le couple sélectionné (get, zéro copie). */}
        {coupleId && (() => {
          const c = couples.find(x => String(x.id) === String(coupleId))
          if (!c) return null
          return (
            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', padding: '10px 12px',
              background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 13 }}>
              <span><span style={{ color: '#94a3b8' }}>Famille : </span><strong style={{ color: '#1e293b' }}>{c.famille}</strong></span>
              <span><span style={{ color: '#94a3b8' }}>Cycle : </span><strong style={{ color: '#1e293b' }}>{c.cycle}</strong></span>
              <span><span style={{ color: '#94a3b8' }}>Niveau : </span><strong style={{ color: '#1e293b' }}>{c.niveau}</strong></span>
            </div>
          )
        })()}

      </div>

      {/* Carte 2 — visible seulement si l'étape 1 (Famille-Couple) est faite (estVisible, règle N-1). */}
      {estVisible('pdf') && (
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
            <Pastille etat={(dejaTraite || resultat) ? 'vert' : 'rouge'} titre="Vert = une ligne référentiel existe en base pour ce couple." />
            Référentiel au format PDF
          </h2>
          {/* DELETE encadré : visible seulement si un référentiel existe (sinon rien à supprimer).
              Rouge + sens interdit ; ouvre une modale de confirmation (jamais de suppression au clic). */}
          {dejaTraite && (
            <button type="button" onClick={() => setShowSuppr(true)} disabled={supprBusy}
              title="Supprimer définitivement ce référentiel (efface la fiche + le PDF). Refusé s'il a déjà servi."
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
                fontSize: 12, fontWeight: 700, padding: '6px 12px', borderRadius: 6,
                cursor: supprBusy ? 'wait' : 'pointer',
                background: '#fee2e2', color: '#dc2626', border: '1px solid #fecaca' }}>
              ⛔ Supprimer le référentiel
            </button>
          )}
        </div>

        {dejaTraite ? (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Fichier PDF</label>
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
              <div style={{ flex: 1 }}>
                <input style={champ} value={etat.referentiel?.fichier || ''} readOnly
                  title="Nom du référentiel déjà enregistré pour ce couple" />
              </div>
              <input id="pdf-maj" type="file" accept="application/pdf,.pdf" style={{ display: 'none' }}
                disabled={busy} onChange={e => recupererDepot(e.target.files[0])} />
              <label htmlFor="pdf-maj" className="btn-primary"
                title="Choisir un nouveau PDF : il remplace le référentiel de ce couple et relance le traitement (texte, prompt, découpe). Les matières ne bougent pas."
                style={{ whiteSpace: 'nowrap', cursor: busy ? 'wait' : 'pointer' }}>
                {busy ? 'Lecture…' : 'Mettre à jour le référentiel'}
              </label>
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
            {/* Trace du forçage : motif lu EN BASE (referentiels.forcage_motif via /etat), affiché
                si l'admin a validé ce référentiel malgré une alerte. Lecture seule (zéro copie). */}
            {etat.referentiel?.forcage_motif && (
              <div style={{ marginTop: 8, padding: '10px 12px', borderRadius: 8,
                background: '#fffbeb', border: '1px solid #fde68a', fontSize: 12, color: '#92400e' }}>
                <strong>⚠ Validé en forçage</strong> — motif : {etat.referentiel.forcage_motif}
              </div>
            )}
            {/* Verdict IA du couple, FIGÉ à la validation (referentiels.verif_couple via /etat).
                Lecture seule, JSON parsé à l'affichage — zéro copie. Absent = rien affiché. */}
            {etat.referentiel?.verif_couple && (() => {
              let v = null
              try { v = JSON.parse(etat.referentiel.verif_couple) } catch { v = null }
              if (!v) return null
              // Libellé du couple + famille : lus dans la liste des couples déjà en main (fc-autorisees),
              // jamais recopiés. Affichage identique à celui du dépôt (zéro copie).
              const fc = couples.find(c => String(c.id) === String(coupleId))
              const cycleLbl = fc?.cycle || ''
              const familleLbl = fc?.famille || ''
              return (
                <div style={{ marginTop: 8, padding: '10px 12px', borderRadius: 8, fontSize: 12,
                  background: v.correspond ? '#f0fdf4' : '#fef2f2',
                  border: `1px solid ${v.correspond ? '#bbf7d0' : '#fecaca'}`,
                  color: v.correspond ? '#166534' : '#991b1b' }}>
                  <strong>{v.correspond
                    ? `✓ Couple : ${cycleLbl} / ${niveau} — confirmé par le document`
                    : `✗ Couple : ${cycleLbl} / ${niveau} — non confirmé par le document`}</strong>
                  {v.niveau_lu ? <div style={{ color: '#475569', marginTop: 2 }}>niveau lu : {v.niveau_lu}</div> : null}
                  {v.raison && <div style={{ color: '#475569', marginTop: 2 }}>{v.raison}</div>}
                  {familleLbl && <div style={{ color: '#166534', marginTop: 4 }}>✓ Cette famille ({familleLbl}) a sa place à ce niveau</div>}
                </div>
              )
            })()}
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
                  style={{ cursor: busy ? 'default' : 'pointer', opacity: busy ? 0.6 : 1, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {busy ? <><Spinner /> Lecture…</> : 'Choisir le fichier'}
                </label>
              </div>
            )}
          </>
        )}

        {/* Famille : dès qu'un PDF est récupéré, l'IA classe. Scénario match (famille trouvée + Valider)
            ou scénario candidate (structure non reconnue → fiche candidate éditable + Valider/Jeter).
            Tant que l'admin n'a pas validé la famille, le bloc document ci-dessous ne s'affiche pas. */}
        {apercu && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <label className="block text-xs text-gray-500">Famille du référentiel</label>
              {detectFamille && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#1d4ed8' }}>
                  <Spinner /> Analyse par l’IA…
                </span>
              )}
            </div>

            {/* Famille validée : rappel (le bloc document apparaît en dessous) */}
            {familleValidee && detection?.famille && (
              <div style={{ padding: '10px 12px', borderRadius: 8, border: '2px solid #16a34a', background: '#f0fdf4' }}>
                <div style={{ fontWeight: 600, fontSize: 13, color: '#166534' }}>✓ Famille : {detection.famille.nom}</div>
                <div style={{ fontSize: 12, color: '#475569', marginTop: 2 }}>{detection.famille.description}</div>
              </div>
            )}

            {/* Scénario candidate, pas encore validé : Bloc A (refus) + Bloc B (fiche éditable) + Valider/Jeter */}
            {!familleValidee && detection?.scenario === 'candidate' && cand && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ border: '1px solid #fecaca', background: '#fef2f2', borderRadius: 8, padding: 12, fontSize: 12, color: '#991b1b' }}>
                  Structure non reconnue — ce référentiel n’est pas ingéré. L’IA propose une nouvelle famille ci-dessous.
                </div>
                <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>Famille proposée par l’IA (éditable)</div>
                  {[['nom', 'Nom'], ['description', 'Description']].map(([k, lab]) => (
                    <div key={k}>
                      <label className="block text-xs text-gray-500 mb-1">{lab}</label>
                      {k === 'nom'
                        ? <input style={champ} value={cand[k] || ''} onChange={e => setCand({ ...cand, [k]: e.target.value })} />
                        : <textarea style={{ ...champ, minHeight: 48, resize: 'vertical' }} value={cand[k] || ''}
                            onChange={e => setCand({ ...cand, [k]: e.target.value })} />}
                    </div>
                  ))}
                  <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                    <button type="button" className="btn-primary" onClick={validerFamilleCandidate} disabled={familleBusy}
                      title="Créer cette famille en base et continuer"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                      {familleBusy ? <><Spinner /> Création…</> : 'Valider'}
                    </button>
                    <button type="button" className="btn-secondary" onClick={jeterDocument} disabled={familleBusy}
                      title="Refuser ce document">Jeter</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Vérifications au dépôt : couple (lu par l'IA) + famille↔couple. Le document à valider
            n'apparaît que si les DEUX passent (garde-fou). */}
        {apercu && familleValidee && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {verif === 'loading' && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#1d4ed8' }}>
                <Spinner /> Vérification du couple et de la famille…
              </span>
            )}
            {verif && verif !== 'loading' && (
              <>
                <div style={{ padding: '10px 12px', borderRadius: 8,
                  border: `2px solid ${verif.couple.correspond ? '#16a34a' : '#dc2626'}`,
                  background: verif.couple.correspond ? '#f0fdf4' : '#fef2f2' }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: verif.couple.correspond ? '#166534' : '#991b1b' }}>
                    {verif.couple.correspond
                      ? `✓ Couple : ${couples.find(c => String(c.id) === String(coupleId))?.cycle || ''} / ${niveau} — confirmé par le document`
                      : `✗ Couple : ${couples.find(c => String(c.id) === String(coupleId))?.cycle || ''} / ${niveau} — le document ne correspond pas`}
                  </div>
                  <div style={{ fontSize: 12, color: '#475569', marginTop: 2 }}>{verif.couple.raison}</div>
                </div>
                <div style={{ padding: '10px 12px', borderRadius: 8,
                  border: `2px solid ${verif.famille.existe ? '#16a34a' : '#dc2626'}`,
                  background: verif.famille.existe ? '#f0fdf4' : '#fef2f2' }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: verif.famille.existe ? '#166534' : '#991b1b' }}>
                    {verif.famille.existe ? '✓ Cette famille a sa place à ce niveau' : '✗ Cette famille n’est pas prévue pour ce niveau'}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* POINT DE CONTRÔLE : dès que les DEUX tests ont répondu. Vert → valider ; rouge → forçage motivé. */}
        {apercu && familleValidee && verif && verif !== 'loading' && (
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
            {verif.couple.correspond && verif.famille.existe ? (
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button type="button" className="btn-primary" title="Confirmer que c’est le bon document : ranger, extraire le texte, enregistrer la provenance"
                  onClick={() => valider(null)} disabled={busy} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {busy ? <><Spinner /> Validation…</> : 'Valider : c’est le bon document'}
                </button>
                <button type="button" className="btn-secondary" title="Ce n’est pas le bon document : recommencer avec un autre lien ou fichier"
                  onClick={() => { setApercu(null); setDetection(null); setCand(null); setFamilleValidee(false); setFamilleId(''); setVerif(null); setForcageMotif('') }} disabled={busy}>
                  Recommencer
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 10 }}>
                <label className="block text-xs text-gray-500">Motif du forçage (obligatoire — tracé en base)</label>
                <textarea style={{ ...champ, minHeight: 60, resize: 'vertical' }} value={forcageMotif}
                  onChange={e => setForcageMotif(e.target.value)}
                  placeholder="Expliquez pourquoi vous validez malgré l’alerte." />
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" className="btn-primary" title="Valider malgré l’alerte : le motif est tracé"
                    onClick={() => valider(forcageMotif)} disabled={busy || !forcageMotif.trim()}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    {busy ? <><Spinner /> Validation…</> : 'Forcer la validation malgré l’alerte'}
                  </button>
                  <button type="button" className="btn-secondary" title="Ce n’est pas le bon document : recommencer avec un autre lien ou fichier"
                    onClick={() => { setApercu(null); setDetection(null); setCand(null); setFamilleValidee(false); setFamilleId(''); setVerif(null); setForcageMotif('') }} disabled={busy}>
                    Recommencer
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {resultat && (
          <div style={{ border: '1px solid #bbf7d0', background: '#f0fdf4', borderRadius: 8, padding: 14, fontSize: 12, color: '#166534' }}>
            Référentiel enregistré pour <strong>{resultat.niveau}</strong> ({resultat.cycle}).<br />
            Document d’origine : <strong>{resultat.fichier_origine}</strong> (conservé en base).<br />
            Rangé dans <code>REFERENTIELS/{resultat.dossier}/referentiel.pdf</code> · {resultat.pages} page(s).
          </div>
        )}

      </div>
      )}

      {estVisible('matieres') && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <div>
              <h2 className="text-base font-semibold text-gray-800">
                <Pastille etat={(etat?.matieres?.length > 0) ? 'vert' : 'rouge'} titre="Vert = des matières sont reliées à ce niveau en base." />
                Matières de ce référentiel
                <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 6, fontSize: 13 }}>
                  ({matieres.length})
                </span>
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                {dejaTraite
                  ? 'Couple déjà traité : voici les matières déjà en base pour ce niveau. Tu peux les renommer, en retirer, ou en ajouter à la main (geste exceptionnel).'
                  : 'Cochée = déjà en base (rien à faire). Décochée = nouvelle : cochez celles à ajouter. « Récupérer » enregistre en base les matières cochées et nouvelles.'}
              </p>
            </div>
            <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title={matieresOuvert ? 'Réduire la liste des matières' : 'Développer la liste des matières'}
              onClick={() => setMatieresOuvert(o => !o)}>
              {matieresOuvert ? 'Réduire' : 'Développer'}
            </button>
          </div>

          {matieresOuvert && (
          <>
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
            {/* Grisé quand il n'y a rien à récupérer : aucune matière cochée qui ne soit PAS déjà en
                base (m.cochee && !m.en_base). État lu (get), zéro copie. Se réactive dès qu'on coche une nouvelle. */}
            <button type="button" className="btn-primary" title="Enregistrer en base les matières cochées et nouvelles"
              onClick={recuperer} disabled={busy || !matieres.some(m => m.cochee && !m.en_base)}>{busy ? 'Enregistrement…' : 'Récupérer'}</button>
            {/* Passage Matières → Prompt (cas exceptionnel). Rôle UNIQUE : afficher la cartouche Prompt.
                N'apparaît que lorsque « Récupérer » est grisé (plus rien à récupérer) ; se grise dès que
                la cartouche est affichée (prompt déjà en base ou clic fait) → jamais actif en permanence. */}
            {estVisible('prompt') && !matieres.some(m => m.cochee && !m.en_base) && (
              <button type="button" className="btn-primary"
                onClick={() => setAfficherPrompt(true)} disabled={afficherPrompt || !!promptDecoupe}
                title="Passer à l'étape suivante : afficher la cartouche « Prompt de découpe »">
                Générer le prompt
              </button>
            )}
            {bilanApercu && <span style={{ fontSize: 12, color: '#475569' }}>{bilanApercu}</span>}
          </div>
          </>
          )}
        </div>
      )}

      {/* Prompt de découpe — GÉNÉRÉ PAR L'IA (méta-prompt en base), affiché, corrigé et validé par
          l'admin. La découpe refuse de tourner tant que le prompt n'est pas validé.
          Affichage SÉQUENTIEL (règle : tant que N-1 n'est pas fini, on n'affiche pas N) : cette carte
          (N) n'apparaît que si le référentiel EXISTE en base (dejaTraite) ET que l'étape Matières (N-1)
          est faite (matières reliées au niveau, lu via /etat). Sans référentiel enregistré — ex. dépôt
          en cours, IA encore en analyse — elle reste CACHÉE, même si des matières traînent en base. */}
      {/* Carte 4 — Prompt. Visible si tout ce qui précède est fait (estVisible) ET que l'admin a
          cliqué « Générer le prompt » OU qu'un prompt existe déjà en base (travail déjà fait). */}
      {estVisible('prompt') && (afficherPrompt || !!promptDecoupe) && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <div>
              <h2 className="text-base font-semibold text-gray-800">
                <Pastille etat={promptValide ? 'vert' : 'rouge'} titre="Vert = prompt de découpe validé (referentiels.prompt_decoupe_valide)." />
                Prompt de découpe (généré par l'IA)
              </h2>
              <p className="text-sm text-gray-500">
                L'IA lit le PDF et propose le prompt qui découpe CE document. Lisez-le, corrigez-le si besoin, validez-le,
                puis déclenchez la découpe. Rien n'est écrit en dur : le prompt vit en base.
              </p>
            </div>
            <button type="button" onClick={() => setPromptOuvert(v => !v)} className="btn-secondary"
              title={promptOuvert ? 'Réduire' : 'Développer'} style={{ whiteSpace: 'nowrap' }}>
              {promptOuvert ? 'Réduire' : 'Développer'}
            </button>
          </div>
          {promptOuvert && (
            <>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
                <button type="button" className="btn-action" onClick={genererPromptDecoupe}
                  disabled={!!promptBusy} title="L'IA génère le prompt de découpe adapté à ce document">
                  {promptBusy === 'generer' ? <><Spinner /> Génération…</> : "Générer le prompt (IA)"}
                </button>
                <span style={{ fontSize: 13, fontWeight: 600, color: promptValide ? '#166534' : '#A63045' }}>
                  {promptValide ? 'Statut : validé' : 'Statut : à valider'}
                </span>
              </div>
              <textarea
                value={promptDecoupe}
                onChange={e => { setPromptDecoupe(e.target.value); setPromptValide(false) }}
                placeholder="Cliquez sur « Générer le prompt (IA) » — le prompt proposé apparaîtra ici, éditable."
                rows={12}
                style={{ width: '100%', fontFamily: 'monospace', fontSize: 12, padding: 10,
                         border: '1px solid #E5E7EB', borderRadius: 8, resize: 'vertical' }}
              />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6,
                            borderTop: '1px dashed #E5E7EB', paddingTop: 10 }}>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>
                  Remarques — dites en français clair ce qui ne va pas dans le prompt ci-dessus
                </label>
                <textarea
                  value={remarques}
                  onChange={e => setRemarques(e.target.value)}
                  placeholder="Ex. : « le prompt garde encore les renvois » ou « il ne sort que le titre, il doit sortir aussi le contenu de l'activité »."
                  rows={4}
                  style={{ width: '100%', fontSize: 13, padding: 10,
                           border: '1px solid #E5E7EB', borderRadius: 8, resize: 'vertical' }}
                />
                <div>
                  <button type="button" className="btn-action" onClick={regenererPromptDecoupe}
                    disabled={!!promptBusy || !promptDecoupe.trim() || !remarques.trim()}
                    title="L'IA reprend le prompt actuel + vos remarques et produit un nouveau prompt qui en tient compte">
                    {promptBusy === 'regenerer' ? <><Spinner /> Régénération…</> : 'Régénérer le prompt en tenant compte de ma remarque ci-dessus'}
                  </button>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {/* Grisé une fois le prompt validé en base (promptValide, lu via /prompt-decoupe).
                    Éditer le prompt remet promptValide à false (onChange) → le bouton se réactive.
                    Ce bouton NE fait QUE valider le prompt — la découpe est la cartouche d'après. */}
                <button type="button" className="btn-primary" onClick={validerPromptDecoupe}
                  disabled={!!promptBusy || !promptDecoupe.trim() || promptValide}
                  title="Valide ce prompt en base (la découpe se fait ensuite, dans la cartouche « Découpe »).">
                  {promptBusy === 'valider' ? <><Spinner /> Validation…</> : 'Valider le prompt'}
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Découpe — ÉTAPE À PART (le prompt et la découpe ne sont pas le même travail). Apparaît une fois
          le prompt validé. On découpe (aperçu, lecture seule), on contrôle les unités, puis on valide le
          découpage : dernière étape → la puce du menu passe au vert (decoupe_valide en base). */}
      {estVisible('decoupe') && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          <div>
            <h2 className="text-base font-semibold text-gray-800">
              <Pastille etat={decoupeValide ? 'vert' : 'rouge'} titre="Vert = découpage validé (referentiels.decoupe_valide) — dernière étape." />
              Découpe
            </h2>
            <p className="text-sm text-gray-500">
              Lancez la découpe avec le prompt validé, contrôlez les unités produites, puis validez le découpage — dernière étape.
            </p>
          </div>
          <div>
            <button type="button" className="btn-action" onClick={declencherDecoupe}
              disabled={!!promptBusy}
              title="Découper le référentiel avec le prompt validé (aperçu, aucune écriture).">
              {promptBusy === 'decouper' ? <><Spinner /> Découpe…</> : 'Découper'}
            </button>
          </div>
          {decoupeUnites && (
            <div style={{ borderTop: '1px solid #E5E7EB', paddingTop: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                Résultat : {decoupeUnites.length} unité(s) produite(s) par l'IA
              </div>
              <ol style={{ margin: 0, paddingLeft: 22, fontSize: 13, color: '#374151' }}>
                {decoupeUnites.map((u, i) => (
                  <li key={i} style={{ marginBottom: 2 }}>{u.titre} <span style={{ color: '#9CA3AF' }}>({u.taille} car.)</span></li>
                ))}
              </ol>
              {/* Bouton FINAL — l'admin a contrôlé la découpe et l'accepte : dernière étape, la puce
                  du menu passe au vert (decoupe_valide en base). Grisé une fois validé. */}
              <div style={{ marginTop: 12 }}>
                <button type="button" className="btn-primary" onClick={validerDecoupe}
                  disabled={!!promptBusy || decoupeValide}
                  title="Accepter ce découpage — dernière étape : le référentiel devient complet (puce verte).">
                  {promptBusy === 'valider-decoupe' ? <><Spinner /> Validation…</>
                    : decoupeValide ? '✓ Découpage validé' : 'Valider le découpage'}
                </button>
              </div>
            </div>
          )}
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

      {/* Modale de confirmation de suppression (DELETE encadré, action destructive → garde-fou explicite,
          bouton rouge + sens interdit). Le refus (référentiel déjà utilisé) est renvoyé par le backend et
          relayé tel quel via showError. Fond cliquable pour annuler (sauf pendant la suppression). */}
      {showSuppr && dejaTraite && (
        <div onClick={() => !supprBusy && setShowSuppr(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 460, padding: '24px 24px 20px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <span style={{ fontSize: 22, lineHeight: 1 }}>⛔</span>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#991b1b' }}>
                Supprimer le référentiel « {coupleLabel} » ?
              </div>
            </div>
            <div style={{ fontSize: 13, color: '#334155', lineHeight: 1.6 }}>
              <p style={{ marginBottom: 10 }}>
                <strong>Action irréversible.</strong> La fiche du référentiel et son <strong>fichier PDF</strong> seront
                définitivement supprimés.
              </p>
              <p style={{ marginBottom: 0 }}>
                Les <strong>matières</strong> et le <strong>couple</strong> ne sont pas touchés. La suppression est
                <strong> refusée</strong> si ce référentiel a déjà servi (unités déjà ingérées).
              </p>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 18 }}>
              <button type="button" onClick={() => setShowSuppr(false)} disabled={supprBusy}
                style={{ fontSize: 13, fontWeight: 600, padding: '8px 14px', borderRadius: 6, cursor: 'pointer',
                  background: '#fff', color: '#475569', border: '1px solid #cbd5e1' }}>
                Annuler
              </button>
              <button type="button" onClick={supprimerReferentiel} disabled={supprBusy}
                title="Confirmer la suppression définitive de ce référentiel"
                style={{ fontSize: 13, fontWeight: 700, padding: '8px 14px', borderRadius: 6,
                  cursor: supprBusy ? 'wait' : 'pointer',
                  background: '#dc2626', color: '#fff', border: '1px solid #dc2626' }}>
                {supprBusy ? 'Suppression…' : 'Supprimer définitivement'}
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  )
}
