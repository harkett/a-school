import { useEffect, useState } from 'react'

// Seuil unique de bascule mobile. Il était recopié dans quatre composants ; désormais il
// s'écrit ici et nulle part ailleurs. 768 px = le point où la deuxième colonne du header ne
// tient plus.
export const SEUIL_MOBILE = 768

// `window.innerWidth < 768` calculé à la volée dans le corps d'un composant est FIGÉ : React
// ne re-rend pas sur un redimensionnement, donc la valeur reste celle du premier rendu. Trois
// composants faisaient exactement ça (Header, Accueil, MesStats) — la fenêtre changeait de
// taille, l'affichage non. Il fallait recharger la page pour retrouver la bonne mise en page.
//
// Un quatrième (Aide) portait déjà la version correcte, avec son écouteur. C'est celle-là qui
// est remontée ici : on n'invente pas un motif, on déplace celui qui marchait déjà.
//
// Le cas visible : le libellé du bouton de déconnexion du header, qui se raccourcit en
// dessous du seuil. Il restait long sur une fenêtre réduite après coup, et débordait.
export default function useIsMobile() {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < SEUIL_MOBILE)

  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < SEUIL_MOBILE)
    window.addEventListener('resize', handler)
    // Retiré au démontage : sans ça, chaque montage empile un écouteur de plus sur une
    // fenêtre qui, elle, ne se démonte jamais.
    return () => window.removeEventListener('resize', handler)
  }, [])

  return isMobile
}
