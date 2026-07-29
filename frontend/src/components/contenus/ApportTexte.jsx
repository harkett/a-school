// Rangée d'APPORT de texte de l'écran Séance — COPIE du procédé de la cartouche « Texte
// source » de l'activité (TexteSource.jsx), adaptée à la zone « Thème / objectif » :
// Fichier TXT · Image/Scan · PDF · Dicter (mêmes appels serveur /api/ocr et /api/transcribe,
// mêmes bips, même visualiseur de volume) + « Propose-moi un thème » (la version séance de
// « Propose-moi une idée » : POST /api/contenus/seances/proposer-theme, thème tiré du
// programme officiel). Le composant ne rend QUE la rangée de boutons + les bandeaux d'état :
// la zone de texte reste dans l'écran, remplie via onChange.
import { useCallback, useEffect, useRef, useState } from 'react'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_LONG } from '../../utils/api.js'
import { showError } from '../../errorDialog'
import { formatTime, computeBarLevels } from '../../utils/audioViz.js'

const NB_BARS = 12  // nombre de barres du visualiseur de volume (comme TexteSource)

// Bandeau « origine du texte » — une phrase par façon de remplir la zone (clavier = rien).
const NOTES_SOURCE = {
  theme:  'Thème proposé à partir du programme officiel de votre niveau — modifiez-le librement, puis générez.',
  dictee: 'Texte issu de votre dictée — relisez-le, corrigez si besoin, puis générez.',
  txt:    'Texte importé depuis votre fichier.',
  image:  'Texte extrait de votre image.',
  pdf:    'Texte extrait de votre PDF.',
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
const IconIdee = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 18h6"/><path d="M10 22h4"/>
    <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5.68.68 1.16 1.46 1.41 2.5"/>
  </svg>
)

export default function ApportTexte({ texte, onChange, disabled = false }) {
  const [ocrLoading, setOcrLoading] = useState(null)          // 'image' | 'pdf' | null
  const [themeLoading, setThemeLoading] = useState(false)     // « Propose-moi un thème » en cours
  const [isListening, setIsListening] = useState(false)
  const [isReady, setIsReady] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [sourceNote, setSourceNote] = useState(null)

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
  useEffect(() => { if (!texte) setSourceNote(null) }, [texte])

  // Zone déjà remplie = tout geste qui REMPLACERAIT le texte demande d'abord confirmation.
  const zoneRemplie = !!(texte || '').trim()
  function confirmerRemplacement() {
    if (!zoneRemplie) return true
    return window.confirm('Remplacer le texte actuel ? Le contenu de la zone sera perdu.')
  }

  // Course d'attention sur les 5 boutons tant que la zone est vide (même dispositif que
  // l'activité — classes btn-action / chase-on du CSS global).
  const actionEnCours = !!ocrLoading || themeLoading || isListening || isTranscribing
  const chaseActif = !zoneRemplie && !disabled && !actionEnCours
  const [chaseIndex, setChaseIndex] = useState(0)
  useEffect(() => {
    if (!chaseActif) { setChaseIndex(0); return }
    const id = setInterval(() => setChaseIndex(i => (i + 1) % 5), 800)
    return () => clearInterval(id)
  }, [chaseActif])
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
    } catch {}
  }, [])

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

  function teardownAnalyser() {
    try { sourceRef.current && sourceRef.current.disconnect() } catch {}
    try { analyserRef.current && analyserRef.current.disconnect() } catch {}
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
      try { mediaRecorderRef.current && mediaRecorderRef.current.stop() } catch {}
    } else {
      if (!isSupported) {
        showError("La dictée vocale n'est pas disponible sur ce navigateur. Utilisez Edge ou un Chrome récent.")
        return
      }
      activeRef.current = true
      setIsListening(true)
      setIsReady(false)
      startRecording()
    }
  }

  // Visualiseur + chronomètre (mutation DOM directe des barres, aucun setState par frame).
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

  // Filet : composant démonté en pleine dictée → tout couper proprement.
  useEffect(() => {
    return () => {
      try { cancelAnimationFrame(rafRef.current) } catch {}
      try { clearInterval(chronoRef.current) } catch {}
      try { if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') mediaRecorderRef.current.stop() } catch {}
      teardownAnalyser()
      stopMediaStream()
    }
  }, [])

  // ── Fichiers : mêmes appels serveur que l'activité. ──
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

  // ── « Propose-moi un thème » — la version séance de « Propose-moi une idée » :
  // thème tiré du programme officiel du niveau (couple lu EN BASE par le serveur). ──
  async function handleTheme() {
    if (themeLoading) return
    if (!confirmerRemplacement()) return
    setThemeLoading(true)
    setSourceNote(null)
    try {
      const res = await apiFetch('/api/contenus/seances/proposer-theme', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      }, TIMEOUT_LONG)
      const data = await lireReponse(res)
      if (data.available && data.texte) {
        onChange(data.texte)
        setSourceNote('theme')
      } else if (data.message) {
        showError(data.message)
      } else {
        showError('Pas de proposition possible pour le moment (programme officiel pas encore chargé pour votre niveau).\n\nDécrivez votre thème dans la zone de texte — ou dictez-le avec le micro.')
      }
    } catch (err) {
      showError(`Proposition de thème impossible.\n\n${messagePourEcran(err)}`)
    } finally {
      setThemeLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {/* La rangée des 5 boutons — grisée d'un coup quand l'écran est occupé (génération). */}
      <div className="flex flex-wrap gap-2" style={{ opacity: disabled ? 0.5 : 1, pointerEvents: disabled ? 'none' : 'auto' }}>

        <label className={btnChase(0)} title="Importer un fichier texte .txt">
          <IconTxt />
          Fichier TXT
          <input type="file" accept=".txt,text/plain" className="hidden" onChange={handleTxt}
            onClick={e => { if (!confirmerRemplacement()) e.preventDefault() }} />
        </label>

        <label
          className={btnChase(1)}
          title="Extraire le texte d'une image (scan, photo de document)"
          style={ocrLoading === 'image' ? { opacity: 0.6, pointerEvents: 'none' } : {}}
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
          style={ocrLoading === 'pdf' ? { opacity: 0.6, pointerEvents: 'none' } : {}}
        >
          <IconPdf />
          {ocrLoading === 'pdf' ? 'Extraction…' : 'PDF'}
          <input type="file" accept="application/pdf,.pdf" className="hidden"
            onChange={e => handleOcr(e, 'pdf')} disabled={!!ocrLoading}
            onClick={e => { if (!confirmerRemplacement()) e.preventDefault() }} />
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
          className={btnChase(4)}
          title="aSchool écrit pour vous un thème de séance tiré du programme officiel de votre niveau — vous le retouchez librement, puis Générer."
          onClick={handleTheme}
          disabled={themeLoading}
          style={themeLoading ? { opacity: 0.6, cursor: 'wait' } : {}}
        >
          {themeLoading
            ? <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
            : <IconIdee />}
          {themeLoading ? 'Génération…' : 'Propose-moi un thème'}
        </button>
      </div>

      {/* Bandeau d'origine du texte courant (le dernier geste gagne, effacé si la zone se vide). */}
      {sourceNote && NOTES_SOURCE[sourceNote] && (
        <div style={{ padding: '7px 12px', background: '#eff6ff', border: '1px solid #bfdbfe',
          borderRadius: 6, fontSize: 12, color: '#1d4ed8' }}>
          {NOTES_SOURCE[sourceNote]}
        </div>
      )}

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
      {isTranscribing && (
        <div style={{ padding: '7px 12px', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: 6, fontSize: 12, color: '#475569', display: 'flex', alignItems: 'center', gap: 8 }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}>
            <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/>
          </svg>
          <span>Transcription de votre dictée…</span>
        </div>
      )}
    </div>
  )
}
