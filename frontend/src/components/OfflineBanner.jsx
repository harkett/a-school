import { useState, useEffect } from 'react'

export default function OfflineBanner() {
  const [offline, setOffline] = useState(!navigator.onLine)

  useEffect(() => {
    const goOffline = () => setOffline(true)
    const goOnline = () => setOffline(false)
    window.addEventListener('offline', goOffline)
    window.addEventListener('online', goOnline)
    return () => {
      window.removeEventListener('offline', goOffline)
      window.removeEventListener('online', goOnline)
    }
  }, [])

  if (!offline) return null

  return (
    <div
      style={{
        background: '#6b001d',
        color: '#fff',
        textAlign: 'center',
        padding: '8px 16px',
        fontSize: '14px',
        fontWeight: 500,
        position: 'sticky',
        top: 0,
        zIndex: 9999,
      }}
    >
      Hors connexion — reconnexion nécessaire pour générer des activités
    </div>
  )
}
