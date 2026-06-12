// Test du helper de sauvegarde d'activité (Phase 2.1 — perte silencieuse supprimée).
// Lance avec :  node --test src/utils/activites.test.js   (depuis frontend/)
//
// Vérifie le CŒUR du fix : l'échec de sauvegarde est bien DÉTECTÉ et REMONTÉ (lève),
// pour que l'UI puisse notifier le prof — au lieu de l'avaler en silence.
import test from 'node:test'
import assert from 'node:assert/strict'
import { sauvegarderActivite, grouperParCouple, coupleKey, formatDateActivite, couleurCouple } from './activites.js'

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

test('dans une section, tri par date décroissante (null en dernier)', () => {
  const secs = grouperParCouple([
    { id: 1, matiere: 'Maths', niveau: '5e', created_at: '2026-06-01T10:00:00' },
    { id: 2, matiere: 'Maths', niveau: '5e', created_at: null },
    { id: 3, matiere: 'Maths', niveau: '5e', created_at: '2026-06-10T10:00:00' },
  ])
  assert.deepEqual(secs[0].items.map(a => a.id), [3, 1, 2])
})

// --- formatDateActivite ---

const NOW = new Date('2026-06-12T12:00:00')

test('date : aujourd’hui / hier / il y a X jours / date complète + drapeau recent', () => {
  assert.equal(formatDateActivite('2026-06-12T08:00:00', NOW).court, "aujourd'hui")
  assert.equal(formatDateActivite('2026-06-12T08:00:00', NOW).recent, true)
  assert.equal(formatDateActivite('2026-06-11T08:00:00', NOW).court, 'hier')
  assert.equal(formatDateActivite('2026-06-09T08:00:00', NOW).court, 'il y a 3 jours')
  assert.equal(formatDateActivite('2026-06-09T08:00:00', NOW).recent, true)
})

test('date : au-delà de 7 jours -> date complète (recent=false), jamais « il y a 247 jours »', () => {
  const r = formatDateActivite('2025-10-08T08:00:00', NOW)
  assert.match(r.court, /^le /)
  assert.ok(!r.court.includes('il y a'))
  assert.equal(r.complet, '8 octobre 2025')
  assert.equal(r.recent, false)
})

test('date : null ou illisible -> libellés vides, recent=false', () => {
  assert.deepEqual(formatDateActivite(null, NOW), { court: '', complet: '', recent: false })
  assert.deepEqual(formatDateActivite('pas-une-date', NOW), { court: '', complet: '', recent: false })
})

// --- couleurCouple ---

test('couleur : déterministe (même clé -> même couleur) et format hex', () => {
  const c1 = couleurCouple(coupleKey('Maths', '5e'))
  const c2 = couleurCouple(coupleKey('Maths', '5e'))
  assert.equal(c1, c2)
  assert.match(c1, /^#[0-9a-f]{6}$/)
})
