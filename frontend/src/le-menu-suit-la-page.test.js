// LA RUBRIQUE OUVERTE SUIT LA PAGE AFFICHÉE.
//
// LE DÉFAUT (16/08/2026) : la rubrique dépliée était calculée au PREMIER affichage seulement.
// Un écran atteint autrement — un lien posé dans une page, une redirection — laissait le menu
// figé sur la rubrique d'avant.
//
// AUJOURD'HUI RIEN NE SE VOIT : aucun lien du back-office ne traverse deux rubriques (le seul,
// dans Prompts → Référentiels, mène à Prompts → Fonctionnalités, même famille). Le premier lien
// qu'on posera le ferait apparaître, et personne ne penserait à regarder le menu.
//
// CE QUE CE TEST ATTRAPE : le retour d'un calcul figé au montage, et le passage par un effet —
// qui redessinerait l'écran deux fois, menu fermé puis ouvert, à chaque changement de page.
//
// Lancer : npm test  (ou  node --test src/le-menu-suit-la-page.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const layout = readFileSync(join(SRC, 'components', 'AdminLayout.jsx'), 'utf8')

test('la rubrique ouverte se recale quand la page change', () => {
  assert.match(
    layout,
    /if \(groupeDeLaPage && groupeDeLaPage !== pagePrecedente\) \{/,
    'Le recalage a disparu : la rubrique dépliée redevient celle du premier affichage, et le menu\n' +
    'se fige dès qu’on atteint un écran autrement que par lui.'
  )
  assert.match(
    layout,
    /setPagePrecedente\(groupeDeLaPage\)[\s\S]{0,80}setOpenGroup\(groupeDeLaPage\)/,
    'Le recalage n’ouvre plus la rubrique de la page courante.'
  )
})

test('le recalage se fait pendant le rendu, pas dans un effet', () => {
  assert.doesNotMatch(
    layout,
    /useEffect\(\(\) => \{\s*if \(groupeDeLaPage\)/,
    'Le recalage est repassé par un effet : l’écran se redessine deux fois à chaque changement de\n' +
    'page — menu fermé, puis ouvert. Le battement se voit.'
  )
})
