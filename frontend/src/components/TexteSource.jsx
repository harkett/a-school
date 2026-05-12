import { useState, useRef } from 'react'
import { fetchWithTimeout, TIMEOUT_GROQ } from '../utils/api.js'

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

export default function TexteSource({ texte, onChange, objet, onObjetChange }) {
  const [isListening, setIsListening] = useState(false)
  const [ocrLoading, setOcrLoading] = useState(null) // 'image' | 'pdf' | null
  const [ocrErreur, setOcrErreur] = useState(null)
  const recognitionRef = useRef(null)
  const activeRef = useRef(false)
  const accumulatedRef = useRef('')
  const textareaRef = useRef(null)

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
    setOcrErreur(null)
    setOcrLoading(type)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetchWithTimeout('/api/ocr', {
        method: 'POST',
        credentials: 'include',
        body: form,
      }, TIMEOUT_GROQ)
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `Erreur ${res.status}`)
      onChange(data.texte)
    } catch (err) {
      setOcrErreur(err.message)
    } finally {
      setOcrLoading(null)
    }
  }

  function startRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.lang = 'fr-FR'
    recognition.continuous = true
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      let interim = ''
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript
        if (event.results[i].isFinal) final += t
        else interim += t
      }
      if (final) {
        accumulatedRef.current = accumulatedRef.current + (accumulatedRef.current ? ' ' : '') + final.trim()
        onChange(accumulatedRef.current)
      } else if (interim) {
        onChange(accumulatedRef.current + (accumulatedRef.current ? ' ' : '') + interim)
      }
    }

    recognition.onerror = (e) => {
      if (e.error === 'not-allowed') {
        alert('Accès au microphone refusé — autorisez-le dans les paramètres du navigateur.')
        activeRef.current = false
        setIsListening(false)
      }
    }

    recognition.onend = () => {
      if (activeRef.current) {
        startRecognition()
      } else {
        setIsListening(false)
      }
    }

    recognitionRef.current = recognition
    recognition.start()
  }

  function toggleDicte() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert('Dictée vocale non supportée par ce navigateur.')
      return
    }
    if (activeRef.current) {
      activeRef.current = false
      recognitionRef.current?.stop()
      setIsListening(false)
      return
    }
    activeRef.current = true
    accumulatedRef.current = texte
    setIsListening(true)
    textareaRef.current?.focus()
    startRecognition()
  }

  return (
    <section className="bg-white rounded border border-gray-200 p-4">
      <div className="section-title mb-3">Texte source</div>

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

      {isListening && (
        <div style={{
          marginTop: 6,
          padding: '7px 12px',
          background: '#fff1f2',
          border: '1px solid #fca5a5',
          borderRadius: 6,
          fontSize: 12,
          color: '#dc2626',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <span style={{ fontSize: 16, lineHeight: 1 }}>🎤</span>
          <span>Dictée active — parlez maintenant. Le texte s'affiche automatiquement. Cliquez <strong>Arrêter</strong> pour terminer.</span>
        </div>
      )}

      {ocrErreur && (
        <div className="mt-2 bg-red-50 border border-red-200 text-red-700 rounded p-2 text-xs">
          {ocrErreur}
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
          className="btn-action"
          title={isListening ? 'Cliquez pour arrêter la dictée' : 'Cliquer pour dicter — parlez en français, cliquez à nouveau pour arrêter'}
          onClick={toggleDicte}
          style={isListening ? { color: '#dc2626', borderColor: '#fca5a5', background: '#fff1f2' } : {}}
        >
          <IconMic active={isListening} />
          {isListening ? 'Arrêter' : 'Dicter'}
        </button>

      </div>
    </section>
  )
}
