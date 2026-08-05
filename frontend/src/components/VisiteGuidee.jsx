import { useState, useEffect, useCallback } from 'react'
import { GUIDE_CREER } from '../utils/aideCreer.js'

const LARGEUR_BULLE = 330
const MARGE = 12

// Visite guidée de l'écran Créer : chaque bulle s'accroche au VRAI élément (ancre
// data-guide posée sur le composant) — un élément qui bouge emmène sa bulle, un élément
// absent (ex. champ conditionnel) fait sauter son étape. Les phrases viennent du
// catalogue unique (utils/aideCreer.js) : les mêmes que la fenêtre « Comment ça marche »
// et le centre d'aide — jamais un texte réécrit ici.
export default function VisiteGuidee({ onFermer, onOuvrirAide }) {
  const [index, setIndex] = useState(0)
  const [rect, setRect] = useState(null)

  const etape = GUIDE_CREER[index]

  const mesurer = useCallback(() => {
    if (!etape) return
    const el = document.querySelector(`[data-guide="${etape.cible}"]`)
    if (!el) { setRect(null); return }
    const r = el.getBoundingClientRect()
    setRect({ top: r.top, left: r.left, width: r.width, height: r.height, bottom: r.bottom })
  }, [etape])

  // Élément absent de l'écran (conditionnel) → étape sautée ; dernière étape absente → fin.
  // Tout se décide APRÈS peinture : c'est l'écran réel qui dit si l'étape a une cible à montrer,
  // et où elle est. Le saut d'étape comme la mesure sortent donc de la même image.
  useEffect(() => {
    if (!etape) { onFermer(); return }
    const id = requestAnimationFrame(() => {
      const el = document.querySelector(`[data-guide="${etape.cible}"]`)
      if (!el) {
        if (index + 1 < GUIDE_CREER.length) setIndex(index + 1)
        else onFermer()
        return
      }
      el.scrollIntoView({ block: 'nearest' })
      mesurer()   // le rect est en coordonnées de la fenêtre : après le scroll éventuel
    })
    return () => cancelAnimationFrame(id)
  }, [index, etape, mesurer, onFermer])

  // L'écran vit (redimensionnement, défilement d'un panneau) → la bulle suit son élément.
  useEffect(() => {
    window.addEventListener('resize', mesurer)
    window.addEventListener('scroll', mesurer, true)
    return () => {
      window.removeEventListener('resize', mesurer)
      window.removeEventListener('scroll', mesurer, true)
    }
  }, [mesurer])

  // Échap = passer (même geste que le bouton).
  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') onFermer() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onFermer])

  if (!etape || !rect) return null

  const derniere = index === GUIDE_CREER.length - 1
  // Bulle sous l'élément si la place le permet, sinon au-dessus ; jamais hors de l'écran.
  const dessous = rect.bottom + 190 < window.innerHeight
  const left = Math.min(Math.max(rect.left, MARGE), window.innerWidth - LARGEUR_BULLE - MARGE)
  const posBulle = dessous
    ? { top: rect.bottom + 14, left }
    : { bottom: window.innerHeight - rect.top + 14, left }

  return (
    <>
      {/* Voile cliquable transparent : bloque l'écran pendant la visite (un clic à côté = Suivant). */}
      <div
        style={{ position: 'fixed', inset: 0, zIndex: 640 }}
        onClick={() => (derniere ? onFermer() : setIndex(index + 1))}
      />
      {/* Projecteur : l'élément commenté reste en pleine lumière, le reste s'assombrit. */}
      <div style={{
        position: 'fixed', zIndex: 641, pointerEvents: 'none',
        top: rect.top - 6, left: rect.left - 6, width: rect.width + 12, height: rect.height + 12,
        borderRadius: 10, boxShadow: '0 0 0 9999px rgba(15,23,42,0.55)',
        transition: 'top 0.25s ease, left 0.25s ease, width 0.25s ease, height 0.25s ease',
      }} />
      {/* La bulle : titre + phrase du catalogue unique. */}
      <div style={{
        position: 'fixed', zIndex: 642, width: LARGEUR_BULLE, ...posBulle,
        background: '#fff', borderRadius: 10, padding: '14px 16px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.3)', display: 'flex', flexDirection: 'column', gap: 8,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: '#1e293b' }}>{etape.titre}</div>
          <div style={{ fontSize: 11, color: '#94a3b8', whiteSpace: 'nowrap' }}>{index + 1} / {GUIDE_CREER.length}</div>
        </div>
        <p style={{ margin: 0, fontSize: 13, color: '#374151', lineHeight: 1.55 }}>{etape.phrase}</p>
        <button
          type="button"
          onClick={() => onOuvrirAide(etape.cle)}
          title="Ouvrir le centre d'aide sur l'explication complète"
          style={{ alignSelf: 'flex-start', background: 'none', border: 'none', padding: 0, fontSize: 12,
                   color: '#1F6EEB', textDecoration: 'underline', cursor: 'pointer', fontFamily: 'inherit' }}
        >
          En savoir plus
        </button>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
          <button
            type="button"
            onClick={onFermer}
            title="Quitter la visite guidée"
            style={{ background: 'none', border: 'none', padding: 0, fontSize: 12, color: '#64748b',
                     textDecoration: 'underline', cursor: 'pointer', fontFamily: 'inherit' }}
          >
            Passer
          </button>
          <button
            type="button"
            onClick={() => (derniere ? onFermer() : setIndex(index + 1))}
            title={derniere ? 'Terminer la visite' : "Passer à l'élément suivant"}
            style={{ padding: '6px 16px', fontSize: 13, borderRadius: 6, border: 'none',
                     background: 'var(--bleu)', color: '#fff', fontWeight: 600, cursor: 'pointer' }}
          >
            {derniere ? 'Terminer' : 'Suivant'}
          </button>
        </div>
      </div>
    </>
  )
}
