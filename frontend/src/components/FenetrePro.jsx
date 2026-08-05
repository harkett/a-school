import { useState, useRef } from 'react'

// LA fenêtre de l'appli (sa demande du 25/07 : « fini les fenêtres rikiki ») — coquille
// UNIQUE : déplaçable par sa barre de titre, étirable par le coin bas-droit, sans voile
// (on continue de voir et toucher l'écran derrière). « Comment ça marche » et « Feedback »
// l'utilisent ; toute future fenêtre aussi — la mécanique n'est écrite qu'ICI.
export default function FenetrePro({ titre, onFermer, largeur = 400, hauteur = 'min(72vh, 640px)',
                                     minWidth = 340, minHeight = 240, zIndex = 450, children }) {
  const [pos, setPos] = useState({ x: Math.max(12, window.innerWidth - largeur - 28), y: 90 })
  const dragRef = useRef(null)   // décalage souris→coin pendant le glisser
  // « On est en train de glisser » est une chose QUI SE VOIT (le curseur passe en main fermée) :
  // c'est donc un état, pas une ref. La ref ne garde que le décalage, dont l'écran n'a rien à faire.
  const [enDrag, setEnDrag] = useState(false)

  function commencerDrag(e) {
    if (e.target.closest('button')) return   // le × garde son clic — pas de capture dessus
    e.preventDefault()
    dragRef.current = { dx: e.clientX - pos.x, dy: e.clientY - pos.y }
    setEnDrag(true)
    e.currentTarget.setPointerCapture(e.pointerId)
  }

  function glisser(e) {
    if (!dragRef.current) return
    setPos({
      x: Math.min(Math.max(e.clientX - dragRef.current.dx, 0), window.innerWidth - 80),
      y: Math.min(Math.max(e.clientY - dragRef.current.dy, 0), window.innerHeight - 40),
    })
  }

  function finirDrag(e) {
    dragRef.current = null
    setEnDrag(false)
    e.currentTarget.releasePointerCapture(e.pointerId)
  }

  return (
    <div style={{
      position: 'fixed', left: pos.x, top: pos.y, width: largeur, height: hauteur,
      minWidth, minHeight, maxWidth: '94vw', maxHeight: '92vh', zIndex,
      background: '#fff', borderRadius: 10, boxShadow: '0 12px 40px rgba(0,0,0,0.28)',
      display: 'flex', flexDirection: 'column', overflow: 'hidden', border: '1px solid #e2e8f0',
      resize: 'both',   // poignée en bas à droite : la fenêtre s'étire librement
    }}>
      {/* Barre de titre = la poignée : on attrape ici pour déplacer la fenêtre. */}
      <div
        onPointerDown={commencerDrag}
        onPointerMove={glisser}
        onPointerUp={finirDrag}
        title="Maintenez et faites glisser pour déplacer la fenêtre"
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
          padding: '10px 14px', background: 'var(--bleu)', color: '#fff', flexShrink: 0,
          cursor: enDrag ? 'grabbing' : 'grab', userSelect: 'none', touchAction: 'none',
        }}
      >
        <div style={{ fontWeight: 700, fontSize: 13 }}>{titre}</div>
        <button
          type="button"
          onClick={onFermer}
          title="Fermer la fenêtre"
          style={{ background: 'none', border: 'none', color: '#fff', fontSize: 18, lineHeight: 1,
                   cursor: 'pointer', padding: '0 2px', fontFamily: 'inherit' }}
        >
          ×
        </button>
      </div>
      {/* Le contenu remplit la fenêtre et défile ; il grandit avec l'étirement. */}
      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {children}
      </div>
    </div>
  )
}
