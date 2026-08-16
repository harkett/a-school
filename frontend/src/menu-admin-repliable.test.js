// LA BARRE DU MENU ADMIN SE REPLIE, ET S'EN SOUVIENT.
//
// LE DÉFAUT QU'ON A EU (16/08/2026) : 220 pixels quoi qu'il arrive. Sur un portable 13 pouces ou
// une fenêtre en demi-écran, les écrans larges — Référentiel, Journal, Formations — se tassaient
// sur ce qui restait, sans aucun moyen de récupérer la place.
//
// LA RÉPARATION : un bouton replie la barre en colonne d'icônes ; le choix est retenu d'une visite
// à l'autre. Les intitulés ne sont pas perdus, la bulle d'aide les donne au survol.
//
// CE QUE CE TEST ATTRAPE : la largeur redevenue fixe, la perte de la mémorisation, les sous-entrées
// laissées visibles dans une colonne de 62 pixels, et la bulle restée collée à l'ancienne largeur.
//
// CE QU'IL N'ATTRAPE PAS : le rendu réel des icônes. Le front tourne sur `node --test`, sans
// jsdom : on lit la SOURCE.
//
// Lancer : npm test  (ou  node --test src/menu-admin-repliable.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const layout = readFileSync(join(SRC, 'components', 'AdminLayout.jsx'), 'utf8')

test('la barre prend la largeur du mode courant, pas une largeur figée', () => {
  assert.match(
    layout,
    /const largeurBarre = reduit \? LARGEUR_REDUITE : LARGEUR_OUVERTE/,
    'La largeur de la barre ne dépend plus du repli : elle est redevenue figée.'
  )
  assert.match(
    layout,
    /<aside style=\{\{ width: largeurBarre/,
    "La barre n'utilise plus la largeur calculée."
  )
})

test('le repli est retenu d’une visite à l’autre', () => {
  assert.match(
    layout,
    /localStorage\.getItem\(CLE_MENU_REDUIT\)/,
    'Le repli n’est plus relu au démarrage : il faudrait le régler à chaque ouverture.'
  )
  assert.match(
    layout,
    /localStorage\.setItem\(CLE_MENU_REDUIT/,
    'Le repli n’est plus enregistré.'
  )
  // La navigation privée refuse localStorage : la lecture et l'écriture doivent être protégées,
  // sinon l'administration entière tombe en écran blanc.
  assert.match(layout, /try \{ return localStorage\.getItem\(CLE_MENU_REDUIT\)/, 'Lecture non protégée.')
  assert.match(layout, /try \{ localStorage\.setItem\(CLE_MENU_REDUIT/, 'Écriture non protégée.')
})

test('replié, le menu ne montre que ce qui tient dans une colonne', () => {
  assert.match(
    layout,
    /\{isOpen && !reduit && \(/,
    'Les sous-entrées s’affichent encore quand la barre est repliée : ce ne sont que des mots, et\n' +
    'il n’y a plus la place de les écrire.'
  )
  assert.match(
    layout,
    /if \(reduit\) \{ setReduit\(false\); setOpenGroup\(item\.label\)/,
    'Cliquer une rubrique dans la barre repliée ne la rouvre plus : la rubrique se déplierait dans\n' +
    'une colonne de 62 pixels.'
  )
})

test('la bulle d’aide suit le bord de la barre', () => {
  assert.match(
    layout,
    /<BulleAide bulle=\{bulle\} gauche=\{largeurBarre\}/,
    'La bulle ne reçoit plus la largeur courante : repliée, elle flotterait loin de la barre ;\n' +
    'dépliée, elle recouvrirait le menu.'
  )
  assert.match(layout, /left: gauche \+ 8/, 'La bulle est revenue à une position codée en dur.')
})
