// Preuve — la logique pure de l'écran Activité (utils/activite.js) :
//   `typeVierge` ne présélectionne RIEN (règle appli : combos sur placeholder gris).
//   (estPageCreer a été démolie le 30/07 avec l'ancien écran Créer.)
// Lancer : npm test  (ou  node --test test/activite.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { typeVierge } from '../src/utils/activite.js'

test('typeVierge : aucun type ni précision présélectionné', () => {
  assert.deepEqual(typeVierge(), {
    activite_type_id: null,
    sous_type: null,
    nb: null,
    avec_correction: false,
  })
})

// Le vrai piège d'avant : on recevait la liste des activités de la matière et on reposait le
// 1er type + sa 1re précision. Même avec une liste bien remplie, plus rien n'est choisi.
test('typeVierge : une liste d\'activités disponible ne repose plus le 1er type', () => {
  const activites = [
    { id: 3, label: 'Compréhension', sous_types: ['inférence', 'mélange'], besoins: ['nb'] },
    { id: 8, label: 'Questions de cours', sous_types: ['x'], besoins: [] },
  ]
  const r = typeVierge(activites)
  assert.equal(r.activite_type_id, null)
  assert.equal(r.sous_type, null)
  assert.equal(r.nb, null)
})

test('typeVierge : garde-fou liste vide / non-tableau → activite_type_id null, pas de crash', () => {
  assert.equal(typeVierge([]).activite_type_id, null)
  assert.equal(typeVierge(undefined).activite_type_id, null)
  assert.equal(typeVierge(null).activite_type_id, null)
})
