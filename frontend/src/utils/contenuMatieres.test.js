// Page « Formations » — ce que l'écran affiche à partir de l'arbre que la base rend.
// Lance avec :  node --test src/utils/contenuMatieres.test.js   (depuis frontend/)
//
// Vérifie : (1) les trois états d'une matière ; (2) l'ordre et la complétude des lignes d'un
// niveau ; (3) le comptage « au programme » qui s'affiche sur la ligne du niveau ; (4) le
// compteur d'en-tête, qui ne dédoublonne PAS par nom — deux référentiels peuvent nommer chacun
// leur « Mathématiques », ce sont deux matières.
import test from 'node:test'
import assert from 'node:assert/strict'
import {
  etatMatiere, lignesMatieres, nbAuProgramme, compterContenu,
  AU_PROGRAMME, DESACTIVEE, PROPOSEE,
} from './contenuMatieres.js'

// Réplique fidèle d'un GET /admin/contenu : un cycle, deux niveaux — l'un pourvu, l'autre nu.
const CYCLES = [{
  id: 1, nom: 'BTS',
  niveaux: [
    {
      id: 10, nom: 'BTS CIEL Option A', referentiel_id: 100,
      matieres: [
        { id: 1, nom: 'Culture générale et expression', validee: true,  actif: true },
        { id: 2, nom: 'Mathématiques',                  validee: true,  actif: true },
        { id: 3, nom: 'Anglais',                        validee: true,  actif: false },
        { id: 4, nom: 'Physique-chimie',                validee: false, actif: true },
      ],
    },
    { id: 11, nom: 'BTS SIO', referentiel_id: null, matieres: [] },
  ],
}]

test('les trois états d’une matière', () => {
  assert.equal(etatMatiere({ validee: true,  actif: true  }), AU_PROGRAMME)
  assert.equal(etatMatiere({ validee: true,  actif: false }), DESACTIVEE)
  assert.equal(etatMatiere({ validee: false, actif: true  }), PROPOSEE)
  // Une proposition reste une proposition, quel que soit son `actif` : elle n'est jamais entrée
  // dans le programme, il n'y a donc rien à désactiver.
  assert.equal(etatMatiere({ validee: false, actif: false }), PROPOSEE)
})

test('chaque matière du niveau donne une ligne, dans l’ordre, avec son état', () => {
  const lignes = lignesMatieres(CYCLES[0].niveaux[0])
  assert.deepEqual(lignes.map(m => m.nom), [
    'Culture générale et expression', 'Mathématiques', 'Anglais', 'Physique-chimie',
  ])
  assert.deepEqual(lignes.map(m => m.etat), [AU_PROGRAMME, AU_PROGRAMME, DESACTIVEE, PROPOSEE])
  assert.deepEqual(lignes.map(m => m.id), [1, 2, 3, 4])
})

test('un niveau sans référentiel : aucune ligne, jamais une erreur', () => {
  assert.deepEqual(lignesMatieres(CYCLES[0].niveaux[1]), [])
  assert.deepEqual(lignesMatieres({}), [])
  assert.deepEqual(lignesMatieres(null), [])
  assert.equal(nbAuProgramme(null), 0)
})

test('la ligne du niveau ne compte que ce que le prof voit', () => {
  // 4 matières en base, 2 seulement dans les menus du prof : une est désactivée, l'autre n'est
  // qu'une proposition de la lecture du document.
  assert.equal(nbAuProgramme(CYCLES[0].niveaux[0]), 2)
  assert.equal(nbAuProgramme(CYCLES[0].niveaux[1]), 0)
})

test('l’en-tête compte les matières SANS dédoublonner par nom', () => {
  assert.deepEqual(compterContenu(CYCLES), { cycles: 1, niveaux: 2, matieres: 2 })

  // Deux référentiels nomment chacun leur « Mathématiques » : deux matières distinctes, jamais
  // fusionnées. Le catalogue global d'avant n'en aurait montré qu'une.
  const deux = [{
    id: 1, nom: 'Lycée',
    niveaux: [
      { id: 20, nom: 'Terminale', referentiel_id: 200, matieres: [{ id: 5, nom: 'Mathématiques', validee: true, actif: true }] },
      { id: 21, nom: 'Première',  referentiel_id: 201, matieres: [{ id: 6, nom: 'Mathématiques', validee: true, actif: true }] },
    ],
  }]
  assert.deepEqual(compterContenu(deux), { cycles: 1, niveaux: 2, matieres: 2 })
  assert.deepEqual(compterContenu([]), { cycles: 0, niveaux: 0, matieres: 0 })
})
