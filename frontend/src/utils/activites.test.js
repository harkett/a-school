// Test du helper de sauvegarde d'activité (Phase 2.1 — perte silencieuse supprimée).
// Lance avec :  node --test src/utils/activites.test.js   (depuis frontend/)
//
// Vérifie le CŒUR du fix : l'échec de sauvegarde est bien DÉTECTÉ et REMONTÉ (lève),
// pour que l'UI puisse notifier le prof — au lieu de l'avaler en silence.
import test from 'node:test'
import assert from 'node:assert/strict'
import { sauvegarderActivite, grouperParCouple, coupleKey } from './activites.js'

test('succès (HTTP ok) -> résout avec le JSON', async () => {
  global.fetch = async () => ({ ok: true, status: 200, json: async () => ({ id: 42 }) })
  const r = await sauvegarderActivite({ activite_key: 'x' })
  assert.deepEqual(r, { id: 42 })
})

test('statut HTTP non-ok (500) -> LÈVE (plus de perte silencieuse)', async () => {
  global.fetch = async () => ({ ok: false, status: 500, json: async () => ({}) })
  await assert.rejects(() => sauvegarderActivite({ activite_key: 'x' }), /HTTP 500/)
})

test('statut HTTP non-ok (401) -> LÈVE', async () => {
  global.fetch = async () => ({ ok: false, status: 401, json: async () => ({}) })
  await assert.rejects(() => sauvegarderActivite({ activite_key: 'x' }), /HTTP 401/)
})

test('échec réseau (fetch rejette) -> LÈVE', async () => {
  global.fetch = async () => { throw new Error('network down') }
  await assert.rejects(() => sauvegarderActivite({ activite_key: 'x' }), /network down/)
})

// --- grouperParCouple : onglet « Toutes mes activités » ---

const ECH = [
  { id: 1, matiere: 'Maths',    niveau: 'Terminale' },
  { id: 2, matiere: 'Français', niveau: 'BTS' },
  { id: 3, matiere: 'Maths',    niveau: 'Terminale' },
  { id: 4, matiere: 'Arts',     niveau: '6e' },
  { id: 5, matiere: null,       niveau: null },        // -> « Non classé »
]

test('groupe par couple et compte les items', () => {
  const secs = grouperParCouple(ECH)
  const maths = secs.find(s => s.key === coupleKey('Maths', 'Terminale'))
  assert.equal(maths.items.length, 2)
  assert.equal(maths.label, 'Maths — Terminale')
  assert.equal(secs.length, 4) // Maths-Term, Français-BTS, Arts-6e, Non classé
})

test('couple courant épinglé en tête', () => {
  const courant = coupleKey('Français', 'BTS')
  const secs = grouperParCouple(ECH, courant)
  assert.equal(secs[0].key, courant)
})

test('« Non classé » toujours en dernier, le reste alphabétique', () => {
  const secs = grouperParCouple(ECH, coupleKey('Français', 'BTS'))
  // [0] = courant (Français-BTS) ; ensuite alphabétique : Arts-6e, Maths-Terminale ; puis Non classé
  assert.equal(secs[secs.length - 1].label, 'Non classé')
  const apresCourant = secs.slice(1, -1).map(s => s.label)
  assert.deepEqual(apresCourant, ['Arts — 6e', 'Maths — Terminale'])
})

test('libellé partiel quand un seul champ est présent', () => {
  const secs = grouperParCouple([{ id: 9, matiere: 'SVT', niveau: null }])
  assert.equal(secs[0].label, 'SVT')
})
