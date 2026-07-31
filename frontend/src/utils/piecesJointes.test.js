// Test de la phrase des formats acceptés (Mes retours + Aide).
// Lance avec :  node --test src/utils/piecesJointes.test.js   (depuis frontend/)
//
// Cette phrase était écrite à la main à trois endroits (« PNG, JPEG, PDF ou TXT », « PNG,
// JPEG, PDF, TXT », « PNG, JPEG ou PDF » dans une infobulle — déjà fausse, elle oubliait le
// TXT). Elle se construit maintenant sur la liste servie par le serveur. Ce qui est vérifié :
// la liaison change selon la phrase d'accueil, et rien de chargé n'invente rien.
import test from 'node:test'
import assert from 'node:assert/strict'
import { listeFormats } from './piecesJointes.js'

const LIMITES = { formats_lisibles: ['PNG', 'JPEG', 'PDF', 'TXT'] }

test('listeFormats : virgules puis la liaison devant le dernier', () => {
  assert.equal(listeFormats(LIMITES), 'PNG, JPEG, PDF ou TXT')
  assert.equal(listeFormats(LIMITES, 'et'), 'PNG, JPEG, PDF et TXT')
})

test('listeFormats : deux formats = pas de virgule, un seul = le format nu', () => {
  assert.equal(listeFormats({ formats_lisibles: ['PDF', 'TXT'] }), 'PDF ou TXT')
  assert.equal(listeFormats({ formats_lisibles: ['PDF'] }), 'PDF')
})

test('listeFormats : rien de chargé → chaîne vide, jamais une liste devinée', () => {
  // L'écran n'annonce alors AUCUN format, plutôt que d'en promettre un que le serveur
  // refuserait. C'est la règle maison : on ne remplace pas une donnée absente par une copie.
  assert.equal(listeFormats(null), '')
  assert.equal(listeFormats(undefined), '')
  assert.equal(listeFormats({}), '')
  assert.equal(listeFormats({ formats_lisibles: [] }), '')
})

test('listeFormats : la liste vient du serveur, elle n\'est pas figée ici', () => {
  // Ajouter un format en amont suffit à changer la phrase — aucun écran à retoucher.
  assert.equal(listeFormats({ formats_lisibles: ['PNG', 'WEBP'] }), 'PNG ou WEBP')
})
