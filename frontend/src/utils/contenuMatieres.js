// Ce que la page « Programmes & contenu » lit dans l'arbre de la base (GET /admin/contenu).
//
// Sorti de l'écran pour être PROUVÉ, même découpage que utils/matieresReferentiel.js face à
// l'écran Référentiel : l'écran rend, ces fonctions décident de ce qu'il rend.
//
// LA GRILLE A DISPARU. L'écran croisait avant un catalogue global de matières avec la liste des
// niveaux : une case à cocher par intersection, et une table `matiere_niveaux` derrière chaque
// case. Ni ce catalogue ni ces paires n'existent — une matière appartient au référentiel d'un
// niveau. Il n'y a donc plus rien à croiser : les matières d'un niveau sont déjà DANS le niveau,
// et la seule question qui reste est leur état.

// Les trois états d'une matière, et ce qu'ils veulent dire pour le prof :
//   au programme  → retenue par l'admin et active : elle est dans ses menus ;
//   désactivée    → retenue mais mise de côté : elle disparaît des menus, rien n'est supprimé ;
//   proposée      → lue dans le document, pas encore retenue : elle n'est jamais arrivée jusqu'à lui.
export const AU_PROGRAMME = 'au_programme'
export const DESACTIVEE   = 'desactivee'
export const PROPOSEE     = 'proposee'

export function etatMatiere(m) {
  if (!m?.validee) return PROPOSEE          // une proposition ne dépend pas de son `actif`
  return m.actif ? AU_PROGRAMME : DESACTIVEE
}

// Les lignes d'un niveau, dans l'ordre de la base, chacune portant son état calculé.
export function lignesMatieres(niveau) {
  return (niveau?.matieres || []).map(m => ({ ...m, etat: etatMatiere(m) }))
}

// Combien de matières ce niveau met RÉELLEMENT à la disposition de ses profs. C'est ce comptage
// — pas la longueur de la liste — qui s'affiche sur la ligne du niveau : un référentiel plein de
// propositions non retenues n'a rien ouvert à personne.
export function nbAuProgramme(niveau) {
  return lignesMatieres(niveau).filter(m => m.etat === AU_PROGRAMME).length
}

// Le compteur d'en-tête, lu sur l'arbre entier. Les matières se comptent SANS dédoublonner par
// nom : le « Mathématiques » du BTS CIEL et celui de la Terminale sont deux matières, portées par
// deux référentiels, et l'admin doit les voir toutes les deux.
export function compterContenu(cycles) {
  const liste = cycles || []
  const niveaux = liste.flatMap(c => c.niveaux || [])
  return {
    cycles: liste.length,
    niveaux: niveaux.length,
    matieres: niveaux.reduce((n, niv) => n + nbAuProgramme(niv), 0),
  }
}
