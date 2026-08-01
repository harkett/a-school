// Chaque étape de la visite guidée doit avoir son ancre POSÉE dans un écran.
//
// CE QUE CE TEST ATTRAPE : une étape déclarée dans GUIDE_CREER dont l'attribut
// `data-guide` n'existe nulle part dans les sources. C'est exactement ce qui s'était
// produit : les écrans ont été reconstruits (démolition du 30/07), les éléments sont
// revenus, mais trois attributs `data-guide` — texte, generer, reprise — n'ont pas
// suivi. VisiteGuidee.jsx cherche son ancre par querySelector et, si elle manque,
// SAUTE l'étape sans rien dire : le prof voyait une visite de 8 étapes en montrer 5,
// et personne ne pouvait s'en apercevoir autrement qu'en la faisant à la main.
//
// CE QU'IL N'ATTRAPE PAS, et il faut le savoir : que l'ancre soit posée sur le BON
// élément, ni qu'elle soit VISIBLE au moment de l'étape. Plusieurs ancres vivent sous
// condition (le résultat n'existe qu'après génération ; « generer » et « reprise » ne
// s'affichent jamais en même temps). Le test porte sur la SOURCE — l'ancre existe.
//
// Lancer : npm test  (ou  node --test src/utils/aideCreer.ancres.test.js)
import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { GUIDE_CREER } from './aideCreer.js'

const SRC = join(dirname(fileURLToPath(import.meta.url)), '..')

function sourcesJsx(dossier) {
  return readdirSync(dossier).flatMap((nom) => {
    const chemin = join(dossier, nom)
    if (statSync(chemin).isDirectory()) return sourcesJsx(chemin)
    return nom.endsWith('.jsx') ? [chemin] : []
  })
}

const TOUT_LE_JSX = sourcesJsx(SRC).map((f) => readFileSync(f, 'utf8')).join('\n')

test('chaque étape de la visite guidée a son ancre data-guide dans un écran', () => {
  const orphelines = GUIDE_CREER
    .filter((e) => !TOUT_LE_JSX.includes(`data-guide="${e.cible}"`))
    .map((e) => `${e.cle} (cible « ${e.cible} »)`)

  assert.deepEqual(
    orphelines,
    [],
    'Étapes annoncées au prof mais sans ancre dans le JSX — elles seront sautées en '
      + `silence pendant la visite : ${orphelines.join(', ')}.`,
  )
})

test('une ancre data-guide n\'est jamais posée deux fois', () => {
  for (const e of GUIDE_CREER) {
    const occurrences = TOUT_LE_JSX.split(`data-guide="${e.cible}"`).length - 1
    assert.equal(
      occurrences,
      1,
      `L'ancre « ${e.cible} » est posée ${occurrences} fois : la bulle s'accrocherait au `
        + 'premier élément trouvé, pas forcément celui qu\'on décrit.',
    )
  }
})
