// LA ligne de pied de page d'aSchool — une seule écriture, pour toutes les sorties.
//
// POURQUOI UNE CONSTANTE. Elle était recopiée dans quatre endroits (le PDF, l'impression brute,
// l'impression de l'aperçu, la signature du mail) et trois d'entre eux s'étaient déjà mis à
// diverger : « Généré avec aSchool — aschool.fr » d'un côté, la ligne complète de l'autre. Un
// document qui sort d'ici en emporte toujours EXACTEMENT le même texte, sinon ce n'est plus une
// signature, c'est une variante.
//
// ELLE EST VISIBLE PARTOUT, pas seulement à l'impression. L'aperçu à l'écran la porte aussi :
// ce qu'on voit doit être ce qui sort. Une des impressions la posait en `display:none` hors
// papier — l'utilisateur ne pouvait pas savoir qu'elle existait.
export const PIED_ASCHOOL = 'Généré avec aSchool — aschool.fr — Créez votre compte gratuit'

// La même, en bloc HTML prêt à coller en fin de document. Le style est écrit en ligne : ces
// documents partent dans une fenêtre, une iframe ou un mail, où aucune feuille de style du site
// ne les suit.
export function piedHtml() {
  return (
    '<div class="pied-aschool" style="margin-top:2.5em;padding-top:8px;'
    + 'border-top:1px solid #e5e7eb;text-align:center;font-size:10px;color:#9ca3af">'
    + PIED_ASCHOOL
    + '</div>'
  )
}
