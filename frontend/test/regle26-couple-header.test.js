// RÈGLE 26 — le couple Matière - Niveau reste affiché en permanence dans le header, juste
// AU-DESSUS de « Changer niveau et/ou matière », sur TOUS les écrans.
//
// CE QUE CE TEST ATTRAPE : la suppression du couple, son passage SOUS le bouton, sa mise sous
// condition (`{x && <div…`), et le démontage du Header dans App.jsx.
//
// CE QU'IL N'ATTRAPE PAS, et il faut le savoir : un `display: none` glissé dans le style, ou
// un couple rendu vide parce que les props arrivent nulles. Le front tourne sur `node --test`
// (le runner intégré de Node), sans jsdom ni testing-library : aucun rendu de composant n'est
// possible ici, et ajouter une dépendance de test au projet est un autre sujet. Le test porte
// donc sur la SOURCE — la structure, pas le pixel.
//
// Lancer : npm test  (ou  node --test test/regle26-couple-header.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = join(dirname(fileURLToPath(import.meta.url)), '..', 'src')
const header = readFileSync(join(SRC, 'components', 'Header.jsx'), 'utf8')
const app = readFileSync(join(SRC, 'App.jsx'), 'utf8')

// La ligne « utile » qui précède celle-ci : on saute le vide et les commentaires, pour voir si
// le bloc est enfermé dans une condition ouverte juste au-dessus (`{cond && (`).
function ligneUtileAvant(source, aiguille) {
  const lignes = source.split('\n')
  const index = lignes.findIndex((l) => l.includes(aiguille))
  assert.notEqual(index, -1, `Introuvable dans la source : ${aiguille}`)
  for (let i = index - 1; i >= 0; i--) {
    const l = lignes[i].trim()
    if (l === '' || l.startsWith('//') || l.startsWith('{/*') || l.startsWith('*')) continue
    return { precedente: l, courante: lignes[index].trim() }
  }
  return { precedente: '', courante: lignes[index].trim() }
}

test('RÈGLE 26 : le couple est construit à partir de la matière ET du niveau', () => {
  assert.match(
    header,
    /const\s+matiereNiveau\s*=\s*\[\s*matiere\s*,\s*niveau\s*\]/,
    'Header.jsx ne compose plus le couple à partir de `matiere` et `niveau`.',
  )
  assert.ok(
    header.includes('{matiereNiveau}'),
    'Header.jsx ne rend plus `{matiereNiveau}` : le couple a disparu de l\'écran.',
  )
})

test('RÈGLE 26 : le couple est AU-DESSUS du bouton « Changer niveau et/ou matière »', () => {
  const posCouple = header.indexOf('{matiereNiveau}')
  const posBouton = header.indexOf('<CoupleBandeau')
  assert.ok(posCouple !== -1 && posBouton !== -1, 'Le couple ou son bouton a disparu du header.')
  assert.ok(
    posCouple < posBouton,
    'Le couple passe SOUS « Changer niveau et/ou matière » : dans une colonne flex, l\'ordre '
      + 'de la source EST l\'ordre à l\'écran. La règle 26 le veut au-dessus.',
  )
})

test('RÈGLE 26 : le bloc du couple n\'est enfermé dans aucune condition', () => {
  const { precedente, courante } = ligneUtileAvant(header, 'data-guide="couple"')
  assert.ok(
    !/(&&|\?)\s*\(?\s*$/.test(precedente),
    `Le bloc du couple est ouvert sous une condition : « ${precedente} ». Le couple s'affiche `
      + 'EN PERMANENCE, il ne se conditionne pas.',
  )
  assert.ok(
    courante.startsWith('<div'),
    `Le bloc du couple est conditionné sur sa propre ligne : « ${courante} ».`,
  )
  const bloc = header.slice(header.indexOf('data-guide="couple"'), header.indexOf('<CoupleBandeau'))
  assert.ok(
    !bloc.includes('&&'),
    'Une condition est apparue entre le conteneur du couple et son affichage.',
  )
})

test('RÈGLE 26 : le Header est monté sur TOUS les écrans, avec le couple', () => {
  const { precedente } = ligneUtileAvant(app, '<Header')
  assert.ok(
    !/(&&|\?)\s*\(?\s*$/.test(precedente),
    `Le Header est monté sous condition dans App.jsx : « ${precedente} ». Il doit l'être sur `
      + 'tous les écrans.',
  )
  const bloc = app.slice(app.indexOf('<Header'), app.indexOf('<Header') + 900)
  assert.match(bloc, /matiere=\{/, 'App.jsx ne passe plus la matière au Header.')
  assert.match(bloc, /niveau=\{/, 'App.jsx ne passe plus le niveau au Header.')
})
