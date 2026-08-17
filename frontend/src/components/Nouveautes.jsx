import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

// « NOUVEAU » — l'annonce d'une fonctionnalité qui vient d'arriver, dans le bandeau d'accueil.
//
// UNE BANDE QUI SE LIT, PAS UN BOUTON QUI ATTEND. La première version posait une pastille
// « Nouveau » en haut à droite : discrète au point de ne rien dire — il fallait la cliquer
// pour apprendre ce qui était arrivé, donc personne ne la cliquait. Le TITRE de la nouveauté
// est maintenant écrit à même le bandeau, sur trois lignes : ce qui arrive (Nouveau), ce que
// c'est (le titre), et ce qu'on peut en faire (Découvrir). On sait quoi avant de cliquer.
//
// Elle reste une BANDE, pas une fenêtre : elle ne barre pas l'écran, ne demande rien, et se
// referme d'une croix.
//
// UNE SEULE À LA FOIS, et c'est la règle de l'administration, pas une limite d'affichage :
// cocher « nouveauté » sur une ligne décoche la précédente (Admin → Tâches à faire → Bientôt
// disponible). Annoncer trois choses, c'est n'en annoncer aucune. D'où l'absence de compteur
// et de défilement ici : il n'y a jamais qu'un titre à lire. Si le serveur en renvoyait
// plusieurs — une base retouchée à la main —, la bande montre la première, elle ne bricole pas
// un carrousel pour un cas qui ne doit pas exister.
//
// « Lu » est gardé dans le navigateur, par code de fonctionnalité : c'est un confort
// d'affichage, pas une donnée de la plateforme. Fermer la bande la range pour de bon ; elle
// ne revient que le jour où l'administration annonce autre chose.
const CLE_VUES = 'aschool_nouveautes_vues'

function lireVues() {
  try { return JSON.parse(localStorage.getItem(CLE_VUES) || '[]') } catch { return [] }
}

// `onNavigate` : la fonction du shell prof qui change d'écran (la même que le menu de gauche).
// Sans elle, « Découvrir » ne serait qu'un mot — c'est ce qu'il était.
export default function Nouveautes({ onNavigate }) {
  const [vues, setVues]     = useState(lireVues)
  const [ouvert, setOuvert] = useState(false)
  const [ferme, setFerme]   = useState(false)
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

  const aLire = nouveautes.filter(n => !vues.includes(n.key))

  // Fermeture du panneau au clic à côté et à Échap — comme toutes les fenêtres de la maison.
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

  if (ferme || aLire.length === 0) return null

  const courante = aLire[0]

  // « DÉCOUVRIR » OUVRE L'ÉCRAN, il ne déplie pas un texte. Une nouveauté qu'on ne peut pas
  // essayer tout de suite ne sert à rien : le clic emmène là où elle vit, par le même chemin
  // que le menu. L'annonce est rangée du même geste — elle a fait son travail. Faute d'écran
  // (fonctionnalité pas encore livrée), on retombe sur le texte de l'annonce.
  function ouvrirLaFonctionnalite() {
    if (courante.page && onNavigate) {
      ranger()
      onNavigate(courante.page)
      return
    }
    setOuvert(o => !o)
  }

  function ranger() {
    const toutes = [...new Set([...vues, ...nouveautes.map(n => n.key)])]
    setVues(toutes)
    try { localStorage.setItem(CLE_VUES, JSON.stringify(toutes)) } catch { /* navigation privée */ }
    setFerme(true)
  }

  return (
    <div ref={zone} style={{ position: 'relative' }}>

      {/* LA BANDE — en verre sur le dégradé du bandeau : elle en fait partie, elle n'est pas
          posée dessus. Trois lignes, dans l'ordre où l'œil les prend. */}
      <div
        onClick={ouvrirLaFonctionnalite}
        title={courante.page
          ? `Ouvrir « ${courante.label} »`
          : `${courante.label} — cliquez pour lire l’annonce`}
        style={{
          display: 'inline-flex', flexDirection: 'column', gap: 3,
          padding: '11px 16px 10px', borderRadius: 10, cursor: 'pointer',
          background: ouvert ? 'rgba(255,255,255,0.22)' : 'rgba(255,255,255,0.13)',
          border: '1px solid rgba(255,255,255,0.28)',
          backdropFilter: 'blur(6px)', transition: 'background 0.15s',
          maxWidth: 300, position: 'relative',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.22)' }}
        onMouseLeave={e => { e.currentTarget.style.background = ouvert ? 'rgba(255,255,255,0.22)' : 'rgba(255,255,255,0.13)' }}
      >
        {/* 1 — CE QUI ARRIVE. Le point ambre est la seule couleur vive de l'écran : il ne bat
            que tant qu'il reste quelque chose à lire. */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          <span style={{
            width: 7, height: 7, borderRadius: '50%', flexShrink: 0, background: '#fbbf24',
            boxShadow: '0 0 0 3px rgba(251,191,36,0.25)',
            animation: 'pulseReady 2s ease-in-out infinite',
          }} />
          <span style={{ fontSize: 10.5, fontWeight: 800, letterSpacing: '0.09em', color: '#fcd34d' }}>
            NOUVEAU
          </span>
        </div>

        {/* 2 — CE QUE C'EST. Le titre, en clair : c'est lui qui décide si on clique. */}
        <div style={{
          fontSize: 14, fontWeight: 700, color: '#fff', lineHeight: 1.25,
          letterSpacing: '-0.01em', paddingRight: 14,
        }}>
          {courante.label}
        </div>

        {/* 3 — CE QU'ON EN FAIT. « Découvrir » n'apparaît que si le clic ouvre vraiment
            l'écran de la fonctionnalité ; sinon le mot ne promet que ce qu'il tient. */}
        <div style={{ fontSize: 11.5, fontWeight: 600, color: 'rgba(255,255,255,0.82)' }}>
          {courante.page ? 'Découvrir →' : 'En savoir plus →'}
        </div>

        {/* La croix range l'annonce pour de bon — elle ne réapparaît qu'à la prochaine. */}
        <button
          type="button"
          onClick={e => { e.stopPropagation(); ranger() }}
          title="Ne plus afficher cette annonce"
          style={{
            position: 'absolute', top: 5, right: 6,
            width: 18, height: 18, padding: 0, borderRadius: '50%',
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'rgba(255,255,255,0.55)', fontSize: 14, lineHeight: '16px',
          }}
          onMouseEnter={e => { e.currentTarget.style.color = '#fff' }}
          onMouseLeave={e => { e.currentTarget.style.color = 'rgba(255,255,255,0.55)' }}
        >
          ×
        </button>
      </div>

      {/* LE PANNEAU — le texte entier, ancré sous la bande. On regarde une annonce, on ne
          s'y arrête pas : il se referme d'un clic à côté. */}
      {ouvert && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 10px)', right: 0, zIndex: 60,
          width: 'min(360px, calc(100vw - 48px))',
          background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
          boxShadow: '0 12px 32px rgba(15,23,42,0.18)', overflow: 'hidden',
          animation: 'fadeInSoft 0.16s ease-out', cursor: 'default',
        }}>
          <div style={{ padding: '13px 16px 10px', borderBottom: '1px solid #f1f5f9' }}>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.01em' }}>
              Ce qui vient d’arriver
            </div>
            <div style={{ fontSize: 11.5, color: '#94a3b8', marginTop: 2 }}>
              La dernière nouveauté d’aSchool
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
              onClick={ranger}
              title="Fermer et ne plus afficher ces annonces"
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
