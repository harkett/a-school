// LA FICHE D'UNE DÉMONSTRATION SE REMPLIT DANS UNE VRAIE FENÊTRE.
//
// CE QU'ON AVAIT (16/08/2026) : « Modifier » dépliait la ligne du tableau et posait le formulaire
// dedans, dans un <td colSpan>. Le tableau sautait de hauteur à chaque ouverture, les lignes
// voisines restaient cliquables — il fallait griser leurs boutons un par un pour empêcher
// d'ouvrir deux fiches à la fois — et la saisie se perdait au milieu des autres démonstrations.
//
// LA NORME DE LA MAISON, c'est FenetrePro : une coquille UNIQUE, déplaçable par sa barre de
// titre, étirable par le coin, avec en-tête et pied. Une boîte figée au milieu de l'écran n'en
// est pas une. Ici, un voile s'ajoute autour : on remplit une fiche, l'écran d'en dessous ne
// doit pas répondre tant qu'on n'a pas validé ou annulé.
//
// CE QUE CE TEST ATTRAPE : le retour du formulaire dans le tableau, une boîte réécrite à la main
// au lieu de la coquille commune, la disparition du voile ou celle du pied.
//
// CE QU'IL N'ATTRAPE PAS : le rendu réel. Le front tourne sur `node --test`, sans jsdom : le test
// porte sur la SOURCE.
//
// Lancer : npm test  (ou  node --test src/la-fiche-demo-s-ouvre-en-fenetre.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const page = readFileSync(join(SRC, 'pages', 'AdminBaseDemos.jsx'), 'utf8')

// Le corps de la fenêtre : de sa déclaration jusqu'au composant suivant.
function corpsDeLaFenetre() {
  const debut = page.indexOf('function FenetreEdition(')
  assert.notEqual(debut, -1,
    'FenetreEdition a disparu : la fiche ne se remplit plus dans une fenêtre.')
  const suite = page.indexOf('\nfunction ', debut + 1)
  return page.slice(debut, suite === -1 ? page.length : suite)
}

test('le formulaire ne vit plus dans une ligne du tableau', () => {
  assert.doesNotMatch(
    page, /LigneEdition/,
    'Le formulaire est revenu dans le tableau (LigneEdition).\n' +
    'Reproduction : Admin → Base de données → Démos → « Modifier » — la ligne ne doit pas se déplier.'
  )
  assert.doesNotMatch(
    corpsDeLaFenetre(), /<t[rd][\s>]/,
    'La fenêtre contient à nouveau des cellules de tableau : elle est retournée dans la grille.'
  )
})

test('c’est LA fenêtre de la maison, pas une boîte réécrite', () => {
  // FenetrePro apporte ce qu'une boîte figée n'a pas : on la déplace par sa barre de titre, on
  // l'étire par le coin, elle a son en-tête et sa croix. La réécrire à la main, c'est reperdre
  // les trois.
  assert.match(page, /import FenetrePro from '\.\.\/components\/FenetrePro\.jsx'/,
    "La page n'importe plus FenetrePro : la fiche a repris une fenêtre figée.")
  const fenetre = corpsDeLaFenetre()
  assert.match(fenetre, /<FenetrePro\b/, 'FenetreEdition n’utilise plus la coquille commune.')
  assert.match(fenetre, /titre=\{titre\}/, 'La fenêtre n’a plus de titre dans sa barre.')
  assert.match(fenetre, /onFermer=/, 'La croix de la fenêtre ne referme plus rien.')
})

test("l'écran derrière est couvert pendant la saisie", () => {
  const fenetre = corpsDeLaFenetre()
  assert.match(fenetre, /position:\s*'fixed',\s*inset:\s*0/,
    'Le voile a disparu : on peut de nouveau cliquer dans l’écran pendant la saisie.')
  // Le voile passe SOUS la fenêtre, sinon il l'avalerait — elle ne se déplacerait plus.
  const voile = fenetre.slice(fenetre.indexOf('inset: 0'))
  const zVoile = Number(/zIndex:\s*(\d+)/.exec(voile)[1])
  const zFenetre = Number(/zIndex=\{(\d+)\}/.exec(fenetre)[1])
  assert.ok(zVoile < zFenetre,
    `Le voile (${zVoile}) est passé au-dessus de la fenêtre (${zFenetre}) : elle devient intouchable.`)
})

test('la fenêtre a son pied, et Échap en sort', () => {
  const fenetre = corpsDeLaFenetre()
  assert.match(fenetre, /key === 'Escape'/, 'Échap ne referme plus la fenêtre.')
  const pied = fenetre.slice(fenetre.lastIndexOf('borderTop'))
  assert.match(pied, /Annuler<\/button>/, 'Le pied de la fenêtre n’a plus son bouton Annuler.')
  assert.match(pied, /btnValider\(/, 'Le pied de la fenêtre n’a plus son bouton Valider.')
})

test("l'échec d'enregistrement se lit dans la fenêtre", () => {
  // La fenêtre reste ouverte quand le serveur refuse. Le message d'erreur de la page, lui, est
  // sous le voile : sans ce relais, l'admin cliquerait « Valider » sans jamais voir pourquoi rien
  // ne se passe.
  assert.match(page, /erreur=\{erreurEcriture\}/,
    'La fenêtre ne reçoit plus l’erreur d’écriture : un refus du serveur resterait invisible.')
  assert.match(corpsDeLaFenetre(), /\{erreur && \(/,
    'La fenêtre n’affiche plus l’erreur qu’on lui passe.')
})

test('le contenu remplit la fenêtre au lieu de la laisser vide', () => {
  // CE QU'ON A VU (16/08/2026) : la fenêtre s'étirait, le vide s'étirait avec elle, et les notes
  // se lisaient par une lucarne de trois lignes qu'il fallait faire défiler.
  const fenetre = corpsDeLaFenetre()
  assert.match(fenetre, /display: 'flex', flexDirection: 'column'/,
    'Le corps de la fenêtre n’est plus une colonne : son contenu ne peut plus s’étirer.')
  assert.match(fenetre, /flex: 1, minHeight: 120/,
    'Les zones de texte ne prennent plus la place restante : le bas de la fenêtre redevient vide.')
  assert.match(page, /const zoneTexte = \{/,
    'Le style des zones de texte a disparu : elles sont sans doute revenues à une hauteur figée.')
  assert.doesNotMatch(fenetre, /height: 56/,
    'Une zone de texte est revenue à une hauteur figée de trois lignes.')
})
