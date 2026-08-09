// LA lecture du markdown — ce que TOUTES les sorties reçoivent (écran, impression, Word, PDF).
//
// Ces tests existent à cause du 07/08/2026 : l'ancien formateur, écrit à la main, ne connaissait
// ni les tableaux, ni les blocs de code, ni les citations, et personne ne s'en était aperçu parce
// qu'il n'avait AUCUN test. 38 activités sur 41 sortaient en barres verticales.
//
// On ne teste pas `marked` (ce n'est pas notre code) : on teste que NOS choix tiennent — l'option
// « retour à la ligne = à la ligne », la mise à plat du texte enrichi, et le fait que les
// constructions qui manquaient sont bien reconnues.

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { lireBlocs, versHtml, morceaux, texteNu } from './markdown.js'

const types = t => lireBlocs(t).map(b => b.type).filter(x => x !== 'space')

test('les trois constructions qui manquaient sont reconnues', () => {
  assert.deepEqual(types('| A | B |\n|---|---|\n| 1 | 2 |'), ['table'])
  assert.deepEqual(types('```js\nconst x = 1\n```'), ['code'])
  assert.deepEqual(types('> une citation'), ['blockquote'])
})

test('un tableau rend ses en-têtes et ses lignes', () => {
  const [t] = lireBlocs('| Critère | Points |\n|---|---|\n| Clarté | 4 |\n| Exactitude | 6 |')
  assert.equal(t.type, 'table')
  assert.deepEqual(t.header.map(h => h.text), ['Critère', 'Points'])
  assert.equal(t.rows.length, 2)
  assert.deepEqual(t.rows[1].map(c => c.text), ['Exactitude', '6'])
})

test('une cellule qui contient une barre verticale échappée ne casse pas le tableau', () => {
  const [t] = lireBlocs('| Opérateur | Sens |\n|---|---|\n| \\| | ou bit à bit |')
  assert.equal(t.rows.length, 1)
  assert.equal(t.rows[0].length, 2, 'la barre échappée ne doit pas créer une troisième colonne')
})

test('un bloc de code garde son texte tel quel, indentation comprise', () => {
  const [c] = lireBlocs('```python\ndef f():\n    return 1\n```')
  assert.equal(c.type, 'code')
  assert.equal(c.lang, 'python')
  assert.equal(c.text, 'def f():\n    return 1')
})

test('un bloc de code non refermé ne fait pas disparaître la suite', () => {
  const html = versHtml('```\ncode oublié\n\nla suite du cours')
  assert.match(html, /code oublié/)
  assert.match(html, /la suite du cours/)
})

test('les titres vont jusqu au niveau 6', () => {
  const blocs = lireBlocs('# un\n\n#### quatre\n\n###### six')
  assert.deepEqual(blocs.filter(b => b.type === 'heading').map(b => b.depth), [1, 4, 6])
})

test('un retour à la ligne simple reste un retour à la ligne (option breaks)', () => {
  // Sans ce choix, markdown collerait les deux lignes en un seul paragraphe et TOUT l'existant
  // se serait resserré du jour au lendemain.
  assert.match(versHtml('ligne un\nligne deux'), /<br\s*\/?>/)
})

test('morceaux met le texte enrichi à plat en gardant les styles', () => {
  const [p] = lireBlocs('**Objectif :** ce que les élèves *construisent*')
  const m = morceaux(p.tokens)
  assert.equal(m[0].texte, 'Objectif :')
  assert.equal(m[0].gras, true)
  assert.equal(m.find(x => x.italique)?.texte, 'construisent')
  assert.equal(texteNu(p.tokens), 'Objectif : ce que les élèves construisent')
})

test('gras et italique imbriqués gardent les deux styles', () => {
  const [p] = lireBlocs('**gras et *les deux* encore**')
  const deux = morceaux(p.tokens).find(m => m.italique)
  assert.equal(deux.gras, true, 'l italique dans du gras doit rester gras')
})

test('un lien rend son libellé, pas son adresse', () => {
  const [p] = lireBlocs('voir [le référentiel](https://exemple.fr/doc.pdf)')
  assert.equal(texteNu(p.tokens), 'voir le référentiel')
})

test('une liste rend ses éléments, ordonnée ou non', () => {
  const [ul] = lireBlocs('- un\n- deux')
  assert.equal(ul.ordered, false)
  assert.equal(ul.items.length, 2)
  const [ol] = lireBlocs('1. un\n2. deux')
  assert.equal(ol.ordered, true)
  assert.equal(ol.items.length, 2)
})

test('le texte vide ne fait rien planter', () => {
  for (const vide of [null, undefined, '', '   ']) {
    assert.doesNotThrow(() => lireBlocs(vide))
    assert.doesNotThrow(() => versHtml(vide))
  }
})

test('les fins de ligne Windows sont acceptées comme les autres', () => {
  assert.deepEqual(types('| A |\r\n|---|\r\n| 1 |'), ['table'])
})
