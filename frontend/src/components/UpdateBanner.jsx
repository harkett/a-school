import { useRegisterSW } from 'virtual:pwa-register/react'

export default function UpdateBanner() {
  const { needRefresh: [needRefresh], updateServiceWorker } = useRegisterSW()

  if (!needRefresh) return null

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
        zIndex: 9998,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '16px',
      }}
    >
      <span>Nouvelle version disponible</span>
      <button
        onClick={() => updateServiceWorker(true)}
        title="Recharger pour appliquer la mise à jour"
        style={{
          background: '#fff',
          color: '#6b001d',
          border: 'none',
          borderRadius: '4px',
          padding: '4px 12px',
          fontSize: '13px',
          fontWeight: 600,
          cursor: 'pointer',
        }}
      >
        Actualiser
      </button>
    </div>
  )
}
