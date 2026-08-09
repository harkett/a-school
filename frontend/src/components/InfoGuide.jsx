import { useState, useEffect, useRef, useCallback } from 'react'

// Petit « i » d'aide posé DERRIÈRE un titre. Deux niveaux, deux gestes :
//  - SURVOL → une bulle COURTE (prop `court`) ;
//  - CLIC   → une carte COMPLÈTE (prop `long`), ÉPINGLÉE : elle reste ouverte jusqu'au ✕,
//             à un clic AILLEURS, ou à la touche Échap (on ne piège jamais le prof).
// Composant générique (titre / court / long) : réutilisable partout où un titre a besoin d'aide.
// Les textes viennent du catalogue (utils/aideProfil.js), jamais réécrits ici.
//
// POURQUOI LA BULLE EST POSÉE EN `fixed` ET NON EN `absolute` (07/08/2026). Elle était placée
// dans le flux, sous le « i », avec `left: 0` : deux défauts qui se cumulaient. Un « i » proche
// du bord droit envoyait la carte hors de l'écran ; et surtout, dès que le « i » vivait dans une
// colonne qui défile (les cartouches de l'écran Créer, les listes de contenus), le conteneur la
// COUPAIT net — le prof lisait « Inclu… », « Qua… », « une… ». En `fixed`, la bulle n'appartient
// plus à aucun conteneur : rien ne peut la rogner, et sa position se recale pour rester dans la
// fenêtre, à gauche du « i » quand il n'y a plus la place à droite, au-dessus quand il n'y a plus
// la place en dessous.

const MARGE = 8         // ce qu'on garde entre la bulle et le bord de la fenêtre
const ECART = 6         // ce qu'on laisse entre le « i » et sa bulle

// Où poser une bulle de `largeur` × `hauteur` sous l'ancre, sans jamais sortir de la fenêtre.
function placement(ancre, largeur, hauteur) {
  const r = ancre.getBoundingClientRect()
  const dispoW = window.innerWidth
  const dispoH = window.innerHeight
  const left = Math.max(MARGE, Math.min(r.left, dispoW - largeur - MARGE))
  const sousLeI = r.bottom + ECART
  // Pas la place en dessous ? On passe au-dessus — mais seulement s'il y en a davantage là-haut.
  const debordeEnBas = sousLeI + hauteur > dispoH - MARGE
  const top = debordeEnBas && r.top > dispoH - r.bottom
    ? Math.max(MARGE, r.top - ECART - hauteur)
    : sousLeI
  return { left, top }
}

// Suit la position de l'ancre tant que la bulle est affichée : le prof peut faire défiler ou
// redimensionner, la bulle ne se décroche pas de son « i ».
//
// LA PREMIÈRE POSITION SE CALCULE AU GESTE (survol, clic), pas dans un effet : c'est au moment
// où le prof pointe le « i » qu'on sait où il est, et React déconseille de poser un état dans le
// corps d'un effet — l'écran serait dessiné une fois pour rien avant d'être redessiné. L'effet
// ci-dessous ne fait donc qu'ÉCOUTER ; il ne repositionne que sur un vrai mouvement.
function useSuivi(ref, actif, recaler) {
  useEffect(() => {
    if (!actif) return
    // `capture` : le défilement d'une colonne interne ne remonte pas jusqu'à `window` sans lui.
    window.addEventListener('scroll', recaler, true)
    window.addEventListener('resize', recaler)
    return () => {
      window.removeEventListener('scroll', recaler, true)
      window.removeEventListener('resize', recaler)
    }
  }, [actif, recaler])
}

export default function InfoGuide({ titre, court, long }) {
  const [survol, setSurvol] = useState(false)
  const [ouvert, setOuvert] = useState(false)   // carte épinglée (au clic)
  const wrapRef = useRef(null)

  const [posBulle, setPosBulle] = useState(null)
  const [posCarte, setPosCarte] = useState(null)

  const LARGEUR_BULLE = 240
  const LARGEUR_CARTE = Math.min(300, typeof window !== 'undefined' ? window.innerWidth - MARGE * 2 : 300)
  // Hauteurs ESTIMÉES : elles ne servent qu'à décider « au-dessus ou en dessous ». Une estimation
  // large fait basculer un peu tôt, ce qui est sans conséquence ; mesurer après coup ferait
  // sauter la bulle sous les yeux du prof.
  const recalerBulle = useCallback(() => {
    if (wrapRef.current) setPosBulle(placement(wrapRef.current, LARGEUR_BULLE, 80))
  }, [LARGEUR_BULLE])
  const recalerCarte = useCallback(() => {
    if (wrapRef.current) setPosCarte(placement(wrapRef.current, LARGEUR_CARTE, 200))
  }, [LARGEUR_CARTE])
  useSuivi(wrapRef, survol && !ouvert, recalerBulle)
  useSuivi(wrapRef, ouvert, recalerCarte)

  // Fermer la carte au clic AILLEURS et à Échap. Le listener n'existe que quand la carte est
  // ouverte (posé après le render qui l'ouvre → le clic d'ouverture ne la referme pas aussitôt).
  useEffect(() => {
    if (!ouvert) return
    const fermer = () => { setOuvert(false); setPosCarte(null) }
    const surClicDehors = e => { if (wrapRef.current && !wrapRef.current.contains(e.target)) fermer() }
    const surEchap = e => { if (e.key === 'Escape') fermer() }
    document.addEventListener('mousedown', surClicDehors)
    document.addEventListener('keydown', surEchap)
    return () => {
      document.removeEventListener('mousedown', surClicDehors)
      document.removeEventListener('keydown', surEchap)
    }
  }, [ouvert])

  return (
    <span ref={wrapRef} style={{ position: 'relative', display: 'inline-flex', verticalAlign: 'middle', marginLeft: 6 }}>
      <button
        type="button"
        aria-label={`Aide : ${titre}`}
        aria-expanded={ouvert}
        onMouseEnter={() => { recalerBulle(); setSurvol(true) }}
        onMouseLeave={() => { setSurvol(false); setPosBulle(null) }}
        onClick={() => {
          // Pas d'effet de bord dans un `setState(o => …)` : React peut rejouer cette fonction,
          // et le recalage partirait deux fois. On lit l'état courant, on décide, on pose.
          if (ouvert) { setOuvert(false); setPosCarte(null) }
          else { recalerCarte(); setOuvert(true) }
          setSurvol(false)
          setPosBulle(null)
        }}
        style={{
          width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1',
          background: ouvert ? '#2563eb' : '#fff', color: ouvert ? '#fff' : '#64748b',
          fontSize: 11, fontWeight: 700, fontStyle: 'italic', lineHeight: 1,
          textTransform: 'none', fontFamily: 'Georgia, "Times New Roman", serif',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', padding: 0, flexShrink: 0,
        }}
      >
        i
      </button>

      {/* SURVOL → bulle courte (masquée dès que la carte est épinglée, pour ne pas se superposer). */}
      {survol && !ouvert && posBulle && (
        <span role="tooltip" style={{
          position: 'fixed', top: posBulle.top, left: posBulle.left, zIndex: 10040,
          background: '#1e293b', color: '#fff', fontSize: 12, fontWeight: 400,
          textTransform: 'none', letterSpacing: 0, lineHeight: 1.4,
          padding: '6px 9px', borderRadius: 6, width: 'max-content', maxWidth: LARGEUR_BULLE,
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)', pointerEvents: 'none',
        }}>
          <span style={{ display: 'block' }}>{court}</span>
          {/* Indice d'usage : dit au prof qu'un clic ouvre la fiche complète (affiché seulement
              s'il y a une fiche `long` à ouvrir). Plus petit, italique, gris clair → discret. */}
          {long && (
            <span style={{ display: 'block', marginTop: 4, fontSize: 11, fontStyle: 'italic', color: '#cbd5e1' }}>
              Cliquez pour en savoir plus
            </span>
          )}
        </span>
      )}

      {/* CLIC → carte complète, épinglée. */}
      {ouvert && posCarte && (
        <span style={{
          position: 'fixed', top: posCarte.top, left: posCarte.left, zIndex: 10050,
          background: '#fff', color: '#374151', border: '1px solid #e2e8f0',
          borderRadius: 8, padding: '10px 12px', width: LARGEUR_CARTE,
          maxHeight: '70vh', overflowY: 'auto',
          textTransform: 'none', letterSpacing: 0,
          boxShadow: '0 8px 24px rgba(0,0,0,0.16)', display: 'block',
        }}>
          <span style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 4 }}>
            <strong style={{ fontSize: 12.5, color: '#1e293b' }}>{titre}</strong>
            <button type="button" aria-label="Fermer l'aide" onClick={() => { setOuvert(false); setPosCarte(null) }}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8',
                       fontSize: 15, lineHeight: 1, padding: 0, flexShrink: 0 }}>
              ✕
            </button>
          </span>
          <span style={{ display: 'block', fontSize: 12.5, fontWeight: 400, lineHeight: 1.5, whiteSpace: 'pre-line' }}>{long}</span>
        </span>
      )}
    </span>
  )
}
