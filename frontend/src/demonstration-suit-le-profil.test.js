// L'ENTRÉE « DÉMONSTRATION » SUIT LE PROFIL DU PROF.
//
// LE DÉFAUT (16/08/2026, vu au sortir d'une inscription) : l'entrée interroge le serveur pour
// savoir si une démonstration existe pour le niveau du prof. Cette question n'était posée qu'UNE
// FOIS, au premier affichage du menu — c'est-à-dire quand le profil est encore vide. Le serveur
// répondait « Choisissez d'abord votre niveau dans Mon profil », et cette phrase restait accrochée
// à l'entrée grisée après que le profil fut rempli : l'en-tête affichait « Mathématiques · 4e »
// pendant que le bas du menu réclamait un niveau. Il fallait recharger la page.
//
// LA RÈGLE SERVEUR N'ÉTAIT PAS EN CAUSE : `/demo/pour-moi` lit `travail_niveau_id or niveau_id`,
// la même source que l'en-tête. C'est la question qui n'était jamais reposée.
//
// CE QUE CE TEST ATTRAPE : le retour d'un appel figé au montage, et la rupture du fil qui porte
// le couple depuis App jusqu'à l'entrée.
//
// Lancer : npm test  (ou  node --test src/demonstration-suit-le-profil.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const sidebar = readFileSync(join(SRC, 'components', 'Sidebar.jsx'), 'utf8')
const app = readFileSync(join(SRC, 'App.jsx'), 'utf8')

test('la question est reposée quand le couple change', () => {
  const i = sidebar.indexOf('function LienDemonstration')
  assert.notEqual(i, -1, 'L’entrée « Démonstration » a disparu de la barre du prof.')
  const bloc = sidebar.slice(i, i + 1600)
  assert.match(
    bloc,
    /\}, \[couple\]\)/,
    'L’appel à /demo/pour-moi est redevenu figé au montage : la réponse obtenue avec un profil\n' +
    'vide reste affichée après que le prof a enregistré son niveau.'
  )
})

test('le couple descend depuis App jusqu’à l’entrée', () => {
  assert.match(
    app,
    /<Sidebar[\s\S]{0,200}couple=\{`\$\{user\?\.travail_matiere \|\| user\?\.subject \|\| ''\}\|\$\{user\?\.travail_niveau \|\| user\?\.niveau \|\| ''\}`\}/,
    'App ne passe plus le couple à la barre : rien ne déclenche la nouvelle question.'
  )
  assert.match(
    sidebar,
    /<LienDemonstration collapsed=\{collapsed\} couple=\{couple\} \/>/,
    'La barre ne transmet plus le couple à l’entrée « Démonstration ».'
  )
})
