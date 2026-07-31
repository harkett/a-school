// Écran « Séquence » du monde MES CONTENUS — même moule que l'écran Séance (SeanceEcran.jsx) :
// DEUX COLONNES (formulaire à gauche, plan à droite), cartouches à pastilles EtapeBadge,
// frise en haut, génération en STREAMING (décision utilisateur 30/07 : les lignes du plan
// apparaissent UNE À UNE, sablier + jauge — jamais d'appel long silencieux).
//
// LE PLAN EST LA LISTE DES SÉANCES : chaque ligne générée devient une VRAIE ligne `seances`
// (rattachée, ordonnée, titre pré-rempli, déroulé vide = « à générer »). Jamais de plan
// stocké en texte à côté. RÈGLE 0 : l'écriture en base = UNE transaction à la FIN du flux
// (POST /contenus/sequences — séquence + séances ensemble), badge « Enregistrée » /
// « Réessayer l'enregistrement ». V1 : le plan ne se génère que sur une séquence NEUVE
// (jamais destructif) — ensuite viennent les gestes (étape 4 du chantier).
//
// ÉDITION (31/07) : une séquence née n'est plus figée. Ses champs restent ouverts et toute
// retouche part en base d'elle-même (PUT, auto-save — aucun bouton « Valider », comme
// partout ailleurs). Seul le PLAN est intouchable ici : les séances existent déjà, chacune
// avec son déroulé et son historique ; on les travaille une à une dans l'écran Séance.
//
// Cascade : UN CLIC = UN ÉTAGE — générer le plan ne génère aucun déroulé de séance.
// LA BOUCLE (30/07) : chaque ligne du plan s'OUVRE (écran Séance pré-rempli, la séance est
// déjà en base) — le prof y génère le déroulé, y accroche ses activités, puis revient ici.
import { useEffect, useRef, useState } from 'react'
import SplitPane from './SplitPane.jsx'
import JaugeAttente from './JaugeAttente.jsx'
import EtapeBadge from './EtapeBadge.jsx'
import ApportTexte from './contenus/ApportTexte.jsx'
import InfoGuide from './InfoGuide.jsx'
import { apiFetch, detailPourEcran, lireReponse, messagePourEcran, refreshSession, TIMEOUT_STD, TIMEOUT_LONG } from '../utils/api.js'
import { showError } from '../errorDialog'
import { TYPES_CONTENUS } from '../utils/typesContenus.js'

// Identité du type Séquence (violet) — même fichier commun que la page liste et le menu.
const TYPE_SEQ = TYPES_CONTENUS.sequence

const MSG_ECHEC_PLAN =
  'La génération du plan de votre séquence n\'a pas pu aboutir. Merci de réessayer.\n' +
  'Si le problème persiste, cliquez ici pour nous le signaler.'

// Origine du texte de la zone Objectif / Compétences — pastille sur la ligne du libellé,
// même motif que l'écran Séance (une entrée par façon de remplir, clavier = rien).
const SOURCES_TEXTE = {
  objectif:    { label: 'Objectif proposé par aSchool',      aide: 'Objectif proposé à partir du programme officiel de votre niveau — modifiez-le librement, puis générez le plan.' },
  competences: { label: 'Compétences proposées par aSchool', aide: 'Compétences proposées depuis le programme officiel de votre niveau, en lien avec votre objectif — retouchez-les librement, une par ligne.' },
  dictee:      { label: 'Texte issu de votre dictée',        aide: 'Texte issu de votre dictée — relisez-le, corrigez si besoin, puis générez.' },
  txt:         { label: 'Texte importé d\'un fichier',       aide: 'Texte importé depuis votre fichier.' },
  image:       { label: 'Texte extrait d\'une image',        aide: 'Texte extrait de votre image.' },
  pdf:         { label: 'Texte extrait d\'un PDF',           aide: 'Texte extrait de votre PDF.' },
}

// Styles partagés — COPIES de l'écran Séance (mêmes cartouches, mêmes libellés).
const CARTE = { background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 10 }
const LABEL = { fontSize: 12, fontWeight: 500, color: '#6b7280' }
const PASTILLE_RESUME = { fontSize: 12, fontWeight: 600, color: '#64748b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '2px 10px', flexShrink: 0 }
const CHAMP = { width: '100%', padding: '9px 12px', fontSize: 13, lineHeight: 1.6, color: '#1e293b', border: '1px solid #cbd5e1', borderRadius: 6, fontFamily: 'inherit', boxSizing: 'border-box', background: '#fff' }

// Une ligne du flux → un titre de séance propre (même nettoyage que le serveur : puces et
// numérotation de tête retirées — on ne fait pas confiance à la forme du modèle).
function nettoyerLignePlan(ligne) {
  let l = ligne.replace(/^[\s\-•*–—]+|[\s\-•*–—]+$/g, '')
  l = l.replace(/^\d+[.)]\s*/, '')
  return l.replace(/^[\s\-•*–—]+|[\s\-•*–—]+$/g, '')
}

// Titre de groupe : même patron que l'écran Séance (pastille EtapeBadge + section-title).
function TitreGroupe({ n, fait, actif, children }) {
  return (
    <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <EtapeBadge n={n} fait={fait} actif={actif} />
      <span style={{ display: 'inline-flex', alignItems: 'center', fontWeight: 700 }}>{children}</span>
    </div>
  )
}

// Frise du haut — même dessin que la frise de l'écran Séance : ① Objectif (obligatoire) →
// ② Précisions (facultatif, vert dès qu'un champ est rempli, jamais surligné « à faire ») →
// ③ Générer le plan. Derrière : le compteur de SÉANCES du plan (croix rouge « Aucune
// séance » tant que le plan n'existe pas, rond vert avec le nombre dès qu'il est écrit).
function FriseSequence({ objectifOk, precisionsFaites, loading, planEcrit, nbSeances = 0 }) {
  const termine = planEcrit && !loading
  const etapes = [
    { n: 1, label: 'Objectif', fait: !!objectifOk },
    { n: 2, label: 'Précisions', fait: !!precisionsFaites },
    { n: 3, label: 'Générer le plan', fait: termine },
  ]
  const courant = loading ? 2 : !objectifOk ? 0 : termine ? -1 : 2
  return (
    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', rowGap: 8 }}>
      {etapes.map((e, i) => {
        const estCourant = i === courant
        const bg = e.fait ? '#16a34a' : estCourant ? 'var(--bordeaux)' : '#fff'
        const fg = (e.fait || estCourant) ? '#fff' : '#94a3b8'
        const bord = e.fait ? '#16a34a' : estCourant ? 'var(--bordeaux)' : '#cbd5e1'
        return (
          <span key={e.n} style={{ display: 'flex', alignItems: 'center' }}>
            {/* Le trait vert suit le CHEMIN OBLIGATOIRE : objectif rempli = route ouverte. */}
            {i > 0 && (
              <span style={{ width: 30, height: 2, borderRadius: 2, margin: '0 9px',
                             background: objectifOk ? '#16a34a' : '#e2e8f0' }} />
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
      <span style={{ display: 'flex', alignItems: 'center' }}>
        <span style={{ width: 30, height: 2, borderRadius: 2, margin: '0 9px',
                       background: nbSeances > 0 ? '#16a34a' : '#e2e8f0' }} />
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          title={nbSeances > 0
            ? 'Les séances du plan, enregistrées « à générer » — chacune se détaillera dans l\'écran Séance'
            : 'Aucune séance pour l\'instant — générez le plan : chaque ligne deviendra une séance'}>
          <span style={{ width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                         display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                         fontSize: 12, fontWeight: 800, fontVariantNumeric: 'tabular-nums',
                         background: nbSeances > 0 ? '#16a34a' : '#dc2626', color: '#fff',
                         border: `1.5px solid ${nbSeances > 0 ? '#16a34a' : '#dc2626'}` }}>
            {nbSeances > 0 ? nbSeances : '✕'}
          </span>
          <span style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap',
                         color: nbSeances > 0 ? '#64748b' : '#dc2626' }}>
            {nbSeances > 0 ? `${nbSeances} séance${nbSeances > 1 ? 's' : ''}` : 'Aucune séance'}
          </span>
        </span>
      </span>
    </div>
  )
}

// `onOuvrirSeance(seanceRow, sequenceId)` : ouvre une séance du plan dans l'écran Séance,
// pré-remplie — avec retour automatique ici (la boucle séquence→séance→activités).
export default function SequenceEcran({ sequence, matiere, niveau, onNavigate, onOuvrirSeance }) {
  // ── Le formulaire entier (chaque champ vit en base — reprise complète à terme) ──
  const [objectif, setObjectif] = useState(sequence?.titre || '')
  const [contexte, setContexte] = useState(sequence?.contexte || '')
  const [ampleur, setAmpleur] = useState(sequence?.ampleur || '')
  const [competencesTexte, setCompetencesTexte] = useState(
    Array.isArray(sequence?.competences) ? sequence.competences.join('\n') : ''
  )

  // ── Génération + règle 0 ──
  const [loading, setLoading] = useState(false)
  const [fluxTexte, setFluxTexte] = useState('')          // le flux brut — les lignes s'en déduisent en direct
  const [seancesCreees, setSeancesCreees] = useState(null) // les VRAIES lignes seances écrites en base (POST)
  const [lignesPretes, setLignesPretes] = useState(null)   // lignes du flux terminé, gardées pour « Réessayer l'enregistrement »
  const [sequenceId, setSequenceId] = useState(sequence?.id || null)
  const [enregistrement, setEnregistrement] = useState(sequence ? 'ok' : null)  // null | 'ok' | 'echec'
  const [baseReplie, setBaseReplie] = useState(false)      // repli manuel de la cartouche ①
  const [precReplie, setPrecReplie] = useState(false)      // repli manuel de la cartouche ②
  const [planCache, setPlanCache] = useState(false)        // colonne « Plan » escamotée (bouton à droite de la frise)
  const [sourceNote, setSourceNote] = useState(null)       // origine de la zone Objectif — pastille du titre ①
  const [sourceNoteComp, setSourceNoteComp] = useState(null) // origine de la zone Compétences (②)

  // Les séances de la séquence = SOURCE UNIQUE en base (get, zéro copie) : relues à la
  // reprise ET après l'écriture du plan — les états « à générer / générée » sont toujours vrais.
  async function chargerSeances(id, { silencieux = false } = {}) {
    try {
      const d = await lireReponse(await apiFetch(`/api/contenus/sequences/${id}/seances`, { credentials: 'include' }, TIMEOUT_STD))
      setSeancesCreees(d.seances || [])
    } catch (err) {
      if (!silencieux) showError(`Impossible de charger les séances de cette séquence.\n\n${messagePourEcran(err)}`)
    }
  }

  useEffect(() => {
    if (sequence?.id) chargerSeances(sequence.id)
  }, [sequence?.id])   // eslint-disable-line react-hooks/exhaustive-deps

  // ── Corriger une séquence DÉJÀ NÉE (auto-save, règle 0) ──────────────────────────────
  // Une séquence écrite n'était plus modifiable du tout : ni renommer, ni corriger l'objectif.
  // Ses champs restent donc ouverts après la naissance, et toute retouche part en base d'
  // elle-même (PUT), sans bouton « Valider » — comme le reste de l'application. Le PLAN n'est
  // jamais touché : les séances existent, chacune avec son déroulé et son historique.
  const dernierEnregistre = useRef(null)   // l'état déjà en base, pour ne pas écrire pour rien

  async function sauverModifs(instantane) {
    try {
      await lireReponse(await apiFetch(`/api/contenus/sequences/${sequenceId}`, {
        method: 'PUT', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          objectif, contexte, ampleur,
          competences: competencesTexte.split('\n').map(l => l.trim()).filter(Boolean),
        }),
      }, TIMEOUT_STD))
      dernierEnregistre.current = instantane
      setEnregistrement('ok')
    } catch (err) {
      setEnregistrement('echec')
      showError(`Vos modifications n'ont pas pu être enregistrées.\n\n${messagePourEcran(err)}`)
    }
  }

  useEffect(() => {
    if (!sequenceId) return
    const instantane = JSON.stringify({ objectif, contexte, ampleur, competencesTexte })
    // Premier passage (reprise ou naissance) : on note l'état de la base, on n'écrit rien.
    if (dernierEnregistre.current === null) { dernierEnregistre.current = instantane; return }
    if (dernierEnregistre.current === instantane) return
    if (!objectif.trim()) return          // le serveur refuse un objectif vide, on n'insiste pas
    const t = setTimeout(() => sauverModifs(instantane), 1200)   // fin de frappe, pas chaque touche
    return () => clearTimeout(t)
  }, [sequenceId, objectif, contexte, ampleur, competencesTexte])   // eslint-disable-line react-hooks/exhaustive-deps

  const objectifOk = !!objectif.trim()
  const precisionsFaites = !!ampleur.trim() || !!competencesTexte.trim()
  const nbSeances = seancesCreees ? seancesCreees.length : 0
  // V1 : le plan ne se génère que sur une séquence NEUVE — une fois écrite, plus de bouton
  // (jamais destructif ; les gestes sur les séances arrivent à l'étape suivante).
  const pretAGenerer = objectifOk && !sequenceId
  // Lignes affichées EN DIRECT pendant le flux (la dernière peut être partielle : elle
  // grandit sous les yeux du prof — c'est voulu, c'est le streaming).
  const lignesEnCours = fluxTexte.split('\n').map(nettoyerLignePlan).filter(Boolean)

  // ── « Propose-moi… » (principe maison : aSchool propose tout, le prof corrige) ──
  const proposerObjectif = {
    label: 'Propose-moi un objectif',
    title: "aSchool écrit pour vous un objectif de séquence tiré du programme officiel de votre niveau — vous le retouchez librement, puis Générer le plan.",
    jauge: 'aSchool lit le programme officiel de votre niveau et prépare un objectif de séquence…',
    note: 'objectif',
    action: async () => {
      try {
        const res = await apiFetch('/api/contenus/sequences/proposer-objectif', {
          method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}),
        }, TIMEOUT_LONG)
        const d = await lireReponse(res)
        if (d.available && d.texte) return d.texte
        showError(d.message || 'Pas de proposition possible pour le moment (programme officiel pas encore chargé pour votre niveau).\n\nDécrivez votre objectif dans la zone de texte — ou dictez-le avec le micro.')
        return null
      } catch (err) {
        showError(`Proposition d'objectif impossible.\n\n${messagePourEcran(err)}`)
        return null
      }
    },
  }

  const proposerCompetences = {
    label: 'Propose-moi des compétences',
    title: "aSchool propose 3 à 6 compétences du programme officiel de votre niveau, en lien avec votre objectif — vous les retouchez librement, une par ligne.",
    jauge: 'aSchool lit le programme officiel de votre niveau et cherche les compétences liées à votre objectif…',
    note: 'competences',
    avant: () => {
      if (objectif.trim()) return true
      showError('Décrivez d\'abord l\'objectif général de la séquence (cartouche 1) : les compétences proposées s\'appuient dessus.')
      return false
    },
    action: async () => {
      try {
        const res = await apiFetch('/api/contenus/sequences/proposer-competences', {
          method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ objectif }),
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
      objectif: objectif.trim(),
      contexte: contexte.trim(),
      ampleur: ampleur.trim(),
      // La zone de texte → la liste attendue en base : une ligne = une compétence.
      competences: competencesTexte.split('\n').map(l => l.trim()).filter(Boolean),
    }
  }

  // ── Règle 0 : UNE transaction à la FIN du flux — séquence + séances ensemble. ──
  async function sauver(lignes) {
    try {
      const d = await lireReponse(await apiFetch('/api/contenus/sequences', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...corpsFormulaire(), seances: lignes }),
      }, TIMEOUT_STD))
      setSequenceId(d.id)
      setSeancesCreees(d.seances || [])
      setEnregistrement('ok')
      // Relecture canonique en base (get, source unique) — en silencieux : le plan est déjà affiché.
      chargerSeances(d.id, { silencieux: true })
    } catch {
      // Un échec d'auto-save DOIT se voir (règle 0 : rien n'attend en mémoire « pour plus tard »).
      setEnregistrement('echec')
      showError("Votre plan est affiché mais n'a pas pu être enregistré.\n\nCliquez sur « Réessayer l'enregistrement » en haut de l'écran.")
    }
  }

  // ── Génération du PLAN en STREAMING — les lignes apparaissent une à une à droite. ──
  async function genererPlan() {
    if (!objectif.trim()) {
      showError('Décrivez d\'abord l\'objectif général de la séquence.')
      return
    }
    setFluxTexte('')
    setSeancesCreees(null)
    setLignesPretes(null)
    setEnregistrement(null)
    setLoading(true)
    try {
      const opts = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(corpsFormulaire()),
      }
      let res = await fetch('/api/contenus/sequences/generer-plan', opts)
      if (res.status === 401 && await refreshSession()) {
        res = await fetch('/api/contenus/sequences/generer-plan', opts)
      }
      if (!res.ok || !res.body) {
        const err = await res.json().catch(() => ({}))
        const message = detailPourEcran(err)   // un 422 renvoie un tableau : filtré, jamais affiché
        if (message) showError(message)
        else showError(MSG_ECHEC_PLAN, { feedback: true })
        return
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let tampon = '', complet = '', erreurFlux = false, termine = false, refIncident = null
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
            try { complet += JSON.parse(data).text; setFluxTexte(complet) } catch { /* bloc partiel ignoré */ }
          } else if (evt === 'error') {
            erreurFlux = true
            try { refIncident = JSON.parse(data).ref || null } catch { /* pas de réf */ }
          } else if (evt === 'done') {
            termine = true
          }
        }
      }

      const lignes = complet.split('\n').map(nettoyerLignePlan).filter(Boolean)
      if (erreurFlux || !termine || lignes.length === 0) {
        setFluxTexte('')
        showError(MSG_ECHEC_PLAN, { feedback: true, ref: refIncident })
        return
      }

      // RÈGLE 0 : le flux réussi s'écrit TOUT DE SUITE en base — une transaction,
      // séquence + séances ensemble. Les lignes restent sous la main pour un réessai.
      setLignesPretes(lignes)
      await sauver(lignes)
    } catch (e) {
      console.error('génération du plan de séquence (Mes contenus) :', e)
      setFluxTexte('')
      showError(MSG_ECHEC_PLAN, { feedback: true })
    } finally {
      setLoading(false)
    }
  }

  const titreBarre = sequence ? `Reprise : ${sequence.titre || 'séquence'}` : 'Nouvelle séquence'

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

      {/* ── Barre du haut : retour + titre + couple + état d'enregistrement (règle 0 visible) ── */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', flexShrink: 0, alignItems: 'center', gap: 8 }}>
        {/* Retour à la page d'où l'on vient : « Mes séquences » (pas « Mes contenus »),
            flèche SVG grande et pleine — demande utilisateur du 30/07. Habit violet du type. */}
        <button
          type="button"
          onClick={() => onNavigate('contenus-sequences')}
          title="Revenir à la page Mes séquences"
          style={{ display: 'inline-flex', alignItems: 'center', gap: 7, margin: '0 0 0 8px', fontSize: 13, fontWeight: 600, color: TYPE_SEQ.accent, background: TYPE_SEQ.fond, border: `1px solid ${TYPE_SEQ.bord}`, borderRadius: 6, padding: '5px 12px', cursor: 'pointer', flexShrink: 0 }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Mes séquences
        </button>
        <div style={{ padding: '10px 12px', fontSize: '13px', fontWeight: 700, color: 'var(--bordeaux)', borderBottom: '2px solid var(--bordeaux)', marginBottom: '-1px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {titreBarre}
        </div>
        {/* Le couple ne se réaffiche PAS ici : le header bleu juste au-dessus est son unique
            afficheur (doublon retiré le 30/07 sur demande utilisateur). */}

        {enregistrement === 'ok' && (
          <span title="Votre séquence et ses séances sont écrites en base — retrouvez-les dans Mes contenus"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600, color: '#166534', background: '#dcfce7', border: '1px solid #86efac', borderRadius: 99, padding: '3px 10px', flexShrink: 0, marginLeft: 'auto', marginRight: 8 }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Enregistrée
          </span>
        )}
        {enregistrement === 'echec' && (
          <button
            type="button"
            onClick={() => lignesPretes && sauver(lignesPretes)}
            title="L'enregistrement automatique a échoué — cliquez pour réessayer"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600, color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 99, padding: '3px 10px', cursor: 'pointer', flexShrink: 0, marginLeft: 'auto', marginRight: 8 }}
          >
            Réessayer l'enregistrement
          </button>
        )}
      </div>

      {/* ── Frise + bouton qui escamote/raffiche la colonne « Plan » (même geste que la
          colonne Déroulé de l'écran Séance). ── */}
      <div style={{ padding: '14px 20px 12px', borderBottom: '1px solid #e2e8f0', flexShrink: 0, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <FriseSequence objectifOk={objectifOk} precisionsFaites={precisionsFaites} loading={loading} planEcrit={nbSeances > 0} nbSeances={nbSeances} />
        </div>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => setPlanCache(c => !c)}
          title={planCache
            ? 'Réafficher la colonne « Plan de la séquence » à droite'
            : 'Cacher la colonne « Plan de la séquence » — le formulaire prend toute la largeur'}
          style={{ flexShrink: 0, marginLeft: 'auto' }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {planCache
              ? <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
              : <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>}
          </svg>
          {planCache ? 'Afficher le plan' : 'Cacher le plan'}
        </button>
      </div>

      <div className="creer-corps">
        {(() => {
          // ── Colonne GAUCHE : le formulaire. ──
          const formulaire = (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

              {/* ① Objectif général — l'obligatoire : la zone d'apport complète (comme le
                  thème de la séance) + le contexte rapide optionnel. */}
              <section style={CARTE}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <TitreGroupe n={1} fait={objectifOk} actif={!objectifOk && !loading}>Objectif général</TitreGroupe>
                    <InfoGuide
                      titre="Objectif général"
                      court="Le but que la séquence doit atteindre au fil de ses séances — c'est lui qui guide tout le plan."
                      long={"Décrivez le BUT de la séquence comme vous le diriez : « maîtriser le récit d'aventure », « préparer la classe au concours », « construire le projet théâtre de l'année »…\n\nUne séquence est une suite ordonnée de séances vers cet objectif, quelle que soit sa durée — quelques séances comme un projet sur deux ans.\n\nRemplissez la zone comme vous voulez : au clavier, en important un fichier TXT / une image / un PDF, en dictant au micro — ou laissez « Propose-moi un objectif » l'écrire depuis le programme officiel de votre niveau.\n\nLe CONTEXTE RAPIDE (optionnel) décrit votre classe : effectif, ambiance, ce qui a marqué l'année… Il affine le plan proposé."}
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
                    {/* Pastille « origine du texte » — sur la ligne du titre, repliée comme dépliée. */}
                    {sourceNote && SOURCES_TEXTE[sourceNote] && (
                      <span
                        title={SOURCES_TEXTE[sourceNote].aide}
                        style={{ fontSize: 12, fontWeight: 600, color: '#1d4ed8', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 99, padding: '2px 10px', flexShrink: 0 }}
                      >
                        {SOURCES_TEXTE[sourceNote].label}
                      </span>
                    )}
                    {/* Pastille « contexte rapide » — toujours affichée, bascule toute seule. */}
                    <span
                      title={contexte.trim()
                        ? 'Un contexte rapide est fourni — aSchool en tient compte pour bâtir le plan.'
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
                  </div>
                  {/* Même procédé d'apport que la séance : TXT / Image / PDF / Dicter +
                      « Propose-moi un objectif ». Replier CACHE la rangée sans la démonter. */}
                  <div style={{ display: baseReplie ? 'none' : 'block', marginLeft: 'auto', minWidth: 0 }}>
                    <ApportTexte texte={objectif} onChange={setObjectif} onSourceNote={setSourceNote} proposer={proposerObjectif} disabled={loading} />
                  </div>
                </div>
                {!baseReplie && (<>
                <label style={LABEL}>
                  Objectif de la séquence
                  <InfoGuide
                    titre="Objectif de la séquence"
                    court="Le but à atteindre au fil des séances — écrivez-le comme vous le diriez."
                    long={"Écrivez l'objectif comme vous le diriez : « maîtriser le récit d'aventure », « préparer le concours », « monter la pièce de fin d'année »…\n\nRemplissez la zone comme vous voulez : au clavier, en important un fichier TXT / une image / un PDF, en dictant au micro — ou laissez « Propose-moi un objectif » l'écrire depuis le programme officiel de votre niveau.\n\nUne fois la séquence créée, cet objectif reste modifiable : corrigez-le quand vous voulez, vos retouches s'enregistrent toutes seules (le badge « Enregistrée » le confirme). Le plan déjà généré n'est pas retouché pour autant — les séances gardent leur déroulé."}
                  />
                </label>
                <textarea
                  value={objectif}
                  onChange={e => setObjectif(e.target.value)}
                  placeholder={"Décrivez l'objectif général de la séquence…\n— ou importez un fichier TXT, une image scannée ou un PDF\n— ou dictez avec le micro\n— ou laissez « Propose-moi un objectif » l'écrire à votre place"}
                  rows={4}
                  disabled={loading}
                  style={{ ...CHAMP, resize: 'vertical' }}
                />
                <label style={LABEL}>
                  Contexte rapide <span style={{ fontWeight: 400, color: '#94a3b8' }}>(optionnel)</span>
                  <InfoGuide
                    titre="Contexte rapide"
                    court="Votre classe en une phrase : effectif, ambiance, ce qui a marqué l'année…"
                    long={"Optionnel : décrivez votre classe telle qu'elle est — effectif, ambiance, ce qui marche bien avec eux, ce qui a bloqué…\n\naSchool en tient compte pour bâtir un plan de séquence adapté."}
                  />
                </label>
                <input
                  type="text"
                  value={contexte}
                  onChange={e => setContexte(e.target.value)}
                  placeholder="Ex : classe de 24, très hétérogène ; le travail en groupe fonctionne bien…"
                  disabled={loading}
                  style={CHAMP}
                />
                </>)}
              </section>

              {/* ② Précisions (facultatif) : l'ampleur souhaitée + les compétences visées.
                  Vert dès qu'un champ est rempli, ne clignote jamais. */}
              <section style={CARTE}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  <TitreGroupe n={2} fait={precisionsFaites} actif={false}>Précisions</TitreGroupe>
                  <InfoGuide
                    titre="Précisions"
                    court="L'ampleur souhaitée et les compétences visées — tout est facultatif, la cartouche passe au vert dès qu'un champ est rempli."
                    long={"L'AMPLEUR SOUHAITÉE : dites en toutes lettres la taille que vous voulez donner à la séquence — « une dizaine de séances », « un trimestre », « un projet sur deux ans »… Sans ampleur, aSchool déduit le nombre de séances de l'objectif seul.\n\nLes COMPÉTENCES / ATTENDUS : ce que les élèves doivent savoir faire à la fin de la séquence. Une compétence par ligne, remplie comme vous voulez : au clavier, en important un fichier TXT / une image / un PDF, en dictant au micro — ou laissez « Propose-moi des compétences » les écrire depuis le programme officiel, en lien avec votre objectif.\n\nTout est facultatif : rien ici ne bloque la génération du plan."}
                  />
                  <button
                    type="button"
                    onClick={() => setPrecReplie(r => !r)}
                    title={precReplie ? 'Déplier la cartouche' : 'Replier la cartouche'}
                    style={{ width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ transition: 'transform 0.2s', transform: precReplie ? 'rotate(-90deg)' : 'none' }}>
                      <polyline points="6 9 12 15 18 9"/>
                    </svg>
                  </button>
                  {/* Repliée : la ligne résumé — ce qui est rempli, en pastilles. */}
                  {precReplie && (<>
                    {!!ampleur.trim() && <span title={ampleur} style={PASTILLE_RESUME}>Ampleur</span>}
                    {competencesTexte.split('\n').filter(l => l.trim()).length > 0 && (
                      <span title={competencesTexte} style={PASTILLE_RESUME}>
                        {competencesTexte.split('\n').filter(l => l.trim()).length} compétence{competencesTexte.split('\n').filter(l => l.trim()).length > 1 ? 's' : ''}
                      </span>
                    )}
                    {!precisionsFaites && (
                      <span title="Cartouche facultative — rien n'y est rempli pour l'instant" style={PASTILLE_RESUME}>rien de renseigné</span>
                    )}
                  </>)}
                </div>
                {!precReplie && (<>
                <label style={LABEL}>
                  Ampleur souhaitée <span style={{ fontWeight: 400, color: '#94a3b8' }}>(optionnel)</span>
                  <InfoGuide
                    titre="Ampleur souhaitée"
                    court="La taille que vous voulez donner à la séquence, en toutes lettres."
                    long={"Dites la taille voulue comme vous le diriez : « une dizaine de séances », « un trimestre », « jusqu'aux vacances de printemps », « un projet sur deux ans »…\n\nSans ampleur, aSchool déduit le nombre de séances de l'objectif seul — une séquence n'a pas de taille imposée."}
                  />
                </label>
                <input
                  type="text"
                  value={ampleur}
                  onChange={e => setAmpleur(e.target.value)}
                  placeholder="Ex : une dizaine de séances · un trimestre · un projet sur deux ans…"
                  disabled={loading}
                  style={CHAMP}
                />
                {/* Zone Compétences — même grammaire que la séance : libellé + pastille
                    d'origine à gauche, la rangée d'apport à droite, la zone dessous. */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <label style={LABEL}>Compétences / attendus <span style={{ fontWeight: 400, color: '#94a3b8' }}>(optionnel)</span></label>
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
                </>)}
              </section>

              {/* ③ Générer le plan — SA cartouche, avec le bouton uniquement (même motif
                  que « Générer la séance »). V1 : une fois le plan écrit, plus de bouton —
                  jamais destructif, les gestes sur les séances arrivent ensuite. */}
              <section style={CARTE}>
                <TitreGroupe n={3} fait={nbSeances > 0 && !loading} actif={pretAGenerer && !loading}>
                  Générer le plan
                </TitreGroupe>
                {loading ? (
                  <span className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, opacity: 0.75, cursor: 'wait' }}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
                    Génération en cours…
                  </span>
                ) : nbSeances > 0 ? (
                  <p style={{ margin: 0, fontSize: 12.5, color: '#64748b' }}>
                    Le plan est écrit : chaque ligne est une séance enregistrée « à générer ».
                    Chaque séance se détaille ensuite, à son tour, dans l'écran Séance — un clic = un étage,
                    le plan ne génère aucun déroulé.
                  </p>
                ) : (
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={genererPlan}
                    disabled={!pretAGenerer}
                    title={pretAGenerer
                      ? 'Générer le plan — chaque ligne deviendra une séance, enregistrée automatiquement dans Mes contenus'
                      : 'Décrivez d\'abord l\'objectif général (cartouche 1)'}
                    style={{ alignSelf: 'flex-start', opacity: pretAGenerer ? 1 : 0.55, cursor: pretAGenerer ? 'pointer' : 'not-allowed' }}
                  >
                    Générer le plan
                  </button>
                )}
              </section>
            </div>
          )

          // ── Colonne DROITE : le plan — les lignes apparaissent UNE À UNE pendant le flux
          // (streaming, décision 30/07), puis la liste des VRAIES séances écrites en base. ──
          const lignesAffichees = seancesCreees
            ? seancesCreees
            : lignesEnCours.map((titre, i) => ({ titre, position: i + 1, resultat: '' }))
          const colonnePlan = (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {loading && (
                <JaugeAttente libelle="aSchool construit le plan de votre séquence, séance après séance…" />
              )}
              {!loading && lignesAffichees.length === 0 && (
                <div style={{
                  border: '1px dashed #cbd5e1', borderRadius: 8, background: '#f8fafc',
                  color: '#94a3b8', fontSize: 14, textAlign: 'center', minHeight: 340,
                  display: 'flex', flexDirection: 'column', alignItems: 'center',
                  justifyContent: 'center', gap: 12, padding: '48px 24px',
                }}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>
                    <line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
                  </svg>
                  <span>Ici s'affichera le plan de votre séquence — une ligne par séance,<br/>et chaque ligne deviendra une vraie séance « à générer ».</span>
                </div>
              )}
              {lignesAffichees.length > 0 && (
                <section className="bg-white rounded border border-gray-200 p-4" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 26, height: 26, borderRadius: '50%', flexShrink: 0, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: seancesCreees ? '#16a34a' : 'var(--bordeaux)', color: '#fff' }}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                    </span>
                    <span className="section-title" style={{ fontWeight: 700 }}>Plan de la séquence</span>
                    <span style={PASTILLE_RESUME} title={seancesCreees ? 'Les séances du plan, écrites en base' : 'Les lignes arrivent au fil de la génération'}>
                      {lignesAffichees.length} séance{lignesAffichees.length > 1 ? 's' : ''}{seancesCreees ? '' : '…'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {lignesAffichees.map((s, i) => (
                      <div key={s.id ?? i} style={{ display: 'flex', alignItems: 'center', gap: 10, border: '1px solid #e2e8f0', borderRadius: 6, padding: '8px 12px' }}>
                        <span style={{ width: 22, height: 22, borderRadius: '50%', flexShrink: 0, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, fontVariantNumeric: 'tabular-nums', background: '#f1f5f9', border: '1px solid #e2e8f0', color: '#475569' }}>
                          {s.position ?? i + 1}
                        </span>
                        <span style={{ flex: 1, minWidth: 0, fontSize: 13, fontWeight: 600, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={s.titre}>
                          {s.titre}
                        </span>
                        {s.resultat && s.resultat.trim() ? (
                          <span
                            title="Le déroulé de cette séance est écrit — « Ouvrir » pour le revoir, le régénérer ou accrocher des activités"
                            style={{ fontSize: 11, fontWeight: 600, color: '#166534', background: '#dcfce7', border: '1px solid #86efac', borderRadius: 99, padding: '2px 9px', flexShrink: 0 }}
                          >
                            générée
                          </span>
                        ) : (
                          <span
                            title="Le déroulé de cette séance n'est pas encore généré — « Ouvrir » pour le générer dans l'écran Séance"
                            style={{ fontSize: 11, fontWeight: 600, color: TYPE_SEQ.accent, background: TYPE_SEQ.fond, border: `1px solid ${TYPE_SEQ.bord}`, borderRadius: 99, padding: '2px 9px', flexShrink: 0 }}
                          >
                            à générer
                          </span>
                        )}
                        {/* LA BOUCLE : une séance ÉCRITE en base (id réel) s'ouvre dans l'écran
                            Séance, pré-remplie — retour automatique ici par « ← Retour à la
                            séquence ». Pendant le flux (lignes sans id), pas encore de bouton. */}
                        {s.id && onOuvrirSeance && (
                          <button
                            type="button"
                            className="btn-secondary"
                            onClick={() => onOuvrirSeance(s, sequenceId)}
                            title="Ouvrir cette séance dans l'écran Séance — générer son déroulé, y accrocher des activités, puis revenir à la séquence"
                          >
                            Ouvrir
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          )

          // Plan caché : le formulaire prend toute la largeur (mêmes classes que l'écran Séance).
          return planCache
            ? <div className="split-pane"><div className="split-col split-col-flex">{formulaire}</div></div>
            : <SplitPane storageKey="contenus-sequence-split-v1" gauche={formulaire} droite={colonnePlan} />
        })()}
      </div>

    </div>
  )
}
