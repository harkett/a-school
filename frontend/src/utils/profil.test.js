// Test de la cascade matière ← niveau (Mon profil — scope par NIVEAU).
// Lance avec :  node --test src/utils/profil.test.js   (depuis frontend/)
//
// Vérifie : (1) la matière est filtrée sur le NIVEAU (le programme du diplôme), dans
// l'ordre fourni par le référentiel ; (2) le libellé « Langues Vivantes (LV) » reste celui
// qui déclenchera le sous-menu langue ; (3) la détection d'incohérence niveau↔matière et
// le blocage de « Valider » ; (4) un profil EXISTANT cohérent n'est pas dérangé.
import test from 'node:test'
import assert from 'node:assert/strict'
import { matieresDuNiveau, matiereConnue, matiereIncoherente, profilPretAValider, niveauxRefDisponibles, niveauDisponible } from './profil.js'

// Réplique fidèle d'un /api/programmes → matieres_par_niveau (ordre = ordre du référentiel).
const PAR_NIVEAU = [
  { niveau: 'BTS CIEL option A', matieres: [
    { id: 1, nom: 'Culture générale et expression' },
    { id: 2, nom: 'Anglais' },
    { id: 3, nom: 'Mathématiques' },
    { id: 4, nom: 'Physique' },
    { id: 5, nom: 'Informatique' },
  ] },
  { niveau: '3e', matieres: [
    { id: 10, nom: 'Français' },
    { id: 11, nom: 'Langues Vivantes (LV)' },
  ] },
]

const TRIGGER_SOUS_MENU_LANGUE = 'Langues Vivantes (LV)'

test('matieresDuNiveau : matières du niveau, dans l\'ordre fourni (référentiel)', () => {
  const noms = matieresDuNiveau(PAR_NIVEAU, 'BTS CIEL option A').map(m => m.nom)
  assert.deepEqual(noms, [
    'Culture générale et expression', 'Anglais', 'Mathématiques', 'Physique', 'Informatique',
  ])  // ordre préservé : pas alphabétique, pas par ordre global de matière
})

test('matieresDuNiveau : null sans niveau ou niveau inconnu (→ repli « tout groupé »)', () => {
  assert.equal(matieresDuNiveau(PAR_NIVEAU, ''), null)
  assert.equal(matieresDuNiveau(PAR_NIVEAU, 'Niveau inexistant'), null)
})

test('matiereIncoherente : matière hors du programme du niveau → true', () => {
  // « Informatique » n'est pas enseignée en 3e (c'est une matière du BTS) :
  assert.equal(matiereIncoherente(PAR_NIVEAU, '3e', 'Informatique'), true)
  // « Français » n'est pas au programme du BTS CIEL option A :
  assert.equal(matiereIncoherente(PAR_NIVEAU, 'BTS CIEL option A', 'Français'), true)
})

test('matiereIncoherente : paire cohérente → false', () => {
  assert.equal(matiereIncoherente(PAR_NIVEAU, 'BTS CIEL option A', 'Informatique'), false)
  assert.equal(matiereIncoherente(PAR_NIVEAU, '3e', 'Français'), false)
})

test('matiereIncoherente : on ne juge pas ce qu\'on ne peut pas trancher', () => {
  assert.equal(matiereIncoherente(PAR_NIVEAU, 'BTS CIEL option A', ''), false)  // pas de matière
  assert.equal(matiereIncoherente(PAR_NIVEAU, '', 'Informatique'), false)       // pas de niveau
  assert.equal(matiereIncoherente([], 'BTS CIEL option A', 'Informatique'), false) // pas chargé
  assert.equal(matiereIncoherente(PAR_NIVEAU, 'Niveau inconnu', 'Informatique'), false)
})

test('profilPretAValider : niveau ET matière valides obligatoires', () => {
  assert.equal(profilPretAValider(PAR_NIVEAU, 'BTS CIEL option A', 'Français'), false)     // incohérent → bloqué
  assert.equal(profilPretAValider(PAR_NIVEAU, 'BTS CIEL option A', ''), false)             // niveau sans matière → bloqué
  assert.equal(profilPretAValider(PAR_NIVEAU, '', 'Informatique'), false)                  // matière sans niveau → bloqué
  assert.equal(profilPretAValider(PAR_NIVEAU, '', ''), false)                              // rien → bloqué (niveau obligatoire)
  assert.equal(profilPretAValider(PAR_NIVEAU, 'BTS CIEL option A', 'Informatique'), true)  // cohérent → OK
})

test('REGRESSION sous-menu langue : la 3e propose EXACTEMENT la valeur déclencheuse', () => {
  const liste = matieresDuNiveau(PAR_NIVEAU, '3e')
  assert.ok(liste.some(m => m.nom === TRIGGER_SOUS_MENU_LANGUE),
    'le niveau 3e doit contenir le libellé exact « Langues Vivantes (LV) »')
})

test('PROFIL EXISTANT cohérent : niveau + matière valides → rien à signaler', () => {
  const liste = matieresDuNiveau(PAR_NIVEAU, '3e')
  assert.equal(matiereConnue(liste, 'Langues Vivantes (LV)'), true)
})

// Côté PROF : les niveaux non disponibles sont CACHÉS (filtrés), pas grisés.
const NIVEAUX_PC = [
  { cycle: 'Lycée',     niveaux: [{ id: 13, nom: '2nde', refDisponible: true }] },
  { cycle: 'Supérieur', niveaux: [
    { id: 26, nom: 'BTS CIEL option A', refDisponible: true },
    { id: 20, nom: 'Master',            refDisponible: false },   // non disponible → caché
  ] },
  { cycle: 'Crèche',    niveaux: [{ id: 1, nom: 'Groupe A', refDisponible: false }] },  // cycle 100% non disponible
]

test('niveauxRefDisponibles : ne garde que les niveaux disponibles, retire les cycles vides', () => {
  const res = niveauxRefDisponibles(NIVEAUX_PC)
  const parCycle = Object.fromEntries(res.map(g => [g.cycle, g.niveaux.map(n => n.nom)]))
  assert.deepEqual(parCycle, {
    'Lycée': ['2nde'],
    'Supérieur': ['BTS CIEL option A'],   // Master (non disponible) retiré
  })  // Crèche (100% non disponible) a disparu
})

test('niveauDisponible : true pour un niveau disponible, false pour caché/inconnu', () => {
  assert.equal(niveauDisponible(NIVEAUX_PC, 'BTS CIEL option A'), true)
  assert.equal(niveauDisponible(NIVEAUX_PC, 'Master'), false)       // hérité sur un niveau caché → modale
  assert.equal(niveauDisponible(NIVEAUX_PC, 'Inexistant'), false)   // niveau disparu → modale
  assert.equal(niveauDisponible(NIVEAUX_PC, ''), true)              // pas de niveau → géré par Valider
})
