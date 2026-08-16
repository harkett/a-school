// ALLER VOIR L'APPLICATION NE FERME PAS L'ADMINISTRATION.
//
// LE DÉFAUT QU'ON A EU (16/08/2026) : le bouton « aSchool », en bas du menu, chargeait
// l'application du prof dans le MÊME onglet. Un clic — souvent par erreur, il est collé au bouton
// de déconnexion — et l'administration disparaissait sans un mot. Il fallait refaire tout le
// chemin pour revenir à l'écran qu'on était en train de régler.
//
// LA RÉPARATION : un lien qui s'ouvre à côté. Rien à confirmer, puisque rien n'est perdu.
//
// CE QUE CE TEST ATTRAPE : le retour d'un bouton qui navigue dans l'onglet courant, et la perte
// du `rel` qui protège l'onglet ouvert.
//
// Lancer : npm test  (ou  node --test src/quitter-l-admin-sans-la-perdre.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const layout = readFileSync(join(SRC, 'components', 'AdminLayout.jsx'), 'utf8')

// La balise du retour vers l'application : on part de son adresse et on remonte au `<` qui
// l'ouvre. Aucune ancre sur un saut de ligne — le fichier est en fins de ligne Windows.
function lienVersApplication() {
  const i = layout.indexOf('href="/"')
  assert.notEqual(i, -1, 'Le lien vers l’application est introuvable dans AdminLayout.jsx')
  return layout.slice(layout.lastIndexOf('<', i), i + 300)
}

test("le retour vers l'application ouvre un nouvel onglet", () => {
  assert.ok(
    !layout.includes("onClick={() => navigate('/')}"),
    "Le bouton « aSchool » recharge à nouveau l'application dans l'onglet courant :\n" +
    "l'administration se ferme sans prévenir, et tout le chemin est à refaire."
  )
  assert.match(lienVersApplication(), /target="_blank"/, 'Le lien ne s’ouvre plus dans un nouvel onglet.')
})

test("l'onglet ouvert ne garde pas la main sur l'administration", () => {
  assert.match(
    lienVersApplication(),
    /rel="noopener noreferrer"/,
    'Sans `noopener`, la page ouverte peut piloter l’onglet de l’administration.'
  )
})
