// Le filigrane « DÉMONSTRATION » — le mot en fond de TOUT l'écran, sur les instances d'essai.
//
// POURQUOI EN PLUS DU BANDEAU. Le bandeau du bas dit où l'on est à qui le lit. Le filigrane, lui,
// tient sur les captures d'écran, sur les photos d'écran prises en réunion, et sur les fenêtres
// modales qui recouvrent le bandeau. Une application de démonstration ressemble trait pour trait
// à la vraie — c'EST la vraie, sur d'autres données : rien à l'image ne les distingue.
//
// CE QU'IL NE FAIT PAS. Il n'intercepte aucun clic (`pointerEvents: none`) : on tape, on clique,
// on fait défiler à travers lui comme s'il n'existait pas. Et il ne se ferme pas — un rappel
// qu'on peut écarter n'en est plus un.
//
// AU-DESSUS ET NON DERRIÈRE. Posé derrière le contenu, il serait masqué par le premier fond
// blanc venu — cartes, tableaux, modales : autant dire partout. Il passe donc PAR-DESSUS.
// Son opacité et sa taille se règlent dans `TUILE_DEMO` (utils/modeDemo.js), une seule fois pour
// l'écran et pour le papier : il doit tenir sur une capture d'écran sans jamais s'interposer
// entre le prof et son texte.

import { useModeDemo, TUILE_DEMO } from '../utils/modeDemo.js'

export default function FiligraneDemo() {
  if (!useModeDemo()) return null
  return (
    <div
      aria-hidden="true"
      style={{
        position: 'fixed', inset: 0, zIndex: 9997,
        pointerEvents: 'none',
        backgroundImage: `url("data:image/svg+xml,${TUILE_DEMO}")`,
        backgroundRepeat: 'repeat',
      }}
    />
  )
}
