// LE MENU ADMIN SE LIT EN TROIS BLOCS.
//
// LE DÉFAUT QU'ON A EU (16/08/2026) : quatre écrans seuls en haut, puis huit rubriques à déplier,
// puis un trait, puis trois écrans seuls. Rien ne disait pourquoi ces quatre-là échappaient au
// rangement alors que tout le reste y était soumis — la règle du fichier veut pourtant que toute
// page loge sous une famille.
//
// LA RÉPARATION : trois blocs séparés par un trait — où l'on arrive (Tableau de bord), ce que l'on
// administre (les familles), ce qui est à soi (Tâches à faire, Mon compte, Aide). Référentiel et
// Formations sont descendus sous une famille « Pédagogie ».
//
// CE QUE CE TEST ATTRAPE : une page reposée à plat dans le bloc du milieu, la perte d'un des deux
// traits, et le retour de l'écran « Consulter » supprimé le même jour.
//
// CE QU'IL N'ATTRAPE PAS : l'ordre des familles entre elles. Le front tourne sur `node --test`,
// sans jsdom : on lit la SOURCE.
//
// Lancer : npm test  (ou  node --test src/menu-admin-range-en-trois-blocs.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const layout = readFileSync(join(SRC, 'components', 'AdminLayout.jsx'), 'utf8')

// La déclaration du menu : de `const NAV_ITEMS = [` à sa fermeture.
function menuDeclare() {
  const debut = layout.indexOf('const NAV_ITEMS = [')
  const fin = layout.indexOf('\nexport default function AdminLayout', debut)
  assert.ok(debut !== -1 && fin !== -1, 'La déclaration du menu est introuvable.')
  return layout.slice(debut, fin)
}

test('le menu est coupé en trois blocs par deux traits', () => {
  const traits = menuDeclare().match(/^\s{2}SEP,$/gm) || []
  assert.equal(
    traits.length, 2,
    `Le menu compte ${traits.length} trait(s) au lieu de 2 : les trois blocs — arrivée, ` +
    'administration, ce qui est à soi — ne se distinguent plus.'
  )
})

test('une seule page reste à plat avant les familles', () => {
  const decl = menuDeclare()
  const avant = decl.slice(0, decl.indexOf('  SEP,'))
  const pages = avant.match(/^\s{4}to:/gm) || []
  assert.equal(
    pages.length, 1,
    `${pages.length} pages posées à plat en tête du menu au lieu de la seule « Tableau de bord ».\n` +
    'Une page qui n’est pas l’écran d’arrivée se range sous une famille.'
  )
  assert.match(avant, /label: 'Tableau de bord'/, 'L’écran d’arrivée n’est plus en tête du menu.')
})

test('Référentiel et Formations vivent sous la famille Pédagogie', () => {
  const decl = menuDeclare()
  const i = decl.indexOf("label:  'Pédagogie'")
  assert.notEqual(i, -1, 'La famille « Pédagogie » a disparu du menu.')
  const famille = decl.slice(i, decl.indexOf('\n  },', i))
  assert.match(famille, /label: 'Référentiel'/, 'Référentiel n’est plus sous Pédagogie.')
  assert.match(famille, /label: 'Formations'/, 'Formations n’est plus sous Pédagogie.')
})

test('l’écran « Consulter » ne revient pas', () => {
  assert.ok(
    !layout.includes('referentiels-consulter'),
    'L’écran « Consulter » est revenu au menu : il montrait ce que montre déjà Référentiel, sans\n' +
    'bouton qui écrit — deux portes vers le même contenu. Supprimé le 16/08/2026 avec sa route,\n' +
    'son fichier et sa ligne au tableau de bord (migration c9f5a3e8d1b6).'
  )
})
