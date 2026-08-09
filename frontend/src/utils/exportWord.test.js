// La porte Word : ce que le prof reçoit dans son .docx.
//
// Avant le 07/08/2026, cet export recopiait le texte ligne à ligne : un tableau de barème
// arrivait en barres verticales, un titre avec son `#`. Ces tests tiennent la conversion —
// un tableau markdown doit devenir un VRAI tableau Word, pas un paragraphe.
//
// On n'écrit aucun fichier : `elementsDocx` est pure, elle rend les objets que `docx` assemblera.

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { Paragraph, Table } from 'docx'
import { elementsDocx } from './exportWord.js'

test('un tableau markdown devient un tableau Word, pas du texte', () => {
  const el = elementsDocx('| Critère | Points |\n|---|---|\n| Clarté | 4 |\n| Méthode | 6 |')
  const tables = el.filter(e => e instanceof Table)
  assert.equal(tables.length, 1, 'il faut un objet Table')
})

// Les lignes et les cellules se lisent dans l'arbre que `docx` assemblera (`.root`).
const lignesDe = table => table.root.filter(x => x.constructor.name === 'TableRow')
const cellulesDe = ligne => ligne.root.filter(x => x.constructor.name === 'TableCell')

test('le tableau a sa ligne d en-tête EN PLUS de ses lignes de données', () => {
  const [table] = elementsDocx('| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |').filter(e => e instanceof Table)
  const lignes = lignesDe(table)
  assert.equal(lignes.length, 3, '1 en-tête + 2 lignes')
  assert.equal(cellulesDe(lignes[0]).length, 2)
  assert.equal(cellulesDe(lignes[2]).length, 2)
})

test('un tableau à trois colonnes ne perd pas de cellule', () => {
  const [table] = elementsDocx('| A | B | C |\n|---|---|---|\n| 1 | 2 | 3 |').filter(e => e instanceof Table)
  assert.equal(cellulesDe(lignesDe(table)[1]).length, 3)
})

test('un titre devient un titre Word, pas un paragraphe avec des dièses', () => {
  const el = elementsDocx('## Phase 1 — Découverte')
  assert.equal(el.length, 1)
  assert.ok(el[0] instanceof Paragraph)
  assert.ok(!JSON.stringify(el[0]).includes('##'), 'les dièses ne doivent pas se retrouver dans le texte')
})

test('un bloc de code rend une ligne par ligne de code', () => {
  const el = elementsDocx('```\nun\ndeux\ntrois\n```')
  assert.equal(el.filter(e => e instanceof Paragraph).length, 3)
})

test('une liste à puces rend un paragraphe par élément', () => {
  const el = elementsDocx('- un\n- deux\n- trois')
  assert.equal(el.length, 3)
})

test('deux listes numérotées ne se suivent pas dans la même numérotation', () => {
  // Word continue la numérotation d'une liste à l'autre si elles partagent la même instance :
  // la deuxième liste repartirait de 4 au lieu de 1.
  const compteur = { n: 0 }
  elementsDocx('1. un\n2. deux', compteur)
  elementsDocx('1. autre\n2. liste', compteur)
  assert.equal(compteur.n, 2, 'chaque liste ordonnée doit consommer sa propre instance')
})

test('le texte enrichi ne perd pas son gras', () => {
  // `docx` n'écrit pas « bold » mais la balise Word `w:b` — c'est elle qu'on cherche.
  const el = elementsDocx('**Objectif :** construire un plan d adressage')
  assert.match(JSON.stringify(el[0]), /"w:b"/)
  assert.ok(!JSON.stringify(el[0]).includes('**'), 'les astérisques ne doivent pas rester dans le texte')
})

test('un texte vide ne produit rien et ne plante pas', () => {
  assert.deepEqual(elementsDocx(''), [])
  assert.doesNotThrow(() => elementsDocx(null))
})

test('un document complet garde tous ses blocs', () => {
  const source = [
    '# Devoir surveillé', '', 'Un paragraphe.', '', '## Barème', '',
    '| Critère | Points |', '|---|---|', '| Clarté | 4 |', '',
    '> Le corrigé est en fin de document.', '', '- un', '- deux', '', '---', '',
  ].join('\n')
  const el = elementsDocx(source)
  assert.equal(el.filter(e => e instanceof Table).length, 1)
  assert.ok(el.filter(e => e instanceof Paragraph).length >= 7)
})
