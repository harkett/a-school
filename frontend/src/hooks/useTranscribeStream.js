import { useState, useRef, useCallback, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { showError } from '../errorDialog'

const AUDIO_MIME_CANDIDATES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/mp4',
]

function pickAudioMime() {
  if (typeof MediaRecorder === 'undefined') return ''
  for (const c of AUDIO_MIME_CANDIDATES) {
    if (MediaRecorder.isTypeSupported?.(c)) return c
  }
  return ''
}

function buildWsUrl() {
  const url = new URL('/api/transcribe/stream', window.location.href)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.searchParams.set('encoding', 'opus')
  return url.toString()
}

export function useTranscribeStream({ onFinal, onWarning } = {}) {
  const { user } = useAuth()

  const [state, setState] = useState('idle') // idle | requesting | recording | unsupported
  const [interim, setInterim] = useState('')
  const [isSupported, setIsSupported] = useState(true)

  const wsRef = useRef(null)
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const mimeRef = useRef('')
  const mountedRef = useRef(true)
  const stateRef = useRef(state)
  const userRef = useRef(user)
  const onFinalRef = useRef(onFinal)
  const onWarningRef = useRef(onWarning)

  useEffect(() => { stateRef.current = state }, [state])
  useEffect(() => { userRef.current = user }, [user])
  useEffect(() => { onFinalRef.current = onFinal }, [onFinal])
  useEffect(() => { onWarningRef.current = onWarning }, [onWarning])

  useEffect(() => {
    const mime = pickAudioMime()
    if (!mime) {
      setIsSupported(false)
      setState('unsupported')
    } else {
      mimeRef.current = mime
    }
  }, [])

  // Ordre critique : recorder.stop() → tracks.stop() → ws.close(1000).
  const cleanup = useCallback(() => {
    try { recorderRef.current?.stop() } catch {}
    try { streamRef.current?.getTracks().forEach(t => t.stop()) } catch {}
    try { wsRef.current?.close(1000) } catch {}
    recorderRef.current = null
    streamRef.current = null
    wsRef.current = null
    if (mountedRef.current) setInterim('')
  }, [])

  useEffect(() => {
    // Reset à true au (re)mount — React 18 strict mode mount/unmount/remount en dev
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      cleanup()
    }
  }, [cleanup])

  const stop = useCallback(() => {
    if (stateRef.current === 'idle' || stateRef.current === 'unsupported') return
    cleanup()
    if (mountedRef.current) setState('idle')
  }, [cleanup])

  const start = useCallback(async () => {
    if (stateRef.current !== 'idle') return

    setState('requesting')

    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch (err) {
      if (!mountedRef.current) return
      setState('idle')
      const messages = {
        NotAllowedError: 'Accès au microphone refusé. Pour utiliser la dictée, autorisez l\'accès dans les paramètres du navigateur.',
        SecurityError: 'Accès au microphone refusé. Pour utiliser la dictée, autorisez l\'accès dans les paramètres du navigateur.',
        NotFoundError: 'Aucun microphone détecté. Branchez un micro et réessayez.',
        NotReadableError: 'Le microphone est occupé par une autre application (Teams, Zoom...). Fermez l\'autre application et réessayez.',
      }
      showError(messages[err?.name] || `Impossible d'accéder au microphone.\n\n${err?.message || 'Erreur inconnue.'}`)
      return
    }

    if (!mountedRef.current) {
      stream.getTracks().forEach(t => t.stop())
      return
    }
    streamRef.current = stream

    let recorder
    try {
      recorder = new MediaRecorder(stream, { mimeType: mimeRef.current })
    } catch (err) {
      cleanup()
      if (!mountedRef.current) return
      setState('idle')
      showError(`Enregistrement audio impossible.\n\n${err?.message || 'Format audio non supporté.'}`)
      return
    }
    recorderRef.current = recorder

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(e.data)
      }
    }

    const ws = new WebSocket(buildWsUrl())
    wsRef.current = ws

    ws.onopen = () => {
      if (!mountedRef.current) return
      setState('recording')
      try {
        recorder.start(250)
      } catch (err) {
        cleanup()
        if (!mountedRef.current) return
        setState('idle')
        showError(`Démarrage de l'enregistrement impossible.\n\n${err?.message || 'Erreur inconnue.'}`)
      }
    }

    ws.onmessage = (event) => {
      if (!mountedRef.current) return
      let msg
      try { msg = JSON.parse(event.data) } catch { return }
      if (msg.type === 'transcript') {
        if (msg.is_final) {
          onFinalRef.current?.(msg.text)
          setInterim('')
        } else {
          setInterim(msg.text)
        }
      } else if (msg.type === 'session_warning') {
        onWarningRef.current?.(msg)
      }
    }

    ws.onerror = (event) => {
      console.warn('[useTranscribeStream] WebSocket error event', event)
    }

    ws.onclose = (event) => {
      cleanup()
      if (!mountedRef.current) return
      setState('idle')

      if (event.code === 1006 || !event.wasClean) {
        if (userRef.current) {
          showError('Service de dictée saturé. Réessayez dans quelques minutes.')
        } else {
          showError('Session expirée. Reconnectez-vous pour utiliser la dictée.')
        }
        return
      }

      if (event.code === 4408) {
        showError('Session de dictée expirée (inactivité ou durée maximale atteinte).')
      } else if (event.code === 4502) {
        showError('Service de dictée indisponible. Réessayez plus tard.')
      } else if (event.code === 4402) {
        showError('Service de dictée temporairement indisponible.')
      } else if (event.code === 1011) {
        showError('Erreur inattendue lors de la dictée. Réessayez.')
      }
    }
  }, [cleanup])

  return { state, interim, isSupported, start, stop }
}
