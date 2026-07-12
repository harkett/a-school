// Page Référentiels — Étape 1 du chantier « Référentiel → matières + chunks ».
// L'admin déclare le couple (cycle + niveau), fournit le PDF officiel par LIEN ou
// par DÉPÔT, CONTRÔLE l'aperçu du document récupéré, puis valide : le système le
// range, en extrait le texte et enregistre sa provenance.
// Hors périmètre étape 1 : extraction des matières, chunks, recherche web automatique.
import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD, TIMEOUT_GROQ, MSG_TIMEOUT } from '../utils/api.js'
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
  // Règle de découpe du couple : { existe, explication_clair, critere_technique, depose_par, valide }
  // ou null si aucune règle n'est déposée pour ce référentiel.
  const [regle, setRegle] = useState(null)
  const [matieresOuvert, setMatieresOuvert] = useState(true)   // bloc Matières repliable (vue d'ensemble)
  const [regleOuvert, setRegleOuvert] = useState(true)         // bloc Règle de découpe repliable
  // Aperçu du découpage : { disponible, total, total_niveau, bande_niveau, options_arbitrage:[…],
  //   unites:[{titre, age_label, bandes, flou, arbitre, dans_niveau}] }
  // ou { disponible:false, raison } ; null si non applicable (pas de règle pour ce cycle).
  // (Nom distinct de `apercu`, qui est l'aperçu du PDF au dépôt.)
  const [apercuDecoupe, setApercuDecoupe] = useState(null)
  const [apercuOuvert, setApercuOuvert] = useState(true)       // bloc Résultat du découpage repliable
  // Arbitrage des cas flous : décisions enregistrées { libellé_flou: [options] }, servies par
  // GET arbitrage-flou. `selection` = choix en cours de l'admin, pré-rempli depuis les décisions.
  // Les OPTIONS proposées viennent de l'aperçu (apercuDecoupe.options_arbitrage, tenu par la
  // fiche) — jamais écrites en dur ici. `savingArbitrage` = libellé en cours d'enregistrement.
  const [selection, setSelection] = useState({})              // { age_label: [options] }
  const [savingArbitrage, setSavingArbitrage] = useState('')
  // TEMPS 2 — demander l'avis d'un professionnel sur un cas flou (statut « en attente » EN BASE).
  const [enAttente, setEnAttente] = useState([])              // [{ label, destinataire }] servis par GET en-attente
  const [demandeOuverte, setDemandeOuverte] = useState('')    // age_label dont le formulaire de demande est ouvert
  const [demandeEmail, setDemandeEmail] = useState('')
  const [demandeMessage, setDemandeMessage] = useState('')
  const [envoiDemande, setEnvoiDemande] = useState('')        // age_label en cours d'envoi
  // Prompt de découpe du couple — GÉNÉRÉ PAR L'IA, stocké en base, corrigé/validé par l'admin.
  const [promptDecoupe, setPromptDecoupe] = useState('')       // texte éditable du prompt
  const [promptValide, setPromptValide] = useState(false)      // garde-fou : découpe refusée tant que false
  const [promptBusy, setPromptBusy] = useState('')             // 'generer' | 'regenerer' | 'valider' | 'decouper' | ''
  const [remarques, setRemarques] = useState('')              // remarques admin (français clair) pour régénérer le prompt
  const [decoupeUnites, setDecoupeUnites] = useState(null)     // résultat de la découpe : [{titre, taille}]
  const [promptOuvert, setPromptOuvert] = useState(true)
  const [ambiguiteOuverte, setAmbiguiteOuverte] = useState('') // age_label dont le panneau « ambiguïté » est ouvert

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
    if (!cycleId || !niveau) { setEtat(null); setMatieres([]); setRegle(null); setApercuDecoupe(null); setSelection({}); setEnAttente([]); setDemandeOuverte(''); return }
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
    // Règle de découpe du couple (EN BASE : colonnes regle_* de referentiels, résolu par cycle + niveau).
    fetchWithTimeout(`/api/admin/referentiels/regle-decoupe?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!annule) setRegle(d && d.existe ? d : null) })
      .catch(() => { if (!annule) setRegle(null) })
    // Aperçu du découpage (lecture seule). Masqué si non applicable (pas de règle pour ce cycle).
    fetchWithTimeout(`/api/admin/referentiels/apercu-decoupage?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_GROQ)
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        if (annule) return
        const ap = d && d.raison !== 'non_applicable' ? d : null
        setApercuDecoupe(ap)
        // Garde-fou (règle « incohérence = modale ») : couple ouvert mais filtre EN ÉCHEC -> modale
        // bloquante qui OBLIGE l'admin à revenir trancher. À l'OUVERTURE du couple seulement (pas
        // après chaque arbitrage), pour ne pas le harceler pendant qu'il tranche.
        if (ap && ap.filtre && !ap.filtre.ok) {
          const n = (ap.unites || []).filter(u => u.flou && !u.arbitre).length
          showError(`Ce couple n'est pas prêt : il reste ${n} cas « âge à confirmer » à trancher.\n\nRevenez les régler dans la carte « Résultat du découpage » ci-dessus. Tant qu'ils ne sont pas tranchés, ce niveau ne peut pas être ingéré.`)
        }
      })
      .catch(() => { if (!annule) setApercuDecoupe(null) })
    // Décisions d'arbitrage des cas flous (EN BASE : colonne referentiels.arbitrage du couple).
    // On pré-remplit la sélection de l'admin avec ce qui est déjà tranché.
    fetchWithTimeout(`/api/admin/referentiels/arbitrage-flou?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!annule) setSelection(d && d.arbitrages ? d.arbitrages : {}) })
      .catch(() => { if (!annule) setSelection({}) })
    // Cas flous EN ATTENTE d'un avis (TEMPS 2) — pour afficher le badge « en attente ».
    fetchWithTimeout(`/api/admin/referentiels/arbitrage-flou/en-attente?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!annule) setEnAttente(d && d.en_attente ? d.en_attente : []) })
      .catch(() => { if (!annule) setEnAttente([]) })
    // Prompt de découpe du couple (EN BASE) — généré par l'IA, corrigé/validé par l'admin.
    fetchWithTimeout(`/api/admin/referentiels/prompt-decoupe?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!annule) { setPromptDecoupe(d && d.prompt ? d.prompt : ''); setPromptValide(!!(d && d.valide)); setDecoupeUnites(null) } })
      .catch(() => { if (!annule) { setPromptDecoupe(''); setPromptValide(false) } })
    return () => { annule = true }
  }, [cycleId, niveau])

  // Bascule une option pour un libellé flou dans la sélection en cours (avant enregistrement).
  function basculerOption(label, opt) {
    setSelection(prev => {
      const actuelles = prev[label] || []
      const majs = actuelles.includes(opt) ? actuelles.filter(o => o !== opt) : [...actuelles, opt]
      return { ...prev, [label]: majs }
    })
  }

  // Enregistre l'arbitrage d'un libellé flou (POST), puis RECHARGE l'aperçu + les décisions :
  // la ligne bascule (arbitre -> vrai, compteur du niveau réévalué). Sélection vide = dé-trancher.
  async function validerAge(label) {
    setSavingArbitrage(label)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/arbitrage-flou', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, label, bandes: selection[label] || [] }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || "L'âge n'a pas pu être enregistré."); return }
      // Recharger l'aperçu (la ligne bascule) et les décisions (source de vérité disque).
      const [ap, arb] = await Promise.all([
        fetchWithTimeout(`/api/admin/referentiels/apercu-decoupage?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
          { credentials: 'include' }, TIMEOUT_GROQ).then(x => (x.ok ? x.json() : null)).catch(() => null),
        fetchWithTimeout(`/api/admin/referentiels/arbitrage-flou?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
          { credentials: 'include' }, TIMEOUT_STD).then(x => (x.ok ? x.json() : null)).catch(() => null),
      ])
      if (ap && ap.raison !== 'non_applicable') setApercuDecoupe(ap)
      if (arb && arb.arbitrages) setSelection(arb.arbitrages)
    } catch {
      showError("L'âge n'a pas pu être enregistré (réseau).")
    } finally {
      setSavingArbitrage('')
    }
  }

  // Corps du mail d'avis pré-rempli (générique + éditable). Le SEUL spécifique vient du texte extrait
  // de l'ambiguïté (l'activité, telle quelle) — aucun mot en dur propre à un référentiel (ni « âge »,
  // ni « crèche ») : l'admin ajuste avant d'envoyer, et un autre référentiel réutilise le même squelette.
  // On pose une question ouverte ; c'est l'admin qui range ensuite la réponse.
  function construireMessageMail(extrait) {
    return [
      'Bonjour,',
      '',
      "Nous préparons des activités pédagogiques à partir des référentiels officiels. Pour l'une d'elles, nous aimerions votre avis de terrain.",
      '',
      "L'activité :",
      '« ' + (extrait || '').trim() + ' »',
      '',
      'Quel est votre avis sur cette activité ? Un simple mot en réponse nous suffit.',
      '',
      'Merci beaucoup pour votre aide.',
      '',
      'Bien cordialement,',
      "L'équipe aSchool",
    ].join('\n')
  }

  function enAttentePour(label) {
    return enAttente.find(e => e.label === label) || null
  }

  // Ouvre (ou referme) le formulaire de demande d'avis pour un cas flou : pré-remplit le message.
  function ouvrirDemande(u) {
    if (demandeOuverte === u.age_label) { setDemandeOuverte(''); return }
    setDemandeOuverte(u.age_label)
    const deja = enAttentePour(u.age_label)
    setDemandeEmail(deja ? deja.destinataire : '')
    setDemandeMessage(construireMessageMail(u.extrait))
  }

  // Déplie / replie le panneau « ambiguïté » d'un cas flou : l'admin y VOIT ce qu'il doit trancher
  // (l'indication du document + l'activité complète) avant de décider ou de demander un avis.
  function basculerAmbiguite(label) {
    setAmbiguiteOuverte(prev => (prev === label ? '' : label))
  }

  // Envoie la demande d'avis (POST /demander) : mail parti + cas « en attente », puis on recharge.
  async function envoyerDemande(label) {
    if (!demandeEmail.trim()) { showError("Indiquez l'adresse du professionnel à qui envoyer la demande."); return }
    if (!demandeMessage.trim()) { showError('Le message à envoyer est vide.'); return }
    setEnvoiDemande(label)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/arbitrage-flou/demander', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, label, email: demandeEmail.trim(), message: demandeMessage }),
      }, TIMEOUT_GROQ)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || "La demande n'a pas pu être envoyée."); return }
      // Recharger les cas en attente (le badge apparaît) et fermer le formulaire.
      const att = await fetchWithTimeout(`/api/admin/referentiels/arbitrage-flou/en-attente?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
        { credentials: 'include' }, TIMEOUT_STD).then(x => (x.ok ? x.json() : null)).catch(() => null)
      if (att && att.en_attente) setEnAttente(att.en_attente)
      setDemandeOuverte('')
    } catch {
      showError("La demande n'a pas pu être envoyée (réseau).")
    } finally {
      setEnvoiDemande('')
    }
  }

  // L'IA génère le prompt de découpe du document → rempli dans la zone éditable (non validé).
  async function genererPromptDecoupe() {
    setPromptBusy('generer')
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/prompt-decoupe/generer', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau }),
      }, TIMEOUT_GROQ)
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
      }, TIMEOUT_GROQ)
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
      setPromptValide(true)
    } catch { showError("La validation a échoué (réseau)."); return }
    finally { setPromptBusy('') }
    // Validé → la découpe se lance automatiquement (pas de second clic).
    await declencherDecoupe()
  }

  // Déclenche la découpe (lecture seule) avec le prompt validé → affiche les unités produites.
  async function declencherDecoupe() {
    setPromptBusy('decouper')
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/prompt-decoupe/decouper', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau }),
      }, TIMEOUT_GROQ)
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

  // Règle de découpe : l'admin valide (valide→true) ou rejette (valide→false) le STATUT.
  // Il ne modifie pas le texte de la règle (pas d'édition des deux faces à ce stade).
  async function majStatutRegle(action) {   // action = 'valider' | 'rejeter'
    setBusy(true)
    try {
      const r = await fetchWithTimeout(`/api/admin/referentiels/regle-decoupe/${action}`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau }),
      }, TIMEOUT_STD)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setRegle(rg => (rg ? { ...rg, valide: d.valide } : rg))
    } catch (e) { showError(`Action sur la règle impossible.\n\n${e.message}`) }
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

        <h2 className="text-base font-semibold text-gray-800">Cycle et niveau</h2>

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

      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">

        <h2 className="text-base font-semibold text-gray-800">Référentiel au format PDF</h2>

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
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <div>
              <h2 className="text-base font-semibold text-gray-800">
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
            <button type="button" className="btn-primary" title="Enregistrer en base les matières cochées et nouvelles"
              onClick={recuperer} disabled={busy}>{busy ? 'Enregistrement…' : 'Récupérer'}</button>
            {bilanApercu && <span style={{ fontSize: 12, color: '#475569' }}>{bilanApercu}</span>}
          </div>
          </>
          )}
        </div>
      )}

      {/* Prompt de découpe — GÉNÉRÉ PAR L'IA (méta-prompt en base), affiché, corrigé et validé par
          l'admin. La découpe refuse de tourner tant que le prompt n'est pas validé.
          Affichage séquentiel : n'apparaît qu'APRÈS l'étape Matières (« Récupérer » → bilanApercu). */}
      {bilanApercu && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <div>
              <h2 className="text-base font-semibold text-gray-800">Prompt de découpe (généré par l'IA)</h2>
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
                    {promptBusy === 'regenerer' ? <><Spinner /> Régénération…</> : 'Régénérer le prompt'}
                  </button>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <button type="button" className="btn-primary" onClick={validerPromptDecoupe}
                  disabled={!!promptBusy || !promptDecoupe.trim()}
                  title="Valide ce prompt en base et lance la découpe dans la foulée">
                  {promptBusy === 'valider' ? <><Spinner /> Validation…</>
                    : promptBusy === 'decouper' ? <><Spinner /> Découpe…</>
                    : 'Valider le prompt et découper'}
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
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Règle de découpe — RESTE de l'ANCIEN système regex, remplacé par la découpe IA (carte D).
          CACHÉE DÉFINITIVEMENT : ne réapparaît jamais. Bloc conservé en place, à supprimer au nettoyage. */}
      {false && regle && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <div>
              <h2 className="text-base font-semibold text-gray-800">Règle de découpe</h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Comment ce référentiel est découpé en unités. Validez si la description est juste ; rejetez pour la remettre en proposition.
              </p>
            </div>
            <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title={regleOuvert ? 'Réduire la règle de découpe' : 'Développer la règle de découpe'}
              onClick={() => setRegleOuvert(o => !o)}>
              {regleOuvert ? 'Réduire' : 'Développer'}
            </button>
          </div>

          {regleOuvert && (
          <>
          {/* Face en clair — ce que l'admin lit et valide */}
          <div style={{ fontSize: 14, color: '#1e293b', lineHeight: 1.5,
            background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: 14 }}>
            {regle.explication_clair}
          </div>

          {/* Face technique — pour le dev, discrète */}
          <div>
            <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 4 }}>
              Critère technique (vérifié par le développeur)
            </div>
            <code style={{ fontSize: 12, color: '#475569', background: '#f1f5f9',
              border: '1px solid #e2e8f0', borderRadius: 6, padding: '6px 10px', display: 'block',
              whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              {regle.critere_technique}
            </code>
          </div>

          {/* Qui a proposé + statut */}
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', fontSize: 12 }}>
            <span style={{ color: '#64748b' }}>Proposé par : <strong>{regle.depose_par || '—'}</strong></span>
            <span style={{ fontWeight: 600, color: regle.valide ? '#16a34a' : '#b45309' }}>
              Statut : {regle.valide ? 'validée' : 'à valider'}
            </span>
          </div>

          {/* Valider / Rejeter = bascule du statut (on désactive celui qui correspond à l'état courant) */}
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="btn-primary"
              title="Valider cette règle de découpe : elle devient la règle retenue"
              onClick={() => majStatutRegle('valider')} disabled={busy || regle.valide}>
              Valider
            </button>
            <button type="button" className="btn-secondary"
              title="Rejeter cette règle : elle repart en proposition"
              onClick={() => majStatutRegle('rejeter')} disabled={busy || !regle.valide}>
              Rejeter
            </button>
          </div>
          </>
          )}
        </div>
      )}

      {/* Résultat du découpage — RESTE de l'ANCIEN système regex, remplacé par la découpe IA (carte D).
          CACHÉE DÉFINITIVEMENT : ne réapparaît jamais. Bloc conservé en place, à supprimer au nettoyage. */}
      {false && apercuDecoupe && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <div>
              <h2 className="text-base font-semibold text-gray-800">Résultat du découpage avec arbitrage des cas ambigus</h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Ce que la règle validée produit : vérifiez qu'aucune unité n'est coupée ni sans titre, et voyez son rattachement au niveau.
              </p>
            </div>
            <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title={apercuOuvert ? 'Réduire le résultat' : 'Développer le résultat'}
              onClick={() => setApercuOuvert(o => !o)}>
              {apercuOuvert ? 'Réduire' : 'Développer'}
            </button>
          </div>

          {apercuOuvert && (
          <>
          {apercuDecoupe.disponible ? (
            <>
              <div style={{ fontSize: 13, color: '#1e293b' }}>
                <strong>{apercuDecoupe.total}</strong> unité(s) découpée(s) ·{' '}
                <strong>{apercuDecoupe.total_niveau}</strong> pour ce niveau
                {apercuDecoupe.bande_niveau ? ` (bande ${apercuDecoupe.bande_niveau})` : ''}
              </div>
              <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
                {(apercuDecoupe.unites || []).map((u, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px',
                    flexWrap: 'wrap',
                    borderTop: i ? '1px solid #f1f5f9' : 'none',
                    background: u.dans_niveau ? '#fff' : '#f8fafc', opacity: u.dans_niveau ? 1 : 0.55 }}>
                    <span style={{ flex: 1, minWidth: 140, fontSize: 13, color: '#1e293b' }}>{u.titre}</span>
                    {/* Cas flou : contrôle actif. Les OPTIONS bouclent sur apercuDecoupe.options_arbitrage
                        (tenu par la fiche via le backend) — aucune valeur d'âge en dur ici. */}
                    {u.flou && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                        <span title={u.arbitre ? 'Âge tranché par l\'admin' : 'Âge ambigu — à confirmer par l\'admin'}
                          style={{ fontSize: 11, fontWeight: 600, borderRadius: 6, padding: '2px 6px', whiteSpace: 'nowrap',
                            color: u.arbitre ? '#166534' : '#92400e',
                            background: u.arbitre ? '#dcfce7' : '#fef3c7',
                            border: u.arbitre ? '1px solid #bbf7d0' : '1px solid #fde68a' }}>
                          {u.arbitre ? 'âge tranché' : 'âge à confirmer'}
                        </span>
                        {(apercuDecoupe.options_arbitrage || []).map(opt => {
                          const on = (selection[u.age_label] || []).includes(opt)
                          return (
                            <button key={opt} type="button"
                              title={`Ranger cette unité dans « ${opt} »`}
                              aria-pressed={on}
                              onClick={() => basculerOption(u.age_label, opt)}
                              style={{ fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 6,
                                cursor: 'pointer', whiteSpace: 'nowrap',
                                border: on ? '1px solid #1F6EEB' : '1px solid #cbd5e1',
                                background: on ? '#1F6EEB' : '#fff', color: on ? '#fff' : '#475569' }}>
                              {opt}
                            </button>
                          )
                        })}
                        <button type="button" className="btn-secondary"
                          title="Enregistrer la tranche d'âge choisie pour cette unité"
                          disabled={savingArbitrage === u.age_label}
                          onClick={() => validerAge(u.age_label)}
                          style={{ fontSize: 11, padding: '2px 8px', whiteSpace: 'nowrap' }}>
                          {savingArbitrage === u.age_label ? '…' : "Valider l'âge"}
                        </button>
                        {/* TEMPS 2 : badge « en attente » + voir l'ambiguïté + demander l'avis d'un pro par mail. */}
                        {enAttentePour(u.age_label) && (
                          <span title={`Avis demandé à ${enAttentePour(u.age_label).destinataire}`}
                            style={{ fontSize: 11, fontWeight: 600, borderRadius: 6, padding: '2px 6px', whiteSpace: 'nowrap',
                              color: '#1e3a8a', background: '#dbeafe', border: '1px solid #bfdbfe' }}>
                            en attente
                          </span>
                        )}
                        <button type="button" className="btn-secondary"
                          title="Voir ce qui rend le cas ambigu : l'indication du document et l'activité complète"
                          onClick={() => basculerAmbiguite(u.age_label)}
                          style={{ fontSize: 11, padding: '2px 8px', whiteSpace: 'nowrap' }}>
                          {ambiguiteOuverte === u.age_label ? "Masquer l'ambiguïté" : "Afficher l'ambiguïté"}
                        </button>
                        <button type="button" className="btn-secondary"
                          title="Demander par mail l'avis d'un professionnel sur ce cas"
                          onClick={() => ouvrirDemande(u)}
                          style={{ fontSize: 11, padding: '2px 8px', whiteSpace: 'nowrap' }}>
                          {demandeOuverte === u.age_label ? 'Fermer' : 'Demander un avis'}
                        </button>
                      </div>
                    )}
                    <span style={{ fontSize: 11, fontWeight: 600, color: '#475569', whiteSpace: 'nowrap' }}>
                      {(u.bandes || []).join(' · ') || '—'}
                    </span>
                    {/* Panneau « ambiguïté » : ce que l'admin doit voir pour trancher — l'indication
                        d'âge écrite dans le document + l'activité complète (titre + matériel + déroulé). */}
                    {u.flou && ambiguiteOuverte === u.age_label && (
                      <div style={{ flexBasis: '100%', marginTop: 8, padding: 10, background: '#fffbeb',
                        border: '1px solid #fde68a', borderRadius: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <div style={{ fontSize: 12, color: '#92400e' }}>
                          <strong>Indication du document :</strong> « {u.age_label} » — imprécise, à trancher.
                        </div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: '#475569' }}>Activité complète</div>
                        <pre style={{ margin: 0, fontSize: 12, color: '#1e293b', whiteSpace: 'pre-wrap',
                          fontFamily: 'inherit' }}>{u.extrait || '—'}</pre>
                      </div>
                    )}
                    {/* Formulaire de demande d'avis (inline, pleine largeur sous la ligne). Mail générique
                        pré-rempli, éditable : l'admin lit, ajuste, envoie. */}
                    {u.flou && demandeOuverte === u.age_label && (
                      <div style={{ flexBasis: '100%', marginTop: 8, padding: 10, background: '#f8fafc',
                        border: '1px solid #e2e8f0', borderRadius: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <label style={{ fontSize: 12, fontWeight: 600, color: '#475569' }}>Adresse du professionnel</label>
                        <input type="email" value={demandeEmail} onChange={e => setDemandeEmail(e.target.value)}
                          placeholder="ex. contact@exemple.fr"
                          style={{ fontSize: 13, padding: '6px 8px', border: '1px solid #cbd5e1', borderRadius: 6 }} />
                        <label style={{ fontSize: 12, fontWeight: 600, color: '#475569' }}>Message (pré-rempli, modifiable)</label>
                        <textarea value={demandeMessage} onChange={e => setDemandeMessage(e.target.value)} rows={12}
                          style={{ fontSize: 12, padding: '6px 8px', border: '1px solid #cbd5e1', borderRadius: 6, fontFamily: 'inherit', resize: 'vertical' }} />
                        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                          <button type="button" className="btn-secondary" title="Annuler la demande"
                            onClick={() => setDemandeOuverte('')} style={{ fontSize: 12, padding: '4px 10px' }}>
                            Annuler
                          </button>
                          <button type="button" className="btn-primary" title="Envoyer la demande d'avis par mail au professionnel"
                            disabled={envoiDemande === u.age_label}
                            onClick={() => envoyerDemande(u.age_label)} style={{ fontSize: 12, padding: '4px 10px' }}>
                            {envoiDemande === u.age_label ? 'Envoi…' : 'Envoyer la demande'}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {(apercuDecoupe.unites || []).length === 0 && (
                  <div style={{ padding: '10px', fontSize: 12, color: '#94a3b8' }}>Aucune unité découpée.</div>
                )}
              </div>
            </>
          ) : apercuDecoupe.raison === 'regle_non_validee' ? (
            <div style={{ fontSize: 13, color: '#b45309' }}>
              Validez d'abord la règle de découpe (ci-dessus) pour voir le résultat.
            </div>
          ) : (
            <div style={{ fontSize: 13, color: '#64748b' }}>
              Résultat indisponible{apercuDecoupe.message ? ` : ${apercuDecoupe.message}` : ''}.
            </div>
          )}
          </>
          )}
        </div>
      )}

      {/* Cartouche « Résultat du filtre par niveau » — verdict du VRAI filtre (backend), sous le
          découpage. Vert = couple prêt ; rouge = il reste des cas à trancher. La modale bloquante se
          déclenche à l'ouverture du couple (effet de chargement ci-dessus, règle « incohérence = modale »). */}
      {apercuDecoupe && apercuDecoupe.disponible && apercuDecoupe.filtre && (
        <div style={{ marginTop: 12, border: '1px solid #e2e8f0', borderRadius: 12, padding: 16,
          background: apercuDecoupe.filtre.ok ? '#f0fdf4' : '#fef2f2' }}>
          <h2 className="text-base font-semibold"
            style={{ color: apercuDecoupe.filtre.ok ? '#166534' : '#991b1b' }}>
            Résultat du filtre par niveau
          </h2>
          {apercuDecoupe.filtre.ok ? (
            <div style={{ fontSize: 13, color: '#166534', marginTop: 6 }}>
              Filtre réussi — <strong>{apercuDecoupe.filtre.gardes}</strong> unités retenues pour ce niveau
              {apercuDecoupe.bande_niveau ? ` (bande ${apercuDecoupe.bande_niveau})` : ''}. Ce niveau est prêt.
            </div>
          ) : (
            <div style={{ fontSize: 13, color: '#991b1b', marginTop: 6 }}>
              Filtre en échec — il reste{' '}
              <strong>{(apercuDecoupe.unites || []).filter(u => u.flou && !u.arbitre).length}</strong> cas
              « âge à confirmer » à trancher pour ce couple. Réglez-les dans la carte « Résultat du découpage » ci-dessus.
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
    </div>
  )
}
