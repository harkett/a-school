import { useState, useRef, useEffect, useCallback } from 'react'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_LONG } from '../utils/api.js'
import { showError } from '../errorDialog'
import { formatTime, computeBarLevels } from '../utils/audioViz.js'
import InfoGuide from './InfoGuide.jsx'
import { aideActivite } from '../utils/aideActivite.js'
import EtapeBadge from './EtapeBadge.jsx'
import JaugeAttente from './JaugeAttente.jsx'

const NB_BARS = 12  // nombre de barres du visualiseur de volume

// Bandeau « origine du texte » de la carte Texte source (visible quand la carte est dépliée) :
// une phrase par façon de remplir la zone. La saisie au clavier n'a pas de note (rien à signaler).
const NOTES_SOURCE = {
  idee:    "Idée proposée à partir du programme officiel de votre niveau — modifiez-la librement, puis générez.",
  exemple: "Exemple généré depuis le référentiel officiel de votre niveau — adaptez-le si besoin.",
  dictee:  "Texte issu de votre dictée — relisez-le, corrigez si besoin, puis générez.",
  txt:     "Texte importé depuis votre fichier.",
  image:   "Texte extrait de votre image.",
  pdf:     "Texte extrait de votre PDF.",
}

// Variantes affichées quand ce prof a déposé un cahier des charges : l'idée et l'exemple sont alors
// générés à partir du programme officiel ET de son cahier — on le DIT (sinon le cahier passe inaperçu).
// Les autres sources (dictée, fichiers) viennent du prof lui-même → pas de cahier à mentionner.
const NOTES_SOURCE_CAHIER = {
  idee:    "Idée proposée à partir du programme officiel de votre niveau ET du cahier des charges de votre établissement — modifiez-la librement, puis générez.",
  exemple: "Exemple généré depuis le référentiel officiel de votre niveau ET le cahier des charges de votre établissement — adaptez-le si besoin.",
}

const IconTxt = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
)

const IconImage = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
    <polyline points="21 15 16 10 5 21"/>
  </svg>
)

const IconPdf = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
    <polyline points="10 9 9 9 8 9"/>
  </svg>
)

const IconMic = ({ active }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8" y1="23" x2="16" y2="23"/>
  </svg>
)

const IconExemple = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4m0 0h18"/>
  </svg>
)

const IconIdee = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 18h6"/><path d="M10 22h4"/>
    <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5.68.68 1.16 1.46 1.41 2.5"/>
  </svg>
)

// Icône « saisi au clavier » (crayon) — provenance par défaut quand le prof a tapé/collé son texte.
const IconClavier = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
  </svg>
)

// Provenance du texte source → pastille affichée dans l'en-tête quand la carte est REPLIÉE (le corps,
// donc le bandeau d'origine, est alors masqué). Mêmes libellés/icônes que les boutons d'apport, en
// plus court. `sourceNote` null + texte présent = saisie/collage au clavier (cas par défaut ci-dessous).
const PROVENANCE = {
  idee:    { label: 'Idée proposée',   Icon: IconIdee },
  exemple: { label: 'Exemple proposé', Icon: IconExemple },
  dictee:  { label: 'Dictée',          Icon: IconMic },
  txt:     { label: 'Fichier TXT',     Icon: IconTxt },
  image:   { label: 'Image / Scan',    Icon: IconImage },
  pdf:     { label: 'PDF',             Icon: IconPdf },
}

export default function TexteSource({ texte, onChange, objet, onObjetChange, matiere, niveau, activiteTypeId, sousType, verrouille = false, cahierPresent = false, onGenerer, loading = false, pretAGenerer = false, hasResultat = false }) {
  const [ocrLoading, setOcrLoading] = useState(null) // 'image' | 'pdf' | null
  const [isListening, setIsListening] = useState(false)   // micro ouvert (enregistrement en cours)
  const [isReady, setIsReady] = useState(false)           // micro prêt après le bip "go"
  const [isTranscribing, setIsTranscribing] = useState(false) // POST /api/transcribe en cours
  const [elapsed, setElapsed] = useState(0)               // chrono d'enregistrement (secondes)
  const [exempleLoading, setExempleLoading] = useState(false) // génération d'un exemple ancré en cours
  const [ideeLoading, setIdeeLoading] = useState(false)       // « Propose-moi une idée » en cours
  // Origine du texte courant → bandeau dans la carte (quand elle est dépliée). Une seule note à la
  // fois : le dernier geste gagne. Effacée dès que la zone est vidée. Clavier = pas de note.
  const [sourceNote, setSourceNote] = useState(null)          // 'idee'|'exemple'|'dictee'|'txt'|'image'|'pdf'|null
  const [replie, setReplie] = useState(false)                 // carte repliée en phase résultat (verrouillée) ; le prof peut déplier
  const audioCtxRef = useRef(null)
  const textareaRef = useRef(null)
  const texteRef = useRef(texte)
  const mediaRecorderRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const audioChunksRef = useRef([])
  const audioMimeRef = useRef('audio/webm')
  const activeRef = useRef(false)
  const analyserRef = useRef(null)   // AnalyserNode (volume temps réel)
  const sourceRef = useRef(null)     // MediaStreamAudioSourceNode
  const rafRef = useRef(null)        // id requestAnimationFrame du visualiseur
  const chronoRef = useRef(null)     // id setInterval du chrono
  const startTimeRef = useRef(0)     // performance.now() au démarrage de l'enregistrement
  const barsRef = useRef([])         // refs DOM des barres (mutation directe, pas de re-render)

  useEffect(() => { texteRef.current = texte }, [texte])

  // Repli automatique : la carte se replie quand elle se verrouille (phase résultat) et se déplie
  // quand elle se déverrouille (« Changer votre demande »). Le prof peut plier/déplier à la main
  // via le chevron tant que c'est verrouillé.
  useEffect(() => { setReplie(verrouille) }, [verrouille])

  // Zone déjà remplie = le chemin est choisi : tout geste qui REMPLACERAIT le texte demande
  // d'abord confirmation (jamais de destruction au clic direct). C'est la confirmation qui
  // protège — AUCUN demi-grisage visuel : les 6 boutons ont tous la même apparence, texte noir
  // quand ils sont actifs, et tous grisés d'un coup (uniformément) quand la rangée est verrouillée.
  const zoneRemplie = !!texte.trim()
  const enRetrait = {}
  function confirmerRemplacement() {
    if (!zoneRemplie) return true
    return window.confirm('Remplacer le texte actuel ? Le contenu de la zone sera perdu.')
  }

  // Course d'attention sur les 6 boutons d'apport : tant que la zone est VIDE (et la carte
  // active, pas en phase résultat), un halo passe d'un bouton au suivant, un par un, pour
  // montrer par où commencer. Dès qu'il y a du texte, la course s'arrête et le relais passe
  // au bouton « Générer » (qui pulse alors). Réduction de mouvement gérée côté CSS.
  // Un clic sur l'un des 6 boutons lance une action (OCR image/PDF, exemple, idée, dictée,
  // transcription) : la course s'arrête AUSSITÔT, sans attendre que le texte arrive — sinon elle
  // tournerait encore pendant la génération. « Fichier TXT » est couvert par zoneRemplie (le texte
  // arrive tout de suite après le choix du fichier).
  const actionEnCours = !!ocrLoading || exempleLoading || ideeLoading || isListening || isTranscribing
  const chaseActif = !zoneRemplie && !verrouille && !actionEnCours
  const [chaseIndex, setChaseIndex] = useState(0)
  useEffect(() => {
    if (!chaseActif) { setChaseIndex(0); return }
    const id = setInterval(() => setChaseIndex(i => (i + 1) % 6), 800)
    return () => clearInterval(id)
  }, [chaseActif])
  // Classe d'un bouton d'apport selon son rang (0→5) : « allumé » quand la course est sur lui.
  const btnChase = i => `btn-action${chaseActif && chaseIndex === i ? ' chase-on' : ''}`

  // Le bandeau d'origine est attaché au texte courant : si le texte est vidé (ex. « Créer » repart
  // d'une activité vierge), il n'a plus de sens → effacé.
  useEffect(() => { if (!texte) setSourceNote(null) }, [texte])

  // Dictée vocale en mode BATCH : enregistrer → stop → POST /api/transcribe (Groq
  // Whisper) → texte inséré à la fin. Le streaming temps réel Deepgram est une
  // amélioration future isolée sur la branche wip/deepgram-streaming.
  const isSupported = typeof MediaRecorder !== 'undefined'
    && !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)

  const playBeep = useCallback((count) => {
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext
      if (!Ctx) return
      if (!audioCtxRef.current) audioCtxRef.current = new Ctx()
      const ctx = audioCtxRef.current
      if (ctx.state === 'suspended') ctx.resume()
      for (let i = 0; i < count; i++) {
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()
        osc.connect(gain)
        gain.connect(ctx.destination)
        osc.type = 'sine'
        osc.frequency.value = 880
        const t = ctx.currentTime + i * 0.18
        gain.gain.setValueAtTime(0.15, t)
        gain.gain.exponentialRampToValueAtTime(0.001, t + 0.12)
        osc.start(t)
        osc.stop(t + 0.12)
      }
    } catch {}
  }, [])

  // Choisit un format d'enregistrement supporté par le navigateur ET accepté par Groq.
  function pickAudioMime() {
    const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
    for (const c of candidates) {
      if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(c)) return c
    }
    return ''
  }

  function stopMediaStream() {
    try { mediaStreamRef.current && mediaStreamRef.current.getTracks().forEach(t => t.stop()) } catch {}
    mediaStreamRef.current = null
    mediaRecorderRef.current = null
  }

  // Débranche l'analyseur de volume (sans fermer l'AudioContext, réutilisé pour les bips).
  function teardownAnalyser() {
    try { sourceRef.current && sourceRef.current.disconnect() } catch {}
    try { analyserRef.current && analyserRef.current.disconnect() } catch {}
    sourceRef.current = null
    analyserRef.current = null
  }

  // Envoi du blob audio au backend. Append-only via texteRef pour éviter la closure
  // stale (onChange peut arriver après plusieurs renders). Le nom de fichier porte une
  // EXTENSION VALIDE — première garantie du fix 400 (la seconde, le `model`, est côté backend).
  async function sendForTranscription(blob) {
    setIsTranscribing(true)
    try {
      const mime = blob.type || ''
      const ext = mime.includes('ogg') ? 'ogg' : mime.includes('mp4') ? 'mp4' : 'webm'
      const form = new FormData()
      form.append('file', blob, `dictee.${ext}`)
      const res = await apiFetch('/api/transcribe', {
        method: 'POST',
        credentials: 'include',
        body: form,
      }, TIMEOUT_LONG)
      const data = await lireReponse(res)
      const transcrit = (data.text || '').trim()
      if (transcrit) {
        const prev = texteRef.current || ''
        const sep = prev && !prev.endsWith(' ') && !prev.endsWith('\n') ? ' ' : ''
        onChange(prev + sep + transcrit)
        setSourceNote('dictee')
      }
    } catch (err) {
      showError(`Transcription impossible.\n\n${messagePourEcran(err)}`)
    } finally {
      setIsTranscribing(false)
    }
  }

  async function startRecording() {
    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch (err) {
      activeRef.current = false
      setIsListening(false)
      setIsReady(false)
      if (err && (err.name === 'NotAllowedError' || err.name === 'SecurityError')) {
        showError("Accès au microphone refusé.\n\nPour utiliser la dictée vocale, autorisez l'accès au microphone dans les paramètres du navigateur.")
      } else {
        showError(`Impossible d'accéder au microphone.\n\n${(err && err.message) || 'Erreur inconnue.'}`)
      }
      return
    }
    mediaStreamRef.current = stream
    // Visualiseur de volume : brancher un AnalyserNode sur le flux micro, SANS le router
    // vers la sortie (sinon le prof s'entendrait → larsen). Réutilise l'AudioContext des bips.
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext
      if (Ctx) {
        if (!audioCtxRef.current) audioCtxRef.current = new Ctx()
        const ctx = audioCtxRef.current
        if (ctx.state === 'suspended') ctx.resume()
        const src = ctx.createMediaStreamSource(stream)
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 64
        analyser.smoothingTimeConstant = 0.7
        src.connect(analyser)
        sourceRef.current = src
        analyserRef.current = analyser
      }
    } catch {}
    const mime = pickAudioMime()
    audioMimeRef.current = mime || 'audio/webm'
    audioChunksRef.current = []
    let recorder
    try {
      recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream)
    } catch (err) {
      stopMediaStream()
      activeRef.current = false
      setIsListening(false)
      setIsReady(false)
      showError(`Enregistrement audio impossible.\n\n${(err && err.message) || 'Format audio non supporté.'}`)
      return
    }
    recorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data) }
    recorder.onstop = async () => {
      const chunks = audioChunksRef.current
      audioChunksRef.current = []
      teardownAnalyser()
      stopMediaStream()
      if (!chunks.length) return
      const blob = new Blob(chunks, { type: audioMimeRef.current })
      await sendForTranscription(blob)
    }
    mediaRecorderRef.current = recorder
    recorder.start()
    // Bip "go" léger une fois le micro réellement ouvert (convention : 1 bip = start).
    setTimeout(() => {
      if (activeRef.current && !isReady) { setIsReady(true); playBeep(1) }
    }, 300)
  }

  // « Document d'exemple » (ex-« Tester un exemple ») — texte source généré par le LLM, ANCRÉ sur le référentiel
  // officiel du couple matière+niveau actif (plus de texte figé qui ignorait le niveau).
  // Règle d'or : si le couple n'a pas de référentiel → available:false → on n'injecte RIEN.
  async function handleExemple() {
    if (exempleLoading) return
    if (!confirmerRemplacement()) return
    setExempleLoading(true)
    setSourceNote(null)
    try {
      // Le couple ne part plus de l'écran : le serveur lit le couple de travail EN BASE
      // (décision du 25/07) — le document d'exemple suit toujours ce que le prof voit.
      const res = await apiFetch('/api/exemple-referentiel', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      }, TIMEOUT_LONG)
      const data = await lireReponse(res)
      if (data.available && data.texte) {
        onChange(data.texte)
        setSourceNote('exemple')
      } else if (data.message) {
        // Référentiel présent mais aucun extrait assez pertinent (seuil) : message honnête du backend.
        // Règle absolue : message = modale bloquante (showError), jamais inline.
        showError(data.message)
      } else {
        // Pas de référentiel pour ce couple : message générique (collez votre propre texte).
        showError(`Pas d'exemple tout prêt, pour le moment, pour ${(matiere && niveau) ? `${matiere} / ${niveau}` : 'ce couple'}.\n\nCollez votre propre texte de cours ou d'exercice ci-dessous — ou importez un fichier, une image, un PDF, ou dictez.`)
      }
    } catch (err) {
      showError(`Génération de l'exemple impossible.\n\n${messagePourEcran(err)}`)
    } finally {
      setExempleLoading(false)
    }
  }

  // « Propose-moi une idée » — même famille que « Document d'exemple » : aSchool fabrique
  // UNE idée de départ à partir de ce que le prof a déjà choisi (type + précision + niveau)
  // et du référentiel officiel, et l'ÉCRIT DANS LA ZONE TEXTE. Le prof reste le patron :
  // il relit, modifie ou efface, puis « Générer » suit le circuit normal.
  async function handleIdee() {
    if (ideeLoading) return
    if (!activiteTypeId) {
      showError("Choisissez d'abord un type d'activité dans les paramètres, puis recliquez sur « Propose-moi une idée ».")
      return
    }
    if (!confirmerRemplacement()) return
    setIdeeLoading(true)
    setSourceNote(null)
    try {
      // Le niveau ne part plus de l'écran : le serveur lit le couple de travail EN BASE.
      const res = await apiFetch('/api/proposer-idee', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ activite_type_id: activiteTypeId, sous_type: sousType || null }),
      }, TIMEOUT_LONG)
      const data = await lireReponse(res)
      if (data.available && data.texte) {
        onChange(data.texte)
        // L'IA propose aussi un titre court pour le champ « Objet » (ligne « Objet : » détachée
        // par le serveur) — remplacé comme le texte : l'idée arrive complète, le prof ajuste.
        if (data.objet && onObjetChange) onObjetChange(data.objet)
        setSourceNote('idee')
      } else if (data.message) {
        // Référentiel présent mais rien d'assez pertinent (seuil) : message honnête du backend.
        showError(data.message)
      } else {
        // Pas de référentiel pour ce niveau : on n'invente rien, on le dit.
        showError(`Pas de proposition possible pour le moment pour ${niveau ? `le niveau ${niveau}` : 'ce niveau'} (programme officiel pas encore chargé).\n\nDécrivez votre idée dans la zone de texte — ou dictez-la avec le micro.`)
      }
    } catch (err) {
      showError(`Proposition d'idée impossible.\n\n${messagePourEcran(err)}`)
    } finally {
      setIdeeLoading(false)
    }
  }

  function handleTxt(e) {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = ev => { onChange(ev.target.result); setSourceNote('txt') }
    reader.readAsText(file, 'utf-8')
    e.target.value = ''
  }

  async function handleOcr(e, type) {
    const file = e.target.files[0]
    if (!file) return
    e.target.value = ''
    setOcrLoading(type)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await apiFetch('/api/ocr', {
        method: 'POST',
        credentials: 'include',
        body: form,
      }, TIMEOUT_LONG)
      const data = await lireReponse(res)
      onChange(data.texte)
      setSourceNote(type === 'image' ? 'image' : 'pdf')
    } catch (err) {
      const source = type === 'image' ? "l'image" : 'le PDF'
      showError(`Extraction du texte depuis ${source} impossible.\n\n${messagePourEcran(err)}`)
    } finally {
      setOcrLoading(null)
    }
  }

  function handleDicteClick() {
    if (isTranscribing) return
    if (isListening) {
      // Bip stop AVANT l'arrêt — feedback sonore immédiat (convention : 2 bips = stop).
      playBeep(2)
      activeRef.current = false
      setIsListening(false)
      setIsReady(false)
      try { mediaRecorderRef.current && mediaRecorderRef.current.stop() } catch {}
    } else {
      if (!isSupported) {
        showError("La dictée vocale n'est pas disponible sur ce navigateur. Utilisez Edge ou un Chrome récent.")
        return
      }
      activeRef.current = true
      setIsListening(true)
      setIsReady(false)
      textareaRef.current?.focus()
      startRecording()
    }
  }

  // Visualiseur + chronomètre : démarrent quand le micro est prêt (bloc d'enregistrement
  // monté), s'arrêtent au stop. Le visualiseur écrit la hauteur des barres DIRECTEMENT sur
  // le DOM via refs — aucun setState par frame (pas de re-render 60×/s). Le chrono met à
  // jour un état 4×/s (léger).
  useEffect(() => {
    if (!(isListening && isReady)) return
    startTimeRef.current = performance.now()
    setElapsed(0)
    chronoRef.current = setInterval(() => {
      setElapsed((performance.now() - startTimeRef.current) / 1000)
    }, 250)
    const analyser = analyserRef.current
    const data = analyser ? new Uint8Array(analyser.frequencyBinCount) : null
    const tick = () => {
      if (analyser && data) {
        analyser.getByteFrequencyData(data)
        const levels = computeBarLevels(data, NB_BARS)
        for (let i = 0; i < NB_BARS; i++) {
          const el = barsRef.current[i]
          if (el) el.style.transform = `scaleY(${0.08 + levels[i] * 0.92})`
        }
      }
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(rafRef.current)
      clearInterval(chronoRef.current)
    }
  }, [isListening, isReady])

  // Filet de sécurité : composant démonté en pleine dictée → tout couper proprement.
  useEffect(() => {
    return () => {
      try { cancelAnimationFrame(rafRef.current) } catch {}
      try { clearInterval(chronoRef.current) } catch {}
      try { if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') mediaRecorderRef.current.stop() } catch {}
      teardownAnalyser()
      stopMediaStream()
    }
  }, [])

  return (
    <section className="bg-white rounded border border-gray-200 p-4">
      {/* En-tête : titre à gauche, la rangée des 6 boutons EN HAUT À DROITE, face au titre
          (son placement du 25/07). Deux familles, mêmes boutons : les 4 façons d'apporter un
          DOCUMENT (TXT / Image / PDF / Document d'exemple) puis les 2 façons de formuler la
          DEMANDE (Dicter / Propose-moi une idée). Sur écran étroit, la rangée passe dessous. */}
      <div className="mb-3" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        {/* Étape ② du stepper — le numéro passe en ✓ vert dès que du texte est saisi. */}
        <div className="section-title" style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <EtapeBadge n={2} fait={!!texte.trim()} actif={!texte.trim()} />
          <span style={{ display: 'inline-flex', alignItems: 'center' }}>
            Texte source
            <InfoGuide {...aideActivite('texte_source', { cahier: cahierPresent })} />
          </span>
          {/* Chevron plier/déplier — cerclé, à côté du « i ». Toujours visible ; grisé et inactif
              tant que la carte n'est pas verrouillée (le pliage n'a de sens qu'en phase résultat). */}
          <button
            type="button"
            disabled={!verrouille}
            onClick={() => setReplie(r => !r)}
            title={!verrouille ? "Pliage disponible une fois le résultat généré" : (replie ? "Déplier le texte source" : "Replier le texte source")}
            style={{ marginLeft: 6, width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: verrouille ? 'pointer' : 'not-allowed', opacity: verrouille ? 1 : 0.4, padding: 0, flexShrink: 0 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ transition: 'transform 0.2s', transform: replie ? 'rotate(-90deg)' : 'none' }}>
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
          {/* Pastille de PROVENANCE — visible seulement quand la carte est repliée (le corps, donc le
              bandeau d'origine, est masqué). Elle rappelle d'où vient CE texte : dictée, PDF, exemple,
              idée, fichier, image, ou saisi au clavier. Même rôle que les puces de la cartouche ①. */}
          {replie && zoneRemplie && (() => {
            const p = PROVENANCE[sourceNote] || { label: 'Saisi au clavier', Icon: IconClavier }
            const { Icon } = p
            return (
              <span
                title={`Provenance du texte source : ${p.label}`}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '2px 10px', fontSize: 12, fontWeight: 600, color: '#475569', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 999, flexShrink: 0 }}
              >
                <Icon /> {p.label}
              </span>
            )
          })()}
        </div>
        {/* Verrouillée en phase résultat (mode « Régénérer tel quel ») : les 6 boutons d'apport
            sont grisés et inertes d'un coup. « Changer votre demande » lève le verrou.
            Masqués quand la carte est repliée (phase résultat). */}
        {!replie && (
        <div data-guide="boutons" className="flex flex-wrap gap-2" style={{ justifyContent: 'flex-end', marginLeft: 'auto', opacity: verrouille ? 0.5 : 1, pointerEvents: verrouille ? 'none' : 'auto' }}>

          <label
            className={btnChase(0)}
            title="Importer un fichier texte .txt"
            style={enRetrait}
          >
            <IconTxt />
            Fichier TXT
            <input type="file" accept=".txt,text/plain" className="hidden" onChange={handleTxt}
              onClick={e => { if (!confirmerRemplacement()) e.preventDefault() }} />
          </label>

          <label
            className={btnChase(1)}
            title="Extraire le texte d'une image (scan, photo de document)"
            style={ocrLoading === 'image' ? { opacity: 0.6, pointerEvents: 'none' } : enRetrait}
          >
            <IconImage />
            {ocrLoading === 'image' ? 'Extraction…' : 'Image / Scan'}
            <input type="file" accept="image/jpeg,image/png,.jpg,.jpeg,.png" className="hidden"
              onChange={e => handleOcr(e, 'image')} disabled={!!ocrLoading}
              onClick={e => { if (!confirmerRemplacement()) e.preventDefault() }} />
          </label>

          <label
            className={btnChase(2)}
            title="Extraire le texte d'un PDF (PDF numérique uniquement — pas les PDF scannés)"
            style={ocrLoading === 'pdf' ? { opacity: 0.6, pointerEvents: 'none' } : enRetrait}
          >
            <IconPdf />
            {ocrLoading === 'pdf' ? 'Extraction…' : 'PDF'}
            <input type="file" accept="application/pdf,.pdf" className="hidden"
              onChange={e => handleOcr(e, 'pdf')} disabled={!!ocrLoading}
              onClick={e => { if (!confirmerRemplacement()) e.preventDefault() }} />
          </label>

          {/* 4e façon d'obtenir un DOCUMENT (famille TXT / Image / PDF) : un document d'exemple
              fabriqué par l'IA depuis le programme officiel — pour essayer sans rien sous la main. */}
          <button
            type="button"
            className={btnChase(3)}
            title={cahierPresent
              ? "aSchool fabrique un document d'exemple (un énoncé, une situation, un texte de travail) tiré du programme officiel de votre niveau et du cahier des charges de votre établissement — comme si vous aviez importé un document, pour essayer sans rien avoir sous la main."
              : "aSchool fabrique un document d'exemple (un énoncé, une situation, un texte de travail) tiré du programme officiel de votre niveau — comme si vous aviez importé un document, pour essayer sans rien avoir sous la main."}
            onClick={handleExemple}
            disabled={exempleLoading}
            style={exempleLoading ? { opacity: 0.6, cursor: 'wait' } : enRetrait}
          >
            {exempleLoading
              ? <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
              : <IconExemple />}
            {exempleLoading ? 'Génération…' : "Document d'exemple"}
          </button>

          <button
            type="button"
            className={btnChase(4)}
            title={
              !isSupported
                ? "La dictée n'est pas disponible sur ce navigateur. Utilisez Edge ou un Chrome récent."
                : isTranscribing
                  ? 'Transcription en cours…'
                  : isListening
                    ? "Arrêter l'enregistrement et transcrire"
                    : 'Dicter avec le microphone'
            }
            onClick={handleDicteClick}
            disabled={!isSupported || isTranscribing}
            style={
              !isSupported || isTranscribing
                ? { opacity: 0.5, cursor: isTranscribing ? 'wait' : 'not-allowed' }
                : isListening
                  ? { background: '#fff1f2', borderColor: '#fca5a5', color: '#dc2626' }
                  : {}
            }
          >
            <IconMic active={isListening} />
            {isTranscribing ? 'Transcription…' : isListening ? 'Arrêter' : 'Dicter'}
          </button>

          <button
            type="button"
            className={btnChase(5)}
            title={cahierPresent
              ? "aSchool écrit pour vous votre demande : une idée d'activité tirée de votre type d'activité, votre précision, le programme officiel et le cahier des charges de votre établissement — vous la retouchez librement, puis Générer."
              : "aSchool écrit pour vous votre demande : une idée d'activité tirée de votre type d'activité, votre précision et le programme officiel — vous la retouchez librement, puis Générer."}
            onClick={handleIdee}
            disabled={ideeLoading}
            style={ideeLoading ? { opacity: 0.6, cursor: 'wait' } : enRetrait}
          >
            {ideeLoading
              ? <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
              : <IconIdee />}
            {ideeLoading ? 'Génération…' : 'Propose-moi une idée'}
          </button>

        </div>
        )}

        {/* Le bouton « Générer l'activité » a été déplacé (28/07) dans sa propre cartouche ③
            « Générer l'activité » (voir App.jsx), avec le même habillage que les autres cartouches
            (badge, titre, « i », chevron). Il n'est plus rendu ici. */}
      </div>

      {/* Corps de la carte — masqué quand elle est repliée (phase résultat). */}
      {!replie && (<>

      {sourceNote && NOTES_SOURCE[sourceNote] && (
        <div style={{ marginBottom: 12, padding: '7px 12px', background: '#eff6ff', border: '1px solid #bfdbfe',
          borderRadius: 6, fontSize: 12, color: '#1d4ed8', animation: 'fadeInSoft 0.4s ease-out' }}>
          {(cahierPresent && NOTES_SOURCE_CAHIER[sourceNote]) || NOTES_SOURCE[sourceNote]}
        </div>
      )}

      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-500 mb-1">
          Objet <span className="font-normal text-gray-400">(optionnel — pour retrouver l'activité facilement)</span>
        </label>
        <input
          type="text"
          value={objet || ''}
          onChange={e => onObjetChange && onObjetChange(e.target.value)}
          placeholder="Ex : Dictée sur les accords, QCM chapitre 3 photosynthèse…"
          maxLength={150}
          disabled={verrouille}
          className="w-full border border-gray-200 rounded px-3 py-2 text-sm text-gray-700 focus:outline-none focus:border-blue-400"
          style={verrouille ? { background: '#f8fafc', color: '#94a3b8', cursor: 'not-allowed' } : undefined}
        />
      </div>

      <textarea
        ref={textareaRef}
        className="w-full border border-gray-300 rounded p-3 text-sm resize-y"
        rows={8}
        value={texte}
        disabled={verrouille}
        onChange={e => onChange(e.target.value)}
        placeholder={"Décrivez votre demande ou collez votre texte ici…\n— ou importez un fichier TXT, une image scannée ou un PDF\n— ou cliquez « Document d'exemple » pour un texte tiré du programme officiel\n— ou dictez avec le micro\n— ou laissez « Propose-moi une idée » écrire la demande à votre place"}
        style={{
          ...(isListening ? { borderColor: '#fca5a5', outline: 'none', boxShadow: '0 0 0 2px #fecaca' } : {}),
          ...(verrouille ? { background: '#f8fafc', color: '#94a3b8', cursor: 'not-allowed' } : {}),
        }}
      />

      {isListening && !isReady && (
        <div style={{
          marginTop: 6,
          padding: '7px 12px',
          background: '#f1f5f9',
          border: '1px solid #cbd5e1',
          borderRadius: 6,
          fontSize: 12,
          color: '#475569',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}>
            <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/>
          </svg>
          <span>Préparation du micro — patientez le bip avant de parler.</span>
        </div>
      )}

      {isListening && isReady && (
        <div style={{
          marginTop: 6,
          padding: '8px 12px',
          background: '#fff1f2',
          border: '1px solid #fca5a5',
          borderRadius: 6,
          fontSize: 12,
          color: '#dc2626',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}>
          <IconMic active={true} />
          {/* Visualiseur de volume — barres CSS pilotées par ref (preuve de vie temps réel) */}
          <div aria-hidden="true" style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 20, flexShrink: 0 }}>
            {Array.from({ length: NB_BARS }).map((_, i) => (
              <div
                key={i}
                ref={el => { barsRef.current[i] = el }}
                style={{
                  width: 3,
                  height: '100%',
                  background: '#dc2626',
                  borderRadius: 2,
                  transform: 'scaleY(0.08)',
                  transformOrigin: 'bottom',
                  transition: 'transform 0.08s ease-out',
                }}
              />
            ))}
          </div>
          <span style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 600, minWidth: 34, textAlign: 'center' }}>
            {formatTime(elapsed)}
          </span>
          <span>Je vous écoute — parlez normalement ; le texte s'affichera quand vous cliquerez sur <strong>Arrêter</strong>.</span>
        </div>
      )}

      {/* Jauge IA — même patron que côté admin : montée UNIQUEMENT pendant l'appel IA. */}
      {exempleLoading && (
        <JaugeAttente libelle="aSchool prépare un document d'exemple tiré du programme officiel de votre niveau…" />
      )}
      {ideeLoading && (
        <JaugeAttente libelle="aSchool lit le programme officiel de votre niveau et prépare une idée…" />
      )}

      {isTranscribing && (
        <div style={{
          marginTop: 6,
          padding: '7px 12px',
          background: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: 6,
          fontSize: 12,
          color: '#1d4ed8',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}>
            <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/>
          </svg>
          <span>Transcription en cours… le texte va s'insérer à la fin.</span>
        </div>
      )}

      </>)}

    </section>
  )
}
