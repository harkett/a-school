// Santé serveur côté client : on ne réagit qu'à des échecs RÉPÉTÉS (jamais un blip),
// et la reprise (1er succès) masque le message aussitôt.
// Lance avec :  node --test src/serverHealth.test.js   (depuis frontend/)
import test, { beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import {
  registerServerHealthHandler,
  reportApiFailure,
  reportApiSuccess,
  SEUIL_PANNE,
  _resetForTests,
} from './serverHealth.js'

beforeEach(() => _resetForTests())

test('1. un échec isolé ne déclenche RIEN (pas de blip)', () => {
  const calls = []
  registerServerHealthHandler(d => calls.push(d))
  reportApiFailure()
  assert.deepEqual(calls, [])
})

test('2. SEUIL_PANNE échecs consécutifs → bandeau affiché (dégradé)', () => {
  const calls = []
  registerServerHealthHandler(d => calls.push(d))
  for (let i = 0; i < SEUIL_PANNE; i++) reportApiFailure()
  assert.deepEqual(calls, [true]) // une seule bascule vers « dégradé »
})

test('3. un succès remet à zéro et masque le bandeau', () => {
  const calls = []
  registerServerHealthHandler(d => calls.push(d))
  for (let i = 0; i < SEUIL_PANNE; i++) reportApiFailure()
  reportApiSuccess()
  assert.deepEqual(calls, [true, false])
})

test('4. des échecs sous le seuil, coupés par un succès, ne déclenchent pas', () => {
  const calls = []
  registerServerHealthHandler(d => calls.push(d))
  for (let i = 0; i < SEUIL_PANNE - 1; i++) reportApiFailure()
  reportApiSuccess() // reset avant d'atteindre le seuil
  for (let i = 0; i < SEUIL_PANNE - 1; i++) reportApiFailure()
  assert.deepEqual(calls, [])
})
