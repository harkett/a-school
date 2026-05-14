import { useEffect, useState } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'
import { APP_VERSION } from '../version'

const COUNTDOWN = 30

export default function UpdateBanner() {
  const { needRefresh: [needRefresh], updateServiceWorker } = useRegisterSW()
  const [webUpdate, setWebUpdate] = useState(false)
  const [secondes, setSecondes] = useState(COUNTDOWN)

  useEffect(() => {
    if (APP_VERSION.endsWith('-dev')) return
    const check = async () => {
      try {
        const res = await fetch('/api/version', { cache: 'no-store' })
        if (!res.ok) return
        const { version } = await res.json()
        if (version && version !== APP_VERSION) setWebUpdate(true)
      } catch {}
    }
    check()
    const onVisible = () => { if (!document.hidden) check() }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [])

  const showBanner = needRefresh || webUpdate

  useEffect(() => {
    if (!showBanner) return
    setSecondes(COUNTDOWN)
    const interval = setInterval(() => {
      setSecondes(s => {
        if (s <= 1) {
          clearInterval(interval)
          needRefresh ? updateServiceWorker(true) : window.location.reload()
          return 0
        }
        return s - 1
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [showBanner])

  if (!showBanner) return null

  const handleUpdate = () => {
    needRefresh ? updateServiceWorker(true) : window.location.reload()
  }

  return (
    <div
      style={{
        background: '#6b001d',
        color: '#fff',
        textAlign: 'center',
        padding: '8px 16px',
        fontSize: '13px',
        fontWeight: 500,
        position: 'sticky',
        top: 0,
        zIndex: 9998,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '16px',
      }}
    >
      <span>Mise à jour disponible — rechargement automatique dans {secondes}s</span>
      <button
        onClick={handleUpdate}
        title="Recharger maintenant pour appliquer la mise à jour"
        style={{
          background: '#fff',
          color: '#6b001d',
          border: 'none',
          borderRadius: '4px',
          padding: '4px 12px',
          fontSize: '12px',
          fontWeight: 600,
          cursor: 'pointer',
          whiteSpace: 'nowrap',
        }}
      >
        Actualiser maintenant
      </button>
    </div>
  )
}
