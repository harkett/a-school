import { useState, useEffect } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'
import { useAuth } from '../context/AuthContext'

const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream
const isStandalone = window.navigator.standalone === true
const isSafari = /Safari/.test(navigator.userAgent) && !/CriOS|FxiOS|OPiOS|mercury/.test(navigator.userAgent)

export default function IOSInstallBanner() {
  const { user } = useAuth()
  const { needRefresh: [needRefresh] } = useRegisterSW()
  const [show, setShow] = useState(false)
  const [offline, setOffline] = useState(!navigator.onLine)

  useEffect(() => {
    const goOffline = () => setOffline(true)
    const goOnline  = () => setOffline(false)
    window.addEventListener('offline', goOffline)
    window.addEventListener('online',  goOnline)
    return () => {
      window.removeEventListener('offline', goOffline)
      window.removeEventListener('online',  goOnline)
    }
  }, [])

  useEffect(() => {
    if (!user || !isIOS || isStandalone || !isSafari) return
    if (localStorage.getItem('iosInstallDismissed') === '1') return
    const t = setTimeout(() => setShow(true), 5000)
    return () => clearTimeout(t)
  }, [user])

  if (!show || offline || needRefresh) return null

  return (
    <div
      style={{
        background: '#6b001d',
        color: '#fff',
        padding: '9px 16px',
        fontSize: '13px',
        fontWeight: 500,
        position: 'sticky',
        top: 0,
        zIndex: 9997,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '14px',
      }}
    >
      <span style={{ lineHeight: 1.4 }}>
        Installer aSchool sur iPhone — Touchez{' '}
        <svg
          width="14" height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ verticalAlign: 'middle', marginBottom: '2px' }}
          aria-hidden="true"
        >
          <polyline points="8 6 12 2 16 6" />
          <line x1="12" y1="2" x2="12" y2="15" />
          <path d="M20 13v7a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-7" />
        </svg>
        {' '}puis <strong>«Sur l'écran d'accueil»</strong>
      </span>
      <button
        onClick={() => {
          localStorage.setItem('iosInstallDismissed', '1')
          setShow(false)
        }}
        title="Ne plus afficher"
        aria-label="Fermer"
        style={{
          background: 'transparent',
          color: '#fff',
          border: '1px solid rgba(255,255,255,0.5)',
          borderRadius: '4px',
          padding: '3px 9px',
          fontSize: '12px',
          cursor: 'pointer',
          flexShrink: 0,
          lineHeight: 1.4,
        }}
      >
        ✕
      </button>
    </div>
  )
}
