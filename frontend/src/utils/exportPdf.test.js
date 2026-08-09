// La porte PDF — ses deux calculs, ceux qui n'ont aucune chance d'être justes du premier coup.
//
// Un PDF n'a ni paragraphes ni tableaux : tout est posé à des coordonnées. Deux calculs portent
// la mise en page, et ce sont les seuls qu'on peut observer sans ouvrir un fichier :
//   · `largeurColonnes` — combien de place pour chaque colonne d'un barème ;
//   · `decouperMorceaux` — où passer à la ligne sans perdre le gras en route.
// Le reste (traits, sauts de page) ne se vérifie qu'à l'œil, sur un vrai PDF.
//
// Le « mesureur » est factice : une lettre = 6 points. C'est ce qui rend ces tests lisibles —
// on raisonne en nombre de caractères, pas en points typographiques.

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { largeurColonnes, decouperMorceaux, composerDocument, pourPdf } from './exportPdf.js'

const mesurer = (t, gras) => String(t).length * (gras ? 6.6 : 6)
const somme = a => a.reduce((x, y) => x + y, 0)

test('un tableau étroit occupe toute la largeur disponible', () => {
  const l = largeurColonnes(['A', 'B'], [['1', '2']], 400, mesurer)
  assert.equal(l.length, 2)
  assert.ok(Math.abs(somme(l) - 400) < 0.01, 'les colonnes doivent remplir la largeur')
})

test('un tableau trop large est réduit sans jamais dépasser', () => {
  const long = 'x'.repeat(200)
  const l = largeurColonnes(['Critère', 'Points'], [[long, '4']], 480, mesurer)
  assert.ok(somme(l) <= 480.01, `somme ${somme(l)} > 480`)
})

test('une colonne étroite ne se fait pas écraser par une colonne bavarde', () => {
  // Le cas réel du barème : « Points » tient en 2 caractères, « Critère » en écrit 200.
  // Sans plancher, « Points » tomberait à quelques points de large et son contenu se
  // couperait lettre par lettre.
  const long = 'critère très détaillé '.repeat(12)
  const l = largeurColonnes(['Critère', 'Points'], [[long, '4']], 480, mesurer)
  assert.ok(l[1] >= 20, `la colonne étroite est tombée à ${l[1]}`)
  assert.ok(l[0] > l[1], 'la colonne bavarde doit rester la plus large')
})

test('la largeur demandée tient compte des en-têtes, pas seulement des cellules', () => {
  const l = largeurColonnes(['Un en-tête très long', 'B'], [['1', '2']], 600, mesurer)
  assert.ok(l[0] > l[1], "l'en-tête long doit élargir sa colonne")
})

test('un tableau sans colonne ne plante pas', () => {
  assert.deepEqual(largeurColonnes([], [], 400, mesurer), [])
})

test('une cellule vide est acceptée', () => {
  const l = largeurColonnes(['A', 'B'], [['', '']], 300, mesurer)
  assert.equal(l.length, 2)
  assert.ok(l.every(x => x > 0))
})

// ── Découpe des lignes ──────────────────────────────────────────────────────────────────────

const texteDes = lignes => lignes.map(l => l.map(m => m.texte).join(''))

test('un texte court tient sur une seule ligne', () => {
  const l = decouperMorceaux([{ texte: 'trois mots ici' }], 300, mesurer)
  assert.equal(l.length, 1)
})

test('un texte long passe à la ligne aux espaces', () => {
  const l = decouperMorceaux([{ texte: 'un deux trois quatre cinq six sept huit' }], 60, mesurer)
  assert.ok(l.length > 1)
  assert.ok(l.every(ligne => ligne.length > 0), 'aucune ligne vide')
})

test('le gras survit au passage à la ligne', () => {
  // « **Objectif :** ce que les élèves construisent » — le cas de TOUTES nos séances.
  const l = decouperMorceaux(
    [{ texte: 'Objectif :', gras: true }, { texte: ' ce que les élèves construisent en classe' }],
    80, mesurer)
  const gras = l.flat().filter(m => m.gras).map(m => m.texte).join(' ')
  assert.match(gras, /Objectif/)
  assert.ok(l.length > 1, 'le texte devait passer à la ligne')
})

test('aucune ligne ne commence par un espace', () => {
  const l = decouperMorceaux([{ texte: 'alpha beta gamma delta epsilon zeta' }], 70, mesurer)
  assert.ok(l.every(ligne => !/^\s/.test(ligne[0]?.texte ?? 'x')))
})

test('un retour à la ligne dans le texte est respecté', () => {
  const l = decouperMorceaux([{ texte: 'première\nseconde' }], 300, mesurer)
  assert.deepEqual(texteDes(l), ['première', 'seconde'])
})

test('un mot plus long que la ligne ne fait pas boucler à l infini', () => {
  const l = decouperMorceaux([{ texte: 'anticonstitutionnellement' }], 20, mesurer)
  assert.ok(l.length >= 1)
  assert.match(texteDes(l).join(''), /anticonstitutionnellement/)
})

test('une liste de morceaux vide rend une ligne vide, pas une erreur', () => {
  assert.deepEqual(decouperMorceaux([], 100, mesurer), [[]])
})

// ── Composition d'un vrai document ──────────────────────────────────────────────────────────
// jsPDF fonctionne hors navigateur : on peut donc composer POUR DE VRAI et vérifier que le
// dessin des tableaux, des sauts de page et des blocs de code ne lève rien. Ce que ces tests
// n'attrapent pas, c'est la laideur — seule une lecture du PDF la voit.

test('une activité complète se compose sans lever, sur une page', async () => {
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF({ unit: 'pt', format: 'a4' })
  const source = [
    '# Devoir surveillé — Adressage IP', '',
    '**Durée :** 1 h · **Documents :** interdits', '',
    '## Barème', '',
    '| Critère | Attendu | Points |',
    '|---|---|---|',
    '| Découpage en sous-réseaux | Masque juste et justifié | 6 |',
    '| Plan d adressage | Aucune plage qui se recouvre | 6 |', '',
    '## Corrigé', '',
    '```',
    '192.168.10.0/26  → 62 hôtes',
    '```', '',
    '> Le corrigé n est distribué qu après la remise des copies.',
  ].join('\n')
  const pages = composerDocument(doc, source)
  assert.equal(pages, 1)
})

test('un long tableau passe à la page suivante sans planter', async () => {
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF({ unit: 'pt', format: 'a4' })
  const lignes = Array.from({ length: 90 }, (_, i) => `| Critère ${i + 1} | Ce qui est attendu de l élève, décrit en clair | ${i % 6} |`)
  const source = ['| Critère | Attendu | Points |', '|---|---|---|', ...lignes].join('\n')
  const pages = composerDocument(doc, source)
  assert.ok(pages >= 2, `un tableau de 90 lignes tient sur ${pages} page(s)`)
})

test('un texte long enchaîne les pages', async () => {
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF({ unit: 'pt', format: 'a4' })
  const paragraphe = 'Les étudiants configurent le commutateur, vérifient la table et documentent. '.repeat(12)
  const pages = composerDocument(doc, Array.from({ length: 12 }, () => paragraphe).join('\n\n'))
  assert.ok(pages >= 2)
})

// ── Ce que la police du PDF sait écrire ─────────────────────────────────────────────────────

test('les flèches et les signes mathématiques sont transcrits, pas déformés', () => {
  assert.equal(pourPdf('Oui ! → je lève 128'), 'Oui ! -> je lève 128')
  assert.equal(pourPdf('−67 dBm'), '-67 dBm')
  assert.equal(pourPdf('signal ≥ -70 dBm'), 'signal >= -70 dBm')
})

test('les accents français passent intacts', () => {
  const phrase = 'Élève, château, où, ça, €, « guillemets », l’apostrophe, œuf'
  assert.equal(pourPdf(phrase), phrase)
})

test('un caractère non représentable devient un point d interrogation, pas un caractère faux', () => {
  assert.equal(pourPdf('émoji \u{1F600} ici'), 'émoji ? ici')
})

test('pourPdf accepte le vide', () => {
  assert.equal(pourPdf(''), '')
  assert.equal(pourPdf(null), '')
})
