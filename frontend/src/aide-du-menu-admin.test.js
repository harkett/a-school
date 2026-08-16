// L'AIDE DU MENU ADMIN NE PASSE PAS PAR LA BULLE DU NAVIGATEUR.
//
// LE DÉFAUT QU'ON A EU (16/08/2026) : les cinq endroits du menu portaient un attribut `title`.
// Il faut attendre une seconde, le texte sort en police système minuscule, et les explications
// longues — 538 caractères pour le Journal — y sont illisibles.
//
// LA RÉPARATION : une bulle maison, ouverte tout de suite à droite de la barre, dans la police de
// l'application, sur une largeur fixe. Elle suit le survol ET le focus clavier.
//
// CE QUE CE TEST ATTRAPE : le retour d'un `title={item.aide}` ou `title={sub.aide}`, la perte du
// branchement clavier, et la disparition de la bulle elle-même.
//
// CE QU'IL N'ATTRAPE PAS : une bulle rendue hors écran, ou un texte d'aide vide en base. Le front
// tourne sur `node --test`, sans jsdom : on lit la SOURCE.
//
// Lancer : npm test  (ou  node --test src/aide-du-menu-admin.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const layout = readFileSync(join(SRC, 'components', 'AdminLayout.jsx'), 'utf8')

test("aucune entrée de menu ne repasse par l'attribut title", () => {
  for (const interdit of ['title={item.aide}', 'title={sub.aide}']) {
    assert.ok(
      !layout.includes(interdit),
      `« ${interdit} » est revenu dans AdminLayout.jsx : l'aide repart dans la bulle grise du\n` +
      "navigateur — une seconde d'attente, police système, texte long illisible."
    )
  }
})

test("l'aide s'ouvre au survol comme au clavier", () => {
  const survols = layout.match(/montrerAide\(e, (item|sub)\.label, \1\.aide\)/g) || []
  // 5 entrées x 2 (souris + focus) : rubriques, sous-entrées, entrée simple, lien externe.
  assert.ok(
    survols.length >= 8,
    `Seulement ${survols.length} branchements d'aide trouvés : une partie du menu n'explique plus rien.`
  )
  assert.match(
    layout,
    /onFocus=\{e => montrerAide\(/,
    "L'aide ne s'ouvre plus au focus : au clavier, le menu redevient muet."
  )
  assert.match(layout, /onBlur=\{cacherAide\}/, 'La bulle ne se referme plus quand le focus part.')
})

test('la bulle est posée en coordonnées écran et se referme au défilement', () => {
  assert.match(
    layout,
    /position: 'fixed'/,
    "La bulle n'est plus en position fixe : la barre de menu défile, elle serait coupée au bord."
  )
  assert.match(
    layout,
    /onScroll=\{cacherAide\}/,
    'La bulle ne se referme plus au défilement du menu : elle resterait affichée en face du vide.'
  )
})
