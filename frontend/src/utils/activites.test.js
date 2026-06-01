// Test du helper de sauvegarde d'activité (Phase 2.1 — perte silencieuse supprimée).
// Lance avec :  node --test src/utils/activites.test.js   (depuis frontend/)
//
// Vérifie le CŒUR du fix : l'échec de sauvegarde est bien DÉTECTÉ et REMONTÉ (lève),
// pour que l'UI puisse notifier le prof — au lieu de l'avaler en silence.
import test from 'node:test'
import assert from 'node:assert/strict'
import { sauvegarderActivite } from './activites.js'

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
