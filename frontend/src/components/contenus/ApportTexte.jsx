// Rangée d'APPORT de texte de l'écran Séance — COPIE du procédé de la cartouche « Texte
// source » de l'activité (TexteSource.jsx) : Fichier TXT · Image/Scan · PDF · Dicter (mêmes
// appels serveur /api/ocr et /api/transcribe, mêmes bips, même visualiseur de volume) +
// UN bouton « Propose-moi… » CONFIGURABLE par zone (prop `proposer`) — principe maison :
// aSchool propose tout, le prof décide et corrige. La même rangée sert ainsi à la zone
// Thème (« Propose-moi un thème ») ET à la zone Compétences (« Propose-moi des
// compétences »). Le composant ne rend QUE la rangée de boutons + les bandeaux d'état :
// la zone de texte reste dans l'écran, remplie via onChange. L'ORIGINE du texte (fichier,
// image, PDF, dictée, proposition) est signalée au parent via onSourceNote : c'est l'écran
// qui l'affiche (pastille sur la ligne du titre, visible cartouche repliée comme dépliée).
//
// `proposer` = { label, title, jauge, note, avant?, action } :
//  - label/title : le bouton ; jauge : le libellé de la JaugeAttente (règle IA) ;
//  - note : la clé d'origine posée via onSourceNote quand la proposition aboutit ;
//  - avant() : garde métier AVANT la confirmation de remplacement (false = stop) ;
//  - action() : l'appel serveur ; rend le TEXTE à poser dans la zone, ou null (échec déjà
//    montré en boîte de dialogue par l'action elle-même).
import { useCallback, useEffect, useRef, useState } from 'react'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_LONG } from '../../utils/api.js'
import { showError } from '../../errorDialog'
import { demanderConfirmation } from '../../confirmDialog'
import { formatTime, computeBarLevels } from '../../utils/audioViz.js'
import JaugeAttente from '../JaugeAttente.jsx'
import IconSablier from '../IconSablier.jsx'
import { JAUGE_IMAGE, JAUGE_PDF, JAUGE_DICTEE, messageMicro } from '../../utils/apportTexte.js'
import { IconIdee, IconImage, IconMic, IconPdf, IconTxt } from '../icones.jsx'

const NB_BARS = 12  // nombre de barres du visualiseur de volume (comme TexteSource)

// Boutons un chouïa plus petits que ceux de l'activité (demande utilisateur du 30/07) —
// la rangée vit dans l'en-tête de la cartouche, face au titre, elle doit rester discrète.
const PETIT = { fontSize: '0.75rem', padding: '0.32rem 0.65rem' }

// Le sablier et les libellés de jauge communs aux deux rangées d'apport vivent maintenant dans
// des modules partagés (IconSablier.jsx, utils/apportTexte.js) — ils étaient écrits deux fois.


export default function ApportTexte({ texte, onChange, onSourceNote, proposer, disabled = false }) {
  const [ocrLoading, setOcrLoading] = useState(null)          // 'image' | 'pdf' | null
  const [propLoading, setPropLoading] = useState(false)       // bouton « Propose-moi… » en cours
  const [isListening, setIsListening] = useState(false)
  const [isReady, setIsReady] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [elapsed, setElapsed] = useState(0)

  const audioCtxRef = useRef(null)
  const texteRef = useRef(texte)
  const mediaRecorderRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const audioChunksRef = useRef([])
  const audioMimeRef = useRef('audio/webm')
  const activeRef = useRef(false)
  const analyserRef = useRef(null)
  const sourceRef = useRef(null)
  const rafRef = useRef(null)
  const chronoRef = useRef(null)
  const startTimeRef = useRef(0)
  const barsRef = useRef([])

  useEffect(() => { texteRef.current = texte }, [texte])
  // Zone vidée = plus d'origine à afficher (le dernier geste gagne, effacé si vide).
  useEffect(() => { if (!texte) onSourceNote(null) }, [texte, onSourceNote])

  // Zone déjà remplie = tout geste qui REMPLACERAIT le texte demande d'abord confirmation.
  const zoneRemplie = !!(texte || '').trim()

  // La question se pose JUSTE AVANT de remplacer, jamais avant d'ouvrir le sélecteur de fichiers
  // (voir la note détaillée dans TexteSource.jsx : bloquer l'ouverture obligerait à rouvrir le
  // sélecteur par `input.click()` après la réponse, ce que les navigateurs n'autorisent que sous
  // conditions — Safari est strict — et qu'aucun test du projet ne couvre).
  async function confirmerRemplacement(nomFichier) {
    if (!zoneRemplie) return true
    return demanderConfirmation({
      titre: 'Remplacer le texte actuel ?',
      message: nomFichier
        ? `Le contenu de la zone sera remplacé par « ${nomFichier} », et le texte actuel sera perdu.`
        : 'Le contenu de la zone sera perdu.',
      confirmLabel: 'Remplacer',
    })
  }

  // Course d'attention sur les boutons tant que la zone est vide (même dispositif que
  // l'activité — classes btn-action / chase-on du CSS global). 5 boutons, ou 4 quand la zone
  // n'a rien à proposer : sans ce compte, le rang 4 s'allumait sur un bouton absent et la
  // course marquait un temps mort.
  const actionEnCours = !!ocrLoading || propLoading || isListening || isTranscribing
  const chaseActif = !zoneRemplie && !disabled && !actionEnCours
  // Le rang allumé n'est lu que quand la course tourne (`btnChase` juste dessous le vérifie) :
  // il n'y a donc rien à remettre à zéro quand elle s'arrête.
  const nbBoutons = proposer ? 5 : 4
  const [chaseIndex, setChaseIndex] = useState(0)
  useEffect(() => {
    if (!chaseActif) return
    let i = 0
    const id = setInterval(() => { i = (i + 1) % nbBoutons; setChaseIndex(i) }, 800)
    return () => clearInterval(id)
  }, [chaseActif, nbBoutons])
  const btnChase = i => `btn-action${chaseActif && chaseIndex === i ? ' chase-on' : ''}`

  // ── Dictée : même mécanique BATCH que TexteSource (bips, visualiseur, /api/transcribe). ──
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
    } catch { /* le bip est un confort : un navigateur qui refuse l'AudioContext dicte quand même */ }
  }, [])

  function pickAudioMime() {
    const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
    for (const c of candidates) {
      if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(c)) return c
    }
    return ''
  }

  function stopMediaStream() {
    try { mediaStreamRef.current && mediaStreamRef.current.getTracks().forEach(t => t.stop()) } catch { /* pistes déjà coupées (onglet fermé, micro débranché) : on voulait juste ça */ }
    mediaStreamRef.current = null
    mediaRecorderRef.current = null
  }

  function teardownAnalyser() {
    try { sourceRef.current && sourceRef.current.disconnect() } catch { /* nœud déjà débranché : c'est l'état voulu */ }
    try { analyserRef.current && analyserRef.current.disconnect() } catch { /* idem */ }
    sourceRef.current = null
    analyserRef.current = null
  }

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
        onSourceNote('dictee')
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
      showError(messageMicro(err))
      return
    }
    mediaStreamRef.current = stream
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
    } catch { /* le vumètre est un confort : sans lui la dictée s'enregistre pareil */ }
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
    setTimeout(() => {
      if (activeRef.current && !isReady) { setIsReady(true); playBeep(1) }
    }, 300)
  }

  function handleDicteClick() {
    if (isTranscribing) return
    if (isListening) {
      playBeep(2)
      activeRef.current = false
      setIsListening(false)
      setIsReady(false)
      try { mediaRecorderRef.current && mediaRecorderRef.current.stop() } catch { /* enregistreur déjà arrêté (fin de flux) : c'est le but du clic */ }
    } else {
      if (!isSupported) {
        showError("La dictée vocale n'est pas disponible sur ce navigateur. Utilisez Edge ou un Chrome récent.")
        return
      }
      activeRef.current = true
      setIsListening(true)
      setIsReady(false)
      setElapsed(0)          // nouvelle dictée : le chrono repart de zéro, dès le clic
      startRecording()
    }
  }

  // Visualiseur + chronomètre (mutation DOM directe des barres, aucun setState par frame).
  useEffect(() => {
    if (!(isListening && isReady)) return
    startTimeRef.current = performance.now()
    // Rien à remettre à zéro ici : le clic qui lance la dictée l'a déjà fait (handleDicteClick).
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

  // Filet : composant démonté en pleine dictée → tout couper proprement.
  useEffect(() => {
    return () => {
      // Démontage : chaque coupure est indépendante des autres — une qui échoue (déjà coupée)
      // ne doit pas empêcher les suivantes, c'est tout l'intérêt des trois try séparés.
      try { cancelAnimationFrame(rafRef.current) } catch { /* boucle déjà arrêtée */ }
      try { clearInterval(chronoRef.current) } catch { /* chrono déjà arrêté */ }
      try { if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') mediaRecorderRef.current.stop() } catch { /* enregistreur déjà arrêté */ }
      teardownAnalyser()
      stopMediaStream()
    }
  }, [])

  // ── Fichiers : mêmes appels serveur que l'activité. ──
  async function handleTxt(e) {
    const file = e.target.files[0]
    e.target.value = ''
    if (!file) return
    if (!await confirmerRemplacement(file.name)) return
    const reader = new FileReader()
    reader.onload = ev => { onChange(ev.target.result); onSourceNote('txt') }
    reader.readAsText(file, 'utf-8')
  }

  async function handleOcr(e, type) {
    const file = e.target.files[0]
    e.target.value = ''
    if (!file) return
    // Demandé AVANT l'extraction : inutile de faire travailler aSchool sur un fichier dont le
    // texte ne remplacera rien.
    if (!await confirmerRemplacement(file.name)) return
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
      onSourceNote(type === 'image' ? 'image' : 'pdf')
    } catch (err) {
      const source = type === 'image' ? "l'image" : 'le PDF'
      showError(`Extraction du texte depuis ${source} impossible.\n\n${messagePourEcran(err)}`)
    } finally {
      setOcrLoading(null)
    }
  }

  // ── Bouton « Propose-moi… » — l'appel serveur vit chez le PARENT (prop `proposer.action`) ;
  // ici on garde les gestes communs : garde métier, confirmation de remplacement, sablier +
  // jauge, pose du texte et de son origine. ──
  async function handleProposer() {
    if (propLoading) return
    if (proposer.avant && !proposer.avant()) return
    if (!await confirmerRemplacement()) return
    setPropLoading(true)
    onSourceNote(null)
    try {
      const texteRecu = await proposer.action()
      if (texteRecu) {
        onChange(texteRecu)
        onSourceNote(proposer.note)
      }
    } finally {
      setPropLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {/* La rangée des 5 boutons — alignée à DROITE, face au titre de la cartouche (même
          placement que l'activité) ; grisée d'un coup quand l'écran est occupé. L'origine du
          texte n'est plus affichée ici : l'écran la porte en pastille sur la ligne du titre. */}
      <div className="flex flex-wrap gap-2" style={{ justifyContent: 'flex-end', opacity: disabled ? 0.5 : 1, pointerEvents: disabled ? 'none' : 'auto' }}>

        <label className={btnChase(0)} title="Importer un fichier texte .txt" style={PETIT}>
          <IconTxt />
          Fichier TXT
          <input type="file" accept=".txt,text/plain" className="hidden" onChange={handleTxt}
            />
        </label>

        <label
          className={btnChase(1)}
          title="Extraire le texte d'une image (scan, photo de document)"
          style={ocrLoading === 'image' ? { ...PETIT, opacity: 0.6, pointerEvents: 'none' } : PETIT}
        >
          {ocrLoading === 'image' ? <IconSablier /> : <IconImage />}
          {ocrLoading === 'image' ? 'Extraction…' : 'Image / Scan'}
          <input type="file" accept="image/jpeg,image/png,.jpg,.jpeg,.png" className="hidden"
            onChange={e => handleOcr(e, 'image')} disabled={!!ocrLoading}
            />
        </label>

        <label
          className={btnChase(2)}
          title="Extraire le texte d'un PDF (PDF numérique uniquement — pas les PDF scannés)"
          style={ocrLoading === 'pdf' ? { ...PETIT, opacity: 0.6, pointerEvents: 'none' } : PETIT}
        >
          {ocrLoading === 'pdf' ? <IconSablier /> : <IconPdf />}
          {ocrLoading === 'pdf' ? 'Extraction…' : 'PDF'}
          <input type="file" accept="application/pdf,.pdf" className="hidden"
            onChange={e => handleOcr(e, 'pdf')} disabled={!!ocrLoading}
            />
        </label>

        <button
          type="button"
          className={btnChase(3)}
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
              ? { ...PETIT, opacity: 0.5, cursor: isTranscribing ? 'wait' : 'not-allowed' }
              : isListening
                ? { ...PETIT, background: '#fff1f2', borderColor: '#fca5a5', color: '#dc2626' }
                : PETIT
          }
        >
          {isTranscribing ? <IconSablier /> : <IconMic active={isListening} />}
          {isTranscribing ? 'Transcription…' : isListening ? 'Arrêter' : 'Dicter'}
        </button>

        {/* `proposer` est facultatif : une zone où aSchool n'a rien à proposer garde les quatre
            façons d'apporter un texte, sans cinquième bouton. */}
        {proposer && (
          <button
            type="button"
            className={btnChase(4)}
            title={proposer.title}
            onClick={handleProposer}
            disabled={propLoading}
            style={propLoading ? { ...PETIT, opacity: 0.6, cursor: 'wait' } : PETIT}
          >
            {propLoading ? <IconSablier /> : <IconIdee />}
            {propLoading ? 'Génération…' : proposer.label}
          </button>
        )}
      </div>

      {/* Bandeaux de dictée : préparation du micro, puis enregistrement (barres + chrono). */}
      {isListening && !isReady && (
        <div style={{ padding: '7px 12px', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: 6, fontSize: 12, color: '#475569', display: 'flex', alignItems: 'center', gap: 8 }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}>
            <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/>
          </svg>
          <span>Préparation du micro — patientez le bip avant de parler.</span>
        </div>
      )}
      {isListening && isReady && (
        <div style={{ padding: '8px 12px', background: '#fff1f2', border: '1px solid #fca5a5', borderRadius: 6, fontSize: 12, color: '#dc2626', display: 'flex', alignItems: 'center', gap: 10 }}>
          <IconMic active={true} />
          <div aria-hidden="true" style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 20, flexShrink: 0 }}>
            {Array.from({ length: NB_BARS }).map((_, i) => (
              <div
                key={i}
                ref={el => { barsRef.current[i] = el }}
                style={{ width: 3, height: 20, borderRadius: 2, background: '#dc2626', transform: 'scaleY(0.08)', transformOrigin: 'bottom' }}
              />
            ))}
          </div>
          <span style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{formatTime(elapsed)}</span>
          <span>Enregistrement en cours — cliquez « Arrêter » quand vous avez terminé.</span>
        </div>
      )}
      {/* Jauges IA — règle maison (sablier ET jauge) : TOUS les appels IA de cette zone
          l'ont, « Propose-moi… » comme les deux OCR et la transcription de la dictée.
          La préparation du micro et l'enregistrement, eux, ne sont pas des appels IA :
          ils gardent leurs bandeaux (barres de volume, chrono). */}
      {propLoading && (
        <JaugeAttente libelle={proposer.jauge} />
      )}
      {ocrLoading === 'image' && (
        <JaugeAttente libelle={JAUGE_IMAGE} />
      )}
      {ocrLoading === 'pdf' && (
        <JaugeAttente libelle={JAUGE_PDF} />
      )}
      {isTranscribing && (
        <JaugeAttente libelle={JAUGE_DICTEE} />
      )}
    </div>
  )
}
