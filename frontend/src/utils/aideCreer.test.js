// Intégrité du CATALOGUE UNIQUE des explications de l'écran Créer (utils/aideCreer.js).
// Trois afficheurs le lisent (bulles de la visite guidée, fenêtre « Comment ça marche »,
// fiche du centre d'aide) : une entrée bancale casserait les trois d'un coup.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { GUIDE_CREER } from './aideCreer.js'

test('catalogue : chaque entrée est complète (cle, cible, titre, phrase, detail)', () => {
  assert.ok(GUIDE_CREER.length >= 4, 'au moins les grands gestes de l\'écran')
  for (const e of GUIDE_CREER) {
    assert.ok(e.cle && typeof e.cle === 'string', `cle manquante : ${JSON.stringify(e)}`)
    assert.ok(e.cible && typeof e.cible === 'string', `cible (ancre data-guide) manquante : ${e.cle}`)
    assert.ok(e.titre && typeof e.titre === 'string', `titre manquant : ${e.cle}`)
    assert.ok(e.phrase && typeof e.phrase === 'string', `phrase (bulle) manquante : ${e.cle}`)
    assert.ok(Array.isArray(e.detail) && e.detail.length > 0, `detail (fiche) manquant : ${e.cle}`)
    assert.ok(e.detail.every(p => typeof p === 'string' && p.length > 0), `paragraphe vide : ${e.cle}`)
  }
})

test('catalogue : clés et cibles uniques (une explication = une place)', () => {
  const cles = GUIDE_CREER.map(e => e.cle)
  const cibles = GUIDE_CREER.map(e => e.cible)
  assert.equal(new Set(cles).size, cles.length, 'cle en double')
  assert.equal(new Set(cibles).size, cibles.length, 'cible en double')
})

test('catalogue : les ancres attendues par l\'écran actuel existent', () => {
  const cibles = new Set(GUIDE_CREER.map(e => e.cible))
  for (const attendue of ['couple', 'type', 'corrige', 'boutons', 'texte', 'generer', 'resultat']) {
    assert.ok(cibles.has(attendue), `ancre absente du catalogue : ${attendue}`)
  }
})
