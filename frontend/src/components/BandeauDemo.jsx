// Le bandeau qui dit où l'on est — visible en permanence dans une instance de démonstration.
//
// POURQUOI IL NE SE FERME PAS. Toute l'application ressemble à la vraie, parce que c'EST la vraie,
// branchée sur une autre base. Un prof qui l'oublie une minute croira avoir perdu ses contenus, ou
// pire, croira que ceux qu'il fabrique ici sont les siens. Le rappel doit donc rester à l'écran
// tout le temps, sans croix pour l'écarter.
//
// Il se pose en bas et non en haut : le haut est déjà pris par l'en-tête fixe (65 px), et un
// second bandeau fixe au-dessus décalerait toutes les pages.
//
// LA QUESTION « suis-je en démonstration ? » N'EST PLUS POSÉE ICI : elle vit dans
// utils/modeDemo.js, partagée avec le filigrane de fond — une seule requête, une seule vérité.
import { useModeDemo, coupleDemo } from '../utils/modeDemo.js'

export default function BandeauDemo() {
  const demo = useModeDemo()
  if (!demo) return null

  // Le couple servi par cette base. Il arrive avec la même réponse que `mode_demo` : quand le
  // bandeau s'affiche, il est déjà là. Vide si la base n'a aucun référentiel découpé — la phrase
  // tient alors toute seule, plutôt que d'afficher un séparateur suivi de rien.
  const couple = coupleDemo()

  return (
    <div
      style={{
        position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 9998,
        background: '#6d28d9', color: '#fff', textAlign: 'center',
        padding: '7px 16px', fontSize: 13, fontWeight: 600,
        boxShadow: '0 -2px 8px rgba(0,0,0,0.18)',
      }}
      title={couple
        ? `Démonstration de ${couple} — vous êtes dans une base d’essai : rien de ce que vous faites ici n’atteint vos vrais contenus.`
        : 'Vous êtes dans une base d’essai : rien de ce que vous faites ici n’atteint vos vrais contenus.'}
    >
      Démonstration
      {couple && (
        <span style={{ opacity: 0.85, fontWeight: 500 }}> · {couple}</span>
      )}
      <span style={{ opacity: 0.85, fontWeight: 500 }}>
        {' '}— rien de ce que vous faites ici n’atteint vos vrais contenus.
      </span>
    </div>
  )
}
