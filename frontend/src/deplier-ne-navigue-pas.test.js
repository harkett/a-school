// DÉPLIER UNE CATÉGORIE DU MENU ADMIN NE CHANGE PAS D'ÉCRAN.
//
// LE DÉFAUT QU'ON A EU (16/08/2026) : le clic sur l'en-tête d'une catégorie repliée faisait deux
// choses d'un coup — il la dépliait, et il envoyait sur sa première sous-entrée. On consultait
// Formations, on ouvrait « Système » pour voir ce qu'elle contenait, et l'écran basculait sur
// Système → Email. Le travail en cours partait avec.
//
// C'était délibéré : on voulait que la surbrillance bleue suive la catégorie fraîchement ouverte.
// Un détail de couleur ne justifie pas de naviguer à la place de l'utilisateur.
//
// CE QUE CE TEST ATTRAPE : la réapparition d'un `navigate(...)` dans le gestionnaire de clic de
// l'en-tête de catégorie.
//
// CE QU'IL N'ATTRAPE PAS : un `navigate` posé ailleurs par un autre chemin (effet, sous-composant).
// Le front tourne sur `node --test`, sans jsdom : le test porte sur la SOURCE, pas sur le pixel.
//
// Lancer : npm test  (ou  node --test src/deplier-ne-navigue-pas.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const layout = readFileSync(join(SRC, 'components', 'AdminLayout.jsx'), 'utf8')

// Le gestionnaire de clic de l'en-tête de catégorie : tout ce qui suit `onClick={` jusqu'à la
// fermeture `}}` ou `)}` — on le lit tel quel, commentaires exclus.
function clicEnTeteCategorie() {
  const marqueur = 'onClick={() => setOpenGroup('
  const autre = layout.indexOf('onClick={() => {\n                      if (isOpen)')
  if (autre !== -1) return layout.slice(autre, autre + 500)   // l'ancienne forme, si elle revient
  const i = layout.indexOf(marqueur)
  assert.notEqual(i, -1, "Le clic de l'en-tête de catégorie est introuvable dans AdminLayout.jsx")
  return layout.slice(i, layout.indexOf('\n', i))
}

test("déplier une catégorie ne fait que basculer l'accordéon", () => {
  const clic = clicEnTeteCategorie()
  assert.doesNotMatch(
    clic,
    /navigate\s*\(/,
    "Le clic sur une catégorie du menu admin navigue à nouveau : déplier doit seulement déplier.\n" +
    "Reproduction : Admin → Formations, puis clic sur « Système » (repliée) → l'écran ne doit pas bouger.\n" +
    'Gestionnaire trouvé : ' + clic
  )
  assert.match(clic, /setOpenGroup\(/, "L'accordéon ne bascule plus du tout.")
})

test("les sous-entrées restent le seul chemin vers un écran", () => {
  // Chaque sous-entrée est un <Link to={sub.to}> : c'est ce clic-là, et lui seul, qui change
  // d'écran. Si les Link disparaissaient au profit d'un onClick, on retomberait dans le flou.
  assert.match(
    layout,
    /<Link\s+key=\{sub\.to\}\s+to=\{sub\.to\}/,
    'Les sous-entrées du menu ne sont plus des liens : le menu ne dit plus où il mène.'
  )
})
