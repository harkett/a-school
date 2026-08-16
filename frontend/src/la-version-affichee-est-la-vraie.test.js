// LE MENU ADMIN AFFICHE LA VRAIE VERSION.
//
// LE DÉFAUT (16/08/2026) : le bas du menu annonçait « v1.3 · 02/05/2026 », écrit en dur. La
// version réelle était 3.2.13 — trois versions et trois mois de retard. C'est pourtant la
// première chose qu'on demande quand quelqu'un signale un défaut.
//
// LA RÉPARATION : la version vient de `package.json`, injectée à la construction par Vite
// (`define: __APP_VERSION__`). Elle ne peut plus diverger. La date figée disparaît, et le gris à
// 20 % laisse la place à quelque chose de lisible.
//
// CE QUE CE TEST ATTRAPE : le retour d'un numéro écrit à la main, et la disparition de
// l'injection côté Vite ou de sa déclaration côté ESLint (sans quoi la construction casse).
//
// Lancer : npm test  (ou  node --test src/la-version-affichee-est-la-vraie.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const RACINE = dirname(SRC)
const layout = readFileSync(join(SRC, 'components', 'AdminLayout.jsx'), 'utf8')
const vite = readFileSync(join(RACINE, 'vite.config.js'), 'utf8')
const eslint = readFileSync(join(RACINE, 'eslint.config.js'), 'utf8')

test('la version affichée n’est pas écrite à la main', () => {
  assert.match(
    layout,
    /v\{__APP_VERSION__\}/,
    'Le menu n’affiche plus la version injectée : un numéro recopié à la main finit toujours par\n' +
    'mentir — c’est ce qui a donné « v1.3 » alors que l’application était en 3.2.13.'
  )
  // Hors commentaires : le commentaire de la correction CITE l'ancienne valeur pour expliquer
  // ce qui n'allait pas, et c'est très bien qu'il la cite.
  const code = layout
    .split('\n')
    .filter(l => !/^\s*(\/\/|\*|\{\/\*|\/\*)/.test(l))
    .join('\n')
  assert.doesNotMatch(
    code,
    /v1\.3|02\/05\/2026/,
    'L’ancienne version figée est revenue dans le menu.'
  )
})

test('la version vient de package.json', () => {
  assert.match(
    vite,
    /__APP_VERSION__: JSON\.stringify\(pkg\.version\)/,
    'Vite n’injecte plus la version : `__APP_VERSION__` serait indéfini à l’exécution.'
  )
  assert.match(
    eslint,
    /__APP_VERSION__: 'readonly'/,
    'ESLint ne connaît plus `__APP_VERSION__` : le lint casse sur « is not defined ».'
  )
})
