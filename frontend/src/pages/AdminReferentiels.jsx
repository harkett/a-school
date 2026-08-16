// Page Référentiels — Étape 1 du chantier « Référentiel → matières + chunks ».
// L'admin déclare le couple (cycle + niveau), fournit le PDF officiel par LIEN ou
// par DÉPÔT, CONTRÔLE l'aperçu du document récupéré, puis valide : le système le
// range, en extrait le texte et enregistre sa provenance.
// Hors périmètre étape 1 : extraction des matières, chunks, recherche web automatique.
import { Fragment, useEffect, useRef, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD, TIMEOUT_LONG, TIMEOUT_XLONG, MSG_TIMEOUT } from '../utils/api.js'
import { lignesMatieres, nbRetenues as compterRetenues, aRetenir as resteARetenir } from '../utils/matieresReferentiel.js'
import FenetrePro from '../components/FenetrePro.jsx'
import Attente from '../components/Attente.jsx'
import { showError } from '../errorDialog.js'
import { demanderConfirmation } from '../confirmDialog.js'
import JaugeAttente from '../components/JaugeAttente.jsx'
import FriseProgression from '../components/FriseProgression.jsx'
import InfoGuide from '../components/InfoGuide.jsx'
import { aideReferentiels } from '../utils/aideReferentiels.js'
import { Spinner } from '../components/icones.jsx'

// Sablier — indicateur d'attente pendant un appel IA lent (génération / découpe). Même motif
// que Consigne/Ambiguites : SVG animé via l'@keyframes `spin` global (index.css).

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

// La table des matières (lignes + les deux comptages qui la pilotent) vit dans
// utils/matieresReferentiel.js, avec ses tests — même découpage que utils/profil.js face à
// MonProfil : l'écran rend, le module décide de ce qu'il rend.

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

// Le MODÈLE réellement en service, lu une seule fois pour tout l'écran. Trois fournisseurs
// cohabitent désormais : « c'est l'IA qui l'a fait » ne suffit plus à comprendre un résultat —
// devant une découpe ratée, la première question est LEQUEL a répondu. Le cache vit au niveau
// module (pas dans un état de page) : le badge est posé une dizaine de fois, il ne doit pas
// déclencher une dizaine d'appels. Échec silencieux : un badge sans modèle vaut mieux qu'un écran
// qui tombe pour un libellé.
let _moteurIACache = null
function useMoteurIA() {
  const [moteur, setMoteur] = useState(_moteurIACache)
  useEffect(() => {
    if (_moteurIACache) return
    let vivant = true
    fetch('/api/admin/ai-models', { credentials: 'include' })
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        if (!d?.courant?.modele) return
        _moteurIACache = d.courant
        if (vivant) setMoteur(d.courant)
      })
      .catch(() => {})
    return () => { vivant = false }
  }, [])
  return moteur
}

// Repère « IA » — petit badge violet posé là où l'IA agit SANS bouton dédié (vérification du
// couple, ingestion). Il signale à l'admin que le résultat vient de l'IA, ET avec quel modèle.
// Même palette IA que les badges d'origine (SOURCE_STYLE.ia) : cohérence, aucune couleur en double.
// Pastille « ça coûte » : le rond ambre au bout d'un bouton d'IA PAYANTE. Le violet dit « c'est
// l'IA », l'ambre dit « ce clic est facturé » — deux informations, deux couleurs, jamais mélangées.
// Le € est écrit une taille au-dessus du libellé du bouton : c'est lui qu'on doit voir en premier.
// LES PROMPTS NE S'ÉCRIVENT PLUS ICI (08/08/2026). Cet écran montrait — et enregistrait — les
// prompts du référentiel, en même temps que l'écran Admin → IA → Prompts. Deux portes pour la même
// donnée, et un admin qui cherchait la sienne sans savoir laquelle faisait foi : « ça fait la 3e
// fois que je pose la même question ». Une seule porte désormais, l'écran Prompts ; ici on regarde.
//
// Les fenêtres gardent leur bouton « Voir » : lire le prompt qui vient de produire une découpe,
// sans changer d'écran, c'est le geste courant. C'est l'écriture qui part, pas l'affichage.
function ZonePromptLecture({ texte, vide }) {
  const propre = (texte || '').trim()
  return (
    <textarea value={propre} readOnly spellCheck={false} placeholder={vide}
      style={{ flex: 1, overflow: 'auto', margin: 0, padding: 14, fontSize: 12,
        color: '#475569', background: '#f1f5f9', border: 'none', outline: 'none',
        resize: 'none', width: '100%', boxSizing: 'border-box',
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', lineHeight: 1.5 }} />
  )
}

function PiedPromptLecture({ niveau, onFermer }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
      borderTop: '1px solid #e2e8f0', background: '#f8fafc' }}>
      <span style={{ fontSize: 12.5, lineHeight: 1.5, color: '#475569' }}>
        Ce prompt ne sert qu’à <strong>{niveau}</strong>. Il se modifie dans{' '}
        <strong>Admin → IA → Prompts → Référentiels</strong> — seul endroit où un prompt s’écrit.
      </span>
      <button type="button" onClick={onFermer} title="Fermer"
        style={{ ...btnTypes('#1F6EEB'), marginLeft: 'auto' }}>
        <span aria-hidden="true">✕</span> Fermer
      </button>
    </div>
  )
}

function PastilleEuro({ taille = 13 }) {
  return (
    <span aria-hidden="true"
      style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        width: taille + 5, height: taille + 5, borderRadius: '50%', background: '#f59e0b',
        color: '#111827', fontSize: taille, fontWeight: 800, lineHeight: 1, flexShrink: 0 }}>
      €
    </span>
  )
}


function BadgeIA({ titre }) {
  const moteur = useMoteurIA()
  return (
    <span
      title={`${titre || "Réalisé par l'IA"}${moteur
        ? ` — moteur en service : ${moteur.fournisseur} / ${moteur.modele}, réponse plafonnée à ${moteur.max_tokens} tokens`
        : ''}`}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 10, fontWeight: 700,
        padding: '2px 7px', borderRadius: 999, background: '#f5f3ff', color: '#7c3aed',
        textTransform: 'uppercase', letterSpacing: '0.5px', verticalAlign: 'middle' }}>
      <span aria-hidden="true">✨</span> IA
      {moteur && (
        // Les trois valeurs qu'on cherche devant une réponse ratée : QUI a répondu, avec QUEL
        // modèle, et jusqu'à COMBIEN il pouvait écrire. En minuscules et sans graisse — le badge
        // informe, il ne crie pas. La place existe sur la ligne, autant la remplir utilement.
        <span style={{ fontWeight: 500, textTransform: 'none', letterSpacing: 0, opacity: 0.85 }}>
          · {moteur.fournisseur} · {moteur.modele} · {moteur.max_tokens} tok
        </span>
      )}
    </span>
  )
}

// La jauge d'attente IA (barre navette + secondes) vit désormais dans
// components/JaugeAttente.jsx — partagée avec les écrans prof (une jauge dès qu'on appelle l'IA).

export default function AdminReferentiels() {
  const [arbre, setArbre] = useState([])        // arbre COMPLET cycles → niveaux (GET /admin/programmes)
  const [refsListe, setRefsListe] = useState([])  // colonne 2 : référentiels déposés (GET /admin/referentiels/liste)
  // Le référentiel dont la fenêtre de transfert est ouverte. `null` = fermée : une opération qui
  // déplace un référentiel entier ne doit pas pouvoir être déclenchée en visant autre chose.
  const [transfertPour, setTransfertPour] = useState(null)
  // Le compte rendu du dernier import réussi. Il INFORME, il n'arrête rien : il reste sous le
  // bouton. Ce qui refuse, lui, passe par la fenêtre bloquante.
  const [importOk, setImportOk] = useState('')
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
  // Table des matières du référentiel — INTERFACE seule ; le code (lecture des
  // candidats + enregistrement en base) sera branché à l'étape suivante.
  const [matieres, setMatieres] = useState([])
  const [nouvelleMatiere, setNouvelleMatiere] = useState('')
  const [editIndex, setEditIndex] = useState(-1)
  const [editNom, setEditNom] = useState('')
  const [bilanApercu, setBilanApercu] = useState('')
  // État du couple sélectionné : { existe_referentiel, referentiel:{fichier,source,date_doc}, matieres:[{id,nom}] }
  const [etat, setEtat] = useState(null)
  const [voirDepot, setVoirDepot] = useState(false)  // « Voir » de la liste des documents déposés
  // Contrôle n°1 au dépôt (SANS IA) : { cycle, cycle_trouve, niveau, niveau_trouve } | null.
  // Gardé pour l'AFFICHER sur la ligne du document déposé.
  const [controle, setControle] = useState(null)
  // Les tâches du bouton « Valider le référentiel ». `taches` est la liste ANNONCÉE par le serveur
  // (première ligne du flux — l'écran n'en garde aucune copie en dur), `tachesFaites` les ids reçus
  // au fur et à mesure. La tâche en cours = la première qui n'est pas encore dans `tachesFaites`.
  const [taches, setTaches] = useState([])
  const [tachesFaites, setTachesFaites] = useState([])
  // Prompt des MATIÈRES de CE référentiel (referentiels.prompt_matieres) : il ne sert qu'à ce
  // couple cycle+niveau. Écrit à la main par l'admin, ou par l'IA au premier « Proposer les
  // matières » s'il est encore vide. Vide = la détection retombe sur le prompt général.
  const [promptMatieres, setPromptMatieres] = useState('')
  const [promptMatieresValide, setPromptMatieresValide] = useState(false)
  const [promptMatieresOuvert, setPromptMatieresOuvert] = useState(false)
  // Texte en cours d'édition dans la fenêtre du prompt — séparé de `promptMatieres`, qui reste ce
  // qui est EN BASE : fermer sans enregistrer ne doit rien changer.
  // MÉTA-PROMPT des matières : la recette qui sert à ÉCRIRE le prompt de lecture. Il peut venir de
  // UN SEUL endroit — la case de ce niveau (referentiels.prompt_meta_matieres). Le repli sur un
  // réglage général a été retiré le 08/08/2026 : `metaSource` vaut 'referentiel' ou 'aucun'.
  // Cet écran lisait le réglage GÉNÉRAL et lui seul : il montrait donc un texte qui n'était pas
  // celui du niveau affiché, alors que la colonne du niveau était remplie. Lu à la demande.
  const [metaOuvert, setMetaOuvert] = useState(false)
  const [metaPrompt, setMetaPrompt] = useState(null)     // null = pas encore lu pour ce couple
  const [metaSource, setMetaSource] = useState('')       // 'referentiel' | 'aucun'
  // MÉTA-PROMPT de la DÉCOUPE : le jumeau du précédent. Il peut venir de DEUX endroits — la case
  // de ce niveau (referentiels.prompt_meta_decoupe) — SEULE source depuis le 08/08/2026 (Setting
  // `prompt_meta_decoupe`). Le serveur dit lequel des deux sert vraiment : `metaDecoupeSource`.
  const [metaDecoupeOuvert, setMetaDecoupeOuvert] = useState(false)
  const [metaDecoupe, setMetaDecoupe] = useState(null)       // null = pas encore lu pour ce couple
  const [metaDecoupeSource, setMetaDecoupeSource] = useState('')  // 'referentiel' | 'aucun'
  // Attente PROPRE aux deux boutons de la liste : 'verifier' | 'valider' | ''. Séparée de `busy`
  // (le dépôt du fichier), sinon un clic sur Vérifier rallume le sablier et la jauge de la lecture.
  const [actionBusy, setActionBusy] = useState('')
  // Phase en cours du dépôt : 'lecture' (le fichier monte et on lit ses pages) puis 'controle'
  // (recherche du cycle et du niveau DANS le document). La jauge dit laquelle des deux tourne.
  const [depotPhase, setDepotPhase] = useState('')
  const [showPdf, setShowPdf] = useState(false)   // fenêtre de relecture du PDF déjà enregistré
  const [showSuppr, setShowSuppr] = useState(false)  // modale de confirmation de suppression du référentiel
  const [supprBusy, setSupprBusy] = useState(false)  // suppression en cours (bouton grisé)
  const [matieresOuvert, setMatieresOuvert] = useState(false)   // bloc Matières repliable (vue d'ensemble) — démarre replié
  // Prompt de découpe DU CYCLE — lu ici en LECTURE SEULE (il s'écrit dans Prompts → Découpe par cycle).
  const [promptDecoupe, setPromptDecoupe] = useState('')       // texte du prompt, affiché tel quel
  const [promptValide, setPromptValide] = useState(false)      // relu par l'admin (voyant seulement)
  const [decoupeValide, setDecoupeValide] = useState(false)    // étape FINALE : découpe validée → puce verte (lu via /prompt-decoupe)
  const [promptBusy, setPromptBusy] = useState('')             // 'decouper' | 'valider-decoupe' | ''
  const [decoupeUnites, setDecoupeUnites] = useState(null)     // résultat de la découpe : [{titre, taille}]
  const [proceduresOuvert, setProceduresOuvert] = useState(false)   // panneau « Comment ça marche ? »
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

  // Le <pre> du document épuré, pour pouvoir en sélectionner le contenu d'un bouton : un texte de
  // 200 000 caractères ne se sélectionne pas à la souris, et Ctrl+A prendrait toute la page.
  const epureRef = useRef(null)
  function selectionnerEpure() {
    const noeud = epureRef.current
    if (!noeud) return
    const plage = document.createRange()
    plage.selectNodeContents(noeud)
    const selection = window.getSelection()
    selection.removeAllRanges()
    selection.addRange(plage)
  }

  // Document épuré : le TEXTE DE TRAVAIL du couple, FIGÉ en base à la validation du dépôt
  // (colonne texte_epure) — get pur au clic, aucun recalcul. C'est exactement ce que l'IA lit.
  //
  // RELU À CHAQUE OUVERTURE, jamais gardé en mémoire. Le texte gardé d'une ouverture à l'autre a
  // fait travailler sur un document PÉRIMÉ le 14/08/2026 : le texte épuré venait d'être refait en
  // base, la fenêtre montrait toujours l'ancien, et rien à l'écran ne le disait. Ce texte part
  // ensuite chez un agent extérieur et sert de référence à la découpe entière — l'économie d'un
  // GET local ne vaut pas ce risque-là.
  function ouvrirEpure() {
    setShowEpure(true)
    setEpureTexte(null)
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
  // Texte en cours d'édition dans la fenêtre du prompt de découpe — séparé de `promptDecoupe`,
  // qui reste ce qui est EN BASE : fermer sans enregistrer ne doit rien changer.
  // Prompt des TYPES D'ACTIVITÉ de CE référentiel (referentiels.prompt_types) — le troisième du
  // même geste que les matières et la découpe : un par couple cycle+niveau.
  // MÉTA-PROMPT des TYPES : le troisième jumeau. Deux endroits possibles — la case de ce niveau
  // (referentiels.prompt_meta_types) — seule source depuis le 08/08/2026 ; le
  // serveur dit lequel sert (`metaTypesSource`). Lu à la demande, à l'ouverture de la fenêtre.
  // LE GABARIT DES PROMPTS DE TYPE (`prompt_gabarit_type`, registre des prompts d'outils).
  // C'est le prompt QUI FABRIQUE les prompts : à la création d'un type — détection ou ajout à la
  // main — il est recopié avec {label} et {niveau} remplis, et le résultat devient le prompt de
  // génération de ce type. Il n'appartient donc à aucun type en particulier : sa place est au
  // BAS de la cartouche, pas sur une ligne. Lecture seule, aucun appel d'IA.
  const [gabaritOuvert, setGabaritOuvert] = useState(false)
  const [gabarit, setGabarit] = useState(null)        // null = pas encore lu
  const [gabaritEnBase, setGabaritEnBase] = useState(false)
  const [metaTypesOuvert, setMetaTypesOuvert] = useState(false)
  const [metaTypes, setMetaTypes] = useState(null)       // null = pas encore lu pour ce couple
  const [metaTypesSource, setMetaTypesSource] = useState('')  // 'referentiel' | 'aucun'
  // MÉTA-PROMPT des PRÉCISIONS : quatrième jumeau. Même règle que les trois autres — la case de
  // ce niveau (referentiels.prompt_meta_precisions) est la seule source (repli général retiré).
  const [metaPrecisionsOuvert, setMetaPrecisionsOuvert] = useState(false)
  // Le PROMPT des précisions, lu d'ici en simple consultation (09/08/2026). Il n'y avait aucun
  // moyen de le voir depuis l'écran où l'on travaille : il fallait sortir dans Prompts. C'est
  // une LECTURE, pas une porte d'écriture — le dépôt reste dans Prompts → Référentiels.
  const [promptPrecisionsOuvert, setPromptPrecisionsOuvert] = useState(false)
  const [promptPrecisions, setPromptPrecisions] = useState(null)
  const [promptPrecisionsValide, setPromptPrecisionsValide] = useState(false)
  const [metaPrecisions, setMetaPrecisions] = useState(null)
  const [metaPrecisionsSource, setMetaPrecisionsSource] = useState('')
  const [promptTypes, setPromptTypes] = useState('')
  const [promptTypesValide, setPromptTypesValide] = useState(false)
  const [promptTypesOuvert, setPromptTypesOuvert] = useState(false)
  // Repli/développement des autres cartouches — état de départ INCHANGÉ (dépliées → true).
  const [coupleOuvert, setCoupleOuvert] = useState(true)
  const [pdfOuvert, setPdfOuvert] = useState(true)
  const [decoupeOuvert, setDecoupeOuvert] = useState(true)
  const [typesOuvert, setTypesOuvert] = useState(true)
  const [precisionsOuvert, setPrecisionsOuvert] = useState(true)
  // ── Types d'activité DU RÉFÉRENTIEL (dernière cartouche) : fenêtre sur `types_activite`, où
  //    chaque ligne appartient au document qui la nomme — exactement comme les matières
  //    (05/08/2026 : plus de catalogue global, plus de liaison N–N). Une seule liste : les
  //    propositions de la détection et les types retenus s'y côtoient, `validee` les distingue.
  //    Cocher = retenir (put en base au clic), puis re-GET. Zéro donnée en dur, zéro tampon.
  const [types, setTypes] = useState([])                       // [{id,label,validee,origine,prompt,nb_precisions}]
  const [typesNouveau, setTypesNouveau] = useState('')         // saisie « ajouter un type à ce référentiel »
  const [typesBusy, setTypesBusy] = useState(false)            // détection / ajout en cours
  const [typesDetecting, setTypesDetecting] = useState(false)  // détection IA en cours → sablier
  const [precisProgress, setPrecisProgress] = useState(null)   // jauge RÉELLE précisions : {fait, total, label} | null
  // Prompt par type : panneau déplié sous la ligne, EN LECTURE SEULE — il se modifie dans
  // Admin → IA → Prompts. `promptEditId` = id du type dont le panneau est ouvert (null = aucun).
  // Le prompt lui-même vit sur la ligne du type (`t.prompt`), lu en base — aucune copie ici.
  const [promptEditId, setPromptEditId] = useState(null)

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
    preparerCouple()
  }

  // On vient de choisir un couple → l'écran repart propre pour LUI. C'est un geste de l'admin
  // (cliquer une ligne, changer un menu), pas une conséquence à rattraper dans un effet : le
  // get qui suit ne fait plus que remplir ce qui vient d'être vidé.
  function preparerCouple() {
    // Un document EN ATTENTE survit à la sélection du couple — la décision de le garder se
    // prend après lecture de l'état (dans l'effet). Sans document en attente : reset simple.
    if (!apercu) setResultat(null)
    setBilanApercu(''); setShowPdf(false)
    setShowEpure(false); setEpureTexte(null)   // changement de couple : le texte épuré de l'ancien ne vaut plus
    setTypesNouveau(''); setPrecisProgress(null)   // repartir propre sur ce couple (le get réhydrate la liste + badges)
    setUniteOuverteId(null); setUniteTexte('')   // changement de couple : on referme la lecture d'unité
    // Les TROIS méta-prompts dépendent du couple (la case du niveau passe devant le réglage
    // général) : changer de couple efface ce qui a été lu, sinon on montrerait celui du voisin.
    setMetaPrompt(null); setMetaSource('')
    setMetaDecoupe(null); setMetaDecoupeSource('')
    setMetaTypes(null); setMetaTypesSource('')
    setMetaPrecisions(null); setMetaPrecisionsSource('')
    setPromptPrecisions(null); setPromptPrecisionsValide(false)
    // À chaque sélection d'un couple : toutes les cartouches repliées (bouton sur « Développer »).
    setCoupleOuvert(false); setPdfOuvert(false); setMatieresOuvert(false); setPromptOuvert(false); setDecoupeOuvert(false); setTypesOuvert(false)
  }

  // Plus aucun couple choisi → l'écran n'a plus rien à montrer de ce couple-là. C'est un GESTE
  // (« + Nouveau », ou vider un des deux menus), pas une conséquence à rattraper après coup dans
  // un effet : on le fait là où l'admin agit, une bonne fois.
  function viderCeQuiDependDuCouple() {
    setEtat(null); setMatieres([])
    setTypes([]); setTypesNouveau('')
  }

  // « + Nouveau » (colonne 2) : remet l'écran en création — aucun couple choisi, tout vide.
  function nouveau() {
    // resetSteps : remet TOUS les done à false via leur source (la table les calcule depuis ces valeurs).
    setCycleId(''); setNiveauId(''); setNiveau('')  // → couple.done = false
    viderCeQuiDependDuCouple()                      // → pdf / matieres / prompt / decoupe.done = false (tous lus depuis etat)
    // Carte « Document PDF » : on repart d'une zone vierge — l'effet [cycleId, niveau] ne vide
    // pas ces états-là quand le couple est déjà vide.
    setApercu(null); setResultat(null); setNomFichier(''); setUrl('')
    setTaches([]); setTachesFaites([])
    setCoupleOuvert(true)                           // repartir en création : la carte Couple s'ouvre (bouton « Réduire »)
  }

  // Bouton FINAL « Valider le découpage » : l'admin accepte la découpe → put decoupe_valide=true en base.
  // C'est la dernière étape : on recharge la liste pour que la puce du menu passe au vert (get, zéro copie).
  async function validerDecoupe() {
    // CE BOUTON N'APPELLE JAMAIS L'IA (08/08/2026). Il écrit la découpe que « Découper » a
    // produite et que l'admin a sous les yeux, et rien d'autre. Sans elle, il est grisé. Les
    // embeddings sont calculés en local : l'opération ne coûte rien.
    if (decoupeValide && !await demanderConfirmation({
      titre: 'Refaire le découpage de ce référentiel ?',
      message: `Ce référentiel a DÉJÀ son découpage validé${decoupeUnites && decoupeUnites.length
        ? ` (${decoupeUnites.length} unités en base)` : ''}. Elles seront sauvegardées, puis remplacées.`
        + '\n\nAucun appel à l’IA : c’est la découpe affichée qui est écrite, et les embeddings '
        + 'sont calculés en local. L’opération est gratuite.',
      confirmLabel: 'Refaire le découpage',
      cancelLabel: 'Annuler',
      danger: true,
    })) return
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
      setEtat(dd); setMatieres(lignesMatieres(dd)); setResultat(null); setApercu(null)
      chargerListe()   // colonne 2 : le référentiel supprimé disparaît (relecture)
    } catch { showError("La suppression du référentiel a échoué (réseau).") }
    finally { setSupprBusy(false) }
  }


  // Le document en attente, lisible depuis la lecture du couple sans en devenir un déclencheur.
  const apercuRef = useRef(apercu)
  useEffect(() => { apercuRef.current = apercu })

  // À la sélection d'un couple (cycle + niveau) : lire son état en base. Si un référentiel
  // est DÉJÀ enregistré (« déjà traité »), on affiche son nom réel + ses matières existantes
  // et on grise la zone de dépôt. Sinon, dépôt normal.
  useEffect(() => {
    if (!cycleId || !niveau) return   // pas de couple : rien à lire (le vidage se fait au geste)
    let annule = false
    fetchWithTimeout(`/api/admin/referentiels/etat?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        if (annule) return
        setEtat(d)
        setMatieres(lignesMatieres(d))
        // Mode AJOUT (couple sans référentiel) : la carte PDF s'ouvre pour déposer tout de suite.
        // Mode « déjà traité » : elle reste repliée (simple relecture).
        setPdfOuvert(!(d && d.existe_referentiel))
        // Document EN ATTENTE : couple DÉJÀ TRAITÉ → le document ne le concerne pas, on le jette
        // (l'écran passe en relecture). Couple libre → on le garde tel quel, sans rien vérifier.
        // Le document en attente est lu par une ref : sa présence est une CONSÉQUENCE de ce que
        // le serveur vient de répondre, elle ne doit pas relancer la lecture du couple.
        if (apercuRef.current && d && d.existe_referentiel) { setApercu(null); setResultat(null) }
      })
      .catch(() => { if (!annule) setEtat(null) })
    // Prompt de découpe du couple (EN BASE) — généré par l'IA, corrigé/validé par l'admin.
    fetchWithTimeout(`/api/admin/referentiels/prompt-decoupe?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!annule) { setPromptDecoupe(d && d.prompt ? d.prompt : ''); setPromptValide(!!(d && d.valide)); setDecoupeValide(!!(d && d.decoupe_valide)) } })
      .catch(() => { if (!annule) { setPromptDecoupe(''); setPromptValide(false); setDecoupeValide(false) } })
    // Prompt des MATIÈRES de CE couple (EN BASE, referentiels.prompt_matieres) — un par
    // référentiel : deux diplômes du même cycle ne se lisent pas avec les mêmes repères.
    fetchWithTimeout(`/api/admin/referentiels/prompt-matieres?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!annule) { setPromptMatieres(d && d.prompt ? d.prompt : ''); setPromptMatieresValide(!!(d && d.valide)) } })
      .catch(() => { if (!annule) { setPromptMatieres(''); setPromptMatieresValide(false) } })
    // Prompt des TYPES D'ACTIVITÉ de CE couple (EN BASE, referentiels.prompt_types).
    fetchWithTimeout(`/api/admin/referentiels/prompt-types?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!annule) { setPromptTypes(d && d.prompt ? d.prompt : ''); setPromptTypesValide(!!(d && d.valide)) } })
      .catch(() => { if (!annule) { setPromptTypes(''); setPromptTypesValide(false) } })
    // Unités du découpage DÉJÀ en base (referentiel_chunks) → réaffichées telles quelles (get, zéro recalcul).
    fetchWithTimeout(`/api/admin/referentiels/decoupe?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!annule) setDecoupeUnites(d && d.unites && d.unites.length ? d.unites : null) })
      .catch(() => { if (!annule) setDecoupeUnites(null) })
    // Types d'activité DU référentiel (propositions + retenus) — lu en base (get, zéro copie).
    fetchWithTimeout(`/api/admin/referentiels/types-activite?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        if (annule || !d) return
        setTypes(d.types || [])
      })
      .catch(() => { if (!annule) setTypes([]) })
    return () => { annule = true }
  }, [cycleId, niveau])


  // ── Prompt des MATIÈRES, propre au RÉFÉRENTIEL ──────────────────────────────────────
  // Rangé sur le couple cycle+niveau (06/08/2026). Il vivait sur le cycle, et c'était faux : le
  // cycle « BTS » porte dix-huit niveaux, et le prompt écrit sur le premier était ensuite servi à
  // tous les autres — un prompt écrit sur les options d'un diplôme n'apprend rien sur ses voisins.
  // Relit le prompt de matières du référentiel (get, zéro copie). Appelée au changement de couple
  // ET après « Proposer les matières », qui peut l'avoir fait écrire par l'IA côté serveur.
  // Ouvre la fenêtre du méta-prompt des matières et le lit au passage. Une seule porte, qui rend le
  // texte de la case du niveau et dit `source` : 'referentiel' ou 'aucun' —
  // exactement comme la découpe. Aucune IA : c'est de la lecture.
  function ouvrirMetaPrompt() {
    setMetaOuvert(true)
    if (metaPrompt !== null) return   // déjà lu pour ce couple
    fetchWithTimeout(`/api/admin/referentiels/prompt-meta-matieres?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => r.ok ? r.json() : null)
      .then(d => { setMetaPrompt(d && typeof d.prompt === 'string' ? d.prompt : ''); setMetaSource(d ? d.source : '') })
      .catch(() => { setMetaPrompt(''); setMetaSource('') })
  }

  // Ouvre la fenêtre du méta-prompt de la DÉCOUPE et le lit au passage. Une seule porte, qui rend
  // le texte de la case du niveau et dit `source` : 'referentiel' ou 'aucun'
  // — plutôt que deux appels et un choix refait ici. Aucune IA : c'est de la lecture.
  function ouvrirMetaDecoupe() {
    setMetaDecoupeOuvert(true)
    if (metaDecoupe !== null) return   // déjà lu pour ce couple
    fetchWithTimeout(`/api/admin/referentiels/prompt-meta-decoupe?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => r.ok ? r.json() : null)
      .then(d => { setMetaDecoupe(d && typeof d.prompt === 'string' ? d.prompt : ''); setMetaDecoupeSource(d ? d.source : '') })
      .catch(() => { setMetaDecoupe(''); setMetaDecoupeSource('') })
  }

  // Ouvre la fenêtre du GABARIT et le lit au passage, dans le registre des prompts d'outils
  // (`GET /api/admin/prompts`, la même source que l'écran Prompts). Aucune IA : lecture seule.
  function ouvrirGabaritType() {
    setGabaritOuvert(true)
    if (gabarit !== null) return   // déjà lu
    fetchWithTimeout('/api/admin/prompts', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        const ligne = (d && d.prompts ? d.prompts : []).find(x => x.key === 'gabarit_type')
        setGabarit(ligne ? (ligne.current || '') : '')
        setGabaritEnBase(!!(ligne && ligne.en_base))
      })
      .catch(() => { setGabarit(''); setGabaritEnBase(false) })
  }

  // Ouvre la fenêtre du méta-prompt des TYPES et le lit au passage. Aucune IA : c'est de la lecture.
  function ouvrirMetaTypes() {
    setMetaTypesOuvert(true)
    if (metaTypes !== null) return   // déjà lu pour ce couple
    fetchWithTimeout(`/api/admin/referentiels/prompt-meta-types?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => r.ok ? r.json() : null)
      .then(d => { setMetaTypes(d && typeof d.prompt === 'string' ? d.prompt : ''); setMetaTypesSource(d ? d.source : '') })
      .catch(() => { setMetaTypes(''); setMetaTypesSource('') })
  }

  // Ouvre la fenêtre du méta-prompt des PRÉCISIONS et le lit au passage. Aucune IA : lecture.
  function ouvrirMetaPrecisions() {
    setMetaPrecisionsOuvert(true)
    if (metaPrecisions !== null) return   // déjà lu pour ce couple
    fetchWithTimeout(`/api/admin/referentiels/prompt-meta-precisions?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => r.ok ? r.json() : null)
      .then(d => { setMetaPrecisions(d && typeof d.prompt === 'string' ? d.prompt : ''); setMetaPrecisionsSource(d ? d.source : '') })
      .catch(() => { setMetaPrecisions(''); setMetaPrecisionsSource('') })
  }

  // Ouvre la fenêtre du PROMPT des précisions et le lit au passage. Aucune IA : lecture.
  function ouvrirPromptPrecisions() {
    setPromptPrecisionsOuvert(true)
    if (promptPrecisions !== null) return   // déjà lu pour ce couple
    fetchWithTimeout(`/api/admin/referentiels/prompt-precisions?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => r.ok ? r.json() : null)
      .then(d => { setPromptPrecisions(d && typeof d.prompt === 'string' ? d.prompt : ''); setPromptPrecisionsValide(!!(d && d.valide)) })
      .catch(() => { setPromptPrecisions(''); setPromptPrecisionsValide(false) })
  }

  async function chargerPromptMatieres() {
    if (!cycleId || !niveau) return
    try {
      const r = await fetchWithTimeout(`/api/admin/referentiels/prompt-matieres?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
        { credentials: 'include' }, TIMEOUT_STD)
      const d = r.ok ? await r.json().catch(() => null) : null
      setPromptMatieres(d && d.prompt ? d.prompt : '')
      setPromptMatieresValide(!!(d && d.valide))
    } catch { /* la zone reste en l'état : une lecture ratée n'efface rien */ }
  }

  // LES QUATRE FONCTIONS D'ÉCRITURE ONT ÉTÉ RETIRÉES le
  // 08/08/2026 (`enregistrerPromptMatieres`, `enregistrerPromptDecoupe`, `enregistrerPromptTypes`,
  // `validerPromptType`). Un prompt ne s'écrit plus que dans Admin → IA → Prompts → Référentiels :
  // deux portes pour la même donnée, c'est un admin qui ne sait plus laquelle fait foi. Les
  // fenêtres d'ici restent, en lecture seule — voir `ZonePromptLecture` / `PiedPromptLecture`.



  // Déclenche la découpe (lecture seule) avec le prompt validé → affiche les unités produites.
  async function declencherDecoupe() {
    // LE BOUTON N'EST PLUS GRISÉ QUAND LE DÉCOUPAGE EST DÉJÀ VALIDÉ (08/08/2026). Un bouton
    // éteint ne dit pas pourquoi, et il ENFERME : refaire une découpe volontairement — parce que
    // le document ou le prompt a changé — devenait impossible sans redéposer le référentiel.
    // À la place, l'avertissement dit franchement ce que le clic va coûter, et il faut le
    // confirmer. C'est le seul geste payant de cette cartouche : il se voit et il se signe.
    const lignes = ['⚠️  CET APPEL EST FACTURÉ. Le texte entier du référentiel part au moteur IA.']
    if (!promptDecoupe.trim()) {
      lignes.push('Ce référentiel n’a PAS de prompt de découpe : l’IA en rédigera d’abord un, '
        + 'puis découpera. DEUX appels payants pour ce seul clic.')
    }
    if (decoupeValide) {
      lignes.push(`Le découpage de ce référentiel est DÉJÀ validé${decoupeUnites && decoupeUnites.length
        ? ` (${decoupeUnites.length} unités en base)` : ''} : relancer repaie un travail déjà fait.`)
    }
    lignes.push('Rien n’est écrit en base par ce clic : la découpe s’affiche en aperçu, et c’est '
      + '« Valider le découpage » qui enregistre.')
    if (!await demanderConfirmation({
      titre: 'Découper avec l’IA — appel payant',
      message: lignes.join('\n\n'),
      confirmLabel: 'Lancer et payer',
      danger: true,
    })) return
    setPromptBusy('decouper')
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/prompt-decoupe/decouper', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau }),
        // TIMEOUT_XLONG (05/08/2026), la MÊME valeur que le dépôt : l'IA lit le document entier
        // et rend la liste de ses unités — sur un référentiel de 88 pages, ça dure plusieurs
        // minutes. À 45 s le navigateur abandonnait un travail que le serveur, lui, finissait
        // dans le vide. Et au premier référentiel d'un cycle, cet appel écrit d'abord le prompt
        // de découpe du cycle : deux appels IA à la suite.
      }, TIMEOUT_XLONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || "La découpe a échoué."); return }
      setDecoupeUnites(d.unites || [])
    } catch (e) {
      showError(e?.message === MSG_TIMEOUT
        ? "La découpe a dépassé le délai de 5 minutes et a été interrompue (délai dépassé) — ce n'est pas une panne réseau."
        : "La découpe a échoué (réseau).")
    }
    finally { setPromptBusy('') }
  }

  // CONTRÔLE N°1, avant que le document entre dans la liste : le PDF nomme-t-il le cycle OU le
  // niveau choisi ? Recherche de texte côté serveur, sans IA. Faux → boîte de message et le
  // document N'EST PAS déposé (rien ne s'affiche dans la liste).
  async function coupleNommeDansDocument(token) {
    setControle(null); setDepotPhase('controle')
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/controle-couple', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, cycle_id: Number(cycleId), niveau_id: Number(niveauId) }),
        // Palier XLONG : ce contrôle lit le document ENTIER — une minute sur un programme de
        // 139 pages. À 45 s l'écran abandonnait AVANT le serveur et accusait le réseau, qui
        // n'y était pour rien : le document était en train d'être lu, normalement.
      }, TIMEOUT_XLONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Contrôle du document impossible (${r.status}).`, { danger: true }); return false }
      if (!d.trouve) {
        // Le message DIT ce qui a été trouvé et ce qui manque : « BTS » présent mais pas le
        // niveau, c'est justement le cas piégeux (164 référentiels de BTS contiennent « BTS »).
        const debut = d.cycle_trouve
          ? `Le cycle « ${d.cycle} » a bien été trouvé dans le document, mais pas le niveau « ${d.niveau} ».`
          : `Ni le cycle « ${d.cycle} » ni le niveau « ${d.niveau} » n’ont été trouvés dans le document.`
        const manque = (d.manquants && d.manquants.length)
          ? `\n\nMots du niveau absents du document : ${d.manquants.map(m => `« ${m} »`).join(', ')}.` : ''
        showError(`${debut}${manque}\n\nCe n’est donc pas le bon référentiel : le document n’a pas été déposé.`,
          { danger: true, titre: 'Document refusé' })
        return false
      }
      setControle(d)   // gardé pour l'afficher sur la ligne du document
      return true
    } catch (e) {
      showError(e?.message === MSG_TIMEOUT
        ? "Le contrôle du document a dépassé le délai de 5 minutes et a été interrompu (délai dépassé) — ce n'est pas une panne réseau."
          + "\n\nLe cycle et le niveau sont cherchés dans TOUTES les pages du document : sur un texte très long, la lecture peut ne pas aboutir."
        : "Contrôle du document impossible : le serveur n'a pas répondu (réseau).", { danger: true })
      return false
    }
    finally { setDepotPhase('') }
  }

  async function recupererLien() {
    if (!url.trim()) { showError('Collez d’abord le lien du PDF.'); return }
    // Nouveau document = nouvelle validation à faire : le constat et les tâches cochées du
    // document précédent s'effacent, sinon le bouton resterait remplacé par son « ✓ ».
    setBusy(true); setDepotPhase('lecture'); setApercu(null); setResultat(null)
    setTaches([]); setTachesFaites([])
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/preparer-lien', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      if (!(await coupleNommeDansDocument(d.token))) { setUrl(''); return }
      setApercu(d); setSource(url.trim()); setBilanApercu('')
    } catch (e) { showError(`Récupération impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  async function recupererDepot(file) {
    if (!file) return
    setNomFichier(file.name)
    // Nouveau document = nouvelle validation à faire : le constat et les tâches cochées du
    // document précédent s'effacent, sinon le bouton resterait remplacé par son « ✓ ».
    setBusy(true); setDepotPhase('lecture'); setApercu(null); setResultat(null)
    setTaches([]); setTachesFaites([])
    try {
      const form = new FormData()
      form.append('file', file)
      const r = await fetchWithTimeout('/api/admin/referentiels/preparer-depot', {
        method: 'POST', credentials: 'include', body: form,
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      if (!(await coupleNommeDansDocument(d.token))) { setNomFichier(''); return }
      setApercu(d); setSource('dépôt manuel'); setBilanApercu('')
    } catch (e) { showError(`Lecture du fichier impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  // Bouton BLEU « Valider le référentiel » — LE geste du dépôt, SANS IA : le document est rangé,
  // son texte est lu et figé, la ligne du référentiel est écrite. Les trois tâches arrivent une
  // par une (flux NDJSON) : chacune se coche À L'INSTANT où le serveur l'a terminée, au lieu d'un
  // écran figé jusqu'au bout. Pas de fetchWithTimeout ici, et c'est voulu : le flux dit lui-même
  // que le serveur travaille, il n'y a donc plus de silence à interrompre.
  async function validerLeReferentiel() {
    if (!apercu) return
    setActionBusy('verifier'); setTaches([]); setTachesFaites([])
    try {
      const r = await fetch('/api/admin/referentiels/valider-flux', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        // `controle_niveau` : la preuve du contrôle n°1 qui a autorisé ce dépôt, transmise pour
        // être FIGÉE en base — sinon elle mourrait avec l'écran. null si le contrôle manque.
        body: JSON.stringify({ token: apercu.token, cycle_id: Number(cycleId), niveau_id: Number(niveauId),
                               source, fichier_origine: apercu.filename,
                               controle_niveau: controle
                                 ? { niveau: controle.niveau, trouve: controle.niveau_trouve,
                                     manquants: controle.manquants || [] }
                                 : null }),
      })
      if (!r.ok || !r.body) throw new Error(`Erreur ${r.status}`)
      const lecteur = r.body.getReader()
      const decodeur = new TextDecoder()
      let reste = '', fin = null, erreur = ''
      for (;;) {
        const { value, done } = await lecteur.read()
        if (done) break
        reste += decodeur.decode(value, { stream: true })
        const lignes = reste.split('\n')
        reste = lignes.pop()          // la dernière peut être coupée en deux : elle attend la suite
        for (const ligne of lignes) {
          if (!ligne.trim()) continue
          let msg
          try { msg = JSON.parse(ligne) } catch { continue }
          if (msg.taches) setTaches(msg.taches)
          else if (msg.faite) setTachesFaites(f => [...f, msg.faite])
          else if (msg.fin) fin = msg.fin
          else if (msg.erreur) erreur = msg.erreur
        }
      }
      if (erreur) throw new Error(erreur)
      if (!fin) throw new Error('Le serveur n’a pas confirmé la validation.')
      // Le document a quitté la zone d'attente : la cartouche « Document PDF » se referme, comme
      // avant. Tout ce qui le concerne (nom, contrôle du niveau) se lit maintenant EN BASE, dans
      // la cartouche « Référentiel au format PDF » — plus rien ne vit à l'écran.
      setResultat(fin); setEpureTexte(null)
      setApercu(null); setControle(null); setNomFichier(''); setBilanApercu('')
      setTaches([]); setTachesFaites([])
      chargerListe()
      await rafraichirEtat()   // le référentiel existe désormais en base (get, zéro copie)
    } catch (e) { showError(`Validation impossible.\n\n${e.message}`, { danger: true }) }
    finally { setActionBusy('') }
  }

  // Bouton « Proposer les matières (IA) » — il vit dans la cartouche MATIÈRES, qui est l'étape
  // d'après : la validation du document ne touche pas aux matières. LE seul appel IA de cette
  // partie : l'IA lit le texte déjà figé en base et PROPOSE des matières (non cochées).
  async function proposerMatieres() {
    // GARDE-FOU DU PORTE-MONNAIE : tout bouton d'IA payante demande d'abord. La fenêtre s'ouvre
    // AVANT le moindre appel réseau — renoncer ici ne coûte donc rien, et c'est ce qui permet
    // d'essayer le bouton sans payer. Sens interdit rouge : ce n'est pas un avertissement de
    // politesse, c'est de l'argent.
    if (!await demanderConfirmation({
      titre: 'ATTENTION — CE CLIC EST PAYANT',
      message: "Le texte complet du référentiel va être envoyé au moteur d'IA, et cet appel est FACTURÉ.\n" +
        "Si ce référentiel n'a pas encore son prompt de lecture des matières, l'IA l'écrira d'abord : DEUX appels au lieu d'un.\n" +
        "Rien n'entre au programme automatiquement — vous cocherez ensuite ce que vous gardez." +
        // Le bouton n'est plus éteint quand la liste est déjà remplie (08/08/2026) : c'est ici que
        // la situation se dit, pas dans un bouton mort qui laisse chercher pourquoi il ne répond pas.
        (dejaPropose ? "\n\nDes propositions sont DÉJÀ à l'écran : relire le document par-dessus "
          + "repaie une lecture déjà faite." : ''),
      confirmLabel: 'Lancer et payer la lecture',
      payant: true,
      cancelLabel: 'Annuler',
      danger: true,
      icone: 'interdit',
    })) return
    setActionBusy('valider')
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/matieres-proposer', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau }),
      }, TIMEOUT_XLONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      // La cartouche du document n'est plus touchée ici : la proposition des matières est l'étape
      // d'après, elle n'a pas à effacer le constat de la validation.
      await rafraichirEtat()
      setMatieresOuvert(true)
      // Le serveur a pu ÉCRIRE le prompt de ce référentiel au passage (il était encore vide).
      // On ne relit la zone QUE si elle est vide : sinon on écraserait, sans prévenir, un texte
      // que l'admin est en train d'écrire ou de coller.
      if (!promptMatieres.trim()) await chargerPromptMatieres()
    } catch (e) { showError(`Proposition des matières impossible.\n\n${e.message}`, { danger: true }) }
    finally { setActionBusy('') }
  }

  const champ = { width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 10px', fontSize: 13 }
  const onglet = (actif) => ({
    fontSize: 12, padding: '6px 14px', borderRadius: 6, cursor: 'pointer',
    border: actif ? '1px solid #1F6EEB' : '1px solid #e2e8f0',
    background: actif ? '#eff6ff' : '#f8fafc', color: actif ? '#1d4ed8' : '#64748b', fontWeight: 600,
  })
  // Petites flèches d'ordre de la liste des documents déposés.
  const btnOrdre = { width: 28, height: 28, borderRadius: 6, border: '1px solid #e2e8f0',
    background: '#f8fafc', color: '#64748b', fontSize: 11, lineHeight: 1 }

  // ── Table des matières : cocher est une interaction d'écran, c'est « Récupérer » qui écrit
  //    (il RETIENT les matières cochées : `validee` passe à vrai en base). Une matière déjà
  //    retenue est verrouillée cochée — pour la sortir du programme, c'est « Retirer ».
  function toggleCochee(i) {
    setMatieres(matieres.map((m, j) => (j === i && !m.validee ? { ...m, cochee: !m.cochee } : m)))
  }
  // « Sélectionner tout » : coche d'un coup toutes les matières PROPOSÉES (les retenues le sont
  // déjà et sont verrouillées). Aucune écriture : « Récupérer » se dégrise tout seul.
  function selectionnerTout() {
    setMatieres(matieres.map(m => (m.validee ? m : { ...m, cochee: true })))
  }
  // Ajout à la main : la ligne n'existe pas encore en base (id null) — « Récupérer » la créera
  // dans CE référentiel, retenue d'emblée.
  function ajouterMain() {
    const nom = nouvelleMatiere.trim()
    if (!nom) return
    setMatieres([...matieres, { id: null, nom, validee: false, cochee: true }])
    setNouvelleMatiere('')
  }
  async function rafraichirEtat() {
    const re = await fetchWithTimeout(`/api/admin/referentiels/etat?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
    if (re.ok) { const dd = await re.json(); setEtat(dd); setMatieres(lignesMatieres(dd)) }
  }
  function demarrerRenommage(i) { setEditIndex(i); setEditNom(matieres[i].nom) }
  async function validerRenommage() {
    const nom = editNom.trim()
    const i = editIndex
    setEditIndex(-1); setEditNom('')
    if (!nom || i < 0) return
    const ligne = matieres[i]
    if (nom === ligne.nom) return
    if (ligne.id) {
      // Renommage EN BASE (garde l'id, donc aucun lien cassé). Portée : CE référentiel, et lui
      // seul — une matière du même nom dans un autre diplôme est une autre matière, elle ne bouge pas.
      if (!await demanderConfirmation({
        titre: `Renommer « ${ligne.nom} » en « ${nom} » ?`,
        message: `Le libellé change pour le référentiel de « ${niveau} », et nulle part ailleurs. Les profs qui ont cette matière la verront sous son nouveau nom.`,
        confirmLabel: 'Renommer',
      })) return
      try {
        const r = await fetchWithTimeout('/api/admin/referentiels/matiere', {
          method: 'PATCH', credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ matiere_id: ligne.id, nouveau_nom: nom }),
        }, TIMEOUT_STD)
        const d = await r.json().catch(() => ({}))
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
    if (!ligne.id) {
      setMatieres(ms => ms.filter((_, j) => j !== i))   // ajoutée à la main, jamais écrite : retrait local
      return
    }
    // Une matière RETENUE sort du programme des profs (désactivation réversible) ; une simple
    // PROPOSITION est SUPPRIMÉE, elle n'est jamais entrée au programme. Deux gestes de poids
    // différents, donc deux questions différentes.
    if (!await demanderConfirmation({
      titre: ligne.validee
        ? `Retirer « ${ligne.nom} » du programme de « ${niveau} » ?`
        : `Supprimer la proposition « ${ligne.nom} » ?`,
      message: ligne.validee
        ? "Elle disparaîtra des menus des profs. Désactivation réversible : l'historique est conservé, rien n'est supprimé."
        : "Elle est effacée de la liste. Elle n'est jamais entrée au programme, personne ne la voit. « Proposer les matières » peut la reproposer.",
      confirmLabel: ligne.validee ? 'Retirer' : 'Supprimer',
    })) return
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/retirer-matiere', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, matiere_id: ligne.id }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      if (d.profs > 0) {
        showError(`« ${d.matiere} » a été retirée de ce niveau (réversible).\n\nÀ savoir : elle est encore choisie par ${d.profs} prof(s). Rien n'a été cassé (désactivation seulement).`)
      }
      await rafraichirEtat()
    } catch (e) { showError(`Retrait impossible.\n\n${e.message}`) }
  }
  // « Supprimer tout » — le même geste que la ligne, en boucle sur les seules PROPOSITIONS. Sert
  // avant de relancer une lecture : la liste repart VRAIMENT vide, on voit ce que le prompt du
  // moment donne, sans l'empilement des lectures précédentes. Les matières RETENUES ne sont
  // jamais touchées — elles sont au programme, des profs les voient.
  async function ecarterTout() {
    const aEcarter = matieres.filter(m => !m.validee && m.id)
    if (!aEcarter.length) { setBilanApercu('Aucune proposition à supprimer.'); return }
    if (!await demanderConfirmation({
      titre: `Supprimer les ${aEcarter.length} propositions ?`,
      message: "Elles sont effacées de la liste. Elles ne sont jamais entrées au programme, personne ne les voit. Les matières que vous avez retenues ne bougent pas. « Proposer les matières » relira le document.",
      confirmLabel: 'Supprimer tout',
    })) return
    setActionBusy('ecarter-tout')
    try {
      for (const m of aEcarter) {
        const r = await fetchWithTimeout('/api/admin/referentiels/retirer-matiere', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cycle_id: Number(cycleId), niveau, matiere_id: m.id }),
        }, TIMEOUT_STD)
        if (!r.ok) {
          const d = await r.json().catch(() => ({}))
          throw new Error(d.detail || `Erreur ${r.status} sur « ${m.nom} »`)
        }
      }
      await rafraichirEtat()   // la liste se relit EN BASE (get, zéro copie)
    } catch (e) { showError(`La suppression des propositions a échoué.\n\n${e.message}`) }
    finally { setActionBusy('') }
  }

  async function recuperer() {
    // On envoie les matières que l'admin RETIENT : les cochées (propositions acceptées et lignes
    // ajoutées à la main). Les déjà retenues n'ont pas besoin d'être renvoyées — le serveur les
    // reconnaîtrait de toute façon comme « déjà présentes ».
    const aEnvoyer = matieres.filter(m => m.cochee && !m.validee).map(m => m.nom)
    if (!aEnvoyer.length) { setBilanApercu('Aucune matière cochée à retenir.'); return }
    setBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/matieres', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, matieres: aEnvoyer }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setBilanApercu(`Retenu : ${d.nb_ajoutees} matière(s), ${d.nb_deja} déjà au programme.`)
      await rafraichirEtat()   // relecture : les matières retenues reviennent avec validee vraie
    } catch (e) { showError(`Enregistrement impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  // ── Types d'activité du référentiel : re-GET (la base fait foi) après chaque écriture.
  async function chargerTypes() {
    if (!cycleId || !niveau) return
    try {
      const r = await fetchWithTimeout(`/api/admin/referentiels/types-activite?cycle_id=${cycleId}&niveau=${encodeURIComponent(niveau)}`,
        { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) return
      const d = await r.json()
      setTypes(d.types || [])
    } catch { /* réseau : on garde l'affichage courant */ }
  }

  // ✎ Prompt → Valider : PUT réel du prompt de CE type (réécrit la colonne de sa ligne), puis re-GET.

  // GET (lecture pure) des précisions de CE type. Aucune écriture, aucun sablier IA. Renvoie le
  // tableau lu (et l'affiche). Utilisé à l'ouverture ET après ajout/suppression (re-lecture).
  async function chargerPrecisType(typeId) {
    try {
      const r = await fetchWithTimeout(`/api/admin/referentiels/types-activite/precisions?cycle_id=${Number(cycleId)}&niveau=${encodeURIComponent(niveau)}&type_id=${typeId}`,
        { credentials: 'include' }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Lecture des précisions impossible (${r.status}).`); setPrecisList([]); return null }
      const list = d.precisions || []
      setPrecisList(list)
      return list
    } catch { showError('Lecture des précisions impossible.'); setPrecisList([]); return null }
  }

  // Ouvre/ferme le panneau. À l'ouverture : GET, et RIEN D'AUTRE. Ouvrir pour regarder lançait
  // l'IA quand la liste était vide (15/08/2026) — un panneau qu'on déplie ne doit rien facturer.
  // Le panneau propose son propre bouton quand il n'a rien à montrer.
  function ouvrirPrecisions(t) {
    if (precisEditId === t.id) { setPrecisEditId(null); setPrecisList([]); setNewPrecis(''); return }
    setPrecisEditId(t.id); setNewPrecis(''); setPrecisList([])
    chargerPrecisType(t.id)
  }

  // Lance l'IA (sablier ✨) : génère les précisions et les ÉCRIT en base, puis les affiche. Appelé
  // UNIQUEMENT quand la lecture est vide sur un type RETENU — jamais après une suppression manuelle.
  async function genererPrecisType(typeId) {
    setPrecisLoading(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/types-activite/precisions/generer', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, type_id: typeId }),
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Génération des précisions impossible (${r.status}).`); return }
      setPrecisList(d.precisions || [])
      await chargerTypes()   // met à jour le badge « N précisions » de la ligne
    } catch { showError('Génération des précisions impossible.') }
    finally { setPrecisLoading(false) }
  }

  // CREATE encadré (précision du type) : Ajouter = POST. Doublon refusé côté back (deja_present) → message humain.
  async function ajouterPrecisType(t) {
    const libelle = newPrecis.trim()
    if (!libelle) { showError('Indiquez un libellé pour la précision.'); return }
    setPrecisBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/types-activite/precisions', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, type_id: t.id, libelle }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Ajout impossible (${r.status}).`); return }
      setNewPrecis('')
      if (d.deja_present) showError(`La précision « ${d.libelle} » existe déjà pour ce type.`)
      await chargerPrecisType(t.id)
      await chargerTypes()   // met à jour le badge « N précisions » de la ligne
    } catch { showError('Ajout impossible.') }
    finally { setPrecisBusy(false) }
  }

  // DELETE encadré (précision du type) : après confirmation, puis re-get.
  async function supprimerPrecisType(t, p) {
    if (!await demanderConfirmation({
      titre: `Supprimer la précision « ${p.libelle} » ?`,
      message: 'Cette action est irréversible.',
      confirmLabel: 'Supprimer',
      danger: true,
    })) return
    setPrecisBusy(true)
    try {
      const r = await fetchWithTimeout(`/api/admin/referentiels/types-activite/precisions/${p.id}?cycle_id=${Number(cycleId)}&niveau=${encodeURIComponent(niveau)}&type_id=${t.id}`,
        { method: 'DELETE', credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) { const e = await r.json().catch(() => ({})); showError(e.detail || `Suppression impossible (${r.status}).`) }
      await chargerPrecisType(t.id)
      await chargerTypes()   // met à jour le badge « N précisions » de la ligne
    } catch { showError('Suppression impossible.') }
    finally { setPrecisBusy(false) }
  }

  // La case EST le put : cocher = type RETENU (le prof le voit), décocher = il redevient une
  // proposition. Écrit direct en base au clic, puis re-GET. C'est LE geste de l'admin sur cette
  // cartouche — celui des matières, une ligne à la fois.
  async function retenirType(t, veutRetenir) {
    if (!cycleId || !niveau) return
    setTypes(ts => ts.map(x => (x.id === t.id ? { ...x, validee: veutRetenir } : x)))   // optimiste
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/types-activite', {
        method: 'PUT', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau, type_id: t.id, validee: veutRetenir }),
      }, TIMEOUT_STD)
      if (!r.ok) { const e = await r.json().catch(() => ({})); showError(e.detail || `Enregistrement impossible (${r.status}).`) }
      await chargerTypes()
      // ET RIEN DE PLUS (15/08/2026). Cocher enchaînait ici sur la génération IA des précisions :
      // un geste gratuit qui déclenchait un geste payant, sans que rien à l'écran ne le dise.
      // Les deux voies du produit — payante et gratuite — se rejoignaient dans la même case.
      // Les précisions ont maintenant leur bouton, avec sa pastille € ; la case ne fait qu'écrire.
    } catch { showError('Enregistrement impossible.'); await chargerTypes() }
  }

  // Le geste de la case, appliqué D'UN COUP à toutes les lignes qui ne sont pas déjà dans l'état
  // voulu. La route ne retient qu'UN type à la fois : on boucle les PUT, et on ne relit qu'à la
  // fin — une seule lecture pour vingt-cinq écritures.
  //
  // ET ON NE GÉNÈRE AUCUNE PRÉCISION ICI, à la différence de la case unitaire. Cocher vingt-cinq
  // propositions d'un clic lancerait vingt-cinq appels IA que personne n'a demandés : le prix
  // d'un clic doit rester lisible. Les précisions gardent leur propre bouton, et leur propre
  // décision.
  async function retenirTousLesTypes(veutRetenir) {
    if (!cycleId || !niveau) return
    const aFaire = types.filter(t => !!t.validee !== veutRetenir)
    if (aFaire.length === 0) return
    const n = aFaire.length
    if (!await demanderConfirmation({
      titre: veutRetenir
        ? `Mettre ${n} type${n > 1 ? 's' : ''} d’activité au programme ?`
        : `Retirer ${n} type${n > 1 ? 's' : ''} d’activité du programme ?`,
      message: veutRetenir
        ? `Ils apparaîtront dans la liste où un professeur de ${coupleLabel} choisit son type d’activité, au moment de préparer une séance. Aucune précision n’est générée : aucun appel IA, aucun coût.`
        : `Ils disparaissent de la liste où le professeur choisit son type d’activité, et redeviennent des propositions ici. Rien n’est perdu : leurs précisions et leurs prompts restent en base, recocher les ramène intacts.`,
      confirmLabel: veutRetenir ? 'Mettre au programme' : 'Retirer',
    })) return
    setTypesBusy(true)
    setTypes(ts => ts.map(t => ({ ...t, validee: veutRetenir })))       // optimiste
    try {
      for (const t of aFaire) {
        const r = await fetchWithTimeout('/api/admin/referentiels/types-activite', {
          method: 'PUT', credentials: 'include', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cycle_id: Number(cycleId), niveau, type_id: t.id, validee: veutRetenir }),
        }, TIMEOUT_STD)
        if (!r.ok) {
          const e = await r.json().catch(() => ({}))
          showError(e.detail || `« ${t.label} » n’a pas pu être enregistré (${r.status}).`)
          break
        }
      }
    } catch { showError('Enregistrement impossible.') }
    finally { setTypesBusy(false); await chargerTypes() }
  }

  // LE ✕ A ÉTÉ RETIRÉ (09/08/2026), avec sa fonction `supprimerType`. Il faisait doublon avec la
  // case à cocher, en pire : le serveur le refusait déjà dès qu'une activité s'appuyait sur le
  // type, si bien qu'il ne pouvait plus agir que sur un type qui n'avait pas encore servi — et là,
  // la seule chose qu'il détruisait vraiment, c'étaient les précisions saisies à la main.
  // Décocher suffit et ne perd rien : le type, ses précisions et son prompt restent en base, le
  // prof ne le voit plus, recocher le ramène intact. La route DELETE du serveur reste en place —
  // plus aucun écran ne l'appelle.

  // Détection : l'IA lit le document épuré et PROPOSE les types que CE référentiel met en œuvre.
  // Tout ce qu'elle rend est écrit NON RETENU — l'admin coche ce qu'il garde. Se lance TOUTE SEULE
  // à l'arrivée sur un couple sans types (auto-détection) ; le bouton ne sert qu'à RELANCER.
  async function detecterTypes() {
    if (!cycleId || !niveau) return
    // MÊME GARDE-FOU QUE LES MATIÈRES ET LA DÉCOUPE (08/08/2026). Ce bouton était ÉTEINT dès
    // qu'un type était retenu : muet sur la raison, et il interdisait de relire un document
    // redéposé. L'avertissement dit maintenant ce que le clic coûte, et il faut le signer.
    if (!await demanderConfirmation({
      titre: 'ATTENTION — CE CLIC EST PAYANT',
      message: "Le texte complet du référentiel va être envoyé au moteur d'IA, et cet appel est FACTURÉ.\n"
        + "Si ce référentiel n'a pas encore son prompt des types, l'IA l'écrira d'abord : DEUX appels au lieu d'un.\n"
        + "Rien n'entre au programme automatiquement — vous cocherez ensuite ce que vous gardez."
        + (nbTypesRetenus > 0
          ? `\n\n${nbTypesRetenus} type(s) sont DÉJÀ au programme de ce niveau : relire le `
            + 'document par-dessus repaie une lecture déjà faite.' : ''),
      confirmLabel: 'Lancer et payer la détection',
      payant: true,
      cancelLabel: 'Annuler',
      danger: true,
      icone: 'interdit',
    })) return
    setTypesBusy(true); setTypesDetecting(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/types-activite/detecter', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau }),
        // TIMEOUT_XLONG : au premier référentiel du cycle, cet appel écrit d'abord le prompt de
        // types du cycle (l'IA lit le document entier) puis détecte — deux appels IA à la suite.
      }, TIMEOUT_XLONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Détection impossible (${r.status}).`); return }
      await chargerTypes()
    } catch { showError('Détection impossible.') }
    finally { setTypesBusy(false); setTypesDetecting(false) }
  }

  // Précisions MANQUANTES des types RETENUS, générées un par un avec une jauge RÉELLE (fait/total).
  // Seuls les types au programme comptent : on ne dépense pas l'IA sur une proposition que l'admin
  // n'a pas gardée (le serveur refuse d'ailleurs, 422). Idempotent : un type qui a déjà ses
  // précisions n'est jamais réécrasé. Relit la base à la fin (badges à jour).
  //
  // ELLE NE PART PLUS TOUTE SEULE (15/08/2026) : c'est un bouton qui l'appelle, et elle annonce
  // AVANT de dépenser combien d'appels elle va faire. Un geste payant se demande, il ne s'attrape
  // pas en cochant une case.
  async function genererPrecisionsManquantes() {
    const rg = await fetchWithTimeout(`/api/admin/referentiels/types-activite?cycle_id=${Number(cycleId)}&niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
    const dg = await rg.json().catch(() => ({}))
    if (!rg.ok) return
    const aFaire = (dg.types || []).filter(x => x.validee && !(x.nb_precisions > 0))
    if (aFaire.length === 0) { showError('Tous les types au programme ont déjà leurs précisions.'); return }
    if (!await demanderConfirmation({
      titre: `Préparer les précisions de ${aFaire.length} type${aFaire.length > 1 ? 's' : ''} ?`,
      message: `Un appel IA facturé PAR TYPE, soit ${aFaire.length} appel${aFaire.length > 1 ? 's' : ''} à la suite. Seuls les types au programme sans précision sont traités ; ceux qui en ont déjà ne sont pas retouchés.`,
      confirmLabel: 'Lancer',
    })) return
    try {
      for (let i = 0; i < aFaire.length; i++) {
        const x = aFaire[i]
        setPrecisProgress({ fait: i, total: aFaire.length, label: x.label || '' })
        const rp = await fetchWithTimeout('/api/admin/referentiels/types-activite/precisions/generer', {
          method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cycle_id: Number(cycleId), niveau, type_id: x.id }),
        }, TIMEOUT_LONG)
        if (!rp.ok) { const e = await rp.json().catch(() => ({})); showError(e.detail || `Génération des précisions impossible (${rp.status}).`); break }
      }
    } finally { setPrecisProgress(null); await chargerTypes() }
  }

  // Ajout MANUEL d'un type À CE RÉFÉRENTIEL (create encadré : anti-doublon par libellé dans ce
  // document). Il naît RETENU, badge 'admin' : l'admin n'a pas à se proposer ce qu'il vient d'écrire.
  async function ajouterType(label) {
    const lib = (label || '').trim()
    if (!lib) return
    setTypesBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/referentiels/types-activite', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label: lib, cycle_id: Number(cycleId), niveau }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || `Ajout impossible (${r.status}).`); return }
      setTypesNouveau('')
      if (d.deja_present) showError(`« ${d.label} » est déjà dans les types de ce référentiel.`)
      await chargerTypes()
      // Pas de génération des précisions ici (15/08/2026) : écrire un type à la main est gratuit,
      // et le rester. Le bouton « Préparer les précisions » les demande quand on le décide.
    } catch { showError('Ajout impossible.') }
    finally { setTypesBusy(false) }
  }

  const dejaTraite = !!(etat && etat.existe_referentiel)
  // Deux comptages DÉRIVÉS de la liste lue (jamais stockés), comme pour les matières : combien de
  // types sont au programme, et combien attendent encore la décision de l'admin.
  const nbTypesRetenus = types.filter(t => t.validee).length
  const nbTypesProposes = types.length - nbTypesRetenus
  // La cartouche des précisions ne travaille QUE sur les types au programme : une proposition non
  // cochée n'a pas de précisions, et le serveur refuse d'en fabriquer (422). Ces deux comptages
  // sont ceux de sa pastille et de son titre.
  const typesRetenus = types.filter(t => t.validee)
  const nbTypesAvecPrecisions = typesRetenus.filter(t => (t.nb_precisions || 0) > 0).length
  const nbTypesSansPrecisions = typesRetenus.length - nbTypesAvecPrecisions

  // Cycle courant + libellé « Cycle · Niveau », lus dans l'arbre des programmes (get, zéro copie).
  const cycleCourant = arbre.find(c => String(c.id) === String(cycleId))
  const coupleLabel = cycleCourant && niveau ? `${cycleCourant.nom} · ${niveau}` : niveau

  // Deux comptages DÉRIVÉS de la liste lue (jamais stockés) : combien de matières sont au
  // programme, et reste-t-il quelque chose à retenir (une case cochée qui n'y est pas encore).
  const nbRetenues = compterRetenues(matieres)
  const aRetenir = resteARetenir(matieres)
  // Le document a-t-il déjà été lu pour ce couple ? Oui dès qu'une proposition est à l'écran.
  // C'est ce qui éteint « Proposer les matières » : on ne relit pas par-dessus une liste remplie.
  // « Supprimer tout » vide les propositions → le bouton se rallume de lui-même.
  const dejaPropose = matieres.some(m => !m.validee)

  // UNE cartouche = UNE étape, ordre FIXE. `done` = le MÊME critère que la pastille de la
  // cartouche (reflet lu en base, jamais un booléen stocké en double). Règle unique d'affichage,
  // valable pour TOUTES les cartouches : la cartouche N+1 n'apparaît que si la N est VERTE
  // (estVisible = tout ce qui précède est fait). Le tableau ne change jamais ; « Nouveau » ne fait
  // que revider l'état lu → les `done` repassent à false.
  // Le `label` sert AUSSI de libellé dans la frise du haut (même composant que les écrans prof) :
  // une seule liste d'étapes pour l'affichage des cartouches ET pour la frise, jamais deux.
  const steps = [
    { id: 'couple',        label: 'Cycle et niveau',   done: !!(cycleId && niveau) },
    // Dépôt : VERT quand le document a fini son parcours — enregistré en base, et soit plus aucun
    // document en cours dans la liste, soit celui qui y est VIENT d'être validé. C'est « Valider le
    // référentiel » qui ouvre la suite : le constat des trois tâches reste affiché pendant ce temps.
    { id: 'depot',         label: 'Document PDF',      done: dejaTraite && !apercu },
    { id: 'pdf',           label: 'Référentiel PDF',   done: dejaTraite || !!resultat },   // même critère que la pastille de la cartouche
    // L'étape n'est faite que si une matière est RETENUE : une proposition non cochée ne met
    // aucune matière au programme, donc elle ne fait pas avancer la procédure.
    { id: 'matieres',      label: 'Matières',          done: (etat?.matieres || []).some(m => m.validee) },
    // Plus d'étape « Prompt » (05/08/2026) : le prompt de découpe est celui du CYCLE, écrit par
    // l'IA à la première découpe — l'admin n'a plus rien à valider avant de découper.
    { id: 'decoupe',       label: 'Découpe',           done: !!etat?.decoupe_valide },          // lu depuis etat (get), comme matieres
    // Comme pour les matières : l'étape n'est faite que si un type est RETENU. Une proposition
    // non cochée ne met aucun type au programme, donc elle ne fait pas avancer la procédure.
    { id: 'types',         label: 'Types d’activité',  done: nbTypesRetenus > 0 },
    // Les précisions ONT LEUR ÉTAPE depuis le 15/08/2026. Elles vivaient au fond de la cartouche
    // des types, mêlées à ses boutons et à ses prompts : deux travaux dans une seule carte, et
    // celui du dessous était le plus long. La procédure en compte quatre — matières, découpe,
    // types, précisions — l'écran en montrait trois.
    { id: 'precisions',    label: 'Précisions',        done: nbTypesAvecPrecisions > 0 },
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
        {/* IMPORTER EST AU-DESSUS DE LA LISTE, jamais dedans : ce bouton CRÉE un référentiel qui
            n'existe pas encore. Le loger dans la fenêtre d'une ligne obligeait à ouvrir le
            transfert d'un AUTRE référentiel pour installer celui-ci — et sur une installation
            vierge, sans aucune ligne, il devenait inatteignable. */}
        <div style={{ padding: '10px 12px', borderBottom: '1px solid #e2e8f0' }}>
          <ImporterReferentiel onImporte={(texte) => { chargerListe(); setImportOk(texte) }} />
          {importOk && (
            <p style={{ margin: '8px 0 0', fontSize: 11.5, color: '#15803d' }}>{importOk}</p>
          )}
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
            // LA LIGNE PORTE DEUX GESTES, donc deux boutons — un bouton dans un bouton n'existe
            // pas en HTML. Le premier ouvre le référentiel, le second son transfert.
            <div key={r.id}
              style={{ display: 'flex', alignItems: 'stretch', borderBottom: '1px solid #f1f5f9',
                background: actif ? '#eff6ff' : '#fff' }}>
              <button type="button" onClick={() => ouvrirRef(r)}
                title={`${r.cycle} · ${r.nom_affichage || r.niveau}`}
                style={{ flex: 1, minWidth: 0, textAlign: 'left', padding: '9px 12px',
                  border: 'none', background: 'transparent', cursor: 'pointer', fontSize: 13,
                  color: actif ? '#1d4ed8' : '#1e293b', fontWeight: actif ? 600 : 400 }}>
                {/* Puce de synthèse : verte = procédure complète (lue en base via /liste : matières +
                    prompt de découpe validé), rouge = à terminer. Reflet, jamais recopié. */}
                <Pastille etat={r.complet ? 'vert' : 'rouge'}
                  titre={r.complet ? 'Procédure complète' : 'Procédure à terminer'} />
                {r.cycle} · {r.nom_affichage || r.niveau}
                {r.forcage_motif && <span title="Validé en forçage" style={{ marginLeft: 6, color: '#b45309' }}>⚠</span>}
              </button>
              {/* LE TRANSFERT S'OUVRE À PART, dans sa propre fenêtre. Il déplace un référentiel
                  entier d'une installation à l'autre : le tenir à l'écart du reste de l'écran,
                  c'est s'assurer qu'on ne le déclenche pas en visant autre chose. */}
              <button type="button" onClick={() => setTransfertPour(r)}
                title={`Transférer « ${r.cycle} · ${r.nom_affichage || r.niveau} » vers une autre installation`}
                style={{ border: 'none', background: 'transparent', cursor: 'pointer',
                  padding: '0 10px', color: '#64748b', display: 'flex', alignItems: 'center' }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="8 3 8 9 5 9 9.5 14 14 9 11 9 11 3" />
                  <polyline points="16 21 16 15 19 15 14.5 10 10 15 13 15 13 21" />
                </svg>
              </button>
            </div>
          )
        })}
      </aside>

      {/* Colonne 3 — l'écran de travail du référentiel. Prend toute la largeur disponible (plus de plafond). */}
      <div className="flex flex-col gap-6" style={{ flex: 1, minWidth: 0 }}>
      {/* Bandeau de tête COLLANT (08/08/2026). L'écran est long — six cartouches, des fenêtres de
          prompt, des listes d'unités — et on y descend loin du haut. La frise disait où on en est
          et le couple disait sur QUOI on travaille : les deux disparaissaient dès le premier
          défilement, au moment précis où l'on clique des boutons payants qui, eux, agissent sur
          le couple qu'on ne voit plus. Ils restent donc à l'écran.
          `top: -32` compense le padding du conteneur de défilement (AdminLayout) : le bloc glisse
          de ses 32 px de marge haute et se cale au ras, sans trou ni saut. */}
      <div style={{ position: 'sticky', top: -32, zIndex: 30, background: '#f0f4f8',
                    paddingTop: 32, paddingBottom: 10, borderBottom: '1px solid #e2e8f0' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
          <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>Référentiels</h2>
          {/* Le couple EN COURS, dans le bandeau : la question « je travaille sur quoi, là ? » se
              pose à chaque clic, pas seulement en haut de page. */}
          {cycleId && niveau && (
            <span style={{ fontSize: 13, fontWeight: 700, color: '#A63045' }}
              title="Le couple sur lequel porte tout ce qui est affiché en dessous">
              {cycleCourant?.nom || ''} · {niveau}
            </span>
          )}
          {/* Les deux façons de monter un référentiel, à demeure en haut de l'écran : par l'IA,
              ou par vos soins. Le texte vit dans le catalogue d'aide, jamais ici. */}
          <button type="button" className="btn-secondary" onClick={() => setProceduresOuvert(true)}
            style={{ marginLeft: 'auto', fontSize: 12, padding: '4px 10px' }}
            title="Les deux façons de monter un référentiel : en laissant l'application appeler l'IA, ou en exécutant les prompts vous-même.">
            ❔ Comment ça marche ?
          </button>
        </div>
        {/* Frise de progression — MÊME composant que les écrans prof (components/FriseProgression.jsx).
            Les étapes viennent de `steps` : un seul endroit décide de l'avancement (reflet base). */}
        <div style={{ marginTop: 10 }}>
          <FriseProgression etapes={steps.map(s => ({ label: s.label, fait: s.done }))} />
        </div>
      </div>

      {/* Carte 0 — Couple : le choix du couple vient EN PREMIER. Toujours affichée (c'est le
          point de départ de l'écran) ; la cascade cycle → niveau ouvre les étapes suivantes. */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">

        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
          <div>
            <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
              <Pastille etat={(cycleId && niveau) ? 'vert' : 'rouge'} titre="Vert = un couple est choisi." />
              Cycle et niveau
              <InfoGuide {...aideReferentiels('couple')} />
              {/* La place vide après le « i » porte l'essentiel de la cartouche : ici le couple
                  choisi, lu dans l'arbre des programmes. Rien tant qu'il n'est pas complet. */}
              {cycleId && niveau && (
                <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 8, fontSize: 13 }}
                  title="Le couple choisi : c'est lui qui décide où le document est rangé">
                  {cycleCourant?.nom || ''} · {niveau}
                </span>
              )}
            </h2>
          </div>
          <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
            title={coupleOuvert ? 'Réduire' : 'Développer'} onClick={() => setCoupleOuvert(o => !o)}>
            {coupleOuvert ? 'Réduire' : 'Développer'}
          </button>
        </div>

        {coupleOuvert && (<>
        {/* Cascade cycle → niveau sur l'arbre COMPLET des programmes (tous les niveaux existants).
            Le dépôt ne propose QUE l'existant : créer un niveau = écran Formations (« + Niveau »). */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 180 }}>
            <label className="block text-xs text-gray-500 mb-1">Cycle</label>
            <select style={{ ...champ, background: '#fff' }} value={cycleId}
              onChange={e => { setCycleId(e.target.value); setNiveauId(''); setNiveau(''); viderCeQuiDependDuCouple() }}
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
                if (n) preparerCouple()
                else viderCeQuiDependDuCouple()   // retour sur « — Choisissez un niveau — »
              }}
              title={cycleId ? 'Choisissez le niveau du cycle' : 'Choisissez d’abord le cycle'}>
              <option value="">{cycleId ? '— Choisissez un niveau —' : '—'}</option>
              {(arbre.find(c => String(c.id) === String(cycleId))?.niveaux || []).map(n => (
                <option key={n.id} value={n.id}>{n.nom}</option>
              ))}
            </select>
            {cycleId && (arbre.find(c => String(c.id) === String(cycleId))?.niveaux || []).length === 0 && (
              <p style={{ fontSize: 12, color: '#b45309', marginTop: 4 }}>
                Ce cycle n’a encore aucun niveau — créez-le d’abord dans l’écran Formations (bouton « + Niveau »).
              </p>
            )}
          </div>
        </div>
        </>)}

      </div>

      {/* Carte 1 — Document PDF : le dépôt du référentiel officiel pour le couple choisi
          au-dessus (dépôt / lien → zone d'attente). Règle N-1 comme les autres cartouches :
          CACHÉE tant que l'étape Couple est rouge (estVisible). Masquée aussi quand le couple
          a déjà son référentiel (la mise à jour reste dans « Référentiel au format PDF »). */}
      {estVisible('depot') && (!dejaTraite || !!apercu) && (
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
        <div>
          <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
            <Pastille etat={apercu ? 'jaune' : dejaTraite ? 'vert' : 'rouge'}
              titre="Rouge = aucun document · Jaune = un document en cours, pas encore validé · Vert = référentiel validé." />
            Document PDF
            <InfoGuide {...aideReferentiels('document_pdf')} />
          </h2>
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
        {/* Règle générale : sablier DANS le bouton + jauge d'attente JUSTE EN DESSOUS pendant
            toute lecture / appel long (même composant que les écrans prof). */}
        {busy && (
          <JaugeAttente libelle={depotPhase === 'controle'
            ? <>Contrôle du couple : recherche du <strong>cycle</strong> et du <strong>niveau</strong> dans le document…
                <br /><small>Toutes les pages sont lues : comptez jusqu’à une minute sur un long document.</small></>
            : (mode === 'lien'
              ? 'Téléchargement du PDF depuis le lien…'
              : 'Lecture du document PDF (nombre de pages et aperçu)…')} />
        )}
        {/* Liste des documents déposés — apparaît dès qu'un fichier est en zone d'attente. */}
        {apercu && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
              {/* Bandeau : combien de documents, et le total à lire */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
                background: '#f8fafc', borderBottom: '1px solid #e2e8f0', padding: '8px 12px' }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: 0.3 }}>
                  1 document(s) déposé(s)
                </span>
                <span style={{ fontSize: 12, color: '#64748b' }}>
                  {apercu.pages} page(s) à lire · {apercu.taille_ko} Ko
                </span>
              </div>
              {/* La ligne du document */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px' }}>
                <span style={{ width: 22, height: 22, flexShrink: 0, borderRadius: 4, background: '#f1f5f9',
                  color: '#64748b', fontSize: 12, fontWeight: 700, display: 'inline-flex',
                  alignItems: 'center', justifyContent: 'center' }}>1</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', overflow: 'hidden',
                    textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{apercu.filename}</div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>
                    {apercu.pages} page(s) · {apercu.taille_ko} Ko · {source === 'dépôt manuel' ? 'par dépôt' : 'par lien'}
                  </div>
                  {/* Résultat du contrôle n°1 : ce que le document nomme vraiment (recherche de
                      texte, sans IA). Le document ne serait pas dans la liste sans au moins un des deux. */}
                  {controle && controle.niveau_trouve && (
                    <div style={{ fontSize: 12, color: '#166534', marginTop: 2 }}>
                      ✓ contient bien le niveau « {controle.niveau} »
                    </div>
                  )}
                </div>
                {/* Ordre : un seul document déposé → les deux flèches sont sans objet (grisées). */}
                <button type="button" disabled title="Monter ce document dans la liste"
                  style={{ ...btnOrdre, opacity: 0.45, cursor: 'not-allowed' }}>▲</button>
                <button type="button" disabled title="Descendre ce document dans la liste"
                  style={{ ...btnOrdre, opacity: 0.45, cursor: 'not-allowed' }}>▼</button>
                <button type="button" onClick={() => setVoirDepot(true)}
                  title="Ouvrir le document déposé"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
                    fontSize: 12, fontWeight: 600, padding: '6px 12px', borderRadius: 6, cursor: 'pointer',
                    background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe' }}>
                  👁 Voir
                </button>
                <button type="button" onClick={() => { setApercu(null); setVoirDepot(false); setNomFichier(''); setControle(null); setTaches([]); setTachesFaites([]) }}
                  title="Retirer ce document de la liste"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
                    fontSize: 12, fontWeight: 600, padding: '6px 12px', borderRadius: 6, cursor: 'pointer',
                    background: '#fee2e2', color: '#dc2626', border: '1px solid #fecaca' }}>
                  ⛔ Retirer
                </button>
              </div>
            </div>
            {/* UNE SEULE ligne : les tâches à gauche, le « i » et le bouton à droite. UN SEUL geste,
                VALIDER : tout le travail du document (rangement, lecture, écriture en base), sans
                aucune IA — les matières sont la cartouche d'après. */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 16, flexWrap: 'wrap' }}>
              {/* Les tâches, cochées UNE À UNE pendant que le serveur travaille : ✓ verte pour la
                  tâche finie, sablier pour celle en cours, puce grise pour celles qui attendent.
                  La liste vient du serveur (flux) — elle n'est écrite nulle part ici. */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap', fontSize: 12.5 }}>
                {taches.map((t, i) => {
                  const faite = tachesFaites.includes(t.id)
                  const enCours = !faite && tachesFaites.length === i && !!actionBusy
                  return (
                    <span key={t.id} style={{ display: 'inline-flex', alignItems: 'center', gap: 6,
                      whiteSpace: 'nowrap',
                      color: faite ? '#166534' : enCours ? '#1e293b' : '#94a3b8',
                      fontWeight: faite || enCours ? 600 : 400 }}>
                      <span aria-hidden="true">{faite ? '✓' : enCours ? '⏳' : '○'}</span>
                      {t.libelle}
                    </span>
                  )
                })}
              </div>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
              {/* Le « i » de la maison (InfoGuide, comme chez les profs) : bulle courte au SURVOL,
                  fiche complète épinglée au CLIC, qui se referme par ✕, clic dehors ou Échap. Ses
                  textes viennent du catalogue utils/aideReferentiels.js — jamais réécrits ici. */}
              <InfoGuide {...aideReferentiels('valider_document')} />
              {/* Validation réussie = la cartouche entière disparaît (le document n'est plus en
                  attente) : ce bouton n'a donc pas d'« après » à afficher. */}
              <button type="button" onClick={validerLeReferentiel} disabled={!!actionBusy}
                title="Range le document dans le dossier du référentiel, lit et fige son texte nettoyé, puis écrit sa fiche en base. Aucune IA n'est appelée."
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
                  fontSize: 13, fontWeight: 700, padding: '9px 16px', borderRadius: 6,
                  cursor: actionBusy ? 'wait' : 'pointer', opacity: actionBusy ? 0.6 : 1,
                  background: 'var(--bleu)', color: '#fff', border: '1px solid var(--bleu)' }}>
                {actionBusy === 'verifier' ? <><Spinner /> Validation en cours…</> : <>✓ Valider le référentiel</>}
              </button>
              </div>
            </div>
            {/* Sablier + jauge pendant l'attente — celle de CE bouton seulement. Le libellé suit la
                tâche en cours (celle que le flux n'a pas encore déclarée faite). */}
            {actionBusy === 'verifier' && (
              <JaugeAttente libelle={`${(taches[tachesFaites.length] || {}).libelle || 'Validation du référentiel'}…`} />
            )}
          </div>
        )}
      </div>
      )}

      {/* Carte 2 — Référentiel au format PDF : règle générale, elle n'apparaît que si la cartouche
          précédente (« Document PDF ») est VERTE, c'est-à-dire un document en zone d'attente ou un
          référentiel déjà enregistré. */}
      {estVisible('pdf') && (
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">

        {/* L'essentiel de la cartouche vit sur la LIGNE DU TITRE : l'état du document, sa relecture
            et sa suppression. Il reste donc visible même quand la cartouche est réduite — c'est
            tout l'intérêt de la réduire. « Réduire » seul à droite, comme partout. */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', minWidth: 0 }}>
            <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
              <Pastille etat={(dejaTraite || resultat) ? 'vert' : 'rouge'} titre="Vert = une ligne référentiel existe en base pour ce couple." />
              Référentiel au format PDF
              <InfoGuide {...aideReferentiels('referentiel_pdf')} />
            </h2>
            {dejaTraite && (<>
              <span style={{ fontSize: 12, color: '#166534' }}>
                Déjà téléchargé, déjà traité.{' '}
                <button type="button" onClick={() => setShowPdf(true)}
                  title="Ouvrir le PDF du référentiel pour le relire"
                  style={{ background: 'none', border: 'none', padding: 0, color: '#1d4ed8',
                    fontSize: 12, fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}>
                  Voir le référentiel
                </button>
              </span>
              {/* DELETE encadré : le mot suffit — la bulle d'aide dit ce qui est effacé et quand
                  c'est refusé. Rouge + sens interdit ; ouvre une modale de confirmation (jamais de
                  suppression au clic). */}
              <button type="button" onClick={() => setShowSuppr(true)} disabled={supprBusy}
                title="Supprimer définitivement ce référentiel (efface la fiche + le PDF). Refusé s'il a déjà servi."
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
                  fontSize: 12, fontWeight: 700, padding: '4px 10px', borderRadius: 6,
                  cursor: supprBusy ? 'wait' : 'pointer',
                  background: '#fee2e2', color: '#dc2626', border: '1px solid #fecaca' }}>
                ⛔ Supprimer
              </button>
            </>)}
          </div>
          <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap', flexShrink: 0 }}
            title={pdfOuvert ? 'Réduire' : 'Développer'} onClick={() => setPdfOuvert(o => !o)}>
            {pdfOuvert ? 'Réduire' : 'Développer'}
          </button>
        </div>

        {pdfOuvert && (<>
        {/* ── Zone 1 : le PDF ORIGINAL — la pièce téléchargée, conservée telle quelle, relue par l'admin. ── */}
        {dejaTraite && (
        <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b' }}>
          Fichier PDF original
          <InfoGuide {...aideReferentiels('pdf_original')} />
        </div>
        )}
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
            {/* PREUVE du contrôle n°1 — le document nomme bien le niveau. Lue EN BASE
                (referentiels.controle_niveau via /etat), figée au dépôt : elle survit au
                rechargement de la page, contrairement à l'affichage du moment du dépôt.
                Absente (dépôt antérieur à la colonne) = rien affiché. */}
            {etat.referentiel?.controle_niveau && (() => {
              let c
              try { c = JSON.parse(etat.referentiel.controle_niveau) } catch { c = null }
              if (!c || !c.trouve) return null
              return (
                <p style={{ fontSize: 12, color: '#166534', marginTop: 4 }}
                   title="Contrôle fait à la remise du document, sans IA : les mots du niveau ont été cherchés dans son texte.">
                  ✓ contient bien le niveau « {c.niveau} »
                </p>
              )
            })()}
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
              let v
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
        ) : !apercu ? (
          <p style={{ fontSize: 13, color: '#64748b', margin: 0 }}>
            Déposez d’abord le document dans la cartouche « Document PDF » au-dessus — sa vérification et sa validation s’afficheront ici.
          </p>
        ) : null}

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
          {/* Le titre garde sa ligne, « Réduire » reste en haut à droite comme dans toutes les
              cartouches. Les gestes de la cartouche descendent sur la ligne d'en dessous. */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
              <Pastille etat={nbRetenues > 0 ? 'vert' : 'rouge'} titre="Vert = au moins une matière est retenue au programme de ce niveau." />
              Matières de ce référentiel
              <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 6, fontSize: 13 }}>
                ({nbRetenues} retenue{nbRetenues > 1 ? 's' : ''}
                {matieres.length - nbRetenues > 0 ? `, ${matieres.length - nbRetenues} proposée${matieres.length - nbRetenues > 1 ? 's' : ''}` : ''})
              </span>
              <span style={{ marginLeft: 8 }}>
                <BadgeIA titre="Matières proposées par la lecture du document — ce référentiel nomme les siennes" />
              </span>
              <InfoGuide {...aideReferentiels('matieres', { niveau })} />
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
              {/* Le prompt SERT dès qu'il existe : ce voyant dit seulement s'il a été relu. Il
                  parle du prompt qui LIT le document, pas des matières de la liste. */}
              <span title="État du prompt qui LIT le document pour y relever les matières (bouton « Voir le prompt des matières » ci-dessous)."
                style={{ fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap',
                color: promptMatieresValide ? '#166534' : promptMatieres.trim() ? '#b45309' : '#A63045' }}>
                {promptMatieresValide ? '● prompt des matières : relu et validé'
                  : promptMatieres.trim() ? '● prompt des matières : écrit par l’IA, à relire'
                  : '● prompt des matières : pas encore écrit'}
              </span>
              <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap', flexShrink: 0 }}
                title={matieresOuvert ? 'Réduire la liste des matières' : 'Développer la liste des matières'}
                onClick={() => setMatieresOuvert(o => !o)}>
                {matieresOuvert ? 'Réduire' : 'Développer'}
              </button>
            </div>
          </div>

          {/* Deux camps sur la MÊME ligne, et l'oeil sait tout de suite lequel il regarde :
              à GAUCHE ce qui se LIT (les prompts, gratuits) ; à DROITE ce qui AGIT sur la liste,
              le geste payant tout au bout. Un bouton qui coûte ne se met pas en tête de ligne,
              là où la main clique sans réfléchir. */}
          {matieresOuvert && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginTop: -6 }}>
            {/* Le MÉTA-prompt : la recette qui sert à écrire le prompt de lecture. On le voit d'ici
                pour comprendre d'où sort le prompt des matières — on ne le modifie pas non plus. */}
            <button type="button" className="btn-secondary"
              style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title="Voir le méta-prompt : la consigne qui sert à l'IA pour RÉDIGER le prompt de lecture des matières (lecture seule)"
              onClick={ouvrirMetaPrompt}>
              <span aria-hidden="true" style={{ fontSize: 15, lineHeight: 1, marginRight: 2 }}>👁</span> Voir le méta-prompt
            </button>
            {/* Chaque « i » reste COLLÉ à son bouton et prend ses distances avec le suivant —
                sinon on ne sait plus lequel des deux il commente. */}
            <span style={{ marginRight: 14, display: 'inline-flex', alignItems: 'center' }}>
              <InfoGuide {...aideReferentiels('meta_prompt_matieres')} />
            </span>
            {/* Le prompt qui lit les matières : on le VOIT d'ici, on ne le modifie pas. Il est rangé
                sur le CYCLE et sert à tous ses référentiels — le corriger depuis un couple
                laisserait croire à un réglage local. Un seul endroit pour l'écrire : l'écran
                Prompts → Matières par cycle. */}
            <button type="button" className="btn-secondary"
              style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title="Voir et corriger le prompt qui lit les matières de CE référentiel (gratuit, aucune IA)"
              onClick={() => setPromptMatieresOuvert(true)}>
              <span aria-hidden="true" style={{ fontSize: 15, lineHeight: 1, marginRight: 2 }}>👁</span> Voir le prompt des matières
            </button>
            <InfoGuide {...aideReferentiels('prompt_matieres')} />

            {/* ── Bloc de DROITE. Un seul `marginLeft: auto`, porté par le groupe : les boutons
                qu'il contient apparaissent et disparaissent, l'alignement, lui, ne bouge pas. ── */}
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              {matieresOuvert && matieres.some(m => !m.validee && !m.cochee) && (
                <button type="button" className="btn-secondary"
                  style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
                  title="Cocher d'un coup toutes les propositions — « Récupérer » s'active ensuite"
                  onClick={selectionnerTout}>
                  Sélectionner tout
                </button>
              )}
              {/* « Supprimer tout » ne vide que les PROPOSITIONS — d'où son absence quand il n'y en a aucune. */}
              {matieresOuvert && matieres.some(m => !m.validee && m.id) && (
                <button type="button" onClick={ecarterTout} disabled={!!actionBusy}
                  title="Supprimer d'un coup toutes les propositions (les matières retenues ne bougent pas) — pour relire le document sur une liste vide"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6,
                    whiteSpace: 'nowrap', fontSize: 12, fontWeight: 600, padding: '4px 10px', borderRadius: 6,
                    cursor: actionBusy ? 'wait' : 'pointer', opacity: actionBusy ? 0.6 : 1,
                    background: '#fee2e2', color: '#dc2626', border: '1px solid #fecaca' }}>
                  {actionBusy === 'ecarter-tout' ? <><Spinner /> Suppression…</> : <>⛔ Supprimer tout</>}
                </button>
              )}
              {/* Le geste payant, au bout de la ligne. PLUS JAMAIS ÉTEINT (08/08/2026) : un bouton
                  gris ne dit pas pourquoi et il enferme — relire volontairement un document
                  redéposé devenait impossible. C'est le dialogue de confirmation qui porte
                  l'avertissement, et il dit combien ça coûte. */}
              <button type="button" onClick={proposerMatieres} disabled={!!actionBusy}
                title={dejaPropose
                  ? 'Le document a déjà été lu : ses propositions sont dans la liste. Relire par-dessus repaie une lecture déjà faite — le clic demande confirmation.'
                  : "Appel IA facturé — le texte du référentiel est envoyé au moteur. L'IA propose des matières, sans en retenir aucune : vous cochez ce que vous gardez."}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
                  fontSize: 12, fontWeight: 600, padding: '4px 10px', borderRadius: 6,
                  cursor: actionBusy ? 'wait' : 'pointer',
                  opacity: actionBusy ? 0.5 : 1,
                  background: '#7c3aed', color: '#fff', border: '1px solid #7c3aed' }}>
                {actionBusy === 'valider' ? <><Spinner /> Lecture…</> : <>✨ Proposer les matières <PastilleEuro /></>}
              </button>
              <InfoGuide {...aideReferentiels('proposer_matieres')} />
            </div>
          </div>
          )}

          {/* Règle générale : sablier DANS le bouton + jauge d'attente juste en dessous à chaque
              appel IA. */}
          {actionBusy === 'valider' && (
            <JaugeAttente libelle="L’IA lit le référentiel et propose les matières…" />
          )}

          {matieresOuvert && (
          <>
          <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
            {matieres.map((m, i) => (
              <div key={m.id ?? `neuve-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px',
                borderTop: i ? '1px solid #f1f5f9' : 'none', background: m.validee ? '#f8fafc' : '#fff' }}>
                <input type="checkbox" checked={m.cochee} disabled={m.validee}
                  title={m.validee ? 'Déjà au programme — pour l’en sortir, utilisez « Retirer »' : 'Cocher pour retenir cette matière'}
                  onChange={() => toggleCochee(i)} />
                {editIndex === i ? (
                  <input style={{ ...champ, flex: 1 }} value={editNom} autoFocus
                    onChange={e => setEditNom(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') validerRenommage(); if (e.key === 'Escape') { setEditIndex(-1); setEditNom('') } }}
                    onBlur={validerRenommage} title="Nouveau libellé de la matière" />
                ) : (
                  <span style={{ flex: 1, fontSize: 13, color: '#1e293b' }}>{m.nom}</span>
                )}
                <span style={{ fontSize: 11, fontWeight: 600, color: m.validee ? '#16a34a' : '#7c3aed' }}
                  title={m.validee
                    ? 'Au programme : les profs de ce niveau la voient.'
                    : 'Lue dans le document, en attente de votre décision.'}>
                  {m.validee ? 'retenue' : 'proposée'}
                </span>
                <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px' }}
                  title="Renommer cette matière (garde le même identifiant)" onClick={() => demarrerRenommage(i)}>
                  Renommer
                </button>
                <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px' }}
                  title={m.validee ? 'Sortir cette matière du programme de ce niveau' : 'Supprimer cette proposition'}
                  onClick={() => retirer(i)}>
                  {m.validee ? 'Retirer' : 'Supprimer'}
                </button>
              </div>
            ))}
            {matieres.length === 0 && (
              <div style={{ padding: '10px', fontSize: 12, color: '#64748b', lineHeight: 1.6 }}>
                {/* Les TROIS voies sont dites ici, à égalité — c'est le seul endroit où l'admin
                    décide s'il dépense. La voie payante est écrite en rouge : le prix se lit
                    AVANT le clic, jamais sur la facture. */}
                Ce référentiel ne porte encore aucune matière.
                <div style={{ marginTop: 8 }}>Trois façons de les obtenir :</div>
                <ul style={{ margin: '4px 0 0', paddingLeft: 18 }}>
                  <li><strong>« Proposer les matières »</strong> : <span style={{ color: '#dc2626' }}>
                    l’IA lit le document et propose la liste — cet appel est payant</span>.</li>
                  <li><strong>Sans rien payer</strong> <InfoGuide {...aideReferentiels('matieres_sans_payer')} />
                    {' '}: récupérez le document épuré, faites écrire le prompt par Fable puis
                    exécuter par Sonnet (abonnement Max, aucun coût pour aSchool), et saisissez
                    le résultat ci-dessous.</li>
                  <li><strong>À la main</strong> : saisissez-les une par une dans le champ ci-dessous.</li>
                </ul>
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
            {/* Grisé quand il n'y a rien à retenir : aucune matière cochée qui ne soit PAS déjà au
                programme. État lu (get), zéro copie. Se réactive dès qu'on coche une proposition. */}
            <button type="button" className="btn-primary" title="Retenir les matières cochées : elles entrent au programme de ce niveau"
              onClick={recuperer} disabled={busy || !aRetenir}>{busy ? 'Enregistrement…' : 'Récupérer'}</button>
            {/* Plus de bouton « Générer le prompt » ici (05/08/2026) : le prompt de découpe est
                rangé sur le CYCLE et l'IA l'écrit toute seule à la première découpe du cycle. */}
            {bilanApercu && <span style={{ fontSize: 12, color: '#475569' }}>{bilanApercu}</span>}
          </div>
          </>
          )}
        </div>
      )}

      {/* Le PROMPT DE DÉCOUPE ne se règle plus ici (05/08/2026). Il est rangé sur le CYCLE
          (cycles.prompt_decoupe) et découpe TOUS ses référentiels : le corriger depuis un couple
          laisserait croire à un réglage local, et deux éditeurs sur la même colonne finissent par
          s'écraser. L'IA l'écrit à la première découpe du cycle ; il se relit et se corrige dans
          Prompts → Découpe par cycle. Ce qu'il en reste ici : un bouton pour le VOIR, dans la
          cartouche Découpe juste en dessous. */}


      {/* Découpe — ÉTAPE À PART (le prompt et la découpe ne sont pas le même travail). Apparaît une fois
          le prompt validé. On découpe (aperçu, lecture seule), on contrôle les unités, puis on valide le
          découpage : dernière étape → la puce du menu passe au vert (decoupe_valide en base). */}
      {estVisible('decoupe') && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          {/* Le titre garde sa ligne, « Réduire » reste en haut à droite. L'état du prompt monte
              ici, juste avant lui : il dit si la cartouche est prête, on doit le lire sans avoir
              à la développer. Les gestes, eux, descendent sur la ligne d'en dessous. */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
              <Pastille etat={decoupeValide ? 'vert' : 'rouge'} titre="Vert = découpage validé (referentiels.decoupe_valide)." />
              Découpe (chunk)
              <span style={{ marginLeft: 8 }}>
                <BadgeIA titre="Document découpé en unités par l'IA (avec le prompt validé)" />
              </span>
              <InfoGuide {...aideReferentiels('decoupe')} />
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
              {/* Le prompt SERT dès qu'il existe : ce voyant dit seulement s'il a été relu. */}
              <span title="État du prompt qui DÉCOUPE le document (bouton « Prompt de découpe » ci-dessous)."
                style={{ fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap',
                color: promptValide ? '#166534' : promptDecoupe.trim() ? '#b45309' : '#A63045' }}>
                {promptValide ? '● prompt de découpe : relu et validé'
                  : promptDecoupe.trim() ? '● prompt de découpe : écrit par l’IA, à relire'
                  : '● prompt de découpe : pas encore écrit'}
              </span>
              <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
                title={decoupeOuvert ? 'Réduire' : 'Développer'} onClick={() => setDecoupeOuvert(o => !o)}>
                {decoupeOuvert ? 'Réduire' : 'Développer'}
              </button>
            </div>
          </div>
          {decoupeOuvert && (<>
          <div>
            {/* Deux camps sur la MÊME ligne, comme dans la cartouche des matières : à GAUCHE ce qui
                se LIT (les prompts, gratuits) ; à DROITE ce qui AGIT, le geste payant tout au bout.
                Un bouton qui coûte ne se met pas en tête de ligne, là où la main clique sans
                réfléchir. */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              {/* Le MÉTA-prompt : la recette qui sert à écrire le prompt de découpe. On le voit
                  d'ici pour comprendre d'où sort ce prompt — on ne le modifie pas non plus. */}
              <button type="button" className="btn-secondary"
                style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
                title="Voir le méta-prompt : la consigne qui sert à l'IA pour RÉDIGER le prompt de découpe (lecture seule)"
                onClick={ouvrirMetaDecoupe}>
                <span aria-hidden="true" style={{ fontSize: 15, lineHeight: 1, marginRight: 2 }}>👁</span> Méta-prompt
              </button>
              {/* Chaque « i » reste COLLÉ à son bouton et prend ses distances avec le suivant —
                  sinon on ne sait plus lequel des deux il commente. */}
              <span style={{ marginRight: 14, display: 'inline-flex', alignItems: 'center' }}>
                <InfoGuide {...aideReferentiels('meta_prompt_decoupe')} />
              </span>
              {/* Le prompt qui découpe : rangé sur CE référentiel — on le lit et on le corrige ici. */}
              <button type="button" className="btn-secondary"
                style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
                title="Voir et corriger le prompt qui découpe CE référentiel (gratuit, aucune IA)"
                onClick={() => setPromptOuvert(true)}>
                <span aria-hidden="true" style={{ fontSize: 15, lineHeight: 1, marginRight: 2 }}>👁</span> Prompt de découpe
              </button>
              <InfoGuide {...aideReferentiels('prompt_decoupe')} />

              {/* ── Bloc de DROITE : le geste payant, seul, au bout de la ligne. ── */}
              <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <button type="button" onClick={declencherDecoupe}
                  disabled={!!promptBusy}
                  style={btnTypes('#7c3aed', !!promptBusy)}
                  title={decoupeValide
                    ? "Le découpage de ce référentiel est déjà validé : ses unités sont en base. Relancer repaie un travail déjà fait — le clic demande confirmation avant tout appel."
                    : "Appel IA facturé — le texte du référentiel est envoyé au moteur, qui le découpe en unités (aperçu, aucune écriture). Sans prompt de découpe, l'IA l'écrit d'abord : deux appels pour un clic. Le clic demande confirmation."}>
                  {promptBusy === 'decouper' ? <><Spinner /> Découpe…</> : <><span aria-hidden="true">✨</span> Découper <PastilleEuro /></>}
                </button>
                <InfoGuide {...aideReferentiels('declencher_decoupe')} />
              </div>
            </div>
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
              <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 8,
                justifyContent: 'flex-end' }}>
                <button type="button" className="btn-primary" onClick={validerDecoupe}
                  disabled={!!promptBusy}
                  title={decoupeValide
                    ? "Ce découpage est déjà validé. Recliquer le refait : les unités en base sont sauvegardées puis remplacées — le clic demande confirmation."
                    : "Enregistrer ce découpage en base — aucun appel à l'IA. L'étape Types d'activité s'ouvre ensuite (dernière étape)."}>
                  {promptBusy === 'valider-decoupe' ? <><Spinner /> Validation…</>
                    : decoupeValide ? '✓ Découpage validé' : 'Valider le découpage'}
                </button>
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
                  : 'Lecture de la découpe enregistrée…'   // aucune IA ici : on relit l’aperçu
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

      {/* Carte 6 — Types d'activité DU RÉFÉRENTIEL. Elle a cessé d'être la dernière le 15/08/2026 :
          les précisions, qu'elle hébergeait au fond d'elle-même, ont pris la carte suivante. Visible seulement
          une fois le découpage (N-1) validé (estVisible, comme les autres cartouches). MÊME GESTE QUE
          LES MATIÈRES : la détection propose (case décochée), l'admin coche ce qui entre au programme
          — écriture directe en base au clic (put). Le badge dit l'ORIGINE du type (IA / ADMIN),
          jamais qui l'a retenu : ça, c'est la case. */}
      {estVisible('types') && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
              <Pastille etat={nbTypesRetenus > 0 ? 'vert' : 'rouge'} titre="Vert = au moins un type d'activité est au programme de ce niveau." />
              Types d'activité de ce référentiel
              <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 6, fontSize: 13 }}>
                ({nbTypesRetenus} au programme{nbTypesProposes > 0 ? `, ${nbTypesProposes} proposé${nbTypesProposes > 1 ? 's' : ''}` : ''})
              </span>
              <span style={{ marginLeft: 8 }}>
                <BadgeIA titre="Types lus dans le document par l'IA — elle propose, vous cochez ce qui entre au programme" />
              </span>
              <InfoGuide {...aideReferentiels('types_activite')} />
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
              {/* Le prompt SERT dès qu'il existe : ce voyant dit seulement s'il a été relu. */}
              <span title="État du prompt qui LIT le document pour y relever les types (bouton « Prompt des types » ci-dessous). À ne pas confondre avec le « ✓ prompt » de chaque ligne, qui est le prompt de CE type d'activité."
                style={{ fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap',
                color: promptTypesValide ? '#166534' : promptTypes.trim() ? '#b45309' : '#A63045' }}>
                {promptTypesValide ? '● prompt des types : relu et validé'
                  : promptTypes.trim() ? '● prompt des types : écrit par l’IA, à relire'
                  : '● prompt des types : pas encore écrit'}
              </span>
              <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
                title={typesOuvert ? 'Réduire' : 'Développer'} onClick={() => setTypesOuvert(o => !o)}>
                {typesOuvert ? 'Réduire' : 'Développer'}
              </button>
            </div>
          </div>

          {typesOuvert && (<>
          {/* Deux camps sur la MÊME ligne, comme dans les cartouches Matières et Découpe : à GAUCHE
              ce qui se LIT (les prompts, gratuits) ; à DROITE ce qui AGIT, le geste payant tout au
              bout. Un bouton qui coûte ne se met pas en tête de ligne, là où la main clique sans
              réfléchir. Le titre ne se répète pas ici : il est déjà sur la ligne du dessus, avec
              ses comptages. */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {/* Le MÉTA-prompt : la recette qui sert à écrire le prompt des types. On le voit d'ici
                pour comprendre d'où sort ce prompt — on ne le modifie pas non plus. */}
            <button type="button" className="btn-secondary"
              style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title="Voir le méta-prompt : la consigne qui sert à l'IA pour RÉDIGER le prompt de lecture des types (lecture seule)"
              onClick={ouvrirMetaTypes}>
              <span aria-hidden="true" style={{ fontSize: 15, lineHeight: 1, marginRight: 2 }}>👁</span> Méta-prompt
            </button>
            {/* Chaque « i » reste COLLÉ à son bouton et prend ses distances avec le suivant —
                sinon on ne sait plus lequel des deux il commente. */}
            <span style={{ marginRight: 14, display: 'inline-flex', alignItems: 'center' }}>
              <InfoGuide {...aideReferentiels('meta_prompt_types')} />
            </span>
            {/* Le prompt qui lit les types : rangé sur CE référentiel — on le lit et on le corrige ici. */}
            <button type="button" className="btn-secondary"
              style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title="Voir et corriger le prompt qui lit les types d'activité de CE référentiel (gratuit, aucune IA)"
              onClick={() => setPromptTypesOuvert(true)}>
              <span aria-hidden="true" style={{ fontSize: 15, lineHeight: 1, marginRight: 2 }}>👁</span> Prompt des types
            </button>
            <InfoGuide {...aideReferentiels('prompt_types')} />

            {/* ── Bloc de DROITE : ce qui AGIT, le geste payant tout au bout. Les deux prompts des
                PRÉCISIONS ont quitté cette ligne le 15/08/2026 : ils appartiennent à la cartouche
                qui porte leur travail, pas à celle d'à côté. ── */}
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <button type="button" onClick={detecterTypes} disabled={typesBusy}
                style={btnTypes('#7c3aed', typesBusy)}
                title={nbTypesRetenus > 0
                  ? "Des types sont déjà au programme de ce niveau : relire le document repaie un travail déjà fait — le clic demande confirmation avant tout appel."
                  : types.length === 0
                  ? "Appel IA facturé — le document est envoyé au moteur, qui relève les types d'activité qu'il met en œuvre. L'IA propose : rien n'entre au programme sans votre coche. Si ce référentiel n'a pas encore son prompt des types, l'IA l'écrit d'abord : deux appels pour un clic."
                  : "Appel IA facturé — relance la lecture du document (utile après un nouveau dépôt). L'IA propose : rien n'entre au programme sans votre coche."}>
                {typesDetecting ? <><Spinner /> Détection en cours…</>
                  : <><span aria-hidden="true">✨</span> {types.length === 0 ? 'Détecter les types' : 'Relancer la détection'} <PastilleEuro /></>}
              </button>
              <InfoGuide {...aideReferentiels('detecter_types')} />
            </div>
          </div>
          {typesDetecting && (
            <JaugeAttente libelle="L’IA lit le document épuré et relève les formats de travail qu’il met en œuvre…" />
          )}

          {/* Cocher / décocher en bloc, JUSTE AU-DESSUS DE LA LISTE (15/08/2026) : ces deux boutons
              n'agissent que sur les cases du dessous — ils vivent donc contre elles, et non sur la
              ligne des prompts où ils étaient nés. Chacun disparaît quand il n'a plus rien à faire. */}
          {types.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              {types.some(t => !t.validee) && (
                <button type="button" className="btn-secondary" disabled={typesBusy}
                  style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap',
                    cursor: typesBusy ? 'not-allowed' : 'pointer', opacity: typesBusy ? 0.6 : 1 }}
                  title="Mettre d'un coup toutes les propositions au programme de ce niveau — gratuit, aucune IA"
                  onClick={() => retenirTousLesTypes(true)}>
                  <span aria-hidden="true" style={{ marginRight: 2 }}>☑</span> Sélectionner tout
                </button>
              )}
              {types.some(t => t.validee) && (
                <button type="button" className="btn-secondary" disabled={typesBusy}
                  style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap',
                    cursor: typesBusy ? 'not-allowed' : 'pointer', opacity: typesBusy ? 0.6 : 1 }}
                  title="Retirer d'un coup tous les types du programme — ils redeviennent des propositions, rien n'est perdu"
                  onClick={() => retenirTousLesTypes(false)}>
                  <span aria-hidden="true" style={{ marginRight: 2 }}>☐</span> Tout décocher
                </button>
              )}
            </div>
          )}

          {/* La liste des types DU RÉFÉRENTIEL — propositions et types retenus ensemble, la case
              les distingue. Cocher = mettre au programme (le prof le voit). ✕ = SUPPRIMER la ligne
              (et ses précisions) ; une future détection la remettra si l'IA relit le type. */}
          <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
              {types.length === 0 ? (
                <p className="text-sm" style={{ padding: '1.25rem 1.5rem', textAlign: 'center', color: '#64748b', lineHeight: 1.7 }}>
                  {typesDetecting ? 'La liste se remplit dès que l’IA a fini sa lecture…' : <>
                    Aucun type d’activité pour ce référentiel.<br />
                    <span style={{ color: '#7c3aed', fontWeight: 600 }}>Cliquez sur « ✨ Détecter les types » ci-dessus</span>
                    {' '}pour que l’IA lise le document — ou ajoutez-en un à la main ci-dessous.
                  </>}
                </p>
              ) : types.map((t, i) => {
                const editOuvert = promptEditId === t.id
                return (
                  <Fragment key={t.id}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
                    background: t.validee ? 'white' : '#fcfcfd',
                    borderBottom: (i < types.length - 1 && !editOuvert) ? '1px solid #f1f5f9' : 'none' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0, cursor: 'pointer' }}
                      title={t.validee
                        ? `« ${t.label} » est au programme : un professeur de ce niveau le trouve dans la liste des types d'activité, quand il prépare une séance. Décocher l'en retire.`
                        : `Proposition lue dans le document. Cocher pour la mettre au programme de ce niveau.`}>
                      <input type="checkbox" checked={!!t.validee} onChange={e => retenirType(t, e.target.checked)}
                        style={{ width: 16, height: 16, cursor: 'pointer', flexShrink: 0 }} />
                      <span style={{ fontWeight: t.validee ? 600 : 400, color: t.validee ? '#1e293b' : '#64748b', fontSize: 13 }}>
                        {t.label}
                      </span>
                      {/* Badge d'ORIGINE : d'où vient le type — lu dans le document (IA) ou ajouté
                          à la main (ADMIN). Il ne dit jamais qui l'a retenu : ça, c'est la case. */}
                      <span style={badgeOrigine(t.origine)}>{SOURCE_LABEL[t.origine] || t.origine}</span>
                      {!t.validee && (
                        <span style={{ fontSize: 11, color: '#94a3b8', fontStyle: 'italic' }}>proposé, pas encore au programme</span>
                      )}
                    </label>
                    {/* Les PRÉCISIONS ont quitté cette ligne (15/08/2026) : elles ont leur propre
                        cartouche, juste dessous. Ici on décide ce qui entre au programme, et rien
                        d'autre — une ligne, une décision. Reste le prompt de génération du type,
                        qui n'appartient qu'à lui. */}
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                      {t.validee && ((t.prompt || '').trim()
                        ? <span title={`« ${t.label} » a son prompt de génération pour ce référentiel`}
                            style={{ color: '#166534', fontWeight: 700, fontSize: 11, whiteSpace: 'nowrap' }}>✓ prompt</span>
                        : <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, background: '#fef2f2', color: '#dc2626', fontWeight: 700, fontSize: 11, whiteSpace: 'nowrap' }}>⚠ vide</span>)}
                      <button type="button" onClick={() => setPromptEditId(editOuvert ? null : t.id)}
                        title={`Voir / corriger le prompt de « ${t.label} » pour ce référentiel`}
                        style={{ padding: '3px 10px', borderRadius: 8, border: '1px solid #cbd5e1',
                          background: editOuvert ? '#eff6ff' : 'white', color: '#334155', cursor: 'pointer', fontSize: 12, whiteSpace: 'nowrap' }}>
                        ✎ Prompt
                      </button>
                    </span>
                  </div>
                  {editOuvert && (
                    <div style={{ padding: '12px 14px', background: '#f8fafc',
                      borderBottom: i < types.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 8 }}>
                        Prompt de « {t.label} » — pour {coupleLabel}
                        <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 8 }}>lecture seule</span>
                      </div>
                      <textarea value={t.prompt || ''} readOnly spellCheck={false}
                        rows={8} placeholder="Ce type n’a pas encore de prompt de génération."
                        style={{ width: '100%', fontFamily: 'monospace', fontSize: 12, padding: 10, border: '1px solid #cbd5e1', borderRadius: 8, resize: 'vertical', boxSizing: 'border-box', background: '#f1f5f9', color: '#475569' }} />
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
                        <span style={{ fontSize: 12, color: '#64748b' }}>
                          Se modifie dans <strong>Admin → IA → Prompts → Référentiels</strong>,
                          groupe « Génération ».
                        </span>
                        <button type="button" onClick={() => setPromptEditId(null)}
                          style={{ marginLeft: 'auto', padding: '0 16px', height: 36, borderRadius: 8, border: '1px solid #cbd5e1', background: 'white', color: '#334155', fontSize: 13, cursor: 'pointer' }}>Fermer</button>
                      </div>
                    </div>
                  )}
                  </Fragment>
                )
              })}
            </div>

          {/* Zone d'ajout MANUEL (champ + bouton) : le libellé crée un type DANS CE référentiel,
              retenu d'emblée (badge ADMIN). Rien n'est écrit ailleurs — aucun autre document ne
              le verra jamais. */}
          {/* LE GABARIT tient sur CETTE MÊME LIGNE, poussé à droite : il ne concerne aucun type
              en particulier — c'est lui qui écrit le prompt de CHACUN, au moment où le type est
              créé. Il ferme donc la ligne d'ajout au lieu d'occuper une ligne pour lui seul.
              Lecture seule, gratuite. Même hauteur que ses deux voisins (règle maison). */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ display: 'flex', gap: 8, flex: '1 1 480px', maxWidth: 480 }}>
              <input value={typesNouveau} onChange={e => setTypesNouveau(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') ajouterType(typesNouveau) }}
                placeholder="Ajouter un type d'activité à ce référentiel…"
                style={{ flex: 1, padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: 13 }} />
              <button onClick={() => ajouterType(typesNouveau)} disabled={typesBusy || !typesNouveau.trim()}
                style={btnTypes('#16a34a', typesBusy || !typesNouveau.trim())}
                title="Ajouter ce type d'activité à ce référentiel (il est au programme d'emblée)"><span aria-hidden="true">＋</span> Ajouter</button>
            </div>
            <button type="button" className="btn-secondary"
              style={{ marginLeft: 'auto', fontSize: 12, height: 36, padding: '0 12px', whiteSpace: 'nowrap' }}
              title="Voir le gabarit : le prompt qui FABRIQUE le prompt de génération de chaque type, au moment où le type est créé (lecture seule)"
              onClick={ouvrirGabaritType}>
              <span aria-hidden="true" style={{ fontSize: 15, lineHeight: 1, marginRight: 2 }}>👁</span> Gabarit des prompts
            </button>
          </div>
          </>)}
        </div>
      )}

      {/* Carte 7 (DERNIÈRE étape) — PRÉCISIONS des types d'activité. Détachée de la cartouche des
          types le 15/08/2026 : elles y vivaient en sous-locataires, leurs deux prompts posés sur la
          ligne du voisin et un panneau dépliable sous chaque ligne. Deux travaux différents, deux
          cartouches — et la procédure en quatre temps (matières, découpe, types, précisions)
          retrouve son quatrième.
          Elle ne montre QUE les types au programme : une proposition non cochée n'a rien à
          décliner, et le serveur refuse d'y travailler (422). */}
      {estVisible('precisions') && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
              <Pastille etat={nbTypesAvecPrecisions > 0 ? 'vert' : 'rouge'} titre="Vert = au moins un type au programme a ses précisions." />
              Précisions des types d’activité
              <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 6, fontSize: 13 }}>
                ({nbTypesAvecPrecisions} type{nbTypesAvecPrecisions > 1 ? 's' : ''} décliné{nbTypesAvecPrecisions > 1 ? 's' : ''}{nbTypesSansPrecisions > 0 ? `, ${nbTypesSansPrecisions} sans précision` : ''})
              </span>
              <span style={{ marginLeft: 8 }}>
                <BadgeIA titre="L'IA propose les précisions d'un type pour ce niveau — vous gardez, vous supprimez, vous ajoutez à la main" />
              </span>
              <InfoGuide {...aideReferentiels('precisions')} />
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
              <button type="button" className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
                title={precisionsOuvert ? 'Réduire' : 'Développer'} onClick={() => setPrecisionsOuvert(o => !o)}>
                {precisionsOuvert ? 'Réduire' : 'Développer'}
              </button>
            </div>
          </div>

          {precisionsOuvert && (<>
          {/* Même partage que les autres cartouches : à GAUCHE ce qui se LIT (les prompts,
              gratuits), à DROITE ce qui AGIT et qui coûte, tout au bout de la ligne. */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <button type="button" className="btn-secondary"
              style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title="Voir le méta-prompt : la consigne qui sert à l'IA pour RÉDIGER le prompt des précisions (lecture seule)"
              onClick={ouvrirMetaPrecisions}>
              <span aria-hidden="true" style={{ fontSize: 15, lineHeight: 1, marginRight: 2 }}>👁</span> Méta-prompt
            </button>
            <span style={{ marginRight: 14, display: 'inline-flex', alignItems: 'center' }}>
              <InfoGuide {...aideReferentiels('meta_prompt_precisions')} />
            </span>
            {/* Le PROMPT des précisions : unique pour tout le référentiel, appelé une fois par type
                (le logiciel remplace le repère du nom de type). CONSULTATION SEULE — le dépôt se
                fait dans Prompts → Référentiels, comme pour tous les autres prompts. */}
            <button type="button" className="btn-secondary"
              style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap' }}
              title="Voir le prompt qui lit les précisions d'un type dans CE référentiel — consultation seule (gratuit, aucune IA)"
              onClick={ouvrirPromptPrecisions}>
              <span aria-hidden="true" style={{ fontSize: 15, lineHeight: 1, marginRight: 2 }}>👁</span> Prompt des précisions
            </button>
            <InfoGuide {...aideReferentiels('prompt_precisions')} />

            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              {nbTypesSansPrecisions > 0 && (
                <button type="button" onClick={genererPrecisionsManquantes}
                  disabled={typesBusy || !!precisProgress}
                  style={btnTypes('#7c3aed', typesBusy || !!precisProgress)}
                  title="Appel IA facturé, un par type — prépare les précisions des types AU PROGRAMME qui n'en ont pas encore. Ceux qui en ont déjà ne sont pas retouchés. Le nombre d'appels est annoncé avant de partir.">
                  {precisProgress ? <><Spinner /> Précisions en cours…</>
                    : <><span aria-hidden="true">✨</span> Préparer les précisions <PastilleEuro /></>}
                </button>
              )}
            </div>
          </div>

          {/* Jauge RÉELLE : générées type par type, sur les types RETENUS seulement. */}
          {precisProgress && (
            <div>
              <div style={{ fontSize: 12, color: '#1d4ed8', marginBottom: 4 }}>
                <BadgeIA titre="L'IA prépare les précisions de chaque type d'activité retenu, pour ce niveau" />{' '}
                Précisions en cours de préparation ({precisProgress.fait + 1}/{precisProgress.total})
                {precisProgress.label ? ` — ${precisProgress.label}` : ''}…
              </div>
              <div style={{ height: 8, borderRadius: 999, background: '#e2e8f0', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${Math.round(100 * precisProgress.fait / Math.max(1, precisProgress.total))}%`,
                  background: '#7c3aed', transition: 'width 0.4s' }} />
              </div>
            </div>
          )}

          {/* Une ligne par type AU PROGRAMME. Le badge dit combien de précisions il porte ; le
              bouton ouvre le panneau, qui ne fait que lire tant qu'on ne lui demande rien. */}
          <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
            {typesRetenus.length === 0 ? (
              <p className="text-sm" style={{ padding: '1.25rem 1.5rem', textAlign: 'center', color: '#64748b', lineHeight: 1.7 }}>
                Aucun type d’activité au programme de ce niveau.<br />
                Cochez-en dans la cartouche du dessus : leurs précisions se travaillent ici.
              </p>
            ) : typesRetenus.map((t, i) => {
              const precisOuvert = precisEditId === t.id
              return (
                <Fragment key={t.id}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: 'white',
                  borderBottom: (i < typesRetenus.length - 1 && !precisOuvert) ? '1px solid #f1f5f9' : 'none' }}>
                  <span style={{ flex: 1, minWidth: 0, fontWeight: 600, color: '#1e293b', fontSize: 13 }}>{t.label}</span>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                    {(t.nb_precisions || 0) > 0
                      ? <span style={{ color: '#166534', fontWeight: 700, fontSize: 11, whiteSpace: 'nowrap' }}>⚑ {t.nb_precisions} précision{t.nb_precisions > 1 ? 's' : ''}</span>
                      : <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, background: '#f1f5f9', color: '#94a3b8', fontWeight: 700, fontSize: 11, whiteSpace: 'nowrap' }}>0 précision</span>}
                    <button type="button" onClick={() => ouvrirPrecisions(t)}
                      title={`Voir et corriger les précisions de « ${t.label} » pour ce niveau (gratuit — rien n'est appelé à l'ouverture)`}
                      style={{ padding: '3px 10px', borderRadius: 8, border: '1px solid #cbd5e1',
                        background: precisOuvert ? '#eff6ff' : 'white', color: '#334155', cursor: 'pointer', fontSize: 12, whiteSpace: 'nowrap' }}>
                      ✎ Précisions
                    </button>
                  </span>
                </div>
                {precisOuvert && (
                  <div style={{ padding: '12px 14px', background: '#f8fafc',
                    borderBottom: i < typesRetenus.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                    {precisLoading ? (
                      <div>
                        <BadgeIA titre="L'IA génère les précisions de ce type d'activité pour ce niveau" />
                        <JaugeAttente libelle="L’IA prépare les précisions adaptées à ce niveau…" />
                      </div>
                    ) : precisList.length > 0 ? (
                      <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {precisList.map(p => (
                          <li key={p.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
                            padding: '6px 10px', borderRadius: 8, border: '1px solid #e2e8f0', background: 'white', fontSize: 13, color: '#1e293b' }}>
                            <span style={{ fontWeight: 500 }}>{p.libelle}</span>
                            <button type="button" disabled={precisBusy}
                              onClick={() => supprimerPrecisType(t, p)}
                              title={`Supprimer « ${p.libelle} »`}
                              style={{ height: 26, width: 26, borderRadius: 6, border: '1px solid #fecaca', background: '#fef2f2', color: '#dc2626',
                                cursor: precisBusy ? 'default' : 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, flexShrink: 0 }}>🗑</button>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      /* Liste vide. Ouvrir ce panneau lançait l'IA tout seul (15/08/2026) :
                         maintenant il propose, et c'est le clic qui dépense. */
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                        <p style={{ fontSize: 12, color: '#94a3b8', margin: 0 }}>Aucune précision pour ce type.</p>
                        <button type="button" onClick={() => genererPrecisType(t.id)}
                          disabled={precisBusy || precisLoading}
                          style={btnTypes('#7c3aed', precisBusy || precisLoading)}
                          title={`Appel IA facturé — l'IA lit le référentiel et propose les précisions de « ${t.label} » pour ce niveau. Vous pouvez aussi les écrire à la main ci-dessous, gratuitement.`}>
                          <span aria-hidden="true">✨</span> Proposer les précisions <PastilleEuro />
                        </button>
                      </div>
                    )}
                    <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                      <input value={newPrecis} onChange={e => setNewPrecis(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); ajouterPrecisType(t) } }}
                        placeholder="Ajouter une précision…"
                        style={{ flex: 1, minWidth: 0, height: 36, padding: '0 12px', fontSize: 13, borderRadius: 8, border: '1px solid #cbd5e1', boxSizing: 'border-box' }} />
                      <button type="button" onClick={() => ajouterPrecisType(t)} disabled={precisBusy || !newPrecis.trim()}
                        style={btnTypes('#0f172a', precisBusy || !newPrecis.trim())}
                        title="Ajouter cette précision pour ce type">＋ Ajouter</button>
                      <button type="button" onClick={() => { setPrecisEditId(null); setPrecisList([]); setNewPrecis('') }}
                        style={{ padding: '0 16px', height: 36, borderRadius: 8, border: '1px solid #cbd5e1', background: 'white', color: '#334155', fontSize: 13, cursor: 'pointer' }}>Fermer</button>
                    </div>
                  </div>
                )}
                </Fragment>
              )
            })}
          </div>
          </>)}
        </div>
      )}

      {/* « Voir » de la liste des documents déposés : le PDF EN ATTENTE s'ouvre tel quel
          (même fenêtre que la relecture du référentiel enregistré). */}
      {voirDepot && apercu && (
        <div onClick={() => setVoirDepot(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                {apercu.filename} · {apercu.pages} page(s)
              </span>
              <button type="button" onClick={() => setVoirDepot(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <iframe
              title="Document déposé"
              src={`/api/admin/referentiels/depot-pdf?token=${encodeURIComponent(apercu.token)}`}
              style={{ flex: 1, width: '100%', border: 'none' }} />
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

      {/* Fenêtre du PROMPT DES MATIÈRES — ÉCRITURE. Le prompt est rangé sur le RÉFÉRENTIEL
          (referentiels.prompt_matieres) : il ne sert qu'à ce couple, donc il s'écrit ici, à
          l'endroit où on le lit. Il vivait sur le cycle et se corrigeait dans un autre écran ;
          c'était faux — un cycle porte dix-huit diplômes qui ne se lisent pas pareil.
          Même patron que les autres fenêtres de cet écran (clic dehors ou ×). */}
      {promptMatieresOuvert && (
        <div onClick={() => setPromptMatieresOuvert(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 10, padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
                fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                Prompt de lecture des matières
                <span style={{ fontWeight: 400, color: '#94a3b8' }}>
                  ({cycleCourant?.nom || ''} — {niveau})
                </span>
                {/* Le prompt SERT dès qu'il existe : ce voyant dit seulement s'il a été relu. */}
                <span style={{ fontSize: 11, fontWeight: 700,
                  color: promptMatieresValide ? '#166534' : promptMatieres.trim() ? '#b45309' : '#A63045' }}>
                  {promptMatieresValide ? '● relu et validé'
                    : promptMatieres.trim() ? '● écrit par l’IA, à relire'
                    : '● pas encore écrit'}
                </span>
              </span>
              <button type="button" onClick={() => setPromptMatieresOuvert(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <ZonePromptLecture texte={promptMatieres}
              vide="Ce référentiel n’a pas encore de prompt de lecture des matières." />
            <PiedPromptLecture niveau={niveau} onFermer={() => setPromptMatieresOuvert(false)} />
          </div>
        </div>
      )}

      {/* Fenêtre du MÉTA-PROMPT des matières — LECTURE SEULE. Ce n'est pas le prompt qui lit le
          document : c'est celui qui sert à l'ÉCRIRE. Il vit dans les réglages, pas sur le cycle. */}
      {metaOuvert && (
        <div onClick={() => setMetaOuvert(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 10, padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
                fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                Méta-prompt des matières
                <span style={{ fontWeight: 400, color: '#94a3b8' }}>
                  {metaSource === 'referentiel'
                    ? `(propre à ce niveau — ${niveau})`
                    : '(aucun — à écrire pour ce niveau)'}
                </span>
                <span style={{ fontSize: 11, fontWeight: 700,
                  color: metaPrompt === null ? '#94a3b8' : metaPrompt.trim() ? '#166534' : '#A63045' }}>
                  {metaPrompt === null ? '● lecture…' : metaPrompt.trim() ? '● en base' : '● absent de la base'}
                </span>
              </span>
              <button type="button" onClick={() => setMetaOuvert(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <pre style={{ flex: 1, overflow: 'auto', margin: 0, padding: 14, fontSize: 12,
              color: '#334155', whiteSpace: 'pre-wrap', background: '#f8fafc' }}>
              {metaPrompt === null
                ? 'Lecture du méta-prompt…'
                : (metaPrompt.trim()
                  || 'Ce référentiel n’a pas encore son méta-prompt des matières. C’est l’état normal d’un référentiel qu’on vient de déposer : un méta-prompt regarde CE document, il ne se recopie pas d’un autre diplôme.\n\nÉcrivez-le dans Prompts → Référentiels, cartouche « Des matières ».')}
            </pre>
            <div style={{ padding: '10px 14px', borderTop: '1px solid #e2e8f0',
              fontSize: 12.5, lineHeight: 1.6, color: '#b91c1c', background: '#fef2f2' }}>
              <strong>Lecture seule.</strong> Ce texte ne lit aucun document : il demande à l’IA d’en
              RÉDIGER un autre — le prompt de lecture des matières. Son repère <code>{'{document}'}</code>
              reçoit le référentiel donné en exemple ; le prompt qu’il fait écrire, lui, portera
              <code>{'{texte}'}</code>. Pour le modifier, ouvrez <strong>Prompts</strong> → onglet
              <strong> Référentiels</strong>, ligne « prompt_meta_matieres » de ce niveau.
            </div>
          </div>
        </div>
      )}

      {/* Fenêtre du MÉTA-PROMPT DE LA DÉCOUPE — LECTURE SEULE, jumelle de celle des matières. Une
          différence : ce texte peut venir de deux endroits, et la fenêtre dit lequel sert. */}
      {metaDecoupeOuvert && (
        <div onClick={() => setMetaDecoupeOuvert(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 10, padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
                fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                Méta-prompt de la découpe
                <span style={{ fontWeight: 400, color: '#94a3b8' }}>
                  {metaDecoupeSource === 'referentiel'
                    ? `(propre à ce niveau — ${niveau})`
                    : '(aucun — à écrire pour ce niveau)'}
                </span>
                <span style={{ fontSize: 11, fontWeight: 700,
                  color: metaDecoupe === null ? '#94a3b8' : metaDecoupe.trim() ? '#166534' : '#A63045' }}>
                  {metaDecoupe === null ? '● lecture…' : metaDecoupe.trim() ? '● en base' : '● absent de la base'}
                </span>
              </span>
              <button type="button" onClick={() => setMetaDecoupeOuvert(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <pre style={{ flex: 1, overflow: 'auto', margin: 0, padding: 14, fontSize: 12,
              color: '#334155', whiteSpace: 'pre-wrap', background: '#f8fafc' }}>
              {metaDecoupe === null
                ? 'Lecture du méta-prompt…'
                : (metaDecoupe.trim()
                  || 'Ce référentiel n’a pas encore son méta-prompt de découpe. C’est l’état normal d’un référentiel qu’on vient de déposer : un méta-prompt regarde CE document, il ne se recopie pas d’un autre diplôme.\n\nÉcrivez-le dans Prompts → Référentiels, cartouche « De découpe ».')}
            </pre>
            <div style={{ padding: '10px 14px', borderTop: '1px solid #e2e8f0',
              fontSize: 12.5, lineHeight: 1.6, color: '#b91c1c', background: '#fef2f2' }}>
              <strong>Lecture seule.</strong> Ce texte ne découpe aucun document : il demande à l’IA
              d’en RÉDIGER un autre — le prompt de découpe. Son repère <code>{'{document}'}</code>
              reçoit le référentiel donné en exemple ; le prompt qu’il fait écrire, lui, portera
              <code>{'{texte}'}</code>. Pour le modifier, ouvrez <strong>Prompts</strong> → onglet
              <strong> Référentiels</strong>, ligne « prompt_meta_decoupe » de ce niveau.
            </div>
          </div>
        </div>
      )}

      {/* Fenêtre du PROMPT DES PRÉCISIONS — CONSULTATION SEULE (09/08/2026). Elle ne double aucune
          porte d'écriture : le dépôt reste dans Prompts → Référentiels, seul endroit où un prompt
          s'écrit. Ici on vérifie d'un coup d'œil, sans quitter l'écran où l'on travaille. */}
      {promptPrecisionsOuvert && (
        <div onClick={() => setPromptPrecisionsOuvert(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 10, padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
                fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                Prompt des précisions
                <span style={{ fontWeight: 400, color: '#94a3b8' }}>(propre à ce niveau — {niveau})</span>
                <span style={{ fontSize: 11, fontWeight: 700,
                  color: promptPrecisions === null ? '#94a3b8' : promptPrecisions.trim() ? '#166534' : '#A63045' }}>
                  {promptPrecisions === null ? '● lecture…' : promptPrecisions.trim() ? '● en base' : '● absent de la base'}
                </span>
                {promptPrecisions !== null && promptPrecisions.trim() && (
                  <span style={{ fontSize: 11, fontWeight: 700, color: promptPrecisionsValide ? '#166534' : '#b45309' }}>
                    {promptPrecisionsValide ? '● validé' : '● non validé'}
                  </span>
                )}
              </span>
              <button type="button" onClick={() => setPromptPrecisionsOuvert(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <pre style={{ flex: 1, overflow: 'auto', margin: 0, padding: 14, fontSize: 12,
              color: '#334155', whiteSpace: 'pre-wrap', background: '#f8fafc' }}>
              {promptPrecisions === null
                ? 'Lecture du prompt…'
                : (promptPrecisions.trim()
                  || 'Aucun prompt des précisions en base pour ce niveau.')}
            </pre>
            <div style={{ padding: '10px 14px', borderTop: '1px solid #e2e8f0',
              fontSize: 12.5, lineHeight: 1.6, color: '#b91c1c', background: '#fef2f2' }}>
              <strong>Consultation seule.</strong> UN SEUL prompt pour tout le référentiel : le logiciel
              l’appelle une fois par type, en remplaçant <code>{'{label}'}</code> par le nom du type ;
              <code>{'{texte}'}</code> reçoit le document. À ne pas confondre avec le ✎ Prompt d’une
              ligne de type, qui GÉNÈRE ce que le professeur reçoit. Pour le déposer ou le corriger,
              ouvrez <strong>Prompts</strong> → onglet <strong>Référentiels</strong>, ligne
              « prompt_precisions » de ce niveau.
            </div>
          </div>
        </div>
      )}

      {/* Fenêtre du MÉTA-PROMPT DES PRÉCISIONS — LECTURE SEULE, quatrième jumelle. */}
      {metaPrecisionsOuvert && (
        <div onClick={() => setMetaPrecisionsOuvert(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 10, padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
                fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                Méta-prompt des précisions
                <span style={{ fontWeight: 400, color: '#94a3b8' }}>
                  {metaPrecisionsSource === 'referentiel'
                    ? `(propre à ce niveau — ${niveau})`
                    : '(aucun — à écrire pour ce niveau)'}
                </span>
                <span style={{ fontSize: 11, fontWeight: 700,
                  color: metaPrecisions === null ? '#94a3b8' : metaPrecisions.trim() ? '#166534' : '#A63045' }}>
                  {metaPrecisions === null ? '● lecture…' : metaPrecisions.trim() ? '● en base' : '● absent de la base'}
                </span>
              </span>
              <button type="button" onClick={() => setMetaPrecisionsOuvert(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <pre style={{ flex: 1, overflow: 'auto', margin: 0, padding: 14, fontSize: 12,
              color: '#334155', whiteSpace: 'pre-wrap', background: '#f8fafc' }}>
              {metaPrecisions === null
                ? 'Lecture du méta-prompt…'
                : (metaPrecisions.trim()
                  || 'Ce référentiel n’a pas encore son méta-prompt des précisions. C’est l’état normal d’un référentiel qu’on vient de déposer : un méta-prompt regarde CE document, il ne se recopie pas d’un autre diplôme.\n\nÉcrivez-le dans Prompts → Référentiels, cartouche « Des précisions ».')}
            </pre>
            <div style={{ padding: '10px 14px', borderTop: '1px solid #e2e8f0',
              fontSize: 12.5, lineHeight: 1.6, color: '#b91c1c', background: '#fef2f2' }}>
              <strong>Lecture seule.</strong> Ce texte ne propose aucune précision : il demande à l’IA
              d’en RÉDIGER un autre — le prompt des précisions. Son repère <code>{'{document}'}</code>
              reçoit le référentiel donné en exemple ; le prompt qu’il fait écrire, lui, portera
              <code>{'{texte}'}</code> et <code>{'{label}'}</code>. Pour le modifier, ouvrez
              <strong> Prompts</strong> → onglet <strong>Référentiels</strong>, ligne
              « prompt_meta_precisions » de ce niveau.
            </div>
          </div>
        </div>
      )}

      {/* Fenêtre du MÉTA-PROMPT DES TYPES — LECTURE SEULE, troisième jumelle. Comme la découpe,
          ce texte peut venir de deux endroits, et la fenêtre dit lequel sert. */}
      {gabaritOuvert && (
        <div onClick={() => setGabaritOuvert(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 10, padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
                fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                Gabarit du prompt de génération d’un type
                <span style={{ fontWeight: 400, color: '#94a3b8' }}>(commun à tous les référentiels)</span>
                <span style={{ fontSize: 11, fontWeight: 700,
                  color: gabarit === null ? '#94a3b8' : gabaritEnBase ? '#166534' : '#A63045' }}>
                  {gabarit === null ? '● lecture…' : gabaritEnBase ? '● en base' : '● absent de la base (texte de référence)'}
                </span>
              </span>
              <button type="button" onClick={() => setGabaritOuvert(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <pre style={{ flex: 1, overflow: 'auto', margin: 0, padding: 14, fontSize: 12,
              color: '#334155', whiteSpace: 'pre-wrap', background: '#f8fafc' }}>
              {gabarit === null ? 'Lecture du gabarit…' : (gabarit.trim() || 'Aucun gabarit lisible.')}
            </pre>
            <div style={{ padding: '10px 14px', borderTop: '1px solid #e2e8f0',
              fontSize: 12.5, lineHeight: 1.6, color: '#b91c1c', background: '#fef2f2' }}>
              <strong>Lecture seule.</strong> Ce texte n’est pas envoyé à une IA : il est RECOPIÉ à la
              création d’un type, <code>{'{label}'}</code> et <code>{'{niveau}'}</code> remplis au
              passage, pour devenir le prompt de génération de ce type. <code>{'{texte}'}</code> et
              <code>{' {referentiel}'}</code> restent intacts — c’est la génération du professeur qui
              les remplira. Le retoucher ne réécrit AUCUN prompt déjà posé : seuls les types créés
              ensuite en héritent. Pour le modifier : <strong>Prompts</strong> → catégorie
              <strong> Admin</strong>, ligne « gabarit_type ».
            </div>
          </div>
        </div>
      )}

      {metaTypesOuvert && (
        <div onClick={() => setMetaTypesOuvert(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 10, padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
                fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                Méta-prompt des types d’activité
                <span style={{ fontWeight: 400, color: '#94a3b8' }}>
                  {metaTypesSource === 'referentiel'
                    ? `(propre à ce niveau — ${niveau})`
                    : '(aucun — à écrire pour ce niveau)'}
                </span>
                <span style={{ fontSize: 11, fontWeight: 700,
                  color: metaTypes === null ? '#94a3b8' : metaTypes.trim() ? '#166534' : '#A63045' }}>
                  {metaTypes === null ? '● lecture…' : metaTypes.trim() ? '● en base' : '● absent de la base'}
                </span>
              </span>
              <button type="button" onClick={() => setMetaTypesOuvert(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <pre style={{ flex: 1, overflow: 'auto', margin: 0, padding: 14, fontSize: 12,
              color: '#334155', whiteSpace: 'pre-wrap', background: '#f8fafc' }}>
              {metaTypes === null
                ? 'Lecture du méta-prompt…'
                : (metaTypes.trim()
                  || 'Ce référentiel n’a pas encore son méta-prompt des types d’activité. C’est l’état normal d’un référentiel qu’on vient de déposer : un méta-prompt regarde CE document, il ne se recopie pas d’un autre diplôme.\n\nÉcrivez-le dans Prompts → Référentiels, cartouche « Des types d’activité ».')}
            </pre>
            <div style={{ padding: '10px 14px', borderTop: '1px solid #e2e8f0',
              fontSize: 12.5, lineHeight: 1.6, color: '#b91c1c', background: '#fef2f2' }}>
              <strong>Lecture seule.</strong> Ce texte ne lit aucun document : il demande à l’IA d’en
              RÉDIGER un autre — le prompt de lecture des types. Son repère <code>{'{document}'}</code>
              reçoit le référentiel donné en exemple ; le prompt qu’il fait écrire, lui, portera
              <code>{'{texte}'}</code>. Pour le modifier, ouvrez <strong>Prompts</strong> → onglet
              <strong> Référentiels</strong>, ligne « prompt_meta_types » de ce niveau .
            </div>
          </div>
        </div>
      )}

      {/* Fenêtre du PROMPT DE DÉCOUPE — ÉCRITURE, jumelle de celle des matières. Le prompt est
          rangé sur le RÉFÉRENTIEL (referentiels.prompt_decoupe) : il ne découpe que ce couple,
          donc il s'écrit ici, à l'endroit où on le lit. */}
      {promptOuvert && (
        <div onClick={() => setPromptOuvert(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 10, padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
                fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                Prompt de découpe du document
                <span style={{ fontWeight: 400, color: '#94a3b8' }}>
                  ({cycleCourant?.nom || ''} — {niveau})
                </span>
                <span style={{ fontSize: 11, fontWeight: 700,
                  color: promptValide ? '#166534' : promptDecoupe.trim() ? '#b45309' : '#A63045' }}>
                  {promptValide ? '● relu et validé'
                    : promptDecoupe.trim() ? '● écrit par l’IA, à relire'
                    : '● pas encore écrit'}
                </span>
              </span>
              <button type="button" onClick={() => setPromptOuvert(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <ZonePromptLecture texte={promptDecoupe}
              vide="Ce référentiel n’a pas encore de prompt de découpe." />
            <PiedPromptLecture niveau={niveau} onFermer={() => setPromptOuvert(false)} />
          </div>
        </div>
      )}

      {/* Fenêtre du PROMPT DES TYPES D'ACTIVITÉ — ÉCRITURE, troisième jumelle. Le prompt est rangé
          sur le RÉFÉRENTIEL (referentiels.prompt_types) : il ne lit que ce couple. */}
      {promptTypesOuvert && (
        <div onClick={() => setPromptTypesOuvert(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 10, padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
                fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                Prompt de lecture des types d’activité
                <span style={{ fontWeight: 400, color: '#94a3b8' }}>
                  ({cycleCourant?.nom || ''} — {niveau})
                </span>
                <span style={{ fontSize: 11, fontWeight: 700,
                  color: promptTypesValide ? '#166534' : promptTypes.trim() ? '#b45309' : '#A63045' }}>
                  {promptTypesValide ? '● relu et validé'
                    : promptTypes.trim() ? '● écrit par l’IA, à relire'
                    : '● pas encore écrit'}
                </span>
              </span>
              <button type="button" onClick={() => setPromptTypesOuvert(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <ZonePromptLecture texte={promptTypes}
              vide="Ce référentiel n’a pas encore de prompt de lecture des types." />
            <PiedPromptLecture niveau={niveau} onFermer={() => setPromptTypesOuvert(false)} />
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
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                {/* Sélectionne tout le texte de la fenêtre — il ne reste qu'à copier (Ctrl+C). */}
                <button type="button" className="btn-secondary" onClick={selectionnerEpure}
                  disabled={!epureTexte}
                  style={{ fontSize: 12, padding: '4px 10px', whiteSpace: 'nowrap',
                    cursor: epureTexte ? 'pointer' : 'not-allowed', opacity: epureTexte ? 1 : 0.5 }}
                  title="Sélectionner tout le texte de cette fenêtre — il ne reste plus qu'à le copier (Ctrl+C)">
                  Sélectionner tout
                </button>
                <button type="button" onClick={() => setShowEpure(false)} title="Fermer"
                  style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
              </span>
            </div>
            <pre ref={epureRef} style={{ flex: 1, overflow: 'auto', margin: 0, padding: 14, fontSize: 12,
              color: '#334155', whiteSpace: 'pre-wrap', background: '#f8fafc' }}>
              {epureTexte === null ? 'Lecture…'
                : (epureTexte || 'Aucun texte de travail enregistré pour ce couple.')}
            </pre>
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
      {/* La fenêtre de transfert — ouverte depuis l'icône d'une ligne, fermée dès que c'est fini. */}
      {transfertPour && (
        <FenetrePro
          titre={`Transfert — ${transfertPour.cycle} · ${transfertPour.nom_affichage || transfertPour.niveau}`}
          largeur={520}
          // `auto` : la fenêtre prend la hauteur de son contenu. La valeur par défaut de la
          // coquille impose 72 % de l'écran quoi qu'on y mette — d'où le grand vide blanc sous
          // les fenêtres courtes. Le plafond (92vh) et l'ascenseur restent, eux, dans la coquille.
          hauteur="auto"
          onFermer={() => setTransfertPour(null)}
        >
          <TransfertReferentiel referentiel={transfertPour} />
        </FenetrePro>
      )}

      {/* Panneau « Comment ça marche ? » — les deux procédures, lues dans le catalogue d'aide.
          Fermé par le ✕, par un clic sur le fond, ou par Échap : on ne piège jamais l'admin. */}
      {proceduresOuvert && (
        <div onClick={() => setProceduresOuvert(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.45)', zIndex: 60,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, maxWidth: 760, width: '100%',
              maxHeight: '85vh', overflow: 'auto', padding: '20px 24px',
              boxShadow: '0 10px 40px rgba(15,23,42,0.25)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#1e293b' }}>
                {aideReferentiels('procedures').titre}
              </h3>
              <button type="button" onClick={() => setProceduresOuvert(false)}
                title="Fermer"
                style={{ marginLeft: 'auto', border: 'none', background: 'transparent',
                  fontSize: 18, cursor: 'pointer', color: '#64748b', lineHeight: 1 }}>✕</button>
            </div>
            <pre style={{ margin: 0, fontFamily: 'inherit', fontSize: 13.5, lineHeight: 1.6,
              color: '#334155', whiteSpace: 'pre-wrap' }}>
              {aideReferentiels('procedures').long}
            </pre>
          </div>
        </div>
      )}
      </div>
    </div>
  )
}


// LE TRANSFERT — un fichier, deux gestes, aucune connexion entre les deux mondes.
//
// POURQUOI PAS UN LIEN DIRECT ENTRE LES DEUX BASES. Parce qu'il vaut mieux qu'elles ne se parlent
// jamais : rien ne part sans que quelqu'un ait porté le fichier lui-même. C'est aussi ce qui rend
// le geste vérifiable — on peut ouvrir le fichier, le garder, le rejouer.
//
// POURQUOI DANS UNE FENÊTRE À PART. Le geste déplace un référentiel entier — le document, ses
// unités vectorisées, ses matières. Sur l'écran principal, à côté des boutons de la procédure,
// il se déclencherait un jour en visant autre chose.
function TransfertReferentiel({ referentiel }) {
  const [occupe, setOccupe] = useState('')
  // Ne reste ici que ce qui INFORME sans arrêter : « fichier téléchargé ». Tout ce qui REFUSE
  // passe par `showError`, une fenêtre qui bloque l'écran — un refus écrit en petit sous un
  // bouton se lit après coup, ou pas du tout.
  const [reussite, setReussite] = useState('')

  async function exporter() {
    setOccupe('export')
    setReussite('')
    try {
      const r = await fetchWithTimeout(`/api/admin/referentiels/exporter?id=${referentiel.id}`,
                                       { credentials: 'include' }, TIMEOUT_LONG)
      if (!r.ok) throw new Error('Export impossible.')
      // On passe par un objet en mémoire plutôt que par un lien direct : c'est le seul moyen
      // d'attraper une erreur du serveur au lieu d'ouvrir un onglet sur une page d'erreur.
      const blob = await r.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `referentiel-${referentiel.nom_affichage || referentiel.id}.json`
        .replace(/[^a-zA-Z0-9._-]+/g, '-')
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
      setReussite('Fichier téléchargé. Portez-le sur l’autre installation.')
    } catch (e) {
      showError(e.message === 'timeout' ? MSG_TIMEOUT : e.message)
    } finally {
      setOccupe('')
    }
  }

  const btn = {
    display: 'inline-flex', alignItems: 'center', gap: 6, height: 32, padding: '0 14px',
    borderRadius: 7, fontSize: 12.5, fontWeight: 500, border: '1px solid transparent',
    cursor: 'pointer',
  }
  const grise = st => ({ ...st, opacity: 0.45, cursor: 'not-allowed' })
  const stExport = { ...btn, background: '#1F6EEB', color: '#fff' }

  return (
    // LA MARGE EST POSÉE ICI, faute d'être dans la coquille : sans elle le texte touche les
    // bords de la fenêtre. À remonter dans `FenetrePro` le jour où on reprendra les quinze
    // fenêtres de l'application d'un coup.
    <div style={{ fontSize: 13, color: '#334155', padding: '16px 18px 18px' }}>
      <p style={{ margin: '0 0 4px', fontWeight: 700, color: '#A63045' }}>
        {referentiel.cycle} · {referentiel.nom_affichage || referentiel.niveau}
      </p>
      <p style={{ margin: '0 0 14px', fontSize: 12.5, color: '#64748b' }}>
        Le document, ses niveaux, ses matières, ses types et ses unités déjà vectorisées.
        Aucun appel d’IA : rien n’est recalculé.
      </p>

      <button
        type="button"
        onClick={exporter}
        disabled={!!occupe}
        title="Télécharger ce référentiel dans un fichier"
        style={occupe ? grise(stExport) : stExport}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        Exporter ce référentiel
      </button>

      {/* L'ATTENTE SE VOIT, elle ne se devine pas. Un référentiel pèse quelques mégaoctets : entre
          le clic et le fichier, il se passe plusieurs secondes pendant lesquelles rien ne bougeait
          — et un écran figé ne se distingue pas d'un écran en panne. */}
      {occupe === 'export' && (
        <div style={{ marginTop: 12 }}>
          <Attente texte="Rassemblement du référentiel…" compact />
        </div>
      )}

      {reussite && (
        <p style={{ marginTop: 14, fontSize: 12.5, color: '#15803d' }}>{reussite}</p>
      )}
    </div>
  )
}


// L'IMPORT N'APPARTIENT À AUCUNE LIGNE — il en CRÉE une.
//
// LA BÊTISE DU 16/08/2026, corrigée ici : il vivait dans la fenêtre de transfert, celle qui
// s'ouvre depuis une ligne existante. Pour installer un référentiel absent, il fallait donc
// ouvrir la fenêtre d'un AUTRE référentiel — et sur une installation vierge, sans aucune ligne,
// le bouton était carrément inatteignable. Sa place est au-dessus de la liste, où il ne dépend
// de rien.
function ImporterReferentiel({ onImporte }) {
  const [occupe, setOccupe] = useState(false)
  const champFichier = useRef(null)

  async function importer(evenement) {
    const fichier = evenement.target.files?.[0]
    evenement.target.value = ''          // pour que le même fichier puisse être redéposé
    if (!fichier) return
    setOccupe(true)
    try {
      const corps = new FormData()
      corps.append('fichier', fichier)
      const r = await fetchWithTimeout('/api/admin/referentiels/importer',
                                       { method: 'POST', credentials: 'include', body: corps },
                                       TIMEOUT_XLONG)
      // UN REFUS EN AMONT NE PARLE PAS JSON. Quand le serveur web écarte le fichier parce qu'il
      // le trouve trop lourd, il rend une page HTML : `r.json()` échoue, et l'écran affichait
      // « Import impossible. » sans rien de plus. Le code 413 se dit en clair.
      if (r.status === 413) {
        throw new Error('Ce fichier est trop lourd pour être envoyé au serveur.\n\n'
                        + 'La limite se règle dans la configuration du serveur web.')
      }
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Import impossible (code ${r.status}).`)
      const total = Object.values(d.compte || {}).reduce((a, b) => a + b, 0)
      onImporte?.(`« ${d.etiquette || 'Référentiel'} » installé — ${total} lignes posées.`)
    } catch (e) {
      showError(e.message === 'timeout' ? MSG_TIMEOUT : e.message)
    } finally {
      setOccupe(false)
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => champFichier.current?.click()}
        disabled={occupe}
        title="Installer un référentiel exporté depuis une autre installation"
        style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                 width: '100%', height: 32, borderRadius: 7, fontSize: 12.5, fontWeight: 500,
                 border: '1px solid #d1d5db', background: '#fff', color: '#374151',
                 cursor: occupe ? 'not-allowed' : 'pointer', opacity: occupe ? 0.45 : 1 }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        Importer un référentiel
      </button>
      <input ref={champFichier} type="file" accept=".json,application/json"
             onChange={importer} style={{ display: 'none' }} />

      {/* L'import est plus long que l'export : le fichier monte, puis chaque ligne se pose. */}
      {occupe && (
        <div style={{ marginTop: 10 }}>
          <Attente texte="Installation du référentiel…" compact />
        </div>
      )}
    </>
  )
}
