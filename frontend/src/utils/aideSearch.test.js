// Tests des fonctions pures de la recherche dans l'Aide (item 41).
// Lance avec :  node --test src/utils/aideSearch.test.js   (depuis frontend/)
import test from 'node:test'
import assert from 'node:assert/strict'
import React from 'react'
import {
  normalize,
  extractText,
  buildSearchIndex,
  searchSections,
  queryTerms,
  highlightSegments,
  makeSnippet,
} from './aideSearch.js'

const h = React.createElement

// ── normalize : accents + majuscules ───────────────────────────────────────
test('normalize : minuscule', () => {
  assert.equal(normalize('Modèle'), 'modele')
  assert.equal(normalize('DICTÉE'), 'dictee')
})

test('normalize : supprime les accents (é è à ç ô ù û)', () => {
  assert.equal(normalize('créér'), 'creer')
  assert.equal(normalize('à côté où ça'), 'a cote ou ca')
})

test('normalize : entrée vide / nulle → chaîne vide', () => {
  assert.equal(normalize(''), '')
  assert.equal(normalize(null), '')
  assert.equal(normalize(undefined), '')
})

// ── extractText : JSX imbriqué ─────────────────────────────────────────────
test('extractText : texte simple', () => {
  assert.equal(extractText(h('p', null, 'bonjour')).trim(), 'bonjour')
})

test('extractText : JSX imbriqué (éléments dans éléments)', () => {
  const node = h('div', null,
    'Pour ',
    h('strong', null, 'dicter'),
    ' le texte, cliquez sur ',
    h('span', null, h('em', null, 'Microphone')),
  )
  const txt = extractText(node)
  assert.ok(txt.includes('dicter'))
  assert.ok(txt.includes('Microphone'))
  assert.ok(txt.includes('Pour'))
})

test('extractText : tableaux et fragments', () => {
  const node = h(React.Fragment, null, ['un', ' ', h('b', null, 'deux'), ' trois'])
  const txt = extractText(node)
  assert.ok(txt.includes('un'))
  assert.ok(txt.includes('deux'))
  assert.ok(txt.includes('trois'))
})

test('extractText : ignore null / booléen / nombre rendu', () => {
  assert.equal(extractText(null), '')
  assert.equal(extractText(true), '')
  assert.equal(extractText(42), '42')
})

// ── searchSections : filtre AND ────────────────────────────────────────────
const sectionsFixture = [
  { id: 'dictee', titre: 'Dictée vocale', nav: 'Dictée', contenu: h('p', null, 'Enregistrez votre voix puis transcription Groq Whisper.') },
  { id: 'iphone', titre: 'Installer sur iPhone', nav: 'iPhone', contenu: h('p', null, 'Ajouter aSchool à l’écran d’accueil iPhone via Safari.') },
  { id: 'compte', titre: 'Créer votre compte', nav: 'Compte', contenu: h('p', null, 'Choisir un mot de passe solide pour votre compte.') },
]

test('searchSections : un mot trouve par le titre', () => {
  const index = buildSearchIndex(sectionsFixture)
  const r = searchSections(index, 'iphone')
  assert.equal(r.length, 1)
  assert.equal(r[0].id, 'iphone')
})

test('searchSections : trouve par le CONTENU, pas seulement le titre', () => {
  const index = buildSearchIndex(sectionsFixture)
  const r = searchSections(index, 'whisper')
  assert.equal(r.length, 1)
  assert.equal(r[0].id, 'dictee')
})

test('searchSections : insensible aux accents et majuscules', () => {
  const index = buildSearchIndex(sectionsFixture)
  assert.equal(searchSections(index, 'DICTEE')[0].id, 'dictee')
  assert.equal(searchSections(index, 'dictée')[0].id, 'dictee')
})

test('searchSections : AND — tous les mots requis', () => {
  const index = buildSearchIndex(sectionsFixture)
  // "mot passe" présents tous deux dans 'compte'
  assert.deepEqual(searchSections(index, 'mot passe').map((s) => s.id), ['compte'])
  // "iphone whisper" : aucun document ne contient les deux
  assert.equal(searchSections(index, 'iphone whisper').length, 0)
})

test('searchSections : requête vide → aucun résultat', () => {
  const index = buildSearchIndex(sectionsFixture)
  assert.equal(searchSections(index, '').length, 0)
  assert.equal(searchSections(index, '   ').length, 0)
})

test('queryTerms : découpe et normalise', () => {
  assert.deepEqual(queryTerms('  Mot  de PASSE '), ['mot', 'de', 'passe'])
  assert.deepEqual(queryTerms(''), [])
})

// ── bonus : highlight & snippet (purs aussi) ───────────────────────────────
test('highlightSegments : marque le terme, insensible aux accents', () => {
  const segs = highlightSegments('La Dictée vocale', ['dictee'])
  const marked = segs.filter((s) => s.match).map((s) => s.text)
  assert.deepEqual(marked, ['Dictée'])
  // le texte recomposé est identique à l'original
  assert.equal(segs.map((s) => s.text).join(''), 'La Dictée vocale')
})

test('highlightSegments : aucun terme → un seul segment non marqué', () => {
  assert.deepEqual(highlightSegments('texte', []), [{ text: 'texte', match: false }])
})

test('makeSnippet : extrait autour du terme avec ellipses', () => {
  const long = 'a'.repeat(100) + ' microphone ' + 'b'.repeat(100)
  const snip = makeSnippet(long, ['microphone'], 20)
  assert.ok(snip.includes('microphone'))
  assert.ok(snip.startsWith('…'))
  assert.ok(snip.endsWith('…'))
})
