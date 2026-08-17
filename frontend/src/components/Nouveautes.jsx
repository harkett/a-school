import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

// « NOUVEAU » — l'annonce d'une fonctionnalité qui vient d'arriver, dans le bandeau d'accueil.
//
// CE QUE FONT LES APPLICATIONS SÉRIEUSES, et rien de plus : une pastille discrète posée près
// du titre, qui se clique pour ouvrir un petit panneau, et qui S'ÉTEINT une fois lue. Pas de
// bulle qui saute au visage, pas de fenêtre à fermer avant de travailler — l'annonce attend
// qu'on veuille bien la regarder. Une pastille qui ne s'éteint jamais, c'est une pastille
// qu'on n'ouvre plus : elle ne revient donc que le jour où l'administration annonce autre
// chose.
//
// CE QUI DÉCIDE, C'EST L'ADMINISTRATION : une fonctionnalité n'arrive ici que si ses deux
// cases sont cochées — livrée, puis annoncée en nouveauté (Admin → Tâches à faire → Bientôt
// disponible). Le serveur ne renvoie que celles-là.
//
// « Lu » est gardé dans le navigateur, par code de fonctionnalité : c'est un confort
// d'affichage, pas une donnée de la plateforme. Une nouveauté ré-annoncée des mois plus tard
// porte le même code — d'où la date d'annonce jointe à la clé : ré-annoncer rallume la
// pastille sans qu'on ait à inventer un second code.
const CLE_VUES = 'aschool_nouveautes_vues'

function lireVues() {
  try { return JSON.parse(localStorage.getItem(CLE_VUES) || '[]') } catch { return [] }
}

export default function Nouveautes() {
  const [ouvert, setOuvert] = useState(false)
  const [vues, setVues]     = useState(lireVues)
  const zone = useRef(null)

  const { data: nouveautes = [] } = useQuery({
    queryKey: ['nouveautes'],
    queryFn: async () => {
      const r = await fetchWithTimeout('/api/nouveautes', { credentials: 'include' }, TIMEOUT_STD)
      return r.ok ? await r.json() : []
    },
    // Une nouveauté n'arrive pas à la seconde près : inutile de redemander à chaque écran.
    staleTime: 5 * 60 * 1000,
  })

  // Fermeture au clic à côté et à Échap — comme toutes les fenêtres de l'application.
  useEffect(() => {
    if (!ouvert) return
    const dehors = e => { if (zone.current && !zone.current.contains(e.target)) setOuvert(false) }
    const echap  = e => { if (e.key === 'Escape') setOuvert(false) }
    document.addEventListener('mousedown', dehors)
    document.addEventListener('keydown', echap)
    return () => {
      document.removeEventListener('mousedown', dehors)
      document.removeEventListener('keydown', echap)
    }
  }, [ouvert])

  if (nouveautes.length === 0) return null

  const nonLues = nouveautes.filter(n => !vues.includes(n.key))

  function marquerLues() {
    const toutes = [...new Set([...vues, ...nouveautes.map(n => n.key)])]
    setVues(toutes)
    try { localStorage.setItem(CLE_VUES, JSON.stringify(toutes)) } catch { /* navigation privée */ }
  }

  function basculer() {
    const onOuvre = !ouvert
    setOuvert(onOuvre)
    if (onOuvre) marquerLues()   // ouvrir vaut lire : la pastille s'éteint en même temps
  }

  return (
    <div ref={zone} style={{ position: 'relative', flexShrink: 0 }}>

      {/* LA PASTILLE — posée sur le bandeau, donc en verre : elle appartient à l'image, elle
          n'est pas collée dessus. Le point ambre est la seule couleur vive de l'écran quand
          il y a du neuf ; lu, il devient blanc et cesse de battre. */}
      <button
        type="button"
        onClick={basculer}
        title={nonLues.length > 0
          ? 'Du nouveau dans aSchool — cliquez pour voir'
          : 'Revoir les dernières nouveautés'}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 7,
          padding: '6px 13px', borderRadius: 99, cursor: 'pointer',
          background: ouvert ? 'rgba(255,255,255,0.24)' : 'rgba(255,255,255,0.14)',
          border: '1px solid rgba(255,255,255,0.30)',
          color: '#fff', fontSize: 12, fontWeight: 700, letterSpacing: '0.01em',
          backdropFilter: 'blur(6px)', transition: 'background 0.15s',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.24)' }}
        onMouseLeave={e => { e.currentTarget.style.background = ouvert ? 'rgba(255,255,255,0.24)' : 'rgba(255,255,255,0.14)' }}
      >
        <span style={{
          width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
          background: nonLues.length > 0 ? '#fbbf24' : 'rgba(255,255,255,0.55)',
          boxShadow: nonLues.length > 0 ? '0 0 0 3px rgba(251,191,36,0.25)' : 'none',
          animation: nonLues.length > 0 ? 'pulseReady 2s ease-in-out infinite' : 'none',
        }} />
        Nouveau
        {nonLues.length > 1 && (
          <span style={{
            fontSize: 10.5, fontWeight: 800, padding: '0 6px', borderRadius: 99,
            background: 'rgba(255,255,255,0.22)', lineHeight: '16px',
          }}>
            {nonLues.length}
          </span>
        )}
      </button>

      {/* LE PANNEAU — ancré sous la pastille, jamais au milieu de l'écran : on regarde une
          annonce, on ne s'y arrête pas. Il se referme d'un clic à côté. */}
      {ouvert && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 10px)', right: 0, zIndex: 60,
          width: 'min(360px, calc(100vw - 48px))',
          background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
          boxShadow: '0 12px 32px rgba(15,23,42,0.18)', overflow: 'hidden',
          animation: 'fadeInSoft 0.16s ease-out',
        }}>
          <div style={{ padding: '13px 16px 10px', borderBottom: '1px solid #f1f5f9' }}>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.01em' }}>
              Ce qui vient d’arriver
            </div>
            <div style={{ fontSize: 11.5, color: '#94a3b8', marginTop: 2 }}>
              {nouveautes.length} nouveauté{nouveautes.length > 1 ? 's' : ''} dans aSchool
            </div>
          </div>

          <div style={{ maxHeight: 320, overflowY: 'auto' }}>
            {nouveautes.map(n => (
              <div key={n.key} style={{ padding: '12px 16px', borderBottom: '1px solid #f8fafc' }}>
                <div style={{ fontSize: 12.5, fontWeight: 700, color: '#1e293b', marginBottom: 3 }}>
                  {n.label}
                </div>
                <div style={{ fontSize: 11.5, lineHeight: 1.55, color: '#64748b' }}>
                  {n.description}
                </div>
              </div>
            ))}
          </div>

          <div style={{ padding: '10px 16px', background: '#f8fafc', textAlign: 'right' }}>
            <button
              type="button"
              onClick={() => setOuvert(false)}
              title="Fermer les nouveautés"
              style={{
                height: 30, padding: '0 16px', borderRadius: 6, cursor: 'pointer',
                background: '#1F6EEB', color: '#fff', border: 'none',
                fontSize: 12.5, fontWeight: 600,
              }}
            >
              Compris
            </button>
          </div>
        </div>
      )}

    </div>
  )
}
