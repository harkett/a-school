// Table « Matières de ce référentiel » — ce que l'écran affiche à partir de ce que la base rend.
// Lance avec :  node --test src/utils/matieresReferentiel.test.js   (depuis frontend/)
//
// Vérifie : (1) chaque ligne de la base donne UNE ligne d'écran, dans l'ordre, avec son état ;
// (2) deux matières de même nom coexistent — l'ancienne fusion en masquait une ; (3) les deux
// comptages dérivés qui pilotent la pastille et le bouton « Récupérer ».
import test from 'node:test'
import assert from 'node:assert/strict'
import { lignesMatieres, nbRetenues, aRetenir } from './matieresReferentiel.js'

// Réplique fidèle d'un GET /admin/referentiels/etat pour un référentiel où l'admin a retenu
// deux matières et où la lecture du document en propose deux autres.
const ETAT = {
  matieres: [
    { id: 1, nom: 'Culture générale et expression', validee: true },
    { id: 2, nom: 'Mathématiques', validee: true },
    { id: 3, nom: 'Physique-chimie', validee: false },
    { id: 4, nom: 'Économie-gestion', validee: false },
  ],
}

test('chaque matière de la base donne une ligne, dans l’ordre, avec son état', () => {
  const lignes = lignesMatieres(ETAT)
  assert.equal(lignes.length, 4)
  assert.deepEqual(lignes.map(m => m.nom), [
    'Culture générale et expression', 'Mathématiques', 'Physique-chimie', 'Économie-gestion',
  ])
  assert.deepEqual(lignes.map(m => m.validee), [true, true, false, false])
  // Une matière retenue arrive cochée (et l'écran la verrouille) ; une proposition, décochée.
  assert.deepEqual(lignes.map(m => m.cochee), [true, true, false, false])
  assert.deepEqual(lignes.map(m => m.id), [1, 2, 3, 4])
})

test('deux matières de même nom coexistent — la fusion en masquait une', () => {
  // Cas réel du nouveau modèle : un document peut nommer deux fois le même intitulé à des
  // niveaux de détail différents, et surtout une proposition peut porter le nom d'une matière
  // déjà retenue. L'ancienne fusion dédoublonnait par nom : la seconde disparaissait de l'écran,
  // donc l'admin ne pouvait ni la voir ni la traiter.
  const lignes = lignesMatieres({
    matieres: [
      { id: 7, nom: 'Mathématiques', validee: true },
      { id: 8, nom: 'mathématiques', validee: false },
    ],
  })
  assert.equal(lignes.length, 2)
  assert.deepEqual(lignes.map(m => m.id), [7, 8])
})

test('aucune matière : liste vide, jamais une erreur', () => {
  assert.deepEqual(lignesMatieres({ matieres: [] }), [])
  assert.deepEqual(lignesMatieres({}), [])
  assert.deepEqual(lignesMatieres(null), [])
})

test('le comptage qui allume la pastille ne compte que les matières AU PROGRAMME', () => {
  assert.equal(nbRetenues(lignesMatieres(ETAT)), 2)
  // Un référentiel qui n'a que des propositions n'a rien mis à la disposition des profs.
  assert.equal(nbRetenues(lignesMatieres({ matieres: [{ id: 9, nom: 'X', validee: false }] })), 0)
})

test('« Récupérer » ne s’active que s’il reste vraiment quelque chose à retenir', () => {
  const lignes = lignesMatieres(ETAT)
  assert.equal(aRetenir(lignes), false)            // au repos : rien de coché en plus

  const cochee = lignes.map(m => (m.id === 3 ? { ...m, cochee: true } : m))
  assert.equal(aRetenir(cochee), true)             // une proposition cochée → le bouton s'allume

  // Une ligne ajoutée à la main (pas encore en base) compte aussi.
  assert.equal(aRetenir([...lignes, { id: null, nom: 'Ajoutée', validee: false, cochee: true }]), true)
})
