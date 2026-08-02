// L'historique reste ATTEIGNABLE quand une génération échoue.
//
// CE QUE CE TEST ATTRAPE, et la panne qu'il ferme. Dans ActiviteEcran, le bouton « Historique »
// était imbriqué dans le bloc des reprises, ouvert par `{resultat && !loading && (`. Or un
// échec de génération fait `setResultat(null)` — deux fois : sur l'événement `error` du flux,
// et dans le `catch`. Le bouton DISPARAISSAIT donc exactement au moment où le prof en avait le
// plus besoin : son texte venait d'être perdu, et la version précédente était à un clic.
//
// La séance n'a jamais eu ce défaut : son bouton ne dépend que de `seanceId`. C'est la
// comparaison des deux écrans qui a fait sortir le bug — les deux font le même geste, ils
// doivent le faire pareil.
//
// CE QU'IL N'ATTRAPE PAS, et il faut le savoir : un bouton rendu invisible par du style, ou une
// condition portée plus haut dans l'arbre. Le front tourne sur `node --test`, sans jsdom ni
// testing-library : aucun rendu de composant n'est possible. Le test porte sur la SOURCE.
//
// Lancer : npm test  (ou  node --test src/historique-accessible-apres-un-echec.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const activite = readFileSync(join(SRC, 'components', 'ActiviteEcran.jsx'), 'utf8')
const seance = readFileSync(join(SRC, 'components', 'SeanceEcran.jsx'), 'utf8')

// Les conditions JSX encore OUVERTES au-dessus d'une ligne donnée : on compte les `{x && (`
// ouverts moins les `)}` fermés, en remontant depuis le début du fichier.
function conditionsOuvertesAvant(source, aiguille) {
  const lignes = source.split('\n')
  const cible = lignes.findIndex((l) => l.includes(aiguille))
  assert.notEqual(cible, -1, `Introuvable dans la source : ${aiguille}`)
  const pile = []
  for (let i = 0; i < cible; i++) {
    const l = lignes[i].trim()
    const ouvre = l.match(/^\{([^}]*?)&&\s*\($/)
    if (ouvre) { pile.push(ouvre[1].trim()); continue }
    if (l === ')}' || l === ')}\n') pile.pop()
  }
  return pile
}

test("le bouton Historique de l'activité ne dépend pas de la présence d'un résultat", () => {
  const conditions = conditionsOuvertesAvant(activite, 'setHistoriqueOuvert(true)')
  const fautives = conditions.filter((c) => /\bresultat\b/.test(c))
  assert.deepEqual(
    fautives, [],
    "Le bouton « Historique » est de nouveau sous une condition portant sur `resultat` : " +
    `${fautives.join(' / ')}. Une génération qui échoue met resultat à null — le prof perd ` +
    "l'accès à ses versions précédentes juste après avoir perdu son texte.",
  )
})

test("l'échec d'une génération remet bien resultat à null (la raison du test ci-dessus)", () => {
  // Si ce fait changeait, le test précédent perdrait son sens : on le vérifie plutôt que de
  // le supposer.
  assert.ok(
    activite.includes('setResultat(null)'),
    "ActiviteEcran ne remet plus `resultat` à null : vérifier si la condition d'affichage de " +
    "l'historique a encore une raison d'être surveillée.",
  )
})

test("l'activité et la séance conditionnent l'historique de la même façon", () => {
  const cetteActivite = conditionsOuvertesAvant(activite, 'setHistoriqueOuvert(true)')
  const cetteSeance = conditionsOuvertesAvant(seance, 'setHistoriqueOuvert(true)')
  // On compare la NATURE de la garde : l'identifiant en base, et rien d'autre.
  const garde = (c) => c.filter((x) => !/^\s*$/.test(x)).map((x) => x.replace(/Id\b/, 'Id'))
  assert.deepEqual(
    garde(cetteActivite).length, garde(cetteSeance).length,
    `L'activité garde son historique derrière ${JSON.stringify(cetteActivite)} et la séance ` +
    `derrière ${JSON.stringify(cetteSeance)}. Deux écrans qui font le même geste doivent le ` +
    "faire pareil — c'est cette comparaison qui a révélé le défaut.",
  )
})

test("les deux écrans exigent quand même que le contenu existe en base", () => {
  // L'autre bord : avant la première écriture, il n'y a aucune version à relire.
  assert.match(activite, /\{activiteId && \(/, "L'activité n'exige plus `activiteId`.")
  assert.match(seance, /\{seanceId && \(/, "La séance n'exige plus `seanceId`.")
})
