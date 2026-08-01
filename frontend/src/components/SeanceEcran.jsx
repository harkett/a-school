// Écran « Séance » du monde MES CONTENUS — même mécanique que l'écran Activité du monde neuf :
// DEUX COLONNES (formulaire à gauche, déroulé généré à droite), pastilles d'étape numérotées
// (bordeaux clignotant tant que l'étape est à faire, vert quand c'est acquis), frise en haut,
// génération en STREAMING (sablier + jauge, règle IA) et RÈGLE 0 native : la séance s'écrit en
// base à la génération même (POST à la 1re, PUT + version aux suivantes) — aucun bouton
// d'enregistrement, badge « Enregistrée » / « Réessayer l'enregistrement ».
//
// La colonne de gauche = 3 CARTOUCHES (regroupement validé par l'utilisateur le 30/07 —
// aucun champ supprimé, seulement regroupés) :
// ① Infos de base (thème + contexte + mode + durée) : TOUT l'obligatoire, verte quand complète ;
// ② Contenu pédagogique (compétences, matériel, contraintes) : facultatif ;
// ③ Déroulé souhaité (esquisse A/B/C, style de production) : facultatif — « souhaité » et pas
//   « généré », pour ne jamais confondre avec le « Déroulé généré » de la colonne de droite.
// ④ Générer la séance : SA cartouche en bas, avec le bouton uniquement (retouche 30/07).
// Les cartouches facultatives passent au vert quand elles sont remplies, mais ne clignotent jamais.
import { useCallback, useEffect, useRef, useState } from 'react'
import SplitPane from './SplitPane.jsx'
import JaugeAttente from './JaugeAttente.jsx'
import EtapeBadge from './EtapeBadge.jsx'
import ApportTexte from './contenus/ApportTexte.jsx'
import InfoGuide from './InfoGuide.jsx'
import HistoriqueVersions from './HistoriqueVersions.jsx'
import { aideSeances } from '../utils/aideSeances.js'
import { corpsHtml, imprimerApercu } from '../utils/apercuHtml.js'
import { apiFetch, detailPourEcran, lireReponse, messagePourEcran, refreshSession, TIMEOUT_STD, TIMEOUT_LONG } from '../utils/api.js'
import { showError } from '../errorDialog'
import { demanderConfirmation } from '../confirmDialog'
import { TYPES_CONTENUS } from '../utils/typesContenus.js'
import { IconPrint } from './icones.jsx'

// Identités de type (fichier commun) : le retour standard porte le vert séance ; le retour
// vers la séquence mère porte le violet séquence — on voit d'où l'on vient.
const TYPE_SEA = TYPES_CONTENUS.seance
const TYPE_SEQ = TYPES_CONTENUS.sequence

const MSG_ECHEC_GENERATION =
  'La génération de votre séance n\'a pas pu aboutir. Merci de réessayer.\n' +
  'Si le problème persiste, cliquez ici pour nous le signaler.'

// Les modes de séance et les styles de production ne sont plus écrits ici : ils sont LUS EN
// BASE (catalogues `seance_modes` / `seance_styles`, servis par /contenus/seances/formulaire).
// Le serveur valide sur les mêmes lignes que celles affichées ici — une seule vérité.

// Origine du texte de départ (étape ①) — pastille sur la LIGNE DU TITRE, toujours visible,
// cartouche repliée comme dépliée (demande utilisateur du 30/07). Une entrée par façon de
// remplir la zone (clavier = rien) ; la phrase complète reste en infobulle.
const SOURCES_TEXTE = {
  theme:       { label: 'Thème proposé par aSchool',        aide: 'Thème proposé à partir du programme officiel de votre niveau — modifiez-le librement, puis générez.' },
  competences: { label: 'Compétences proposées par aSchool', aide: 'Compétences proposées depuis le programme officiel de votre niveau, en lien avec votre thème — retouchez-les librement, une par ligne.' },
  materiel:    { label: 'Matériel proposé par aSchool',      aide: 'Matériel proposé d\'après votre thème et votre cadre — retouchez-le librement.' },
  contraintes: { label: 'Contraintes proposées par aSchool', aide: 'Contraintes proposées d\'après votre thème et votre cadre — retouchez-les librement.' },
  dictee:      { label: 'Texte issu de votre dictée',       aide: 'Texte issu de votre dictée — relisez-le, corrigez si besoin, puis générez.' },
  txt:         { label: 'Texte importé d\'un fichier',      aide: 'Texte importé depuis votre fichier.' },
  image:       { label: 'Texte extrait d\'une image',       aide: 'Texte extrait de votre image.' },
  pdf:         { label: 'Texte extrait d\'un PDF',          aide: 'Texte extrait de votre PDF.' },
}

const CARTE = { background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 10 }
// Sous-libellé DANS un groupe : COPIE des libellés de champ de l'écran Activité
// (text-xs font-medium text-gray-500) — petit, gris, casse normale. Le titre de groupe
// (section-title, majuscules) reste le seul niveau fort.
const LABEL = { fontSize: 12, fontWeight: 500, color: '#6b7280' }
// Titre de SOUS-GROUPE dans une cartouche (Esquisse du déroulé, Style de production) : le
// gras est réservé à ce niveau — les libellés de champ (A/B/C…) restent en LABEL normal.
const TITRE_SOUS_GROUPE = { fontSize: 12, fontWeight: 700, color: '#1e293b' }
const MENTION_OPTIONNEL = { fontWeight: 400, color: '#94a3b8' }
// Pastille résumé sur la ligne d'un titre de cartouche (choix faits, cartouche repliée).
const PASTILLE_RESUME = { fontSize: 12, fontWeight: 600, color: '#64748b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '2px 10px', flexShrink: 0 }
const CHAMP = { width: '100%', padding: '9px 12px', fontSize: 13, lineHeight: 1.6, color: '#1e293b', border: '1px solid #cbd5e1', borderRadius: 6, fontFamily: 'inherit', boxSizing: 'border-box', background: '#fff' }


// Titre de groupe : COPIE du patron des cartouches de l'écran Activité — pastille d'étape
// (EtapeBadge) + titre en classe `section-title` (majuscules, gras, filet bordeaux).
function TitreGroupe({ n, fait, actif, children }) {
  return (
    <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <EtapeBadge n={n} fait={fait} actif={actif} />
      <span style={{ display: 'inline-flex', alignItems: 'center', fontWeight: 700 }}>{children}</span>
    </div>
  )
}

// Bouton « Propose-moi… » d'un champ à UNE ligne (matériel, contraintes) — même habit que
// les boutons d'apport (btn-action, petite taille), sablier pendant l'appel (la jauge, elle,
// s'affiche sous le champ — règle IA : sablier ET jauge).
function BoutonPropose({ enCours, label, title, onClick, disabled }) {
  return (
    <button
      type="button"
      className="btn-action"
      title={title}
      onClick={onClick}
      disabled={disabled || enCours}
      style={{ fontSize: '0.75rem', padding: '0.32rem 0.65rem', ...(enCours ? { opacity: 0.6, cursor: 'wait' } : {}) }}
    >
      {enCours
        ? <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
        : <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5.68.68 1.16 1.46 1.41 2.5"/></svg>}
      {enCours ? 'Génération…' : label}
    </button>
  )
}

// Pastille radio maison (même motif que les boutons de mode de l'outil existant).
function Pastille({ actif, label, title, onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      title={title || label}
      style={{
        padding: '5px 12px', fontSize: 12, fontWeight: actif ? 700 : 400,
        border: `1.5px solid ${actif ? 'var(--bordeaux)' : '#e2e8f0'}`,
        borderRadius: 5, cursor: disabled ? 'default' : 'pointer',
        background: actif ? '#fff0f0' : '#f8fafc',
        color: actif ? 'var(--bordeaux)' : '#64748b',
      }}
    >
      {label}
    </button>
  )
}

// Frise du haut — même dessin que la frise de l'écran Activité (FriseProgression), 3 étapes
// alignées sur les 3 cartouches : Infos de base (obligatoire) → Affinage (facultatif : vert
// dès qu'un champ de ② ou ③ est rempli, mais jamais surligné « à faire ») → Générer. Le
// surlignage « étape courante » SAUTE donc l'Affinage : Infos de base complètes = Générer.
function FriseSeance({ infosOk, affinageFait, loading, resultat, nbActivites = 0 }) {
  const termine = !!resultat && !loading
  const etapes = [
    { n: 1, label: 'Infos de base', fait: !!infosOk },
    { n: 2, label: 'Affinage', fait: !!affinageFait },
    { n: 3, label: 'Générer', fait: termine },
  ]
  const courant = loading ? 2 : !infosOk ? 0 : termine ? -1 : 2
  return (
    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', rowGap: 8 }}>
      {etapes.map((e, i) => {
        const estCourant = i === courant
        const bg = e.fait ? '#16a34a' : estCourant ? 'var(--bordeaux)' : '#fff'
        const fg = (e.fait || estCourant) ? '#fff' : '#94a3b8'
        const bord = e.fait ? '#16a34a' : estCourant ? 'var(--bordeaux)' : '#cbd5e1'
        return (
          <span key={e.n} style={{ display: 'flex', alignItems: 'center' }}>
            {/* Le trait vert suit le CHEMIN OBLIGATOIRE : dès que les Infos de base sont
                complètes, la route vers Générer est ouverte (l'Affinage ne bloque rien). */}
            {i > 0 && (
              <span style={{ width: 30, height: 2, borderRadius: 2, margin: '0 9px',
                             background: infosOk ? '#16a34a' : '#e2e8f0' }} />
            )}
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                             display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                             fontSize: 12, fontWeight: 800, fontVariantNumeric: 'tabular-nums',
                             background: bg, color: fg, border: `1.5px solid ${bord}`,
                             boxShadow: estCourant ? '0 0 0 4px rgba(140,29,64,0.14)' : 'none' }}>
                {e.fait ? '✓' : e.n}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap',
                             color: estCourant ? '#1e293b' : e.fait ? '#64748b' : '#94a3b8' }}>
                {e.label}
              </span>
            </span>
          </span>
        )
      })}
      {/* Indicateur ACTIVITÉS, derrière « Générer » (demande 30/07) : croix ROUGE
          « Aucune activité » tant que rien n'est accroché à la séance, rond VERT avec le
          NOMBRE dès la première (« 3 activités »). Purement informatif — jamais bloquant. */}
      <span style={{ display: 'flex', alignItems: 'center' }}>
        <span style={{ width: 30, height: 2, borderRadius: 2, margin: '0 9px',
                       background: nbActivites > 0 ? '#16a34a' : '#e2e8f0' }} />
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          title={nbActivites > 0
            ? 'Les activités rattachées à cette séance (cartouche 5)'
            : 'Aucune activité rattachée à cette séance — optionnel, la cartouche 5 sert à en accrocher'}>
          <span style={{ width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                         display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                         fontSize: 12, fontWeight: 800, fontVariantNumeric: 'tabular-nums',
                         background: nbActivites > 0 ? '#16a34a' : '#dc2626', color: '#fff',
                         border: `1.5px solid ${nbActivites > 0 ? '#16a34a' : '#dc2626'}` }}>
            {nbActivites > 0 ? nbActivites : '✕'}
          </span>
          <span style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap',
                         color: nbActivites > 0 ? '#64748b' : '#dc2626' }}>
            {nbActivites > 0 ? `${nbActivites} activité${nbActivites > 1 ? 's' : ''}` : 'Aucune activité'}
          </span>
        </span>
      </span>
    </div>
  )
}

// `onCreerActivite(seanceId)` : ouvre l'écran Activité en création RATTACHÉE à cette séance.
// `onOuvrirActivite(a)` : rouvre une activité liée dans son écran (reprise complète).
// `onRetourSequence` (nullable) : posé quand la séance est ouverte DEPUIS l'écran Séquence
// (la boucle séquence→séance→activités, 30/07) — le bouton retour ramène alors à la
// séquence relue en base, pas à la liste des séances.
export default function SeanceEcran({ seance, matiere, niveau, onNavigate, onCreerActivite, onOuvrirActivite, onRetourSequence = null }) {
  // ── Le formulaire entier (reprise complète si une séance est rouverte) ──
  const [theme, setTheme] = useState(seance?.titre || '')
  const [contexte, setContexte] = useState(seance?.contexte || '')
  const [dureeSaisie, setDureeSaisie] = useState(seance?.duree ? String(seance.duree) : '')
  const [mode, setMode] = useState(seance?.mode || null)          // AUCUN mode pré-coché (règle maison)
  // Compétences = UNE ZONE DE TEXTE, une compétence par ligne (décision 30/07 — même
  // grammaire que le thème : aSchool propose, le prof corrige). En base ça reste une liste :
  // découpée à l'envoi, recollée à la reprise.
  const [competencesTexte, setCompetencesTexte] = useState(
    Array.isArray(seance?.competences) ? seance.competences.join('\n') : ''
  )
  const [materiel, setMateriel] = useState(seance?.materiel || '')
  const [esquisse, setEsquisse] = useState({
    a: seance?.esquisse?.a || '', b: seance?.esquisse?.b || '', c: seance?.esquisse?.c || '',
  })
  const [contraintes, setContraintes] = useState(seance?.contraintes || '')
  const [style, setStyle] = useState(seance?.style || null)       // AUCUN style pré-coché

  // ── Génération + règle 0 (mêmes états que l'écran Activité) ──
  const [resultat, setResultat] = useState(seance?.resultat || null)
  const [loading, setLoading] = useState(false)
  const [baseReplie, setBaseReplie] = useState(false)       // repli manuel de la cartouche ① Infos de base (affichage éphémère)
  const [contenuReplie, setContenuReplie] = useState(false) // repli manuel de la cartouche ② Contenu pédagogique (même geste)
  const [derouleReplie, setDerouleReplie] = useState(false) // repli manuel de la cartouche ③ Déroulé souhaité (même geste)
  const [sourceNote, setSourceNote] = useState(null)      // origine du texte de départ ('txt'|'image'|'pdf'|'dictee'|'theme') — pastille du titre ①
  const [sourceNoteComp, setSourceNoteComp] = useState(null) // origine de la zone Compétences — pastille sur la ligne de son libellé (②)
  const [sourceNoteMat, setSourceNoteMat] = useState(null)   // origine du champ Matériel ('materiel' | null) — pastille sur sa ligne de libellé
  const [sourceNoteCont, setSourceNoteCont] = useState(null) // origine du champ Contraintes ('contraintes' | null) — idem
  const [matLoading, setMatLoading] = useState(false)        // « Propose-moi du matériel » en cours (sablier + jauge)
  const [contLoading, setContLoading] = useState(false)      // « Propose-moi des contraintes » en cours (sablier + jauge)
  const [esqLoading, setEsqLoading] = useState(null)         // phase de l'esquisse en cours de proposition ('a'|'b'|'c'|null)
  const [esqNotes, setEsqNotes] = useState({ a: false, b: false, c: false })  // zone proposée par aSchool → pastille
  // Catalogues du formulaire, LUS EN BASE (aucune liste en dur ici). Tant qu'ils ne sont pas
  // arrivés, les choix ne s'affichent pas : l'écran ne montre jamais une liste inventée.
  const [modes, setModes] = useState([])
  const [styles, setStyles] = useState([])
  const [bornesDuree, setBornesDuree] = useState(null)   // { min, max } — réglages lus en base
  const [catalogueRate, setCatalogueRate] = useState(false)
  const [seanceId, setSeanceId] = useState(seance?.id || null)
  const [historiqueOuvert, setHistoriqueOuvert] = useState(false)   // fenêtre « Historique des versions »
  const [enregistrement, setEnregistrement] = useState(seance ? 'ok' : null)   // null | 'ok' | 'echec'
  const resultatRef = useRef(null)

  // ── Activités RATTACHÉES à la séance (activites.seance_id) — la zone n'existe que
  // lorsque la séance EST en base (seanceId posé par l'auto-save ou la reprise). ──
  const [activitesLiees, setActivitesLiees] = useState([])
  const [actReplie, setActReplie] = useState(false)     // repli manuel de la cartouche (même geste)
  const [derouleCache, setDerouleCache] = useState(false) // colonne « Déroulé généré » escamotée (bouton à droite de la frise)
  const [selecteur, setSelecteur] = useState(false)     // fenêtre « Ajouter une activité existante »
  const [catalogue, setCatalogue] = useState(null)      // toutes mes activités (chargées à l'ouverture de la fenêtre)
  const [voirToutes, setVoirToutes] = useState(false)   // lever le filtre couple courant dans la fenêtre

  // Durée = UN champ libre en minutes (la combo de durées courantes a été supprimée le 30/07).
  // Les bornes viennent du SERVEUR (réglages en base) : cet écran ne décide plus tout seul de
  // ce qu'il accepte — il applique exactement ce que le serveur appliquera. Tant qu'elles ne
  // sont pas arrivées, la génération n'est pas offerte : on ne valide pas au jugé.
  const duree = parseInt(dureeSaisie, 10) || 0
  const dureeOk = !!bornesDuree && duree >= bornesDuree.min && duree <= bornesDuree.max
  const texteOk = !!theme.trim()
  const cadreOk = !!mode && dureeOk
  const pretAGenerer = texteOk && cadreOk
  // Remplissage des cartouches FACULTATIVES ② et ③ — pilote leur pastille verte et l'étape
  // « Affinage » de la frise ; ne conditionne jamais la génération.
  const contenuFait = !!competencesTexte.trim() || !!materiel.trim() || !!contraintes.trim()
  const derouleFait = !!(esquisse.a.trim() || esquisse.b.trim() || esquisse.c.trim() || style)
  // Résumés des cartouches ② et ③ quand elles sont REPLIÉES : pastilles face au titre.
  const nbCompetences = competencesTexte.split('\n').map(l => l.trim()).filter(Boolean).length
  const esquisseLettres = ['a', 'b', 'c'].filter(k => esquisse[k].trim()).map(k => k.toUpperCase())

  // ── Les deux « Propose-moi… » (principe maison : aSchool propose tout, le prof corrige).
  // La mécanique commune (confirmation, sablier + jauge, pastille d'origine) vit dans
  // ApportTexte ; ici seulement l'appel serveur propre à chaque zone. ──
  const proposerTheme = {
    label: 'Propose-moi un thème',
    title: "aSchool écrit pour vous un thème de séance tiré du programme officiel de votre niveau — vous le retouchez librement, puis Générer.",
    jauge: 'aSchool lit le programme officiel de votre niveau et prépare un thème de séance…',
    note: 'theme',
    action: async () => {
      try {
        const res = await apiFetch('/api/contenus/seances/proposer-theme', {
          method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}),
        }, TIMEOUT_LONG)
        const d = await lireReponse(res)
        if (d.available && d.texte) return d.texte
        showError(d.message || 'Pas de proposition possible pour le moment (programme officiel pas encore chargé pour votre niveau).\n\nDécrivez votre thème dans la zone de texte — ou dictez-le avec le micro.')
        return null
      } catch (err) {
        showError(`Proposition de thème impossible.\n\n${messagePourEcran(err)}`)
        return null
      }
    },
  }
  // « Propose-moi… » des champs à UNE ligne (matériel, contraintes) — mêmes gestes que les
  // zones de texte : garde thème, confirmation de remplacement, sablier + jauge, pastille.
  async function proposerLigne({ url, valeur, setValeur, setNote, note, setLoad, erreur }) {
    if (!theme.trim()) {
      showError('Décrivez d\'abord le thème de la séance (cartouche 1) : la proposition s\'appuie dessus.')
      return
    }
    if (valeur.trim() && !await demanderConfirmation({
      titre: 'Remplacer le texte actuel ?',
      message: 'Le contenu de la zone sera perdu.',
      confirmLabel: 'Remplacer',
    })) return
    setLoad(true)
    setNote(null)
    try {
      const res = await apiFetch(url, {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, mode, duree: duree || null, contexte }),
      }, TIMEOUT_LONG)
      const d = await lireReponse(res)
      if (d.available && d.texte) {
        setValeur(d.texte)
        setNote(note)
      } else {
        showError(d.message || 'Pas de proposition possible pour le moment. Remplissez le champ à la main.')
      }
    } catch (err) {
      showError(`${erreur}\n\n${messagePourEcran(err)}`)
    } finally {
      setLoad(false)
    }
  }

  // « Propose-moi cette phase » d'une zone de l'esquisse (A, B ou C) — la proposition est
  // ancrée sur le thème/cadre ET sur les autres zones déjà remplies (cohérence du déroulé).
  async function proposerEsquisse(phase, phaseLabel) {
    if (esqLoading) return
    if (!theme.trim()) {
      showError('Décrivez d\'abord le thème de la séance (cartouche 1) : la proposition s\'appuie dessus.')
      return
    }
    if (esquisse[phase].trim() && !await demanderConfirmation({
      titre: 'Remplacer le texte actuel ?',
      message: 'Le contenu de la zone sera perdu.',
      confirmLabel: 'Remplacer',
    })) return
    setEsqLoading(phase)
    setEsqNotes(prev => ({ ...prev, [phase]: false }))
    try {
      const res = await apiFetch('/api/contenus/seances/proposer-esquisse', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, mode, duree: duree || null, contexte, phase, esquisse }),
      }, TIMEOUT_LONG)
      const d = await lireReponse(res)
      if (d.available && d.texte) {
        setEsquisse(prev => ({ ...prev, [phase]: d.texte }))
        setEsqNotes(prev => ({ ...prev, [phase]: true }))
      } else {
        showError(d.message || 'Pas de proposition possible pour le moment. Remplissez la zone à la main.')
      }
    } catch (err) {
      showError(`Proposition impossible pour la phase « ${phaseLabel} ».\n\n${messagePourEcran(err)}`)
    } finally {
      setEsqLoading(null)
    }
  }

  // ── Modes et styles : lus au serveur, qui les lit en base. Une panne ne fait pas semblant
  // d'une liste vide — les choix disparaissent et un « Réessayer » prend leur place. ──
  const chargerCatalogues = useCallback(async () => {
    setCatalogueRate(false)
    try {
      const d = await lireReponse(await apiFetch('/api/contenus/seances/formulaire', { credentials: 'include' }, TIMEOUT_STD))
      setModes(d.modes || [])
      setStyles(d.styles || [])
      setBornesDuree({ min: d.duree_min, max: d.duree_max })
    } catch (err) {
      setCatalogueRate(true)
      showError(messagePourEcran(err))
    }
  }, [])

  useEffect(() => { chargerCatalogues() }, [chargerCatalogues])

  // ── Activités de la séance : lecture + rattacher + détacher (jamais supprimer). ──
  async function chargerActivitesLiees(id) {
    try {
      const d = await lireReponse(await apiFetch(`/api/contenus/seances/${id}/activites`, { credentials: 'include' }, TIMEOUT_STD))
      setActivitesLiees(d.activites || [])
    } catch (err) {
      showError(`Impossible de charger les activités de cette séance.\n\n${messagePourEcran(err)}`)
    }
  }

  useEffect(() => {
    if (seanceId) chargerActivitesLiees(seanceId)
  }, [seanceId])

  async function detacherActivite(a) {
    if (!await demanderConfirmation({
      titre: 'Détacher cette activité ?',
      message: `« ${a.titre} » ne sera plus rattachée à cette séance.\n\nElle reste dans vos activités — rien n'est supprimé.`,
      confirmLabel: 'Détacher',
    })) return
    try {
      await lireReponse(await apiFetch(`/api/contenus/activites/${a.id}/seance`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ seance_id: null }),
      }, TIMEOUT_STD))
      await chargerActivitesLiees(seanceId)
    } catch (err) {
      showError(`Le détachement n'a pas abouti.\n\n${messagePourEcran(err)}`)
    }
  }

  async function rattacherActivite(row) {
    // Une activité n'a qu'UN parent : déjà rangée ailleurs = elle déménage, après confirmation.
    if (row.parent && row.parent.id !== seanceId) {
      const nom = row.parent.titre ? `« ${row.parent.titre} »` : 'une autre séance'
      if (!await demanderConfirmation({
        titre: 'Déplacer cette activité ?',
        message: `Elle est déjà rattachée à la séance ${nom}.\n\nUne activité n'a qu'une seule séance : elle quittera l'autre pour venir ici.`,
        confirmLabel: 'Déplacer',
      })) return
    }
    try {
      await lireReponse(await apiFetch(`/api/contenus/activites/${row.id}/seance`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ seance_id: seanceId }),
      }, TIMEOUT_STD))
      setSelecteur(false)
      await chargerActivitesLiees(seanceId)
    } catch (err) {
      showError(`Le rattachement n'a pas abouti.\n\n${messagePourEcran(err)}`)
    }
  }

  async function ouvrirSelecteur() {
    setSelecteur(true)
    setVoirToutes(false)
    setCatalogue(null)
    try {
      const d = await lireReponse(await apiFetch('/api/mes-contenus', { credentials: 'include' }, TIMEOUT_STD))
      setCatalogue((d.contenus || []).filter(c => c.type === 'activite'))
    } catch (err) {
      setSelecteur(false)
      showError(`Impossible de charger vos activités.\n\n${messagePourEcran(err)}`)
    }
  }

  const proposerCompetences = {
    label: 'Propose-moi des compétences',
    title: "aSchool propose 3 à 5 compétences du programme officiel de votre niveau, en lien avec votre thème — vous les retouchez librement, une par ligne.",
    jauge: 'aSchool lit le programme officiel de votre niveau et cherche les compétences liées à votre thème…',
    note: 'competences',
    avant: () => {
      if (theme.trim()) return true
      showError('Décrivez d\'abord le thème de la séance (cartouche 1) : les compétences proposées s\'appuient dessus.')
      return false
    },
    action: async () => {
      try {
        const res = await apiFetch('/api/contenus/seances/proposer-competences', {
          method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ theme }),
        }, TIMEOUT_LONG)
        const d = await lireReponse(res)
        if (d.available && Array.isArray(d.competences) && d.competences.length > 0) return d.competences.join('\n')
        showError(d.message || 'Pas de proposition possible pour le moment (programme officiel pas encore chargé pour votre niveau).\n\nÉcrivez vos compétences dans la zone, une par ligne.')
        return null
      } catch (err) {
        showError(`Proposition de compétences impossible.\n\n${messagePourEcran(err)}`)
        return null
      }
    },
  }

  function corpsFormulaire() {
    return {
      theme: theme.trim(),
      contexte: contexte.trim(),
      duree,
      mode,
      // La zone de texte → la liste attendue en base : une ligne = une compétence.
      competences: competencesTexte.split('\n').map(l => l.trim()).filter(Boolean),
      materiel: materiel.trim(),
      esquisse,
      contraintes: contraintes.trim(),
      style: style || null,
    }
  }

  // ── Règle 0 : l'écriture en base suit CHAQUE génération réussie ──
  async function sauver(complet) {
    const corps = { ...corpsFormulaire(), resultat: complet }
    try {
      if (seanceId) {
        await lireReponse(await apiFetch(`/api/contenus/seances/${seanceId}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps),
        }, TIMEOUT_STD))
      } else {
        const d = await lireReponse(await apiFetch('/api/contenus/seances', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps),
        }, TIMEOUT_STD))
        setSeanceId(d.id)
      }
      setEnregistrement('ok')
    } catch {
      // Un échec d'auto-save DOIT se voir (règle 0 : rien n'attend en mémoire « pour plus tard »).
      setEnregistrement('echec')
      showError("Votre séance est affichée mais n'a pas pu être enregistrée.\n\nCliquez sur « Réessayer l'enregistrement » en haut de l'écran.")
    }
  }

  // ── Génération en STREAMING — même mécanique que l'écran Activité (SSE delta/error/done). ──
  async function generer() {
    if (!theme.trim()) {
      showError('Décrivez d\'abord le thème ou l\'objectif de la séance.')
      return
    }
    if (!mode) {
      showError('Choisissez un mode de séance avant de générer.')
      return
    }
    if (!dureeOk) {
      showError(bornesDuree
        ? `Indiquez une durée entre ${bornesDuree.min} et ${bornesDuree.max} minutes.`
        : "Les réglages de l'écran n'ont pas pu être chargés. Réessayez de charger la page.")
      return
    }
    setResultat(null)
    setEnregistrement(null)
    setLoading(true)
    try {
      const opts = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(corpsFormulaire()),
      }
      let res = await fetch('/api/contenus/seances/generer', opts)
      if (res.status === 401 && await refreshSession()) {
        res = await fetch('/api/contenus/seances/generer', opts)
      }
      if (!res.ok || !res.body) {
        const err = await res.json().catch(() => ({}))
        const message = detailPourEcran(err)   // un 422 renvoie un tableau : filtré, jamais affiché
        if (message) showError(message)
        else showError(MSG_ECHEC_GENERATION, { feedback: true })
        return
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let tampon = '', complet = '', erreurFlux = false, termine = false, refIncident = null
      setResultat('')
      setTimeout(() => resultatRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        tampon += decoder.decode(value, { stream: true })
        let sep
        while ((sep = tampon.indexOf('\n\n')) >= 0) {
          const bloc = tampon.slice(0, sep)
          tampon = tampon.slice(sep + 2)
          const evt  = (bloc.split('\n').find(l => l.startsWith('event:')) || '').slice(6).trim()
          const data = (bloc.split('\n').find(l => l.startsWith('data:'))  || '').slice(5).trim()
          if (evt === 'delta') {
            try { complet += JSON.parse(data).text; setResultat(complet) } catch { /* bloc partiel ignoré */ }
          } else if (evt === 'error') {
            erreurFlux = true
            try { refIncident = JSON.parse(data).ref || null } catch { /* pas de réf */ }
          } else if (evt === 'done') {
            termine = true
          }
        }
      }

      if (erreurFlux || !termine || !complet) {
        setResultat(null)
        showError(MSG_ECHEC_GENERATION, { feedback: true, ref: refIncident })
        return
      }

      // RÈGLE 0 : la génération réussie s'écrit TOUT DE SUITE en base (tables neuves).
      await sauver(complet)
    } catch (e) {
      console.error('génération séance (Mes contenus) :', e)
      setResultat(null)
      showError(MSG_ECHEC_GENERATION, { feedback: true })
    } finally {
      setLoading(false)
    }
  }

  const titreBarre = seance
    ? `Reprise : ${seance.titre || 'séance'}`
    : 'Nouvelle séance'

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

      {/* ── Barre du haut : retour + titre + couple + état d'enregistrement (règle 0 visible) ── */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', flexShrink: 0, alignItems: 'center', gap: 8 }}>
        {/* Retour : flèche SVG grande et pleine (demande utilisateur 30/07). Standard =
            « Mes séances » en vert séance ; depuis une séquence = violet séquence. */}
        <button
          type="button"
          onClick={() => (onRetourSequence ? onRetourSequence() : onNavigate('contenus-seances'))}
          title={onRetourSequence
            ? 'Revenir à la séquence — son plan se met à jour (séance générée ou non)'
            : 'Revenir à la page Mes séances'}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 7, margin: '0 0 0 8px', fontSize: 13, fontWeight: 600,
                   color: onRetourSequence ? TYPE_SEQ.accent : TYPE_SEA.accent,
                   background: onRetourSequence ? TYPE_SEQ.fond : TYPE_SEA.fond,
                   border: `1px solid ${onRetourSequence ? TYPE_SEQ.bord : TYPE_SEA.bord}`,
                   borderRadius: 6, padding: '5px 12px', cursor: 'pointer', flexShrink: 0 }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          {onRetourSequence ? 'Retour à la séquence' : 'Mes séances'}
        </button>
        <div style={{ padding: '10px 12px', fontSize: '13px', fontWeight: 700, color: 'var(--bordeaux)', borderBottom: '2px solid var(--bordeaux)', marginBottom: '-1px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {titreBarre}
        </div>
        {/* Le couple ne se réaffiche PAS ici : le header bleu au-dessus est son unique
            afficheur (doublon retiré le 30/07 sur demande utilisateur). */}

        {enregistrement === 'ok' && (
          <span title="Votre séance est écrite en base — retrouvez-la dans Mes contenus"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600, color: '#166534', background: '#dcfce7', border: '1px solid #86efac', borderRadius: 99, padding: '3px 10px', flexShrink: 0, marginLeft: 'auto', marginRight: 8 }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Enregistrée
          </span>
        )}
        {enregistrement === 'echec' && (
          <button
            type="button"
            onClick={() => resultat && sauver(resultat)}
            title="L'enregistrement automatique a échoué — cliquez pour réessayer"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600, color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 99, padding: '3px 10px', cursor: 'pointer', flexShrink: 0, marginLeft: 'auto', marginRight: 8 }}
          >
            Réessayer l'enregistrement
          </button>
        )}
      </div>

      {/* ── Frise de progression — même dessin que l'écran Activité. À sa DROITE, le bouton
          qui escamote/raffiche la colonne « Déroulé généré » (demande 30/07). ── */}
      <div style={{ padding: '14px 20px 12px', borderBottom: '1px solid #e2e8f0', flexShrink: 0, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <FriseSeance infosOk={pretAGenerer} affinageFait={contenuFait || derouleFait} loading={loading} resultat={resultat} nbActivites={activitesLiees.length} />
        </div>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => setDerouleCache(c => !c)}
          title={derouleCache
            ? 'Réafficher la colonne « Déroulé généré » à droite'
            : 'Cacher la colonne « Déroulé généré » — le formulaire prend toute la largeur'}
          style={{ flexShrink: 0, marginLeft: 'auto' }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {derouleCache
              ? <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
              : <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>}
          </svg>
          {derouleCache ? 'Afficher le déroulé' : 'Cacher le déroulé'}
        </button>
        {/* L'historique promis par l'infobulle de génération, enfin lisible : chaque jalon a
            figé une version, celle-ci s'ouvre et se restaure (règle 0). Disponible dès que la
            séance existe en base. */}
        {seanceId && (
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setHistoriqueOuvert(true)}
            title="Historique : relire les versions précédentes de cette séance et revenir à l'une d'elles. Rien n'est jamais supprimé."
            style={{ flexShrink: 0 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/><polyline points="12 7 12 12 15 14"/></svg>
            Historique
          </button>
        )}
      </div>

      {historiqueOuvert && seanceId && (
        <HistoriqueVersions
          base={`/api/contenus/seances/${seanceId}`}
          variante="style"
          titre={theme.trim() || 'Votre séance'}
          aide={aideSeances('historique')}
          onFermer={() => setHistoriqueOuvert(false)}
          onRestaure={d => { setResultat(d.resultat); setStyle(d.style); setEnregistrement('ok') }}
        />
      )}

      <div className="creer-corps">
        {(() => {
          // ── Colonne GAUCHE : le formulaire, dans la chronologie validée (30/07). ──
          const formulaire = (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

              {/* ① Infos de base — TOUT l'obligatoire regroupé (thème + contexte + mode + durée,
                  décision du 30/07). « i » d'aide + chevron plier/déplier (mêmes gestes que
                  les cartouches de l'écran Activité). */}
              <section style={CARTE}>
                {/* En-tête de la cartouche — COPIE du placement de l'activité : titre + « i » +
                    chevron à gauche, la rangée des boutons d'apport EN HAUT À DROITE, face au
                    titre. Sur écran étroit, la rangée passe dessous. */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <TitreGroupe n={1} fait={pretAGenerer} actif={!pretAGenerer && !loading}>Infos de base</TitreGroupe>
                    <InfoGuide
                      titre="Infos de base"
                      court="L'obligatoire pour générer : le thème, le mode et la durée — plus le contexte de votre classe si vous voulez."
                      long={"Décrivez le THÈME ou l'objectif de la séance : c'est lui qui guide toute la génération. Remplissez la zone comme vous voulez : au clavier, en important un fichier TXT / une image / un PDF, en dictant au micro — ou laissez « Propose-moi un thème » l'écrire depuis le programme officiel de votre niveau.\n\nLe CONTEXTE RAPIDE (optionnel) décrit votre classe : effectif, ambiance, ce qui a bloqué la dernière fois… Il affine la séance, et c'est lui qui donne tout son sens au mode Remédiation.\n\nChoisissez ensuite le MODE (rien n'est pré-coché) et indiquez la DURÉE en minutes" + (bornesDuree ? ` (${bornesDuree.min} à ${bornesDuree.max})` : "") + ". Thème, mode et durée sont les trois champs nécessaires pour générer : la cartouche passe au vert quand ils sont là."}
                    />
                    <button
                      type="button"
                      onClick={() => setBaseReplie(r => !r)}
                      title={baseReplie ? 'Déplier la cartouche' : 'Replier la cartouche'}
                      style={{ width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ transition: 'transform 0.2s', transform: baseReplie ? 'rotate(-90deg)' : 'none' }}>
                        <polyline points="6 9 12 15 18 9"/>
                      </svg>
                    </button>
                    {/* Pastille « origine du texte » — SUR LA LIGNE DU TITRE, toujours affichée
                        une fois le choix fait (fichier, image, PDF, dictée, thème proposé),
                        cartouche repliée comme dépliée. Effacée seulement si la zone est vidée. */}
                    {sourceNote && SOURCES_TEXTE[sourceNote] && (
                      <span
                        title={SOURCES_TEXTE[sourceNote].aide}
                        style={{ fontSize: 12, fontWeight: 600, color: '#1d4ed8', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 99, padding: '2px 10px', flexShrink: 0 }}
                      >
                        {SOURCES_TEXTE[sourceNote].label}
                      </span>
                    )}
                    {/* Pastille « contexte rapide » — TOUJOURS affichée, elle bascule toute
                        seule : gris « sans contexte rapide » (champ vide) / vert « avec
                        contexte rapide » (champ rempli). Visible repliée comme dépliée. */}
                    <span
                      title={contexte.trim()
                        ? 'Un contexte rapide est fourni — aSchool en tient compte pour adapter la séance.'
                        : 'Aucun contexte rapide — champ optionnel de cette cartouche : votre classe en une phrase.'}
                      style={{
                        fontSize: 12, fontWeight: 600, borderRadius: 99, padding: '2px 10px', flexShrink: 0,
                        color: contexte.trim() ? '#166534' : '#64748b',
                        background: contexte.trim() ? '#dcfce7' : '#f1f5f9',
                        border: `1px solid ${contexte.trim() ? '#86efac' : '#e2e8f0'}`,
                      }}
                    >
                      {contexte.trim() ? 'avec contexte rapide' : 'sans contexte rapide'}
                    </span>
                    {/* Pastilles des CHOIX FAITS — le mode et la durée choisis restent affichés
                        sur la ligne du titre, cartouche repliée comme dépliée. */}
                    {mode && (
                      <span
                        title={`Mode choisi : ${(modes.find(m => m.code === mode) || {}).label || mode}`}
                        style={{ fontSize: 12, fontWeight: 600, color: '#64748b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '2px 10px', flexShrink: 0 }}
                      >
                        {(modes.find(m => m.code === mode) || {}).label || mode}
                      </span>
                    )}
                    {duree > 0 && (
                      <span
                        title="Durée choisie pour la séance"
                        style={{ fontSize: 12, fontWeight: 600, color: '#64748b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '2px 10px', flexShrink: 0 }}
                      >
                        {duree} min
                      </span>
                    )}
                  </div>
                  {/* Même procédé d'apport que la zone texte de l'activité : TXT / Image / PDF /
                      Dicter (copiés tels quels) + « Propose-moi un thème » (version séance).
                      Replier CACHE la rangée sans la démonter (display:none) : son état interne
                      survit au pliage, comme l'activité. */}
                  <div style={{ display: baseReplie ? 'none' : 'block', marginLeft: 'auto', minWidth: 0 }}>
                    <ApportTexte texte={theme} onChange={setTheme} onSourceNote={setSourceNote} proposer={proposerTheme} disabled={loading} />
                  </div>
                </div>
                {!baseReplie && (<>
                <label style={LABEL}>
                  Thème / objectif de la séance
                  <InfoGuide
                    titre="Thème / objectif de la séance"
                    court="Décrivez ce que la séance doit travailler — c'est lui qui guide toute la génération."
                    long={"Écrivez le thème ou l'objectif comme vous le diriez : « le récit d'aventure », « comprendre les fractions », « préparer l'exposé »…\n\nRemplissez la zone comme vous voulez : au clavier, en important un fichier TXT / une image / un PDF, en dictant au micro — ou laissez « Propose-moi un thème » l'écrire depuis le programme officiel de votre niveau."}
                  />
                </label>
                <textarea
                  value={theme}
                  onChange={e => setTheme(e.target.value)}
                  placeholder={"Décrivez le thème ou l'objectif de la séance…\n— ou importez un fichier TXT, une image scannée ou un PDF\n— ou dictez avec le micro\n— ou laissez « Propose-moi un thème » l'écrire à votre place"}
                  rows={4}
                  disabled={loading}
                  style={{ ...CHAMP, resize: 'vertical' }}
                />
                <label style={LABEL}>
                  Contexte rapide <span style={{ fontWeight: 400, color: '#94a3b8' }}>(optionnel)</span>
                  <InfoGuide
                    titre="Contexte rapide"
                    court="Votre classe en une phrase : effectif, ambiance, ce qui a bloqué…"
                    long={"Optionnel : décrivez votre classe telle qu'elle est — effectif, ambiance, ce qui a bloqué la dernière fois, ce qui marche bien avec eux…\n\naSchool en tient compte pour adapter la séance, et c'est ce contexte qui donne tout son sens au mode Remédiation."}
                  />
                </label>
                <input
                  type="text"
                  value={contexte}
                  onChange={e => setContexte(e.target.value)}
                  placeholder="Ex : groupe plutôt agité en fin de journée ; la dernière séance est mal passée pour la moitié d'entre eux…"
                  disabled={loading}
                  style={CHAMP}
                />
                {/* Mode ET durée sur la MÊME ligne, chacun avec SON libellé au-dessus de son
                    champ — rangés dans les Infos de base depuis le regroupement du 30/07. */}
                <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <label style={LABEL}>Mode de séance</label>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {catalogueRate
                        ? <button type="button" onClick={chargerCatalogues} className="btn-secondary" style={{ fontSize: 12, padding: '5px 12px' }}>Réessayer</button>
                        : modes.map(m => (
                            <Pastille key={m.code} actif={mode === m.code} label={m.label} title={m.description}
                              onClick={() => setMode(m.code)} disabled={loading} />
                          ))}
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <label style={LABEL}>Durée</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {/* Mêmes mensurations que les pastilles de mode voisines (police 12,
                          padding 5px, bordure 1.5px, rayon 5) — même hauteur de ligne. */}
                      <input
                        type="number"
                        min={bornesDuree?.min}
                        max={bornesDuree?.max}
                        value={dureeSaisie}
                        onChange={e => setDureeSaisie(e.target.value)}
                        placeholder="minutes"
                        disabled={loading || !bornesDuree}
                        title={bornesDuree
                          ? `Durée de la séance en minutes — entre ${bornesDuree.min} et ${bornesDuree.max}`
                          : 'Durée de la séance en minutes'}
                        style={{ width: 90, padding: '5px 10px', fontSize: 12, color: '#1e293b',
                                 border: '1.5px solid #e2e8f0', borderRadius: 5, background: '#fff',
                                 fontFamily: 'inherit', boxSizing: 'border-box' }}
                      />
                      <span style={{ fontSize: 12, color: '#64748b' }}>min</span>
                    </div>
                  </div>
                </div>
                </>)}
              </section>

              {/* ② Contenu pédagogique (facultatif) : compétences + matériel + contraintes —
                  regroupement du 30/07 (ex-cartouches « Ce qu'on vise » et « Ce qu'il faut
                  prévoir », plus les contraintes de l'ex-« Déroulé dans le temps »). */}
              <section style={CARTE}>
                {/* En-tête de la cartouche — mêmes gestes que la ① : titre + « i » d'aide +
                    chevron plier/déplier. */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  <TitreGroupe n={2} fait={contenuFait} actif={false}>Contenu pédagogique</TitreGroupe>
                  <InfoGuide
                    titre="Contenu pédagogique"
                    court="Compétences visées, matériel, contraintes — tout est facultatif, la cartouche passe au vert dès qu'un champ est rempli."
                    long={"Les COMPÉTENCES / ATTENDUS : ce que les élèves doivent savoir faire à la fin (le thème de la cartouche 1, lui, dit de quoi parle la séance). Une compétence par ligne, remplie comme vous voulez : au clavier, en important un fichier TXT / une image / un PDF, en dictant au micro — ou laissez « Propose-moi des compétences » les écrire depuis le programme officiel, en lien avec votre thème. Sans compétence listée, aSchool s'appuie sur le thème et le programme officiel de votre niveau.\n\nLe MATÉRIEL nécessaire et vos CONTRAINTES / consignes spéciales (matériel imposé, élève à part, rituel de classe…) sont pris en compte dans le déroulé.\n\nTout est facultatif : rien ici ne bloque la génération."}
                  />
                  <button
                    type="button"
                    onClick={() => setContenuReplie(r => !r)}
                    title={contenuReplie ? 'Déplier la cartouche' : 'Replier la cartouche'}
                    style={{ width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ transition: 'transform 0.2s', transform: contenuReplie ? 'rotate(-90deg)' : 'none' }}>
                      <polyline points="6 9 12 15 18 9"/>
                    </svg>
                  </button>
                  {/* Repliée : la ligne résumé — ce qui est rempli, en pastilles (survol = le contenu). */}
                  {contenuReplie && (<>
                    {nbCompetences > 0 && (
                      <span title={competencesTexte} style={PASTILLE_RESUME}>
                        {nbCompetences} compétence{nbCompetences > 1 ? 's' : ''}
                      </span>
                    )}
                    {!!materiel.trim() && <span title={materiel} style={PASTILLE_RESUME}>Matériel</span>}
                    {!!contraintes.trim() && <span title={contraintes} style={PASTILLE_RESUME}>Contraintes</span>}
                    {!contenuFait && (
                      <span title="Cartouche facultative — rien n'y est rempli pour l'instant" style={PASTILLE_RESUME}>rien de renseigné</span>
                    )}
                  </>)}
                </div>
                {!contenuReplie && (<>
                {/* Zone Compétences — MÊME GRAMMAIRE que le thème de ① (décision 30/07) :
                    libellé + pastille d'origine à gauche, la rangée des 5 boutons d'apport à
                    droite (« Propose-moi des compétences », ancré sur le thème), la zone de
                    texte dessous — une compétence par ligne, le prof corrige librement. */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <label style={LABEL}>Compétences / attendus</label>
                    {sourceNoteComp && SOURCES_TEXTE[sourceNoteComp] && (
                      <span
                        title={SOURCES_TEXTE[sourceNoteComp].aide}
                        style={{ fontSize: 12, fontWeight: 600, color: '#1d4ed8', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 99, padding: '2px 10px', flexShrink: 0 }}
                      >
                        {SOURCES_TEXTE[sourceNoteComp].label}
                      </span>
                    )}
                  </div>
                  <div style={{ marginLeft: 'auto', minWidth: 0 }}>
                    <ApportTexte texte={competencesTexte} onChange={setCompetencesTexte} onSourceNote={setSourceNoteComp} proposer={proposerCompetences} disabled={loading} />
                  </div>
                </div>
                <textarea
                  value={competencesTexte}
                  onChange={e => setCompetencesTexte(e.target.value)}
                  placeholder={"Une compétence ou un attendu par ligne…\n— ou importez un fichier TXT, une image scannée ou un PDF\n— ou dictez avec le micro\n— ou laissez « Propose-moi des compétences » les écrire depuis le programme"}
                  rows={3}
                  disabled={loading}
                  style={{ ...CHAMP, resize: 'vertical' }}
                />
                {/* Matériel + contraintes — rangés ici depuis le regroupement du 30/07 ; chacun
                    a SON « Propose-moi… » (principe maison : aSchool propose, le prof corrige). */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <label style={LABEL}>Matériel nécessaire</label>
                    {sourceNoteMat && SOURCES_TEXTE[sourceNoteMat] && (
                      <span title={SOURCES_TEXTE[sourceNoteMat].aide}
                        style={{ fontSize: 12, fontWeight: 600, color: '#1d4ed8', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 99, padding: '2px 10px', flexShrink: 0 }}>
                        {SOURCES_TEXTE[sourceNoteMat].label}
                      </span>
                    )}
                  </div>
                  <BoutonPropose
                    enCours={matLoading}
                    disabled={loading}
                    label="Propose-moi du matériel nécessaire"
                    title="aSchool propose le matériel d'après votre thème et votre cadre — vous corrigez librement."
                    onClick={() => proposerLigne({ url: '/api/contenus/seances/proposer-materiel', valeur: materiel, setValeur: setMateriel, setNote: setSourceNoteMat, note: 'materiel', setLoad: setMatLoading, erreur: 'Proposition de matériel impossible.' })}
                  />
                </div>
                <textarea
                  value={materiel}
                  onChange={e => { setMateriel(e.target.value); if (!e.target.value.trim()) setSourceNoteMat(null) }}
                  placeholder="Liste du matériel…"
                  rows={2}
                  disabled={loading}
                  style={{ ...CHAMP, resize: 'vertical' }}
                />
                {matLoading && (
                  <JaugeAttente libelle="aSchool prépare une liste de matériel adaptée à votre séance…" />
                )}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <label style={LABEL}>Contraintes / consignes spéciales</label>
                    {sourceNoteCont && SOURCES_TEXTE[sourceNoteCont] && (
                      <span title={SOURCES_TEXTE[sourceNoteCont].aide}
                        style={{ fontSize: 12, fontWeight: 600, color: '#1d4ed8', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 99, padding: '2px 10px', flexShrink: 0 }}>
                        {SOURCES_TEXTE[sourceNoteCont].label}
                      </span>
                    )}
                  </div>
                  <BoutonPropose
                    enCours={contLoading}
                    disabled={loading}
                    label="Propose-moi des contraintes spéciales"
                    title="aSchool propose des points de vigilance d'après votre thème et votre cadre — vous corrigez librement."
                    onClick={() => proposerLigne({ url: '/api/contenus/seances/proposer-contraintes', valeur: contraintes, setValeur: setContraintes, setNote: setSourceNoteCont, note: 'contraintes', setLoad: setContLoading, erreur: 'Proposition de contraintes impossible.' })}
                  />
                </div>
                <textarea
                  value={contraintes}
                  onChange={e => { setContraintes(e.target.value); if (!e.target.value.trim()) setSourceNoteCont(null) }}
                  placeholder="Notes particulières…"
                  rows={2}
                  disabled={loading}
                  style={{ ...CHAMP, resize: 'vertical' }}
                />
                {contLoading && (
                  <JaugeAttente libelle="aSchool cherche les points de vigilance utiles pour votre séance…" />
                )}
                </>)}
              </section>

              {/* ③ Déroulé souhaité (facultatif) : esquisse A/B/C + style de production —
                  « souhaité » et pas « généré », pour ne jamais confondre avec le « Déroulé
                  généré » de la colonne de droite. */}
              <section style={CARTE}>
                {/* En-tête de la cartouche — mêmes gestes que ① et ② : titre + « i » d'aide +
                    chevron plier/déplier. */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  <TitreGroupe n={3} fait={derouleFait} actif={false}>Déroulé souhaité</TitreGroupe>
                  <InfoGuide
                    titre="Déroulé souhaité"
                    court="Vos idées pour les trois moments de la séance — rien n'est obligatoire : une zone vide, c'est aSchool qui décide."
                    long={"La séance générée a toujours un début, un milieu et une fin — c'est aSchool qui l'écrit, dans la colonne de droite. Cette cartouche sert à IMPOSER votre volonté sur ces moments, si vous en avez une.\n\nA, B et C sont les trois moments successifs de la MÊME séance — A = la mise en route, B = l'activité principale, C = le retour / trace écrite. Ce ne sont PAS trois options à départager.\n\nTout est permis : rien rempli → aSchool invente tout (le cas le plus courant). Une seule zone — par exemple seulement C, « terminer par un exercice sur ardoise » → aSchool invente le début et le milieu, mais la séance finira comme VOUS l'avez décidé. Deux ou trois zones → aSchool suit votre squelette. Une zone vide n'est jamais une erreur : c'est « aSchool décide pour ce moment-là ».\n\n« Propose-moi cette phase » écrit dans une zone à votre place si vous voulez de l'aide pour formuler — en cohérence avec les zones déjà remplies.\n\nLe STYLE DE PRODUCTION (optionnel) : la FAÇON dont le document final est rédigé — même séance, même contenu, présentation différente. Classique = une fiche de préparation traditionnelle, sobre. Ludique = chaque phase passe par un jeu (défi, énigme, jeu de rôle…). Structuré = phases minutées, listes à puces, transitions explicites. Très concis = télégraphique, la séance tient sur une page. « Aucun style » (le défaut) = aSchool rédige à sa façon habituelle."}
                  />
                  <button
                    type="button"
                    onClick={() => setDerouleReplie(r => !r)}
                    title={derouleReplie ? 'Déplier la cartouche' : 'Replier la cartouche'}
                    style={{ width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ transition: 'transform 0.2s', transform: derouleReplie ? 'rotate(-90deg)' : 'none' }}>
                      <polyline points="6 9 12 15 18 9"/>
                    </svg>
                  </button>
                  {/* Repliée : la ligne résumé — ce qui est rempli, en pastilles (survol = le contenu). */}
                  {derouleReplie && (<>
                    {esquisseLettres.length > 0 && (
                      <span
                        title={['a', 'b', 'c'].filter(k => esquisse[k].trim()).map(k => `${k.toUpperCase()} : ${esquisse[k].trim()}`).join('\n')}
                        style={PASTILLE_RESUME}
                      >
                        Esquisse {esquisseLettres.join(' · ')}
                      </span>
                    )}
                    {style && (
                      <span title="Style de production choisi" style={PASTILLE_RESUME}>
                        {(styles.find(s => s.code === style) || {}).label || style}
                      </span>
                    )}
                    {!derouleFait && (
                      <span title="Cartouche facultative — rien n'y est rempli pour l'instant" style={PASTILLE_RESUME}>rien de renseigné</span>
                    )}
                  </>)}
                </div>
                {!derouleReplie && (<>
                {/* Esquisse A/B/C — zones EMPILÉES pleine largeur (meilleure visibilité,
                    demande 30/07), chacune avec SON « Propose-moi cette phase » : aSchool
                    propose la phase visée, cohérente avec les autres zones déjà remplies.
                    Le TITRE du sous-groupe porte le gras et l'explication ; les libellés
                    A/B/C sont des libellés de champ normaux (retouche 30/07). */}
                <label style={TITRE_SOUS_GROUPE}>
                  Esquisse du déroulé <span style={MENTION_OPTIONNEL}>(optionnel) — vos idées pour les trois moments de la séance, qu'aSchool respectera à la génération</span>
                </label>
                {[
                  ['a', 'A. Mise en route', 'Ex : 2-5 min, réactivation…'],
                  ['b', 'B. Activité principale', 'Activité centrale…'],
                  ['c', 'C. Retour / trace écrite', 'Synthèse ou évaluation…'],
                ].map(([cle, titreCol, placeholder]) => (
                  <div key={cle} style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                        <span style={LABEL}>{titreCol}</span>
                        {esqNotes[cle] && (
                          <span
                            title="Phase proposée d'après votre thème, votre cadre et les autres phases — retouchez-la librement."
                            style={{ fontSize: 12, fontWeight: 600, color: '#1d4ed8', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 99, padding: '2px 10px', flexShrink: 0 }}
                          >
                            Proposée par aSchool
                          </span>
                        )}
                      </div>
                      <BoutonPropose
                        enCours={esqLoading === cle}
                        disabled={loading || (esqLoading !== null && esqLoading !== cle)}
                        label="Propose-moi cette phase"
                        title={`aSchool propose la phase « ${titreCol} » d'après votre thème, votre cadre et les autres phases déjà esquissées — vous corrigez librement.`}
                        onClick={() => proposerEsquisse(cle, titreCol)}
                      />
                    </div>
                    <textarea
                      value={esquisse[cle]}
                      onChange={e => { const v = e.target.value; setEsquisse(prev => ({ ...prev, [cle]: v })); if (!v.trim()) setEsqNotes(prev => ({ ...prev, [cle]: false })) }}
                      placeholder={placeholder}
                      rows={2}
                      disabled={loading}
                      title="Esquisse facultative — aSchool la respectera à la génération"
                      style={{ ...CHAMP, resize: 'vertical' }}
                    />
                    {esqLoading === cle && (
                      <JaugeAttente libelle={`aSchool esquisse la phase « ${titreCol} » de votre séance…`} />
                    )}
                  </div>
                ))}
                <label style={TITRE_SOUS_GROUPE}>
                  Style de production <span style={MENTION_OPTIONNEL}>(optionnel)</span>
                </label>
                {/* « Aucun style » = l'état par défaut rendu VISIBLE et cliquable (un style
                    cliqué par erreur se retire d'un clic clair, pas d'un geste caché). */}
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <Pastille
                    actif={!style}
                    label="Aucun style"
                    title="aSchool rédige la séance à sa façon habituelle — le choix par défaut. Un clic ici retire un style choisi par erreur."
                    onClick={() => setStyle(null)}
                    disabled={loading}
                  />
                  {catalogueRate
                    ? <button type="button" onClick={chargerCatalogues} className="btn-secondary" style={{ fontSize: 12, padding: '5px 12px' }}>Réessayer</button>
                    : styles.map(s => (
                        <Pastille key={s.code} actif={style === s.code} label={s.label} title={s.description}
                          onClick={() => setStyle(style === s.code ? null : s.code)} disabled={loading} />
                      ))}
                </div>
                </>)}
              </section>

              {/* ④ Générer la séance — SA cartouche, avec le bouton uniquement (retouche
                  30/07 : fini le bouton nu en bas de colonne). */}
              <section style={CARTE}>
                <TitreGroupe n={4} fait={!!resultat && !loading} actif={pretAGenerer && !loading && !resultat}>
                  Générer la séance
                </TitreGroupe>
                {loading ? (
                  <span className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, opacity: 0.75, cursor: 'wait' }}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
                    Génération en cours…
                  </span>
                ) : (
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={generer}
                    disabled={!pretAGenerer}
                    title={pretAGenerer
                      ? (resultat ? 'Régénérer la séance — l\'ancienne version reste dans l\'historique' : 'Générer la séance — elle s\'enregistrera automatiquement dans Mes contenus')
                      : 'Complétez d\'abord le thème, le mode et la durée (cartouche 1)'}
                    style={{ alignSelf: 'flex-start', opacity: pretAGenerer ? 1 : 0.55, cursor: pretAGenerer ? 'pointer' : 'not-allowed' }}
                  >
                    {resultat ? 'Régénérer la séance' : 'Générer la séance'}
                  </button>
                )}
              </section>

              {/* ⑤ Activités de cette séance — visible dès que la séance EXISTE en base
                  (seanceId posé par l'auto-save ou la reprise). Optionnel, jamais bloquant :
                  créer ici (naît rattachée) ou ajouter une existante ; détacher ≠ supprimer. */}
              {seanceId && (
                <section style={CARTE}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <TitreGroupe n={5} fait={activitesLiees.length > 0} actif={false}>Activités de cette séance</TitreGroupe>
                    <InfoGuide
                      titre="Activités de cette séance"
                      court="Accrochez des activités à cette séance — optionnel, rien d'obligatoire."
                      long={"Une séance peut porter des activités. Deux façons d'en accrocher : « Créer une activité ici » ouvre l'écran Activité et la nouvelle activité naît RATTACHÉE à cette séance ; « Ajouter une activité existante » va chercher une activité déjà présente dans vos contenus.\n\nUne activité n'a qu'UNE séance : en ajouter une déjà rangée ailleurs la déplace (l'écran demande confirmation avant).\n\nDétacher ne supprime JAMAIS l'activité : elle reste dans vos contenus, simplement « non rangée ». Et supprimer une séance libère ses activités de la même façon — rien ne se perd."}
                    />
                    <button
                      type="button"
                      onClick={() => setActReplie(r => !r)}
                      title={actReplie ? 'Déplier la cartouche' : 'Replier la cartouche'}
                      style={{ width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ transition: 'transform 0.2s', transform: actReplie ? 'rotate(-90deg)' : 'none' }}>
                        <polyline points="6 9 12 15 18 9"/>
                      </svg>
                    </button>
                    {activitesLiees.length > 0 && (
                      <span style={PASTILLE_RESUME} title="Le nombre d'activités rattachées à cette séance">
                        {activitesLiees.length} activité{activitesLiees.length > 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                  {!actReplie && (<>
                  {activitesLiees.length === 0 ? (
                    <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>
                      Aucune activité rattachée pour l'instant — c'est optionnel.
                    </p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {activitesLiees.map(a => (
                        <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 8, border: '1px solid #e2e8f0', borderRadius: 6, padding: '7px 10px' }}>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {a.titre}
                            </div>
                            <div style={{ fontSize: 11, color: '#94a3b8' }}>
                              {a.activite_label}{a.sous_type ? ` · ${a.sous_type}` : ''}{a.nb ? ` · ${a.nb} questions` : ''}
                            </div>
                          </div>
                          <button
                            type="button"
                            className="btn-secondary"
                            onClick={() => onOuvrirActivite(a)}
                            title="Rouvrir cette activité dans son écran (modifier, régénérer)"
                          >
                            Ouvrir
                          </button>
                          <button
                            type="button"
                            onClick={() => detacherActivite(a)}
                            title="Détacher de la séance — l'activité reste dans vos contenus, rien n'est supprimé"
                            style={{ fontSize: 12, fontWeight: 600, color: '#475569', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', flexShrink: 0 }}
                          >
                            Détacher
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => onCreerActivite(seanceId)}
                      title="Créer une nouvelle activité — elle naîtra rattachée à cette séance"
                    >
                      + Créer une activité ici
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={ouvrirSelecteur}
                      title="Choisir une activité déjà présente dans vos contenus pour la rattacher à cette séance"
                    >
                      Ajouter une activité existante
                    </button>
                  </div>
                  </>)}
                </section>
              )}
            </div>
          )

          // ── Colonne DROITE : le déroulé généré (texte en direct pendant le flux, mis en
          // forme à la fin) — même logique que la colonne résultat de l'écran Activité. ──
          const colonneResultat = (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {loading && (
                <JaugeAttente libelle="aSchool construit votre séance, phase par phase…" />
              )}
              {!loading && !resultat && (
                <div style={{
                  border: '1px dashed #cbd5e1', borderRadius: 8, background: '#f8fafc',
                  color: '#94a3b8', fontSize: 14, textAlign: 'center', minHeight: 340,
                  display: 'flex', flexDirection: 'column', alignItems: 'center',
                  justifyContent: 'center', gap: 12, padding: '48px 24px',
                }}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
                  </svg>
                  <span>Ici s'affichera le déroulé de votre séance.</span>
                </div>
              )}
              {resultat !== null && (loading ? (
                // Pendant le flux : le texte brut défile en direct.
                <div ref={resultatRef} className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed rounded p-4"
                  style={{ background: '#f8faff', border: '1px solid #e2e8f0', borderLeftWidth: 4, borderLeftColor: 'var(--bordeaux)' }}>
                  {resultat}
                </div>
              ) : (
                // Flux terminé : le déroulé mis en forme + Imprimer.
                <section ref={resultatRef} className="bg-white rounded border border-gray-200 p-4" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ width: 26, height: 26, borderRadius: '50%', flexShrink: 0, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: '#16a34a', color: '#fff' }}>
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                      </span>
                      <span className="section-title" style={{ fontWeight: 700 }}>Déroulé généré</span>
                    </div>
                    <button type="button" onClick={() => imprimerApercu(corpsHtml(resultat))}
                      title="Imprimer cette séance mise en forme" className="btn-secondary">
                      <IconPrint taille={14} /> Imprimer
                    </button>
                  </div>
                  <div className="apercu-corps" style={{ color: '#1e293b', lineHeight: 1.7, fontSize: 14 }}
                    dangerouslySetInnerHTML={{ __html: corpsHtml(resultat) }} />
                  <style>{`
                    .apercu-corps h1,.apercu-corps h2,.apercu-corps h3{color:#0f172a;line-height:1.3;margin:1.4em 0 .4em}
                    .apercu-corps h1{font-size:1.4rem}.apercu-corps h2{font-size:1.15rem}.apercu-corps h3{font-size:1.05rem}
                    .apercu-corps p{margin:.6em 0}
                    .apercu-corps ul,.apercu-corps ol{margin:.6em 0 .6em 1.4em;padding:0}.apercu-corps li{margin:.3em 0}
                    .apercu-corps hr{border:none;border-top:1px solid #e2e8f0;margin:1.4em 0}
                    .apercu-corps strong{color:#0f172a}
                  `}</style>
                </section>
              ))}
            </div>
          )

          // Déroulé caché : le formulaire prend toute la largeur (mêmes classes de défilement
          // que les colonnes du SplitPane) ; sinon les deux colonnes habituelles.
          return derouleCache
            ? <div className="split-pane"><div className="split-col split-col-flex">{formulaire}</div></div>
            : <SplitPane storageKey="contenus-seance-split-v1" gauche={formulaire} droite={colonneResultat} />
        })()}
      </div>

      {/* ── Fenêtre « Ajouter une activité existante » — liste du monde neuf, filtrée par
          défaut sur le couple courant, RIEN de présélectionné. Un clic sur une ligne la
          rattache (avec confirmation si elle déménage d'une autre séance). ── */}
      {selecteur && (() => {
        const coupleM = seance?.matiere || matiere || ''
        const coupleN = seance?.niveau || niveau || ''
        const disponibles = (catalogue || [])
          .filter(a => !(a.parent && a.parent.id === seanceId))   // déjà ici → rien à faire
          .filter(a => voirToutes || ((a.matiere || '') === coupleM && (a.niveau || '') === coupleN))
        return (
          <div
            onClick={() => setSelecteur(false)}
            style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}
          >
            <div
              onClick={e => e.stopPropagation()}
              style={{ background: '#fff', borderRadius: 12, maxWidth: 560, width: '100%', maxHeight: '80vh', display: 'flex', flexDirection: 'column', boxShadow: '0 20px 60px rgba(0,0,0,0.3)', overflow: 'hidden' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '13px 16px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
                <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a', flex: 1 }}>Ajouter une activité existante</span>
                <button
                  type="button"
                  onClick={() => setSelecteur(false)}
                  title="Fermer sans rien ajouter"
                  aria-label="Fermer"
                  style={{ width: 28, height: 28, borderRadius: '50%', border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 16px', fontSize: 12.5, color: '#475569', borderBottom: '1px solid #f1f5f9', cursor: 'pointer', flexShrink: 0 }}>
                <input type="checkbox" checked={voirToutes} onChange={e => setVoirToutes(e.target.checked)} />
                Voir toutes mes activités (autres matières et niveaux)
              </label>
              <div style={{ overflowY: 'auto', padding: '10px 16px 16px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                {catalogue === null && (
                  <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>Chargement de vos activités…</p>
                )}
                {catalogue !== null && disponibles.length === 0 && (
                  <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>
                    {voirToutes
                      ? 'Aucune activité disponible à rattacher.'
                      : `Aucune activité disponible en ${[coupleM, coupleN].filter(Boolean).join(' — ') || 'votre couple courant'} — cochez « Voir toutes mes activités » pour élargir.`}
                  </p>
                )}
                {catalogue !== null && disponibles.map(a => (
                  <button
                    key={a.id}
                    type="button"
                    onClick={() => rattacherActivite(a)}
                    title={a.parent
                      ? `Déjà rattachée à « ${a.parent.titre} » — la choisir la déplacera ici (confirmation demandée)`
                      : 'Rattacher cette activité à la séance'}
                    style={{ textAlign: 'left', background: '#fff', border: '1px solid #e2e8f0', borderRadius: 6, padding: '8px 12px', cursor: 'pointer', fontFamily: 'inherit' }}
                  >
                    <span style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {a.titre}
                    </span>
                    <span style={{ display: 'block', fontSize: 11, color: '#94a3b8' }}>
                      {a.activite_label}{a.sous_type ? ` · ${a.sous_type}` : ''}{a.nb ? ` · ${a.nb} questions` : ''}
                      {voirToutes && (a.matiere || a.niveau) ? ` · ${[a.matiere, a.niveau].filter(Boolean).join(' — ')}` : ''}
                      {a.parent ? ` · déjà dans « ${a.parent.titre} »` : ''}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )
      })()}

    </div>
  )
}
