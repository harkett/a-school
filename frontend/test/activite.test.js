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

test('typeParDefaut : prend le 1er type de la liste (identité = id, besoin nb lu du prompt)', () => {
  const activites = [
    { id: 3, label: 'Compréhension', sous_types: [], besoins: ['nb'] },
    { id: 8, label: 'Questions de cours', sous_types: ['x'], besoins: [] },
  ]
  assert.deepEqual(typeParDefaut(activites), {
    activite_type_id: 3,
    sous_type: null,
    nb: 5,
    avec_correction: false,
  })
})

test('typeParDefaut : 1er sous-type pris quand il existe', () => {
  const activites = [{ id: 7, label: 'Compréhension', sous_types: ['inférence', 'mélange'], besoins: ['nb', 'sous_type'] }]
  const r = typeParDefaut(activites)
  assert.equal(r.activite_type_id, 7)
  assert.equal(r.sous_type, 'inférence')
  assert.equal(r.nb, 5)
})

test('typeParDefaut : pas de nb quand le prompt du type ne le demande pas', () => {
  const activites = [{ id: 5, label: 'Fiche', sous_types: [], besoins: [] }]
  assert.equal(typeParDefaut(activites).nb, null)
})

test('typeParDefaut : garde-fou liste vide / non-tableau → activite_type_id null, pas de crash', () => {
  assert.equal(typeParDefaut([]).activite_type_id, null)
  assert.equal(typeParDefaut(undefined).activite_type_id, null)
  assert.equal(typeParDefaut(null).activite_type_id, null)
})
