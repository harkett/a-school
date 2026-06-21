import { useState, useRef, useEffect, useCallback } from 'react'
import { apiFetch, TIMEOUT_GROQ } from '../utils/api.js'
import { showError } from '../errorDialog'
import { formatTime, computeBarLevels } from '../utils/audioViz.js'

const NB_BARS = 12  // nombre de barres du visualiseur de volume

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

export default function TexteSource({ texte, onChange, objet, onObjetChange, matiere, niveau }) {
  const [ocrLoading, setOcrLoading] = useState(null) // 'image' | 'pdf' | null
  const [isListening, setIsListening] = useState(false)   // micro ouvert (enregistrement en cours)
  const [isReady, setIsReady] = useState(false)           // micro prêt après le bip "go"
  const [isTranscribing, setIsTranscribing] = useState(false) // POST /api/transcribe en cours
  const [elapsed, setElapsed] = useState(0)               // chrono d'enregistrement (secondes)
  const [exempleLoading, setExempleLoading] = useState(false) // génération d'un exemple ancré en cours
  const [exempleNote, setExempleNote] = useState(null)        // 'ancre' (exemple injecté) | 'absent' (pas de référentiel pour ce couple)
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

  // Le bandeau « exemple généré » est attaché au texte courant : si le texte est vidé
  // (ex. « Créer » repart d'une activité vierge), le bandeau n'a plus de sens → on l'efface.
  useEffect(() => { if (!texte) setExempleNote(null) }, [texte])

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
      }, TIMEOUT_GROQ)
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `Erreur ${res.status}`)
      const transcrit = (data.text || '').trim()
      if (transcrit) {
        const prev = texteRef.current || ''
        const sep = prev && !prev.endsWith(' ') && !prev.endsWith('\n') ? ' ' : ''
        onChange(prev + sep + transcrit)
      }
    } catch (err) {
      showError(`Transcription impossible.\n\n${err.message}`)
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

  // « Tester un exemple » — texte source généré par le LLM, ANCRÉ sur le référentiel
  // officiel du couple matière+niveau actif (plus de texte figé qui ignorait le niveau).
  // Règle d'or : si le couple n'a pas de référentiel → available:false → on n'injecte RIEN.
  async function handleExemple() {
    if (exempleLoading) return
    setExempleLoading(true)
    setExempleNote(null)
    try {
      const res = await apiFetch('/api/exemple-referentiel', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ matiere, niveau }),
      }, TIMEOUT_GROQ)
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `Erreur ${res.status}`)
      if (data.available && data.texte) {
        onChange(data.texte)
        setExempleNote('ancre')
      } else if (data.message) {
        // Référentiel présent mais aucun extrait assez pertinent (seuil) : message honnête du backend.
        // Règle absolue : message = modale bloquante (showError), jamais inline.
        showError(data.message)
      } else {
        // Pas de référentiel pour ce couple : message générique (collez votre propre texte).
        showError(`Pas d'exemple tout prêt, pour le moment, pour ${(matiere && niveau) ? `${matiere} / ${niveau}` : 'ce couple'}.\n\nCollez votre propre texte de cours ou d'exercice ci-dessous — ou importez un fichier, une image, un PDF, ou dictez.`)
      }
    } catch (err) {
      showError(`Génération de l'exemple impossible.\n\n${err.message}`)
    } finally {
      setExempleLoading(false)
    }
  }

  function handleTxt(e) {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = ev => onChange(ev.target.result)
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
      }, TIMEOUT_GROQ)
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `Erreur ${res.status}`)
      onChange(data.texte)
    } catch (err) {
      const source = type === 'image' ? "l'image" : 'le PDF'
      showError(`Extraction du texte depuis ${source} impossible.\n\n${err.message}`)
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
      <div className="mb-3" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-title">Texte source</div>
        <button
          type="button"
          title="Générer un exemple de texte source à partir du référentiel officiel de votre niveau"
          onClick={handleExemple}
          disabled={exempleLoading}
          style={{ fontSize: '11px', color: '#6366f1', background: 'none', border: '1px solid #c7d2fe',
            borderRadius: '5px', padding: '3px 10px', cursor: exempleLoading ? 'wait' : 'pointer',
            display: 'flex', alignItems: 'center', gap: '5px', opacity: exempleLoading ? 0.6 : 1 }}
        >
          {exempleLoading
            ? <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
            : <IconExemple />}
          {exempleLoading ? 'Génération...' : 'Tester un exemple'}
        </button>
      </div>

      {exempleNote === 'ancre' && (
        <div style={{ marginBottom: 12, padding: '7px 12px', background: '#eff6ff', border: '1px solid #bfdbfe',
          borderRadius: 6, fontSize: 12, color: '#1d4ed8', animation: 'fadeInSoft 0.4s ease-out' }}>
          Exemple généré depuis le référentiel officiel de votre niveau — adaptez-le si besoin.
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
          className="w-full border border-gray-200 rounded px-3 py-2 text-sm text-gray-700 focus:outline-none focus:border-blue-400"
        />
      </div>

      <textarea
        ref={textareaRef}
        className="w-full border border-gray-300 rounded p-3 text-sm resize-y"
        rows={8}
        value={texte}
        onChange={e => onChange(e.target.value)}
        placeholder={"Collez un extrait de texte ici\n— ou importez un fichier TXT\n— ou extrayez le texte d'une image (scan, photo)\n— ou extrayez le texte d'un PDF\n— ou dictez avec le micro"}
        style={isListening ? { borderColor: '#fca5a5', outline: 'none', boxShadow: '0 0 0 2px #fecaca' } : {}}
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

      <div className="mt-3 flex flex-wrap gap-2">

        <label
          className="btn-action"
          title="Importer un fichier texte .txt"
        >
          <IconTxt />
          Fichier TXT
          <input type="file" accept=".txt,text/plain" className="hidden" onChange={handleTxt} />
        </label>

        <label
          className="btn-action"
          title="Extraire le texte d'une image (scan, photo de document)"
          style={ocrLoading === 'image' ? { opacity: 0.6, pointerEvents: 'none' } : {}}
        >
          <IconImage />
          {ocrLoading === 'image' ? 'Extraction…' : 'Image / Scan'}
          <input type="file" accept="image/jpeg,image/png,.jpg,.jpeg,.png" className="hidden"
            onChange={e => handleOcr(e, 'image')} disabled={!!ocrLoading} />
        </label>

        <label
          className="btn-action"
          title="Extraire le texte d'un PDF (PDF numérique uniquement — pas les PDF scannés)"
          style={ocrLoading === 'pdf' ? { opacity: 0.6, pointerEvents: 'none' } : {}}
        >
          <IconPdf />
          {ocrLoading === 'pdf' ? 'Extraction…' : 'PDF'}
          <input type="file" accept="application/pdf,.pdf" className="hidden"
            onChange={e => handleOcr(e, 'pdf')} disabled={!!ocrLoading} />
        </label>

        <button
          type="button"
          className="btn-action"
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

      </div>
    </section>
  )
}
