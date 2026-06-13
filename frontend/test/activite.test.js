// Preuve — la logique pure de l'écran « Créer » (utils/activite.js) :
//   1. `estPageCreer` ne déclenche la remise à zéro QUE pour 'creer-activite'.
//   2. `typeParDefaut` remet le type au 1er de la matière, avec garde-fou liste vide.
// Lancer : npm test  (ou  node --test test/activite.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { estPageCreer, typeParDefaut } from '../src/utils/activite.js'

test('estPageCreer : vrai seulement pour creer-activite', () => {
  assert.equal(estPageCreer('creer-activite'), true)
  assert.equal(estPageCreer('mes-activites'), false)
  assert.equal(estPageCreer('accueil'), false)
  assert.equal(estPageCreer('creer-sequence'), false)
})

test('typeParDefaut : prend le 1er type de la liste', () => {
  const activites = [
    { key: 'gen_comprehension', sous_types: [], params: ['nb'] },
    { key: 'gen_questions_cours', sous_types: ['x'], params: [] },
  ]
  assert.deepEqual(typeParDefaut(activites), {
    activite_key: 'gen_comprehension',
    sous_type: null,
    nb: 5,
    avec_correction: false,
  })
})

test('typeParDefaut : 1er sous-type pris quand il existe', () => {
  const activites = [{ key: 'comprehension', sous_types: ['inférence', 'mélange'], params: ['nb', 'sous_type'] }]
  const r = typeParDefaut(activites)
  assert.equal(r.activite_key, 'comprehension')
  assert.equal(r.sous_type, 'inférence')
  assert.equal(r.nb, 5)
})

test('typeParDefaut : pas de nb quand le type ne le demande pas', () => {
  const activites = [{ key: 'fiche', sous_types: [], params: [] }]
  assert.equal(typeParDefaut(activites).nb, null)
})

test('typeParDefaut : garde-fou liste vide / non-tableau → activite_key vide, pas de crash', () => {
  assert.equal(typeParDefaut([]).activite_key, '')
  assert.equal(typeParDefaut(undefined).activite_key, '')
  assert.equal(typeParDefaut(null).activite_key, '')
})
