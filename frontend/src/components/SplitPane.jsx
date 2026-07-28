import { useRef, useState, useCallback } from 'react'

// Deux colonnes côte à côte séparées par une poignée verticale que l'on tire à la souris pour
// ÉLARGIR l'une ou l'autre. La largeur choisie est mémorisée (localStorage) → elle revient au
// prochain passage. Double-clic sur la poignée = retour à l'équilibre. Sur écran étroit, les
// deux colonnes s'empilent (géré en CSS via .split-pane, cf. index.css) — pas de scroll latéral.
// Maison, sans librairie externe.
const MIN = 25   // % — bornes : aucune colonne ne peut disparaître
const MAX = 75

export default function SplitPane({ gauche, droite, storageKey = 'split', defautGauche = 50 }) {
  const ref = useRef(null)
  const enCours = useRef(false)
  const [pct, setPct] = useState(() => {
    try {
      const v = Number(localStorage.getItem(storageKey))
      if (v >= MIN && v <= MAX) return v
    } catch { /* localStorage indisponible : on garde le défaut */ }
    return defautGauche
  })

  const majDepuisX = useCallback((clientX) => {
    const el = ref.current
    if (!el) return
    const r = el.getBoundingClientRect()
    if (r.width <= 0) return
    const p = ((clientX - r.left) / r.width) * 100
    setPct(Math.min(MAX, Math.max(MIN, p)))
  }, [])

  function onPointerDown(e) {
    enCours.current = true
    try { e.currentTarget.setPointerCapture(e.pointerId) } catch { /* pas de capture : le move global prend le relais */ }
    e.preventDefault()
  }
  function onPointerMove(e) {
    if (enCours.current) majDepuisX(e.clientX)
  }
  function onPointerUp(e) {
    if (!enCours.current) return
    enCours.current = false
    try { e.currentTarget.releasePointerCapture(e.pointerId) } catch { /* rien à libérer */ }
    try { localStorage.setItem(storageKey, String(Math.round(pct))) } catch { /* ignore */ }
  }
  function reset() {
    setPct(defautGauche)
    try { localStorage.setItem(storageKey, String(defautGauche)) } catch { /* ignore */ }
  }

  return (
    <div ref={ref} className="split-pane">
      <div className="split-col" style={{ width: `${pct}%` }}>{gauche}</div>
      <div
        className="split-divider"
        role="separator"
        aria-orientation="vertical"
        title="Glisser pour élargir · double-clic pour rééquilibrer"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onDoubleClick={reset}
      >
        <span className="split-grip" />
      </div>
      <div className="split-col split-col-flex">{droite}</div>
    </div>
  )
}
