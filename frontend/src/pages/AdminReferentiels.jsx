// Page Référentiels — Étape 1 du chantier « Référentiel → matières + chunks ».
// L'admin déclare le couple (cycle + niveau), fournit le PDF officiel par LIEN ou
// par DÉPÔT, CONTRÔLE l'aperçu du document récupéré, puis valide : le système le
// range, en extrait le texte et enregistre sa provenance.
// Hors périmètre étape 1 : extraction des matières, chunks, recherche web automatique.
import { Fragment, useEffect, useRef, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD, TIMEOUT_LONG, TIMEOUT_XLONG, MSG_TIMEOUT } from '../utils/api.js'
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

// Badge d'ORIGINE d'un type coché : IA (violet) | ADMIN (vert) | SYSTÈME (gris). Le badge dit d'où
// VIENT le type (origine tracée sur le lien), jamais qui a coché.
const SOURCE_LABEL = { ia: 'IA', admin: 'ADMIN', systeme: 'SYSTÈME' }
const SOURCE_STYLE = {
  ia:      { background: '#f5f3ff', color: '#7c3aed' },
  admin:   { background: '#f0fdf4', color: '#16a34a' },
  systeme: { background: '#f1f5f9', color: '#64748b' },
}
const badgeOrigine = (s) => ({
  display: 'inline-block', fontSize: 10, fontWeight: 700, padding: '1px 6px', borderRadius: 6, marginLeft: 8,
  textTransform: 'uppercase', letterSpacing: '0.5px',
  ...(SOURCE_STYLE[s] || SOURCE_STYLE.systeme),
})
// Norme boutons : hauteur unique (36px) + centrage + icône ; grisé (off) = fond gris, texte estompé,
// curseur « sens interdit ». Voir norme-boutons-ui.
const btnTypes = (bg, off = false) => ({
  height: 36, padding: '0 16px', borderRadius: 8, border: 'none',
  background: off ? '#e2e8f0' : bg, color: off ? '#94a3b8' : 'white',
  fontSize: 13, fontWeight: 600, cursor: off ? 'not-allowed' : 'pointer',
  display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
})

// Repère « IA » — petit badge violet posé là où l'IA agit SANS bouton dédié (vérification du
// couple, ingestion). Il signale à l'admin que le résultat vient de l'IA.
// Même palette IA que les badges d'origine (SOURCE_STYLE.ia) : cohérence, aucune couleur en double.
function BadgeIA({ titre }) {
  return (
    <span title={titre || "Réalisé par l'IA"} style={{
      display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 10, fontWeight: 700,
      padding: '2px 7px', borderRadius: 999, background: '#f5f3ff', color: '#7c3aed',
      textTransform: 'uppercase', letterSpacing: '0.5px', verticalAlign: 'middle' }}>
      <span aria-hidden="true">🤖</span> IA
    </span>
  )
}

// Jauge d'attente réutilisable pour UN appel IA d'un bloc (durée inconnue, pas d'étapes mesurables) :
// barre navette animée + secondes écoulées — jamais de faux pourcentage. Montée uniquement pendant
// l'attente (le montage/démontage remet le compteur à zéro).
function JaugeAttente({ libelle }) {
  const [sec, setSec] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setSec(s => s + 1), 1000)
    return () => clearInterval(t)
  }, [])
  return (
    <div style={{ marginTop: 10 }}>
      <style>{'@keyframes jaugeAttente { 0% { margin-left: -35%; } 100% { margin-left: 100%; } }'}</style>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12,
        color: '#475569', marginBottom: 4 }}>
        <span>{libelle}</span>
        <span style={{ fontWeight: 600 }}>{sec} s</span>
      </div>
      <div style={{ height: 8, borderRadius: 999, background: '#e2e8f0', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: '35%', background: '#7c3aed',
          borderRadius: 999, animation: 'jaugeAttente 1.6s linear infinite' }} />
      </div>
    </div>
  )
}

export default function AdminReferentiels() {
  const [arbre, setArbre] = useState([])        // arbre COMPLET cycles → niveaux (GET /admin/programmes)
  const [refsListe, setRefsListe] = useState([])  // colonne 2 : référentiels déposés (GET /admin/referentiels/liste)
  const [cycleId, setCycleId] = useState('')    // cycle choisi (cascade, 1er select)
  const [niveauId, setNiveauId] = useState('')  // niveau choisi (cascade, 2e select) — envoyé à valider/verifier-depot
  const [niveau, setNiveau] = useState('')      // NOM du niveau choisi (requis par les endpoints post-dépôt)
  const [mode, setMode] = useState('depot')       // 'depot' | 'lien'
  const [url, setUrl] = useState('')
  const [nomFichier, setNomFichier] = useState('')  // nom du PDF choisi (zone « Par dépôt »)
  const [source, setSource] = useState('')
  const [busy, setBusy] = useState(false)
  const [apercu, setApercu] = useState(null)      // { token, filename, pages, taille_ko, apercu }
  const [resultat, setResultat] = useState(null)  // { cycle, niveau, dossier, pages, caracteres_extraits, nom_fixe }
  // Vérification au dépôt (backend verifier-depot) : { couple:{correspond,niveau_lu,raison} }
  // 'loading' pendant l'appel, null au repos. Le document à valider ne s'affiche que si elle passe.
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
  const [matieresOuvert, setMatieresOuvert] = useState(false)   // bloc Matières repliable (vue d'ensemble) — démarre replié
  // Prompt de découpe du couple — GÉNÉRÉ PAR L'IA, stocké en base, corrigé/validé par l'admin.
  const [promptDecoupe, setPromptDecoupe] = useState('')       // texte éditable du prompt
  const [promptValide, setPromptValide] = useState(false)      // garde-fou : découpe refusée tant que false
  const [decoupeValide, setDecoupeValide] = useState(false)    // étape FINALE : découpe validée → puce verte (lu via /prompt-decoupe)
  const [promptBusy, setPromptBusy] = useState('')             // 'generer' | 'regenerer' | 'valider' | 'decouper' | ''
  const [remarques, setRemarques] = useState('')              // remarques admin (français clair) pour régénérer le prompt
  const [decoupeUnites, setDecoupeUnites] = useState(null)     // résultat de la découpe : [{titre, taille}]
  const [decoupeProgress, setDecoupeProgress] = useState(null) // jauge : avancement RÉEL lu via /decoupe/statut ({etape, fait, total})
  const [uniteOuverteId, setUniteOuverteId] = useState(null)   // lecture d'une unité : id choisi dans la liste (unités EN BASE seulement)
  const [uniteTexte, setUniteTexte] = useState('')             // texte complet de l'unité choisie (get à la demande, zéro copie)
  const [uniteLoading, setUniteLoading] = useState(false)
  const [uniteEdit, setUniteEdit] = useState(false)            // édition de l'unité ouverte (geste de nettoyage)
  const [uniteBrouillon, setUniteBrouillon] = useState('')
  const [uniteSaving, setUniteSaving] = useState(false)
  const [epurationOuvert, setEpurationOuvert] = useState(false)  // consultation des règles d'épuration (repliée)
  const [epurationRegles, setEpurationRegles] = useState(null)   // lues chez le serveur au premier dépliage (get)
  const [showEpure, setShowEpure] = useState(false)              // fenêtre du document épuré (le texte de travail)
  const [epureTexte, setEpureTexte] = useState(null)             // texte épuré lu en base au premier clic (get, figé au dépôt)

  // Consultation pure des règles d'épuration : lecture au premier dépliage, puis simple repli/dépli.
  function ouvrirEpuration() {
    setEpurationOuvert(o => !o)
    if (epurationRegles) return
    fetchWithTimeout('/api/admin/referentiels/epuration', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d && d.regles) setEpurationRegles(d.regles) })
      .catch(() => {})
  }

  // Document épuré : le TEXTE DE TRAVAIL du couple, FIGÉ en base à la validation du dépôt
  // (colonne texte_epure) — get pur au clic, aucun recalcul. C'est exactement ce que l'IA lit.
  function ouvrirEpure() {
    setShowEpure(true)
    if (epureTexte !== null) return
    fetchWithTimeout(`/api/admin/referentiels/epure?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => setEpureTexte(d && typeof d.texte === 'string' ? d.texte : ''))
      .catch(() => setEpureTexte(''))
  }

  // Valider l'édition d'une unité : put du texte + recalcul de son empreinte dans le MÊME geste
  // (côté serveur) — l'empreinte est calculée à partir du texte, elle doit le suivre.
  async function validerUnite() {
    const texte = uniteBrouillon.trim()
    if (!texte) { showError('Le texte de l’unité ne peut pas être vide.'); return }
    setUniteSaving(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/decoupe/unite', {
        method: 'PUT', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, unite_id: uniteOuverteId, texte }),
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || 'Enregistrement de l’unité impossible.'); return }
      setUniteTexte(texte); setUniteEdit(false); setUniteBrouillon('')
      // Relit la liste (titres/tailles depuis la base) : l'affichage suit ce qui est réellement stocké.
      fetchWithTimeout(`/api/admin/referentiels/decoupe?cycle_id=${Number(cycleId)}&niveau=${encodeURIComponent(niveau)}`,
        { credentials: 'include' }, TIMEOUT_STD)
        .then(rr => (rr.ok ? rr.json() : null))
        .then(dd => { if (dd && dd.unites && dd.unites.length) setDecoupeUnites(dd.unites) })
        .catch(() => {})
    } catch { showError('Enregistrement de l’unité impossible.') }
    finally { setUniteSaving(false) }
  }

  // Clic sur une unité de la découpe : lit son texte COMPLET en base (get pur, à la demande).
  // Re-clic sur la même unité = referme la lecture. Les unités d'aperçu (pas encore en base,
  // donc sans id) ne sont pas cliquables.
  async function ouvrirUnite(u) {
    if (!u.id) return
    setUniteEdit(false); setUniteBrouillon('')
    if (uniteOuverteId === u.id) { setUniteOuverteId(null); setUniteTexte(''); return }
    setUniteOuverteId(u.id); setUniteTexte(''); setUniteLoading(true)
    try {
      const r = await fetchWithTimeout(
        `/api/admin/referentiels/decoupe/unite?cycle_id=${Number(cycleId)}&niveau=${encodeURIComponent(niveau)}&unite_id=${u.id}`,
        { credentials: 'include' }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || 'Lecture de cette unité impossible.'); setUniteOuverteId(null); return }
      setUniteTexte(d.texte || '')
    } catch { showError('Lecture de cette unité impossible.'); setUniteOuverteId(null) }
    finally { setUniteLoading(false) }
  }
  const [promptOuvert, setPromptOuvert] = useState(false)   // démarre replié
  // Repli/développement des autres cartouches — état de départ INCHANGÉ (dépliées → true).
  const [coupleOuvert, setCoupleOuvert] = useState(true)
  const [pdfOuvert, setPdfOuvert] = useState(true)
  const [decoupeOuvert, setDecoupeOuvert] = useState(true)
  const [typesOuvert, setTypesOuvert] = useState(true)
  // ── Types d'activité du couple (dernière cartouche) : fenêtre sur le CATALOGUE global
  //    `types_activite` + la LIAISON `referentiel_types_activite`. Cocher/décocher = écriture
  //    directe en base au clic (put), puis re-GET. Zéro donnée en dur, zéro tampon.
  const [typesCatalogue, setTypesCatalogue] = useState([])     // [{id, key, label, is_default}]
  const [typesChecked, setTypesChecked] = useState(new Set())  // ids cochés (reflet base, relu à chaque put)
  const [typesSource, setTypesSource] = useState({})           // {id: 'ia'|'admin'|'systeme'} → badge d'origine
  const [typesNouveau, setTypesNouveau] = useState('')         // saisie « ajouter un type à ce couple »
  const [typesBusy, setTypesBusy] = useState(false)            // détection / ajout en cours
  const [typesDetecting, setTypesDetecting] = useState(false)  // détection IA en cours → sablier
  const [typesInit, setTypesInit] = useState(false)            // 1re lecture des liaisons du couple faite (base lue)
  const [precisProgress, setPrecisProgress] = useState(null)   // jauge RÉELLE précisions : {fait, total, label} | null
  const autoDetectFait = useRef('')                            // clé couple : l'auto-détection ne se lance qu'UNE fois par couple affiché
  // MAQUETTE prompt par type (spécifique au couple) : éditeur déplié sous la ligne. `promptEditId` = id du
  // type dont l'éditeur est ouvert (null = aucun) ; `promptBrouillon` = texte en cours (local, pas encore en base).
  // La génération IA et l'enregistrement PAR COUPLE (colonne prompt sur le lien) = chantier backend d'après.
  const [promptEditId, setPromptEditId] = useState(null)
  const [promptBrouillon, setPromptBrouillon] = useState('')
  const [typesPrompt, setTypesPrompt] = useState({})   // {activite_type_id: prompt} — prompt PAR couple, lu en base
  const [typesNbPrecis, setTypesNbPrecis] = useState({})   // {activite_type_id: nb} — comptage précisions PAR couple, lu en base (/etat)
  const [promptSaving, setPromptSaving] = useState(false)

  // Précisions PAR COUPLE × type (table `referentiel_type_precisions`, fille de la liaison — comme le prompt).
  const [precisEditId, setPrecisEditId] = useState(null)   // id du type dont le panneau Précisions est ouvert (null = aucun)
  const [precisList, setPrecisList] = useState([])          // précisions du type ouvert, LUES en base (zéro copie)
  const [precisLoading, setPrecisLoading] = useState(false)
  const [newPrecis, setNewPrecis] = useState('')            // saisie « Ajouter une précision »
  const [precisBusy, setPrecisBusy] = useState(false)

  useEffect(() => {
    // Arbre COMPLET cycles → niveaux (tous les niveaux, même sans matière) : la source de la
    // cascade « Couple » de la Carte 1. Lu en base via /admin/programmes (get, zéro copie).
    fetchWithTimeout('/api/admin/programmes', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) setArbre(d.cycles || []) })
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

  // Clic sur une ligne de la colonne 2 : sélectionne le couple (comme la cascade) → l'écran
  // de droite charge ce référentiel via l'effet [cycleId, niveau]. La liste porte cycle_id,
  // niveau_id et le nom du niveau : la cascade se cale directement dessus.
  function ouvrirRef(r) {
    setCycleId(String(r.cycle_id)); setNiveauId(String(r.niveau_id)); setNiveau(r.niveau)
  }

  // « + Nouveau » (colonne 2) : remet l'écran en création — aucun couple choisi, tout vide.
  function nouveau() {
    // resetSteps : remet TOUS les done à false via leur source (la table les calcule depuis ces valeurs).
    setCycleId(''); setNiveauId(''); setNiveau('')  // → couple.done = false
    setEtat(null)                                   // → pdf / matieres / prompt / decoupe.done = false (tous lus depuis etat)
    setCoupleOuvert(true)                           // repartir en création : la carte Couple s'ouvre (bouton « Réduire »)
  }

  // Bouton FINAL « Valider le découpage » : l'admin accepte la découpe → put decoupe_valide=true en base.
  // C'est la dernière étape : on recharge la liste pour que la puce du menu passe au vert (get, zéro copie).
  async function validerDecoupe() {
    setPromptBusy('valider-decoupe')
    setDecoupeProgress({ etape: 'decoupe', fait: 0, total: 0 })   // la jauge démarre tout de suite
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
          setDecoupeProgress(null)
          if (Number(cycleId) === c && niveau === nv) { setDecoupeValide(true); setPromptBusy(''); await rafraichirEtat(); setTypesOuvert(true) }  // découpe validée → relit /etat (decoupe_valide=true → estVisible('types') vrai) → cartouche Types apparaît, dépliée
          // Relit la liste des unités depuis la BASE (avec leur id) : elles deviennent cliquables (lecture du texte).
          fetchWithTimeout(`/api/admin/referentiels/decoupe?cycle_id=${c}&niveau=${encodeURIComponent(nv)}`,
            { credentials: 'include' }, TIMEOUT_STD)
            .then(r => (r.ok ? r.json() : null))
            .then(dd => { if (dd && dd.unites && dd.unites.length && Number(cycleId) === c && niveau === nv) setDecoupeUnites(dd.unites) })
            .catch(() => {})
          chargerListe()          // la puce du menu passe au vert (relecture base)
          return
        }
        if (d.status === 'error') {
          setDecoupeProgress(null)
          showError(d.message || "La découpe n'a pas pu aboutir. Réessayez dans un instant.")
          if (Number(cycleId) === c && niveau === nv) setPromptBusy('')
          return
        }
        if (d.status === 'running' && d.progress) setDecoupeProgress(d.progress)   // la jauge suit l'avancement réel
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
    if (!cycleId || !niveau) {
      setEtat(null); setMatieres([]); setAfficherPrompt(false)
      setTypesCatalogue([]); setTypesChecked(new Set()); setTypesSource({}); setTypesNouveau(''); setTypesInit(false)
      return
    }
    setApercu(null); setResultat(null); setBilanApercu(''); setShowPdf(false); setAfficherPrompt(false)
    setShowEpure(false); setEpureTexte(null)   // changement de couple : le texte épuré de l'ancien ne vaut plus
    setTypesNouveau(''); setTypesInit(false); setPrecisProgress(null)   // repartir propre sur ce couple (le get réhydrate la liste + badges)
    // À chaque sélection d'un couple : toutes les cartouches repliées (bouton sur « Développer »).
    setCoupleOuvert(false); setPdfOuvert(false); setMatieresOuvert(false); setPromptOuvert(false); setDecoupeOuvert(false); setTypesOuvert(false)
    let annule = false
    fetchWithTimeout(`/api/admin/referentiels/etat?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        if (annule) return
        setEtat(d)
        setMatieres(construireLignesMatieres(d))
        // Mode AJOUT (couple sans référentiel) : la carte PDF s'ouvre pour déposer tout de suite.
        // Mode « déjà traité » : elle reste repliée (simple relecture).
        setPdfOuvert(!(d && d.existe_referentiel))
      })
      .catch(() => { if (!annule) setEtat(null) })
    // Prompt de découpe du couple (EN BASE) — généré par l'IA, corrigé/validé par l'admin.
    fetchWithTimeout(`/api/admin/referentiels/prompt-decoupe?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!annule) { setPromptDecoupe(d && d.prompt ? d.prompt : ''); setPromptValide(!!(d && d.valide)); setDecoupeValide(!!(d && d.decoupe_valide)) } })
      .catch(() => { if (!annule) { setPromptDecoupe(''); setPromptValide(false); setDecoupeValide(false) } })
    // Unités du découpage DÉJÀ en base (referentiel_chunks) → réaffichées telles quelles (get, zéro recalcul).
    setUniteOuverteId(null); setUniteTexte('')   // changement de couple : on referme la lecture d'unité
    fetchWithTimeout(`/api/admin/referentiels/decoupe?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!annule) setDecoupeUnites(d && d.unites && d.unites.length ? d.unites : null) })
      .catch(() => { if (!annule) setDecoupeUnites(null) })
    // Types d'activité du couple (catalogue + cases cochées) — lu en base, badges compris (get, zéro copie).
    fetchWithTimeout(`/api/admin/referentiels/types-activite?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        if (annule || !d) return
        setTypesCatalogue(d.catalogue || [])
        setTypesChecked(new Set((d.coches || []).map(x => x.activite_type_id)))
        setTypesSource(Object.fromEntries((d.coches || []).map(x => [x.activite_type_id, x.source])))
        setTypesPrompt(Object.fromEntries((d.coches || []).map(x => [x.activite_type_id, x.prompt || ''])))
        setTypesNbPrecis(Object.fromEntries((d.coches || []).map(x => [x.activite_type_id, x.nb_precisions || 0])))
        setTypesInit(true)   // 1re lecture des liaisons faite → l'auto-détection peut juger
      })
      .catch(() => { if (!annule) { setTypesCatalogue([]); setTypesChecked(new Set()); setTypesSource({}); setTypesPrompt({}) } })
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
      await rafraichirEtat()  // relit /etat → prompt_decoupe_valide passe à true → estVisible('decoupe') devient vrai (la cartouche apparaît)
      setDecoupeOuvert(true)  // prompt validé → ouvrir la cartouche Découpe (dépliée)
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
      setApercu(d); setSource(url.trim()); setBilanApercu(''); lancerVerifDepot(d.token)
    } catch (e) { showError(`Récupération impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  // Dès qu'un PDF est récupéré : vérif n°1 au dépôt — l'IA lit le couple visé par le document
  // et le compare au couple cycle → niveau déclaré. Le document à valider ne s'affiche qu'après.
  async function lancerVerifDepot(token) {
    if (!token || !cycleId || !niveauId) return
    setVerif('loading'); setForcageMotif('')
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/verifier-depot', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, cycle_id: Number(cycleId), niveau_id: Number(niveauId) }),
      }, TIMEOUT_LONG)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setVerif(d)
    } catch (e) { setVerif(null); showError(`Vérification du dépôt impossible.\n\n${e.message}`) }
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
      setApercu(d); setSource('dépôt manuel'); setBilanApercu(''); lancerVerifDepot(d.token)
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
        body: JSON.stringify({ token: apercu.token, cycle_id: Number(cycleId), niveau_id: Number(niveauId), source, fichier_origine: apercu.filename, forcage_motif: forcageArg, verif_couple: (verif && verif.couple) ? verif.couple : null }),
        // TIMEOUT_XLONG : la validation épure le texte ET détecte les matières (IA) en un seul
        // appel (~3 min mesurées). Abandonner avant le serveur = reclics sur jeton consommé.
      }, TIMEOUT_XLONG)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setResultat(d); setApercu(null); setVerif(null); setForcageMotif(''); setBilanApercu('')
      setEpureTexte(null)   // nouveau PDF validé = nouveau texte de travail figé en base : on relira au clic
      chargerListe()   // un nouveau référentiel vient d'apparaître → recharger la colonne 2
      // Relire l'état du couple EN BASE (get) : le référentiel existe désormais, donc
      // etat.existe_referentiel passe à true → la cartouche Matières (et la suite) se déroule
      // sans re-sélectionner le couple. rafraichirEtat réhydrate aussi la table matières
      // (candidates du nouveau PDF + matières déjà en base). Zéro copie : on relit la base.
      await rafraichirEtat()
      setMatieresOuvert(true)   // référentiel validé → ouvrir la cartouche Matières
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
  // « Sélectionner tout » : coche d'un coup toutes les matières NOUVELLES de la liste (les « déjà
  // en base » sont déjà cochées et verrouillées). Interaction d'écran uniquement — aucune écriture :
  // c'est « Récupérer » (le put) qui enregistre, et il se dégrise tout seul dès qu'une nouvelle est cochée.
  function selectionnerTout() {
    setMatieres(matieres.map(m => (m.en_base ? m : { ...m, cochee: true })))
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

  // ── Types d'activité du couple : re-GET (la base fait foi) après chaque écriture.
  async function chargerTypes() {
    if (!cycleId || !niveau) return
    try {
      const r = await fetchWithTimeout(`/api/admin/referentiels/types-activite?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
        { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) return
      const d = await r.json()
      setTypesCatalogue(d.catalogue || [])
      setTypesChecked(new Set((d.coches || []).map(x => x.activite_type_id)))
      setTypesSource(Object.fromEntries((d.coches || []).map(x => [x.activite_type_id, x.source])))
      setTypesPrompt(Object.fromEntries((d.coches || []).map(x => [x.activite_type_id, x.prompt || ''])))
      setTypesNbPrecis(Object.fromEntries((d.coches || []).map(x => [x.activite_type_id, x.nb_precisions || 0])))
      if ((d.coches || []).some(x => x.source === 'ia')) setTypesDejaDetecte(true)
    } catch { /* réseau : on garde l'affichage courant */ }
  }

  // ✎ Prompt → Valider : PUT réel du prompt de CE type POUR CE couple (réécrit la colonne du lien), puis re-GET.
  async function validerPromptType(t) {
    if (!promptBrouillon.trim()) return
    setPromptSaving(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/types-activite/prompt', {
        method: 'PUT', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, activite_type_id: t.id, prompt: promptBrouillon }),
      }, TIMEOUT_STD)
      if (!r.ok) { const e = await r.json().catch(() => ({})); showError(e.detail || `Enregistrement impossible (${r.status}).`); return }
      setPromptEditId(null); setPromptBrouillon('')
      await chargerTypes()
    } catch { showError('Enregistrement impossible.') }
    finally { setPromptSaving(false) }
  }

  // GET (lecture pure) des précisions de CE type POUR CE couple. Aucune écriture, aucun sablier IA.
  // Renvoie le tableau lu (et l'affiche). Utilisé à l'ouverture ET après ajout/suppression (re-lecture).
  async function chargerPrecisCouple(typeId) {
    try {
      const r = await fetchWithTimeout(`/api/admin/referentiels/types-activite/precisions?cycle_id=${Number(cycleId)}&niveau=${encodeURIComponent(niveau)}&activite_type_id=${typeId}`,
        { credentials: 'include' }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Lecture des précisions impossible (${r.status}).`); setPrecisList([]); return null }
      const list = d.precisions || []
      setPrecisList(list)
      return list
    } catch { showError('Lecture des précisions impossible.'); setPrecisList([]); return null }
  }

  // Ouvre/ferme le panneau. À l'ouverture : GET (lecture). S'il y a des précisions → on les affiche.
  // S'il n'y en a AUCUNE → on lance l'IA pour aller les chercher (seul cas où l'IA tourne).
  function ouvrirPrecisions(t) {
    if (precisEditId === t.id) { setPrecisEditId(null); setPrecisList([]); setNewPrecis(''); return }
    setPrecisEditId(t.id); setNewPrecis(''); setPrecisList([])
    chargerPrecisCouple(t.id).then(list => {
      if (Array.isArray(list) && list.length === 0) genererPrecisCouple(t.id)
    })
  }

  // Lance l'IA (sablier 🤖) : génère les précisions et les ÉCRIT en base, puis les affiche. Appelé
  // UNIQUEMENT quand la lecture est vide — jamais après une suppression manuelle.
  async function genererPrecisCouple(typeId) {
    setPrecisLoading(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/types-activite/precisions/generer', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, activite_type_id: typeId }),
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Génération des précisions impossible (${r.status}).`); return }
      setPrecisList(d.precisions || [])
      await chargerTypes()   // met à jour le badge « N précisions » de la ligne
    } catch { showError('Génération des précisions impossible.') }
    finally { setPrecisLoading(false) }
  }

  // CREATE encadré (précision du couple) : Ajouter = POST. Doublon refusé côté back (deja_present) → message humain.
  async function ajouterPrecisCouple(t) {
    const libelle = newPrecis.trim()
    if (!libelle) { showError('Indiquez un libellé pour la précision.'); return }
    setPrecisBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/types-activite/precisions', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, activite_type_id: t.id, libelle }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Ajout impossible (${r.status}).`); return }
      setNewPrecis('')
      if (d.deja_present) showError(`La précision « ${d.libelle} » existe déjà pour ce couple.`)
      await chargerPrecisCouple(t.id)
      await chargerTypes()   // met à jour le badge « N précisions » de la ligne
    } catch { showError('Ajout impossible.') }
    finally { setPrecisBusy(false) }
  }

  // DELETE encadré (précision du couple) : après confirmation, puis re-get.
  async function supprimerPrecisCouple(t, p) {
    if (!window.confirm(`Supprimer la précision « ${p.libelle} » ?\nCette action est irréversible.`)) return
    setPrecisBusy(true)
    try {
      const r = await fetchWithTimeout(`/api/admin/referentiels/types-activite/precisions/${p.id}?cycle_id=${Number(cycleId)}&niveau=${encodeURIComponent(niveau)}&activite_type_id=${t.id}`,
        { method: 'DELETE', credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) { const e = await r.json().catch(() => ({})); showError(e.detail || `Suppression impossible (${r.status}).`) }
      await chargerPrecisCouple(t.id)
      await chargerTypes()   // met à jour le badge « N précisions » de la ligne
    } catch { showError('Suppression impossible.') }
    finally { setPrecisBusy(false) }
  }

  // La case EST le put : cocher = lien actif, décocher = lien inactif — écrit direct en base au clic, puis re-GET.
  async function basculerType(id) {
    if (!cycleId || !niveau) return
    const veutCocher = !typesChecked.has(id)
    setTypesChecked(prev => { const n = new Set(prev); veutCocher ? n.add(id) : n.delete(id); return n })  // optimiste
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/types-activite', {
        method: 'PUT', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, activite_type_id: id, actif: veutCocher }),
      }, TIMEOUT_STD)
      if (!r.ok) { const e = await r.json().catch(() => ({})); showError(e.detail || `Enregistrement impossible (${r.status}).`) }
      await chargerTypes()
    } catch { showError('Enregistrement impossible.'); await chargerTypes() }
  }

  // Détection : l'IA lit le document épuré AVEC le catalogue des types sous les yeux — tout ce
  // qu'elle retient est collé au couple (correspondance = type de la table, nouveauté = type créé
  // origine 'ia'), prompt gabarit posé. Puis, DANS LA FOULÉE, les précisions manquantes sont
  // générées type par type (jauge réelle). Se lance TOUTE SEULE à l'arrivée sur un couple sans
  // types (auto-détection) ; le bouton ne sert qu'à RELANCER.
  async function detecterTypes() {
    if (!cycleId || !niveau) return
    setTypesBusy(true); setTypesDetecting(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/types-activite/detecter', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau }),
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Détection impossible (${r.status}).`); return }
      await chargerTypes()
      setTypesDetecting(false)
      await genererPrecisionsManquantes()   // dans la foulée : prompts déjà posés, précisions générées
    } catch { showError('Détection impossible.') }
    finally { setTypesBusy(false); setTypesDetecting(false) }
  }

  // Précisions MANQUANTES du couple, générées type par type avec une jauge RÉELLE (fait/total).
  // Idempotent côté serveur : un type qui a déjà des précisions n'est jamais réécrasé — on ne
  // dépense l'IA que sur les types à 0 précision. Relit la base à la fin (badges à jour).
  async function genererPrecisionsManquantes() {
    const rg = await fetchWithTimeout(`/api/admin/referentiels/types-activite?cycle_id=${Number(cycleId)}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
    const dg = await rg.json().catch(() => ({}))
    if (!rg.ok) return
    const aFaire = (dg.coches || []).filter(x => !(x.nb_precisions > 0))
    if (aFaire.length === 0) return
    const labels = Object.fromEntries((dg.catalogue || []).map(t => [t.id, t.label]))
    try {
      for (let i = 0; i < aFaire.length; i++) {
        const x = aFaire[i]
        setPrecisProgress({ fait: i, total: aFaire.length, label: labels[x.activite_type_id] || '' })
        const rp = await fetchWithTimeout('/api/admin/referentiels/types-activite/precisions/generer', {
          method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cycle_id: Number(cycleId), niveau, activite_type_id: x.activite_type_id }),
        }, TIMEOUT_LONG)
        if (!rp.ok) { const e = await rp.json().catch(() => ({})); showError(e.detail || `Génération des précisions impossible (${rp.status}).`); break }
      }
    } finally { setPrecisProgress(null); await chargerTypes() }
  }

  // Ajout d'un type À CE COUPLE (create encadré : anti-doublon par libellé au catalogue global, puis
  // coche pour le couple). fromSuggestion → badge 'ia' (suggestion de la détection) ; sinon 'admin'.
  async function ajouterTypeCatalogue(label, fromSuggestion = false) {
    const lib = (label || '').trim()
    if (!lib) return
    setTypesBusy(true)
    try {
      const payload = { label: lib, cycle_id: Number(cycleId), niveau, suggestion_ia: fromSuggestion }
      const r = await fetchWithTimeout('/api/admin/referentiels/types-activite/catalogue', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Ajout impossible (${r.status}).`); return }
      setTypesNouveau('')
      await chargerTypes()
      await genererPrecisionsManquantes()   // le type ajouté reçoit ses précisions dans la foulée
    } catch { showError('Ajout impossible.') }
    finally { setTypesBusy(false) }
  }

  const dejaTraite = !!(etat && etat.existe_referentiel)
  // Types RETENUS pour ce couple = liaisons actives (reflet base). L'écran n'affiche plus le
  // catalogue entier : le couple ne voit que SES types.
  const typesDuCouple = typesCatalogue.filter(t => typesChecked.has(t.id))

  // AUTO-DÉTECTION : à l'arrivée sur un couple dont la découpe est validée et qui n'a ENCORE AUCUN
  // type, l'IA se lance toute seule (une seule fois par couple affiché — clé dans autoDetectFait).
  // Tout est proposition d'IA de toute façon : l'admin fait ensuite le ménage sur la liste (✕ / ajout).
  useEffect(() => {
    if (!cycleId || !niveau || !typesInit || typesDetecting || typesBusy) return
    if (!etat?.decoupe_valide) return            // la carte Types n'existe qu'après la découpe validée
    if (typesChecked.size > 0) return            // le couple a déjà ses types : rien d'automatique
    const cle = `${cycleId}|${niveau}`
    if (autoDetectFait.current === cle) return   // déjà lancée pour ce couple
    autoDetectFait.current = cle
    detecterTypes()
  }, [cycleId, niveau, typesInit, typesChecked, etat, typesDetecting, typesBusy])  // eslint-disable-line react-hooks/exhaustive-deps
  // Cycle courant + libellé « Cycle · Niveau », lus dans l'arbre des programmes (get, zéro copie).
  const cycleCourant = arbre.find(c => String(c.id) === String(cycleId))
  const coupleLabel = cycleCourant && niveau ? `${cycleCourant.nom} · ${niveau}` : niveau

  // Les 5 cartouches = 5 étapes, ordre FIXE. `done` = REFLET lu en base (get, zéro copie), jamais un
  // booléen stocké en double : couple = couple choisi ; pdf = référentiel enregistré ;
  // matieres = matières reliées ; prompt = prompt validé ; decoupe = découpage validé. Règle unique
  // d'affichage : une carte n'est visible que si TOUT ce qui la précède est fait (estVisible). Le
  // tableau ne change jamais ; « Nouveau » ne fait que revider l'état lu → les `done` repassent à false.
  const steps = [
    { id: 'couple',        done: !!(cycleId && niveau) },
    { id: 'pdf',           done: dejaTraite },   // = etat.existe_referentiel (une seule source : etat)
    { id: 'matieres',      done: !!(etat?.matieres?.length > 0) },
    { id: 'prompt',        done: !!etat?.prompt_decoupe_valide },   // lu depuis etat (get), comme matieres
    { id: 'decoupe',       done: !!etat?.decoupe_valide },          // lu depuis etat (get), comme matieres
    { id: 'types',         done: typesChecked.size > 0 },           // dernière étape : au moins un type coché
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

      {/* Colonne 3 — l'écran de travail du référentiel. Prend toute la largeur disponible (plus de plafond). */}
      <div className="flex flex-col gap-6" style={{ flex: 1, minWidth: 0 }}>
      <div>
        <h2 className="text-base font-semibold text-gray-800">Référentiels</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Fournissez le référentiel officiel (par lien ou en déposant le PDF), vérifiez que c’est le bon document, puis validez : le système le range et en extrait le texte.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">

        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
          <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
            <Pastille etat={(cycleId && niveau) ? 'vert' : 'rouge'} titre="Vert = un couple est choisi." />
            Couple (cycle + niveau)
          </h2>
          <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
            title={coupleOuvert ? 'Réduire' : 'Développer'} onClick={() => setCoupleOuvert(o => !o)}>
            {coupleOuvert ? 'Réduire' : 'Développer'}
          </button>
        </div>

        {coupleOuvert && (<>
        {/* Cascade cycle → niveau sur l'arbre COMPLET des programmes (tous les niveaux existants).
            Le dépôt ne propose QUE l'existant : créer un niveau = écran Programmes (« + Niveau »). */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 180 }}>
            <label className="block text-xs text-gray-500 mb-1">Cycle</label>
            <select style={{ ...champ, background: '#fff' }} value={cycleId}
              onChange={e => { setCycleId(e.target.value); setNiveauId(''); setNiveau('') }}
              title="Choisissez d'abord le cycle — les niveaux de ce cycle apparaissent à droite">
              <option value="">— Choisissez un cycle —</option>
              {arbre.map(c => <option key={c.id} value={c.id}>{c.nom}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 180 }}>
            <label className="block text-xs text-gray-500 mb-1">Niveau</label>
            <select style={{ ...champ, background: '#fff' }} value={niveauId} disabled={!cycleId}
              onChange={e => {
                const id = e.target.value
                setNiveauId(id)
                const n = (arbre.find(c => String(c.id) === String(cycleId))?.niveaux || [])
                  .find(x => String(x.id) === String(id))
                setNiveau(n ? n.nom : '')
              }}
              title={cycleId ? 'Choisissez le niveau du cycle' : 'Choisissez d’abord le cycle'}>
              <option value="">{cycleId ? '— Choisissez un niveau —' : '—'}</option>
              {(arbre.find(c => String(c.id) === String(cycleId))?.niveaux || []).map(n => (
                <option key={n.id} value={n.id}>{n.nom}</option>
              ))}
            </select>
            {cycleId && (arbre.find(c => String(c.id) === String(cycleId))?.niveaux || []).length === 0 && (
              <p style={{ fontSize: 12, color: '#b45309', marginTop: 4 }}>
                Ce cycle n’a encore aucun niveau — créez-le d’abord dans l’écran Programmes (bouton « + Niveau »).
              </p>
            )}
          </div>
        </div>
        </>)}

      </div>

      {/* Carte 2 — visible seulement si l'étape 1 (Couple) est faite (estVisible, règle N-1). */}
      {estVisible('pdf') && (
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
            <Pastille etat={(dejaTraite || resultat) ? 'vert' : 'rouge'} titre="Vert = une ligne référentiel existe en base pour ce couple." />
            Référentiel au format PDF
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
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
            <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title={pdfOuvert ? 'Réduire' : 'Développer'} onClick={() => setPdfOuvert(o => !o)}>
              {pdfOuvert ? 'Réduire' : 'Développer'}
            </button>
          </div>
        </div>

        {pdfOuvert && (<>
        {/* ── Zone 1 : le PDF ORIGINAL — la pièce téléchargée, conservée telle quelle, relue par l'admin. ── */}
        <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b' }}>
          Fichier PDF original <span style={{ fontWeight: 400, color: '#64748b' }}>(téléchargé — pièce d’origine consultable, matière première du dépôt, réserve pour l’avenir)</span>
        </div>
        {dejaTraite ? (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Nom du fichier téléchargé</label>
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
              // Libellé du cycle : lu dans l'arbre des programmes déjà en main, jamais recopié.
              const cycleLbl = cycleCourant?.nom || ''
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
                  <div style={{ marginTop: 6 }}><BadgeIA titre="Couple vérifié par l'IA à la validation (verdict figé)" /></div>
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

        {/* Vérif n°1 au dépôt : le couple (lu par l'IA dans le document) vs le couple déclaré.
            Le document à valider n'apparaît que si elle a répondu (garde-fou). */}
        {apercu && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {verif === 'loading' && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#1d4ed8' }}>
                <Spinner /> Vérification du couple…
              </span>
            )}
            {verif && verif !== 'loading' && (
              <div style={{ padding: '10px 12px', borderRadius: 8,
                border: `2px solid ${verif.couple.correspond ? '#16a34a' : '#dc2626'}`,
                background: verif.couple.correspond ? '#f0fdf4' : '#fef2f2' }}>
                <div style={{ fontWeight: 600, fontSize: 13, color: verif.couple.correspond ? '#166534' : '#991b1b' }}>
                  {verif.couple.correspond
                    ? `✓ Couple : ${cycleCourant?.nom || ''} / ${niveau} — confirmé par le document`
                    : `✗ Couple : ${cycleCourant?.nom || ''} / ${niveau} — le document ne correspond pas`}
                </div>
                <div style={{ fontSize: 12, color: '#475569', marginTop: 2 }}>{verif.couple.raison}</div>
                <div style={{ marginTop: 6 }}><BadgeIA titre="Couple vérifié par l'IA (lecture du document)" /></div>
              </div>
            )}
          </div>
        )}

        {/* POINT DE CONTRÔLE : dès que la vérif a répondu. Vert → valider ; rouge → forçage motivé. */}
        {apercu && verif && verif !== 'loading' && (
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
            {verif.couple.correspond ? (
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button type="button" className="btn-primary" title="Confirmer que c’est le bon document : ranger, extraire le texte, enregistrer la provenance"
                  onClick={() => valider(null)} disabled={busy} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {busy ? <><Spinner /> Validation en cours — épuration du texte et lecture des matières (jusqu’à 2-3 min)…</> : 'Valider : c’est le bon document'}
                </button>
                <button type="button" className="btn-secondary" title="Ce n’est pas le bon document : recommencer avec un autre lien ou fichier"
                  onClick={() => { setApercu(null); setVerif(null); setForcageMotif('') }} disabled={busy}>
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
                    {busy ? <><Spinner /> Validation en cours — épuration du texte et lecture des matières (jusqu’à 2-3 min)…</> : 'Forcer la validation malgré l’alerte'}
                  </button>
                  <button type="button" className="btn-secondary" title="Ce n’est pas le bon document : recommencer avec un autre lien ou fichier"
                    onClick={() => { setApercu(null); setVerif(null); setForcageMotif('') }} disabled={busy}>
                    Recommencer
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {resultat && (
          <div style={{ border: '1px solid #bbf7d0', background: '#f0fdf4', borderRadius: 8, padding: 14, fontSize: 12, color: '#166534' }}>
            {resultat.deja_valide && <><strong>Ce document avait déjà été validé</strong> — l’écran vient de se remettre à jour depuis la base.<br /></>}
            Référentiel enregistré pour <strong>{resultat.niveau}</strong> ({resultat.cycle}).<br />
            Document d’origine : <strong>{resultat.fichier_origine}</strong> (conservé en base).<br />
            Rangé dans <code>REFERENTIELS/{resultat.dossier}/referentiel.pdf</code>{resultat.pages != null && <> · {resultat.pages} page(s)</>}.
          </div>
        )}

        {/* ── Zone 2 : le document ÉPURÉ — le texte de travail que l'IA lit (colonne texte_epure,
            figée à la validation du dépôt). Lien de lecture + consultation pure des règles
            d'épuration (liste lue chez le serveur, une seule source : le module d'épuration ;
            l'admin voit, ne modifie pas — une nouvelle règle se fabrique avec le DEV). ── */}
        <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: 10 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b' }}>
            Fichier PDF épuré <span style={{ fontWeight: 400, color: '#64748b' }}>(utilisé par l’IA)</span>
          </div>
          {(dejaTraite || resultat) ? (
            <div style={{ marginTop: 6 }}>
              <button type="button" onClick={ouvrirEpure}
                title="Ouvrir le texte de travail épuré de ce référentiel — celui que l'IA lit (figé au dépôt)"
                style={{ background: 'none', border: 'none', padding: 0, color: '#1d4ed8',
                  fontSize: 12, fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}>
                Voir le document épuré
              </button>
            </div>
          ) : (
            <p style={{ fontSize: 12, color: '#94a3b8', margin: '6px 0 0' }}>
              Créé automatiquement à la validation du dépôt : le texte nettoyé que l’IA lira.
            </p>
          )}
          <div style={{ marginTop: 8 }}>
            <button type="button" onClick={ouvrirEpuration}
              title="Voir les règles de nettoyage appliquées automatiquement au texte de chaque PDF déposé"
              style={{ background: 'none', border: 'none', padding: 0, fontSize: 12, color: '#64748b',
                cursor: 'pointer', textDecoration: 'underline', textDecorationColor: '#cbd5e1' }}>
              {epurationOuvert ? '▾' : '▸'} Épuration automatique du document
              {epurationRegles ? ` (${epurationRegles.length} règles)` : ''}
            </button>
            {epurationOuvert && epurationRegles && (
              <ul style={{ margin: '8px 0 0', paddingLeft: 18, fontSize: 12, color: '#475569',
                display: 'flex', flexDirection: 'column', gap: 6 }}>
                {epurationRegles.map((r, i) => (
                  <li key={i}>
                    <strong style={{ color: '#1e293b' }}>{r.nom}</strong> — {r.description}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        </>)}

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
                <span style={{ marginLeft: 8 }}>
                  <BadgeIA titre="Matières proposées par l'IA (lecture du document + table des matières existantes)" />
                </span>
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                {dejaTraite
                  ? 'Couple déjà traité : voici les matières déjà en base pour ce niveau. Tu peux les renommer, en retirer, ou en ajouter à la main (geste exceptionnel).'
                  : 'Cochée = déjà en base (rien à faire). Décochée = nouvelle : cochez celles à ajouter. « Récupérer » enregistre en base les matières cochées et nouvelles.'}
              </p>
            </div>
            <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
              {matieresOuvert && matieres.some(m => !m.en_base && !m.cochee) && (
                <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
                  title="Cocher d'un coup toutes les matières de la liste — « Récupérer » s'active ensuite"
                  onClick={selectionnerTout}>
                  Sélectionner tout
                </button>
              )}
              <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
                title={matieresOuvert ? 'Réduire la liste des matières' : 'Développer la liste des matières'}
                onClick={() => setMatieresOuvert(o => !o)}>
                {matieresOuvert ? 'Réduire' : 'Développer'}
              </button>
            </div>
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
            {/* Passage Matières → Prompt (cas exceptionnel) : UN seul geste — affiche la cartouche
                Prompt ET lance la génération IA dans la foulée (le bouton fait ce qu'il dit).
                N'apparaît que lorsque « Récupérer » est grisé (plus rien à récupérer) ; se grise dès que
                la cartouche est affichée (prompt déjà en base ou clic fait) → jamais actif en permanence,
                donc jamais de génération par-dessus un prompt existant. */}
            {estVisible('prompt') && !matieres.some(m => m.cochee && !m.en_base) && (
              <button type="button" className="btn-primary"
                onClick={() => { setAfficherPrompt(true); setPromptOuvert(true); genererPromptDecoupe() }}
                disabled={afficherPrompt || !!promptDecoupe}
                title="Ouvrir la cartouche « Prompt de découpe » et lancer la génération du prompt par l'IA">
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
                Prompt de découpe
                <span style={{ marginLeft: 8 }}>
                  <BadgeIA titre="Prompt généré par l'IA (lecture du document) — relu, corrigé et validé par l'admin" />
                </span>
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
                <button type="button" onClick={genererPromptDecoupe}
                  disabled={!!promptBusy}
                  style={{ ...btnTypes('#7c3aed', !!promptBusy), cursor: promptBusy ? 'wait' : 'pointer' }}
                  title="L'IA génère le prompt de découpe adapté à ce document">
                  {promptBusy === 'generer' ? <><Spinner /> Génération…</> : <><span aria-hidden="true">🤖</span> Générer le prompt (IA)</>}
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
                  <button type="button" onClick={regenererPromptDecoupe}
                    disabled={!!promptBusy || !promptDecoupe.trim() || !remarques.trim()}
                    style={btnTypes('#7c3aed', !!promptBusy || !promptDecoupe.trim() || !remarques.trim())}
                    title="L'IA reprend le prompt actuel + vos remarques et produit un nouveau prompt qui en tient compte">
                    {promptBusy === 'regenerer' ? <><Spinner /> Régénération…</> : <><span aria-hidden="true">🤖</span> Régénérer le prompt en tenant compte de ma remarque ci-dessus</>}
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
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <div>
              <h2 className="text-base font-semibold text-gray-800">
                <Pastille etat={decoupeValide ? 'vert' : 'rouge'} titre="Vert = découpage validé (referentiels.decoupe_valide)." />
                Découpe
                <span style={{ marginLeft: 8 }}>
                  <BadgeIA titre="Document découpé en unités par l'IA (avec le prompt validé)" />
                </span>
              </h2>
              <p className="text-sm text-gray-500">
                Lancez la découpe avec le prompt validé, contrôlez les unités produites, puis validez le découpage — l'étape Types d'activité s'ouvre ensuite.
              </p>
            </div>
            <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title={decoupeOuvert ? 'Réduire' : 'Développer'} onClick={() => setDecoupeOuvert(o => !o)}>
              {decoupeOuvert ? 'Réduire' : 'Développer'}
            </button>
          </div>
          {decoupeOuvert && (<>
          <div>
            <button type="button" onClick={declencherDecoupe}
              disabled={!!promptBusy}
              style={btnTypes('#7c3aed', !!promptBusy)}
              title="Découper le référentiel avec le prompt validé (aperçu, aucune écriture).">
              {promptBusy === 'decouper' ? <><Spinner /> Découpe…</> : <><span aria-hidden="true">🤖</span> Découper</>}
            </button>
            {promptBusy === 'decouper' && (
              <JaugeAttente libelle="L’IA lit le document et le découpe en unités…" />
            )}
          </div>
          {decoupeUnites && (
            <div style={{ borderTop: '1px solid #E5E7EB', paddingTop: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                Résultat : {decoupeUnites.length} unité(s) produite(s) par l'IA
                {decoupeUnites.some(u => u.id) && (
                  <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 8, fontSize: 12 }}>
                    — cliquez sur une unité pour lire son texte complet
                  </span>
                )}
              </div>
              {/* Liste à gauche (cliquable si l'unité est EN BASE, donc a un id) ; lecture à droite :
                  le texte COMPLET de l'unité choisie — la matière première exacte de l'IA des profs. */}
              <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                <ol style={{ margin: 0, paddingLeft: 22, fontSize: 13, color: '#374151',
                  flex: uniteOuverteId ? '0 0 42%' : 1, minWidth: 0 }}>
                  {decoupeUnites.map((u, i) => (
                    <li key={u.id || i} style={{ marginBottom: 2 }}>
                      {u.id ? (
                        <button type="button" onClick={() => ouvrirUnite(u)}
                          title={uniteOuverteId === u.id ? 'Refermer la lecture' : 'Lire le texte complet de cette unité'}
                          style={{ background: 'none', border: 'none', padding: 0, font: 'inherit', textAlign: 'left',
                            cursor: 'pointer', color: uniteOuverteId === u.id ? '#1d4ed8' : '#374151',
                            fontWeight: uniteOuverteId === u.id ? 600 : 400, textDecoration: 'underline',
                            textDecorationColor: '#cbd5e1' }}>
                          {u.titre}
                        </button>
                      ) : u.titre}
                      {' '}<span style={{ color: '#9CA3AF' }}>({u.taille} car.)</span>
                    </li>
                  ))}
                </ol>
                {uniteOuverteId && (
                  <div style={{ flex: 1, minWidth: 0, border: '1px solid #e2e8f0', borderRadius: 8,
                    background: '#f8fafc', padding: '10px 12px' }}>
                    {uniteLoading ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#64748b' }}>
                        <Spinner /> Lecture…
                      </div>
                    ) : uniteEdit ? (
                      <>
                        <textarea value={uniteBrouillon} onChange={e => setUniteBrouillon(e.target.value)}
                          rows={14} disabled={uniteSaving}
                          style={{ width: '100%', fontFamily: 'inherit', fontSize: 13, color: '#1e293b',
                            border: '1px solid #cbd5e1', borderRadius: 8, padding: '8px 10px', resize: 'vertical' }} />
                        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                          <button type="button" className="btn-primary" onClick={validerUnite} disabled={uniteSaving}
                            title="Enregistrer le texte corrigé — son empreinte de recherche est recalculée dans le même geste">
                            {uniteSaving ? 'Enregistrement…' : 'Valider'}
                          </button>
                          <button type="button" className="btn-secondary" onClick={() => { setUniteEdit(false); setUniteBrouillon('') }}
                            disabled={uniteSaving} title="Abandonner la modification (rien n'est écrit)">
                            Annuler
                          </button>
                        </div>
                        {uniteSaving && (
                          <JaugeAttente libelle="Enregistrement du texte + recalcul de son empreinte de recherche…" />
                        )}
                      </>
                    ) : (
                      <>
                        <pre style={{ margin: 0, fontFamily: 'inherit', fontSize: 13, color: '#1e293b',
                          whiteSpace: 'pre-wrap', maxHeight: 420, overflow: 'auto' }}>{uniteTexte}</pre>
                        <div style={{ marginTop: 8 }}>
                          <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px' }}
                            onClick={() => { setUniteEdit(true); setUniteBrouillon(uniteTexte) }}
                            title="Corriger ce texte (nettoyage : numéro de page, coquille) — l'empreinte de recherche sera recalculée">
                            ✎ Modifier
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
              {/* L'admin a contrôlé la découpe et l'accepte : les unités sont vectorisées et écrites
                  en base (decoupe_valide → vert), puis l'étape Types d'activité s'ouvre. Grisé une
                  fois validé. */}
              <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                <button type="button" className="btn-primary" onClick={validerDecoupe}
                  disabled={!!promptBusy || decoupeValide}
                  title="Accepter ce découpage : les unités sont enregistrées en base, puis l'étape Types d'activité s'ouvre (dernière étape).">
                  {promptBusy === 'valider-decoupe' ? <><Spinner /> Validation…</>
                    : decoupeValide ? '✓ Découpage validé' : 'Valider le découpage'}
                </button>
                <BadgeIA titre="Découpe + embeddings réalisés par l'IA à la validation" />
              </div>
              {/* Jauge d'avancement RÉEL de la validation (lu via /decoupe/statut, jamais simulé) :
                  découpe IA → préparation des unités (fait/total) → écriture en base. */}
              {promptBusy === 'valider-decoupe' && decoupeProgress && (() => {
                const p = decoupeProgress
                const pct = p.etape === 'vectorisation' && p.total > 0
                  ? Math.round(15 + 80 * (p.fait / p.total))
                  : p.etape === 'ecriture' ? 97 : 8
                const libelle = p.etape === 'vectorisation'
                  ? `Préparation des unités pour la recherche (${p.fait}/${p.total})…`
                  : p.etape === 'ecriture' ? 'Enregistrement en base…'
                  : 'L’IA lit et découpe le document…'
                return (
                  <div style={{ marginTop: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12,
                      color: '#475569', marginBottom: 4 }}>
                      <span>{libelle}</span>
                      <span style={{ fontWeight: 600 }}>{pct} %</span>
                    </div>
                    <div style={{ height: 8, borderRadius: 999, background: '#e2e8f0', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: '#7c3aed',
                        borderRadius: 999, transition: 'width 0.6s ease' }} />
                    </div>
                  </div>
                )
              })()}
            </div>
          )}
          </>)}
        </div>
      )}

      {/* Carte 6 (DERNIÈRE étape de la chaîne) — Types d'activité de ce couple. Visible seulement une
          fois le découpage (N-1) validé (estVisible, comme les autres cartouches). Cocher/décocher =
          écriture directe en base au clic (put) ; badges = origine du type (IA/ADMIN/SYSTÈME). */}
      {estVisible('types') && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <div>
              <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
                <Pastille etat={typesChecked.size > 0 ? 'vert' : 'rouge'} titre="Vert = au moins un type d'activité coché pour ce couple." />
                Types d'activité de ce couple
                <span style={{ marginLeft: 8 }}>
                  <BadgeIA titre="Types détectés et suggérés par l'IA (lecture du référentiel) — cochés par l'admin" />
                </span>
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                L’IA se lance toute seule : elle lit le document épuré avec la table des types sous les yeux, retient les types de ce couple (prompts et précisions générés dans la foulée). Toi tu fais le ménage : ✕ pour retirer, le champ du bas pour ajouter.
              </p>
            </div>
            <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title={typesOuvert ? 'Réduire' : 'Développer'} onClick={() => setTypesOuvert(o => !o)}>
              {typesOuvert ? 'Réduire' : 'Développer'}
            </button>
          </div>

          {typesOuvert && (<>
          {/* Ligne du haut : le compte des types retenus + le seul bouton restant (RELANCER la
              détection — la première se lance toute seule à l'arrivée sur un couple vierge). */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <h3 className="text-sm font-bold text-gray-800" style={{ margin: 0 }}>
              Types retenus pour ce couple
              <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 6, fontSize: 13 }}>({typesDuCouple.length})</span>
            </h3>
            <button onClick={detecterTypes} disabled={typesBusy} style={{ ...btnTypes('#7c3aed', typesBusy), marginLeft: 'auto' }}
              title="Relancer la lecture du document par l'IA (utile après un nouveau dépôt ou une table enrichie)">
              {typesDetecting ? <><Spinner /> Détection en cours…</> : '🤖 Relancer la détection'}
            </button>
          </div>
          {typesDetecting && (
            <JaugeAttente libelle="L’IA lit le document épuré et le compare à la table des types…" />
          )}
          {/* Jauge RÉELLE des précisions : générées type par type juste après la détection. */}
          {precisProgress && (
            <div>
              <div style={{ fontSize: 12, color: '#1d4ed8', marginBottom: 4 }}>
                <BadgeIA titre="L'IA prépare les précisions de chaque type pour ce niveau" />{' '}
                Précisions en cours de préparation ({precisProgress.fait + 1}/{precisProgress.total})
                {precisProgress.label ? ` — ${precisProgress.label}` : ''}…
              </div>
              <div style={{ height: 8, borderRadius: 999, background: '#e2e8f0', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${Math.round(100 * precisProgress.fait / Math.max(1, precisProgress.total))}%`,
                  background: '#7c3aed', transition: 'width 0.4s' }} />
              </div>
            </div>
          )}

          {/* Types RETENUS pour ce couple — chaque ligne = une ligne de lien en base, rien d'autre.
              Retirer (✕) = confirmation puis SUPPRESSION réelle du lien (+ ses précisions, cascade) ;
              une future détection recrée la ligne si l'IA relit le type dans le document. */}
          <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
              {typesDuCouple.length === 0 ? (
                <p className="text-sm" style={{ padding: '1.5rem', textAlign: 'center', color: '#94a3b8' }}>
                  {typesDetecting ? 'La liste se remplit dès que l’IA a fini sa lecture…'
                    : 'Aucun type pour ce couple — la détection se lance toute seule, ou ajoute un type ci-dessous.'}
                </p>
              ) : typesDuCouple.map((t, i) => {
                const coche = true
                const editOuvert = promptEditId === t.id
                const precisOuvert = precisEditId === t.id
                return (
                  <Fragment key={t.id}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
                    borderBottom: (i < typesDuCouple.length - 1 && !editOuvert && !precisOuvert) ? '1px solid #f1f5f9' : 'none' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
                      <span style={{ fontWeight: 600, color: '#1e293b', fontSize: 13 }}>{t.label}</span>
                      {t.is_default && <span style={{ ...badgeOrigine('admin'), background: '#fefce8', color: '#a16207' }}>défaut</span>}
                      {/* Badge DOUBLE : d'où vient le type × qui l'a retenu. « SYSTÈME · IA » = type de
                          notre table retenu par l'IA ; « IA » = type né de la détection ; « ADMIN » = ajout manuel. */}
                      {typesSource[t.id] && (
                        <span style={badgeOrigine(typesSource[t.id])}>
                          {typesSource[t.id] === 'ia'
                            ? (t.origine === 'ia' ? 'IA' : 'SYSTÈME · IA')
                            : (SOURCE_LABEL[typesSource[t.id]] || typesSource[t.id])}
                        </span>
                      )}
                    </span>
                    {/* Prompt du type POUR CE COUPLE — état lu en base + bouton d'édition. */}
                    {coche && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                        {(typesPrompt[t.id] || '').trim()
                          ? <span style={{ color: '#166534', fontWeight: 700, fontSize: 11, whiteSpace: 'nowrap' }}>✓ prompt</span>
                          : <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, background: '#fef2f2', color: '#dc2626', fontWeight: 700, fontSize: 11, whiteSpace: 'nowrap' }}>⚠ vide</span>}
                        <button type="button" onClick={() => { setPromptEditId(editOuvert ? null : t.id); setPromptBrouillon(editOuvert ? '' : (typesPrompt[t.id] || '')) }}
                          title={`Voir / corriger le prompt de « ${t.label} » pour ce couple`}
                          style={{ padding: '3px 10px', borderRadius: 8, border: '1px solid #cbd5e1',
                            background: editOuvert ? '#eff6ff' : 'white', color: '#334155', cursor: 'pointer', fontSize: 12, whiteSpace: 'nowrap' }}>
                          ✎ Prompt
                        </button>
                        {(typesNbPrecis[t.id] || 0) > 0
                          ? <span style={{ color: '#166534', fontWeight: 700, fontSize: 11, whiteSpace: 'nowrap' }}>⚑ {typesNbPrecis[t.id]} précision{typesNbPrecis[t.id] > 1 ? 's' : ''}</span>
                          : <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, background: '#f1f5f9', color: '#94a3b8', fontWeight: 700, fontSize: 11, whiteSpace: 'nowrap' }}>0 précision</span>}
                        <button type="button" onClick={() => ouvrirPrecisions(t)}
                          title={`Précisions de « ${t.label} » pour ce couple`}
                          style={{ padding: '3px 10px', borderRadius: 8, border: '1px solid #cbd5e1',
                            background: precisOuvert ? '#eff6ff' : 'white', color: '#334155', cursor: 'pointer', fontSize: 12, whiteSpace: 'nowrap' }}>
                          ✎ Précisions
                        </button>
                        <button type="button"
                          onClick={() => { if (window.confirm(`Retirer « ${t.label} » des types de ce couple ?\n\nSes précisions pour ce couple seront supprimées aussi. Une future détection le remettra si l'IA le relit dans le document.`)) basculerType(t.id) }}
                          title={`Retirer « ${t.label} » de ce couple — supprime ce type et ses précisions pour ce couple (les autres niveaux ne sont pas touchés)`}
                          style={{ height: 26, width: 26, borderRadius: 6, border: '1px solid #fecaca', background: '#fef2f2',
                            color: '#dc2626', cursor: 'pointer', display: 'inline-flex', alignItems: 'center',
                            justifyContent: 'center', fontSize: 13, flexShrink: 0 }}>✕</button>
                      </span>
                    )}
                  </div>
                  {editOuvert && (
                    <div style={{ padding: '12px 14px', background: '#f8fafc',
                      borderBottom: i < typesDuCouple.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 8 }}>
                        Prompt de « {t.label} » — pour {coupleLabel}
                      </div>
                      <textarea value={promptBrouillon} onChange={e => setPromptBrouillon(e.target.value)}
                        rows={8} placeholder="Prompt généré automatiquement au coche, avec {texte} et {referentiel} — éditable ici."
                        style={{ width: '100%', fontFamily: 'monospace', fontSize: 12, padding: 10, border: '1px solid #cbd5e1', borderRadius: 8, resize: 'vertical', boxSizing: 'border-box' }} />
                      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                        <button type="button" onClick={() => validerPromptType(t)} disabled={promptSaving || !promptBrouillon.trim()}
                          style={btnTypes('#16a34a', promptSaving || !promptBrouillon.trim())}
                          title="Enregistrer ce prompt pour ce couple">{promptSaving ? 'Enregistrement…' : 'Valider'}</button>
                        <button type="button" onClick={() => { setPromptEditId(null); setPromptBrouillon('') }}
                          style={{ padding: '0 16px', height: 36, borderRadius: 8, border: '1px solid #cbd5e1', background: 'white', color: '#334155', fontSize: 13, cursor: 'pointer' }}>Annuler</button>
                      </div>
                    </div>
                  )}
                  {precisOuvert && (
                    <div style={{ padding: '12px 14px', background: '#f8fafc',
                      borderBottom: i < typesDuCouple.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 8 }}>
                        Précisions de « {t.label} » — pour {coupleLabel}
                      </div>
                      {precisLoading ? (
                        <div>
                          <BadgeIA titre="L'IA génère les précisions de ce type pour ce niveau" />
                          <JaugeAttente libelle="L’IA prépare les précisions adaptées à ce niveau…" />
                        </div>
                      ) : precisList.length > 0 ? (
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
                          {precisList.map(p => (
                            <li key={p.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
                              padding: '6px 10px', borderRadius: 8, border: '1px solid #e2e8f0', background: 'white', fontSize: 13, color: '#1e293b' }}>
                              <span style={{ fontWeight: 500 }}>{p.libelle}</span>
                              <button type="button" disabled={precisBusy}
                                onClick={() => supprimerPrecisCouple(t, p)}
                                title={`Supprimer « ${p.libelle} »`}
                                style={{ height: 26, width: 26, borderRadius: 6, border: '1px solid #fecaca', background: '#fef2f2', color: '#dc2626',
                                  cursor: precisBusy ? 'default' : 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, flexShrink: 0 }}>🗑</button>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p style={{ fontSize: 12, color: '#94a3b8', margin: 0 }}>Aucune précision pour ce couple.</p>
                      )}
                      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                        <input value={newPrecis} onChange={e => setNewPrecis(e.target.value)}
                          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); ajouterPrecisCouple(t) } }}
                          placeholder="Ajouter une précision…"
                          style={{ flex: 1, minWidth: 0, height: 36, padding: '0 12px', fontSize: 13, borderRadius: 8, border: '1px solid #cbd5e1', boxSizing: 'border-box' }} />
                        <button type="button" onClick={() => ajouterPrecisCouple(t)} disabled={precisBusy || !newPrecis.trim()}
                          style={btnTypes('#0f172a', precisBusy || !newPrecis.trim())}
                          title="Ajouter cette précision pour ce couple">＋ Ajouter</button>
                        <button type="button" onClick={() => { setPrecisEditId(null); setPrecisList([]); setNewPrecis('') }}
                          style={{ padding: '0 16px', height: 36, borderRadius: 8, border: '1px solid #cbd5e1', background: 'white', color: '#334155', fontSize: 13, cursor: 'pointer' }}>Fermer</button>
                      </div>
                    </div>
                  )}
                  </Fragment>
                )
              })}
            </div>

          {/* Zone d'ajout MANUEL (champ + bouton) : le libellé rejoint le catalogue s'il est nouveau
              (anti-doublon) et est collé à CE couple dans le même geste (badge admin). */}
          <div style={{ display: 'flex', gap: 8, maxWidth: 480 }}>
            <input value={typesNouveau} onChange={e => setTypesNouveau(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') ajouterTypeCatalogue(typesNouveau) }}
              placeholder="Ajouter un type à ce couple…"
              style={{ flex: 1, padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: 13 }} />
            <button onClick={() => ajouterTypeCatalogue(typesNouveau)} disabled={typesBusy || !typesNouveau.trim()}
              style={btnTypes('#16a34a', typesBusy || !typesNouveau.trim())}
              title="Ajouter ce type pour ce couple (rejoint le catalogue s'il est nouveau)"><span aria-hidden="true">＋</span> Ajouter</button>
          </div>
          </>)}
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

      {/* Fenêtre du DOCUMENT ÉPURÉ : le texte de travail lu par l'IA (colonne texte_epure,
          figée à la validation du dépôt). Même patron que la fenêtre PDF (clic dehors ou ×). */}
      {showEpure && (
        <div onClick={() => setShowEpure(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                Document épuré — le texte de travail que l’IA lit (figé au dépôt)
              </span>
              <button type="button" onClick={() => setShowEpure(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <pre style={{ flex: 1, overflow: 'auto', margin: 0, padding: 14, fontSize: 12,
              color: '#334155', whiteSpace: 'pre-wrap', background: '#f8fafc' }}>
              {epureTexte === null ? 'Lecture…'
                : (epureTexte || 'Aucun texte de travail enregistré pour ce couple.')}
            </pre>
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
