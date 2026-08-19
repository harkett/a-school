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

// La carte s'ouvre large, se prend par son titre pour la déplacer et s'étire par son coin —
// PARTOUT. Une procédure en quatre points dans une colonne de 300 px se lisait en accordéon,
// texte coupé et ascenseur invisible. Essayé sur une seule fiche (14/08/2026), l'usage a
// confirmé : la prop `redimensionnable` a disparu le 15/08/2026, il n'y a plus qu'une carte.
// `variante` : 'aide' → le « i » bleu de l'aide ; 'astuce' → un « a » violet, même mécanique
// (survol = phrase courte, clic = fiche épinglée). Deux lettres, un seul composant : une astuce
// se lit exactement comme une aide, le prof n'a qu'un geste à connaître.
export default function InfoGuide({ titre, court, long, variante = 'aide' }) {
  const estAstuce = variante === 'astuce'
  const [survol, setSurvol] = useState(false)
  const [ouvert, setOuvert] = useState(false)   // carte épinglée (au clic)
  const wrapRef = useRef(null)

  const [posBulle, setPosBulle] = useState(null)
  const [posCarte, setPosCarte] = useState(null)

  const LARGEUR_BULLE = 240
  const LARGEUR_VOULUE = 560
  const LARGEUR_CARTE = Math.min(LARGEUR_VOULUE, typeof window !== 'undefined' ? window.innerWidth - MARGE * 2 : LARGEUR_VOULUE)
  // Hauteurs ESTIMÉES : elles ne servent qu'à décider « au-dessus ou en dessous ». Une estimation
  // large fait basculer un peu tôt, ce qui est sans conséquence ; mesurer après coup ferait
  // sauter la bulle sous les yeux du prof.
  const recalerBulle = useCallback(() => {
    if (wrapRef.current) setPosBulle(placement(wrapRef.current, LARGEUR_BULLE, 80))
  }, [LARGEUR_BULLE])
  // Une carte que l'utilisateur a DÉPLACÉE reste où il l'a mise : la recaler sur son « i » au
  // moindre défilement lui reprendrait des mains ce qu'il vient de poser.
  const [deplacee, setDeplacee] = useState(false)
  const recalerCarte = useCallback(() => {
    if (wrapRef.current && !deplacee) setPosCarte(placement(wrapRef.current, LARGEUR_CARTE, 200))
  }, [LARGEUR_CARTE, deplacee])
  useSuivi(wrapRef, survol && !ouvert, recalerBulle)
  useSuivi(wrapRef, ouvert, recalerCarte)

  // TAILLE POSÉE À LA MAIN. Tant que le prof n'a rien étiré, elle vaut `null` : la carte prend sa
  // largeur d'ouverture et la hauteur de son texte. Dès qu'il tire un bord, c'est lui qui décide.
  const [taille, setTaille] = useState({ w: null, h: null })
  const MIN_L = 280
  const MIN_H = 160

  // Fermer la carte au clic AILLEURS et à Échap. Le listener n'existe que quand la carte est
  // ouverte (posé après le render qui l'ouvre → le clic d'ouverture ne la referme pas aussitôt).
  useEffect(() => {
    if (!ouvert) return
    const fermer = () => { setOuvert(false); setPosCarte(null); setDeplacee(false); setTaille({ w: null, h: null }) }
    const surClicDehors = e => { if (wrapRef.current && !wrapRef.current.contains(e.target)) fermer() }
    const surEchap = e => { if (e.key === 'Escape') fermer() }
    document.addEventListener('mousedown', surClicDehors)
    document.addEventListener('keydown', surEchap)
    return () => {
      document.removeEventListener('mousedown', surClicDehors)
      document.removeEventListener('keydown', surEchap)
    }
  }, [ouvert])

  // CE QUI RESTE SOUS LA CARTE, en pixels. C'était LE défaut (15/08/2026) : la hauteur était
  // plafonnée à `85vh` dans l'absolu, sans regarder où la carte était posée. Ouverte sous un « i »
  // du haut d'écran, une fiche longue descendait sous le bord de la fenêtre : le texte était coupé
  // par l'ÉCRAN et non par la carte — donc pas d'ascenseur (rien ne débordait, de son point de
  // vue) et pas de poignée (le coin bas était hors de vue). Bornée à la place réelle, la carte
  // reste entière à l'écran, son texte défile, ses bords se prennent.
  const hauteurDispo = posCarte && typeof window !== 'undefined'
    ? Math.max(MIN_H, window.innerHeight - posCarte.top - MARGE)
    : undefined
  // Même borne à droite : élargie sans regarder où elle est posée, la carte sortirait par le côté
  // et son bord droit — donc sa prise en largeur — passerait hors de l'écran.
  const largeurDispo = posCarte && typeof window !== 'undefined'
    ? Math.max(MIN_L, window.innerWidth - posCarte.left - MARGE)
    : undefined

  // Étirer par un bord. `sens` porte 'e' (largeur), 's' (hauteur) ou les deux (le coin).
  const etirer = (sens) => (e) => {
    if (e.button !== 0) return
    const boite = e.currentTarget.parentNode.getBoundingClientRect()
    const depart = { x: e.clientX, y: e.clientY, w: boite.width, h: boite.height }
    const plafondL = largeurDispo
    const bouger = ev => setTaille({
      w: sens.includes('e')
        ? Math.min(plafondL, Math.max(MIN_L, depart.w + ev.clientX - depart.x))
        : depart.w,
      h: sens.includes('s')
        ? Math.min(hauteurDispo, Math.max(MIN_H, depart.h + ev.clientY - depart.y))
        : depart.h,
    })
    const lacher = () => {
      document.removeEventListener('mousemove', bouger)
      document.removeEventListener('mouseup', lacher)
    }
    document.addEventListener('mousemove', bouger)
    document.addEventListener('mouseup', lacher)
    e.preventDefault()   // sinon le navigateur sélectionne le texte de la carte pendant le geste
  }

  // Glisser la carte par sa barre de titre. Les écouteurs vivent sur `document` : la souris sort
  // vite de la carte pendant le geste, et un écouteur posé sur elle lâcherait prise en route.
  const prendreLaCarte = e => {
    if (!posCarte || e.button !== 0) return
    const depart = { x: e.clientX, y: e.clientY, top: posCarte.top, left: posCarte.left }
    const bouger = ev => setPosCarte({
      top: Math.max(MARGE, depart.top + ev.clientY - depart.y),
      left: depart.left + ev.clientX - depart.x,
    })
    const lacher = () => {
      document.removeEventListener('mousemove', bouger)
      document.removeEventListener('mouseup', lacher)
    }
    setDeplacee(true)
    document.addEventListener('mousemove', bouger)
    document.addEventListener('mouseup', lacher)
    e.preventDefault()   // sinon le navigateur sélectionne le texte du titre pendant le geste
  }

  return (
    <span ref={wrapRef} style={{ position: 'relative', display: 'inline-flex', verticalAlign: 'middle', marginLeft: 6 }}>
      <button
        type="button"
        aria-label={`${estAstuce ? 'Astuce' : 'Aide'} : ${titre}`}
        aria-expanded={ouvert}
        onMouseEnter={() => { recalerBulle(); setSurvol(true) }}
        onMouseLeave={() => { setSurvol(false); setPosBulle(null) }}
        onClick={() => {
          // Pas d'effet de bord dans un `setState(o => …)` : React peut rejouer cette fonction,
          // et le recalage partirait deux fois. On lit l'état courant, on décide, on pose.
          if (ouvert) { setOuvert(false); setPosCarte(null); setDeplacee(false) }
          else { setDeplacee(false); setTaille({ w: null, h: null }); recalerCarte(); setOuvert(true) }
          setSurvol(false)
          setPosBulle(null)
        }}
        style={{
          width: 16, height: 16, borderRadius: '50%',
          border: `1px solid ${estAstuce ? '#ddd6fe' : '#cbd5e1'}`,
          background: ouvert ? (estAstuce ? '#7c3aed' : '#2563eb') : '#fff',
          color: ouvert ? '#fff' : (estAstuce ? '#7c3aed' : '#64748b'),
          fontSize: 11, fontWeight: 700, fontStyle: 'italic', lineHeight: 1,
          textTransform: 'none', fontFamily: 'Georgia, "Times New Roman", serif',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', padding: 0, flexShrink: 0,
        }}
      >
        {estAstuce ? 'a' : 'i'}
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

      {/* CLIC → carte complète, épinglée. La carte est un CADRE qui ne défile pas (titre et
          poignées restent en place) ; seul le texte défile, dans sa propre zone. */}
      {ouvert && posCarte && (
        <span style={{
          position: 'fixed', top: posCarte.top, left: posCarte.left, zIndex: 10050,
          width: taille.w ?? LARGEUR_CARTE, height: taille.h ?? undefined,
          minWidth: MIN_L, maxWidth: largeurDispo, maxHeight: hauteurDispo,
          background: '#fff', color: '#374151', border: '1px solid #e2e8f0',
          borderRadius: 8, padding: 0,
          textTransform: 'none', letterSpacing: 0,
          boxShadow: '0 8px 24px rgba(0,0,0,0.16)',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
        }}>
          <span onMouseDown={prendreLaCarte}
            title="Glissez pour déplacer — tirez un bord ou le coin pour agrandir"
            style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8,
                     padding: '10px 12px 4px', flexShrink: 0, cursor: 'move' }}>
            <strong style={{ fontSize: 12.5, color: '#1e293b' }}>{titre}</strong>
            <button type="button" aria-label="Fermer l'aide" onClick={() => { setOuvert(false); setPosCarte(null); setTaille({ w: null, h: null }) }}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8',
                       fontSize: 15, lineHeight: 1, padding: 0, flexShrink: 0 }}>
              ✕
            </button>
          </span>

          {/* Le texte, et lui seul, défile. `minHeight: 0` : sans lui un enfant de colonne flex
              refuse de rétrécir sous sa hauteur naturelle et l'ascenseur ne sort jamais.
              `scrollbarColor` : l'ascenseur du navigateur est si pâle qu'il passe pour une
              bordure — teinté, le prof VOIT qu'il reste du texte au lieu de le deviner. */}
          <span style={{
            display: 'block', flex: '1 1 auto', minHeight: 0,
            overflowY: 'auto', overflowX: 'hidden',
            scrollbarWidth: 'auto', scrollbarColor: '#94a3b8 #eef2f7',
            padding: '0 12px 12px', fontSize: 12.5, fontWeight: 400, lineHeight: 1.5,
            whiteSpace: 'pre-line',
          }}>{long}</span>

          {/* TROIS PRISES, pas une. `resize: both` du navigateur ne donne qu'un coin, invisible sur
              fond blanc et inutilisable dès que la carte touche un bord : ici le bord droit règle
              la largeur, le bord bas la hauteur, le coin les deux. */}
          <span onMouseDown={etirer('e')} aria-hidden="true"
            style={{ position: 'absolute', top: 30, right: 0, width: 8, height: 'calc(100% - 46px)', cursor: 'ew-resize' }} />
          <span onMouseDown={etirer('s')} aria-hidden="true"
            style={{ position: 'absolute', left: 0, bottom: 0, height: 8, width: 'calc(100% - 18px)', cursor: 'ns-resize' }} />
          <span onMouseDown={etirer('es')} aria-hidden="true"
            title="Tirez pour agrandir"
            style={{ position: 'absolute', right: 2, bottom: 2, width: 14, height: 14, cursor: 'nwse-resize',
                     borderRight: '2px solid #94a3b8', borderBottom: '2px solid #94a3b8',
                     borderBottomRightRadius: 6 }} />
        </span>
      )}
    </span>
  )
}
