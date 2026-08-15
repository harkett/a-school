import { createContext, useContext, useEffect } from 'react'

// LES BOUTONS D'UNE PAGE, AFFICHÉS DANS L'EN-TÊTE FIXE DE L'ADMINISTRATION.
//
// Le problème : l'en-tête appartient à `AdminLayout`, les boutons appartiennent à la page (elle
// seule sait quel formulaire ouvrir). Il fallait donc un chemin de la page vers l'en-tête.
//
// POURQUOI PAS UN PORTAIL. Un `createPortal` vers un `<div id=…>` a été essayé le 15/08/2026 et
// n'affichait rien : il dépend de l'ordre des effets et d'un nœud du DOM qui doit exister au bon
// moment — quand ça rate, le bouton disparaît sans erreur, ce qui est le pire des échecs. Ici tout
// reste dans React : la page dépose son JSX dans l'état du layout, qui le rend. Aucun DOM manipulé
// à la main, aucun timing à deviner.
//
// DANS SON PROPRE FICHIER, et pas dans `AdminLayout` : un module qui exporte à la fois des
// composants et des fonctions casse le rechargement à chaud de Vite (règle `react-refresh`).
export const ActionsEcran = createContext(() => {})

// À appeler dans une page : `useActionsEcran(<button …/>, [ce dont il dépend])`.
// Le nettoyage au démontage est ce qui empêche les boutons d'une page de survivre sur la suivante.
export function useActionsEcran(noeud, deps = []) {
  const poser = useContext(ActionsEcran)
  useEffect(() => {
    poser(noeud)
    return () => poser(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}
