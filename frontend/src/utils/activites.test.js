// Tests de la logique pure partagée par les pages listes de Mes contenus.
// Lance avec :  node --test src/utils/activites.test.js   (depuis frontend/)
// (Les tests de sauvegarderActivite ont été démolis le 30/07 avec POST /api/mes-activites.)
import test from 'node:test'
import assert from 'node:assert/strict'
import { grouperParCouple, coupleKey, formatDateActivite, couleurCouple, correspondProfil, typeVierge } from './activites.js'

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

// --- correspondProfil : garde « Reprendre » (activité vs profil courant) ---

test('correspondProfil : même matière ET même niveau -> true', () => {
  assert.equal(correspondProfil({ matiere: 'Réseaux', niveau: 'BTS CIEL option A' }, 'Réseaux', 'BTS CIEL option A'), true)
})

test('correspondProfil : matière différente -> false', () => {
  assert.equal(correspondProfil({ matiere: 'Français', niveau: 'BTS CIEL option A' }, 'Réseaux', 'BTS CIEL option A'), false)
})

test('correspondProfil : niveau différent -> false (même si matière OK)', () => {
  assert.equal(correspondProfil({ matiere: 'Réseaux', niveau: 'Master' }, 'Réseaux', 'BTS CIEL option A'), false)
})

test('correspondProfil : activité nulle/indéfinie -> false (pas de crash)', () => {
  assert.equal(correspondProfil(null, 'Réseaux', 'BTS CIEL option A'), false)
  assert.equal(correspondProfil(undefined, 'Réseaux', 'BTS CIEL option A'), false)
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
  assert.deepEqual(formatDateActivite(null, NOW), { court: '', complet: '', numerique: '', recent: false, heure: '' })
  assert.deepEqual(formatDateActivite('pas-une-date', NOW), { court: '', complet: '', numerique: '', recent: false, heure: '' })
})

test('heure : HH:MM de la sauvegarde', () => {
  assert.equal(formatDateActivite('2026-06-12T08:05:00', NOW).heure, '08:05')
  assert.equal(formatDateActivite('2026-06-12T14:32:00', NOW).heure, '14:32')
})

test('numerique : JJ/MM/AAAA à deux chiffres', () => {
  assert.equal(formatDateActivite('2026-07-26T09:27:00', NOW).numerique, '26/07/2026')
  assert.equal(formatDateActivite('2026-01-05T09:27:00', NOW).numerique, '05/01/2026')
})

// --- couleurCouple ---

test('couleur : déterministe (même clé -> même couleur) et format hex', () => {
  const c1 = couleurCouple(coupleKey('Maths', '5e'))
  const c2 = couleurCouple(coupleKey('Maths', '5e'))
  assert.equal(c1, c2)
  assert.match(c1, /^#[0-9a-f]{6}$/)
})

// --- typeVierge : les combos du type d'activité démarrent vierges ---
// (venait de test/activite.test.js, rapatrié le 01/08 avec la fonction elle-même)

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
