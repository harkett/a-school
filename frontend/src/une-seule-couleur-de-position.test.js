// UNE SEULE COULEUR DIT « VOUS ÊTES ICI » DANS LE MENU ADMIN.
//
// LE DÉFAUT QU'ON A EU (16/08/2026) : la rubrique active portait un trait BLEU, la sous-entrée
// active un trait BORDEAUX — deux couleurs vives à deux lignes d'écart sur la même colonne. Le
// bordeaux est par ailleurs la couleur de la marque (logo, icône d'en-tête, pied de page, trente-
// quatre fichiers) : à servir aussi de balise de position, elle ne signifiait plus rien nulle part.
//
// LA RÉPARATION : le bleu, et lui seul. Plein sur la page où l'on est (sous-entrée ou entrée
// simple), atténué sur la rubrique qui la contient — elle situe, elle ne désigne pas.
//
// CE QUE CE TEST ATTRAPE : le retour du bordeaux comme marque de position dans le menu.
//
// Lancer : npm test  (ou  node --test src/une-seule-couleur-de-position.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const layout = readFileSync(join(SRC, 'components', 'AdminLayout.jsx'), 'utf8')

// La barre de navigation seule : de l'ouverture du <nav> à sa fermeture. Le bordeaux reste
// légitime PARTOUT AILLEURS dans le fichier — en-tête, pied de page, bouton d'aide — c'est la
// couleur de la marque. Ce test ne juge que le menu.
function menu() {
  const debut = layout.indexOf('<nav className="admin-nav"')
  const fin = layout.indexOf('</nav>', debut)
  assert.ok(debut !== -1 && fin !== -1, 'La barre de navigation est introuvable dans AdminLayout.jsx')
  return layout.slice(debut, fin)
}

test('le menu ne se sert plus du bordeaux pour marquer la position', () => {
  const trouve = menu().match(/#A63045|166,\s*48,\s*69/gi) || []
  assert.equal(
    trouve.length, 0,
    'Le bordeaux est revenu dans le menu : c’est la couleur de la marque, pas un « vous êtes ici ».\n' +
    'Trouvé : ' + trouve.join(', ')
  )
})

test('la page où l’on se trouve porte le bleu plein, sa rubrique le bleu atténué', () => {
  const m = menu()
  assert.match(
    m,
    /isSubActive \? '3px solid #3b82f6'/,
    'La sous-entrée active ne porte plus le bleu plein : on ne voit plus quelle page est ouverte.'
  )
  assert.match(
    m,
    /isGroupActive \? '3px solid rgba\(59,130,246,0\.5\)'/,
    'La rubrique active porte à nouveau un trait aussi fort que la page elle-même : deux repères\n' +
    'de même intensité sur la même colonne, on ne sait plus lequel désigne l’écran ouvert.'
  )
})
