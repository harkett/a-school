import { useEffect, useRef, useState } from 'react'
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
      } catch { /* version illisible (hors ligne, serveur qui redémarre) : la prochaine visite reposera la question */ }
    }
    check()
    const onVisible = () => { if (!document.hidden) check() }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [])

  const showBanner = needRefresh || webUpdate

  // LE geste de mise à jour, gardé dans une ref : le service worker en donne une version neuve
  // à chaque rendu, et le décompte ne doit pas repartir de zéro pour autant. La ref est posée à
  // chaque rendu, le décompte ne dépend que de l'apparition de la bannière.
  const appliquerRef = useRef(null)
  useEffect(() => {
    appliquerRef.current = () => { needRefresh ? updateServiceWorker(true) : window.location.reload() }
  })

  // Le décompte : un tic par seconde, jamais remis à zéro en cours de route — la bannière ne
  // disparaît plus une fois montrée (la page se recharge au bout), `secondes` part de COUNTDOWN.
  useEffect(() => {
    if (!showBanner) return
    const interval = setInterval(() => setSecondes(s => Math.max(0, s - 1)), 1000)
    return () => clearInterval(interval)
  }, [showBanner])

  // Fin du décompte → on applique. Séparé du tic : recharger la page est un effet de bord, il
  // n'a rien à faire dans le calcul de la seconde suivante.
  useEffect(() => {
    if (showBanner && secondes === 0) appliquerRef.current?.()
  }, [showBanner, secondes])

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
        zIndex: 10000,
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
