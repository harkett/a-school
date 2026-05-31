// Test des fonctions pures du visualiseur de dictée.
// Lance avec :  node --test src/utils/audioViz.test.js   (depuis frontend/)
import test from 'node:test'
import assert from 'node:assert/strict'
import { formatTime, computeBarLevels } from './audioViz.js'

test('formatTime : format m:ss', () => {
  assert.equal(formatTime(0), '0:00')
  assert.equal(formatTime(4), '0:04')
  assert.equal(formatTime(59), '0:59')
  assert.equal(formatTime(60), '1:00')
  assert.equal(formatTime(83), '1:23')
  assert.equal(formatTime(725), '12:05')
})

test('formatTime : robustesse (négatif / undefined -> 0:00)', () => {
  assert.equal(formatTime(-3), '0:00')
  assert.equal(formatTime(undefined), '0:00')
  assert.equal(formatTime(null), '0:00')
})

test('computeBarLevels : nBars niveaux bornés 0..1', () => {
  const levels = computeBarLevels(new Uint8Array(32).fill(128), 12)
  assert.equal(levels.length, 12)
  for (const v of levels) assert.ok(v >= 0 && v <= 1, `niveau hors bornes: ${v}`)
})

test('computeBarLevels : plein volume -> 1, silence -> 0', () => {
  assert.ok(computeBarLevels(new Uint8Array(32).fill(255), 12).every(v => v === 1))
  assert.ok(computeBarLevels(new Uint8Array(32).fill(0), 12).every(v => v === 0))
})

test('computeBarLevels : entrée vide / absente -> nBars zéros', () => {
  assert.deepEqual(computeBarLevels(null, 5), [0, 0, 0, 0, 0])
  assert.deepEqual(computeBarLevels(new Uint8Array(0), 4), [0, 0, 0, 0])
})
