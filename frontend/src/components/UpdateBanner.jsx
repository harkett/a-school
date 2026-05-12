import { useEffect, useState } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'

const COUNTDOWN = 30

export default function UpdateBanner() {
  const { needRefresh: [needRefresh], updateServiceWorker } = useRegisterSW()
  const [secondes, setSecondes] = useState(COUNTDOWN)

  useEffect(() => {
    if (!needRefresh) return
    setSecondes(COUNTDOWN)
    const interval = setInterval(() => {
      setSecondes(s => {
        if (s <= 1) {
          clearInterval(interval)
          updateServiceWorker(true)
          return 0
        }
        return s - 1
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [needRefresh])

  if (!needRefresh) return null

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
        onClick={() => updateServiceWorker(true)}
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
