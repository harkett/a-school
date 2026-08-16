// ENTRER DANS L'ADMINISTRATION, C'EST ARRIVER SUR LE TABLEAU DE BORD.
//
// LE DÉFAUT (16/08/2026) : la connexion ouvrait Supervision → Connexions — le journal des
// connexions, un écran de contrôle qui ne dit rien de l'état de la plateforme. Et `/admin` tout
// court menait à Supervision → Serveur : des courbes de CPU en guise d'accueil.
//
// LA RÉPARATION : les deux mènent au Tableau de bord (`/admin/mise-en-route`). La branche
// « branchement incomplet » de la connexion y menait déjà : les deux cas se rejoignent, et
// l'interrogation qui les départageait a disparu avec eux.
//
// CE QUE CE TEST ATTRAPE : le retour d'un atterrissage sur un écran de Supervision, d'un côté
// comme de l'autre.
//
// Lancer : npm test  (ou  node --test src/on-arrive-sur-le-tableau-de-bord.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const app = readFileSync(join(SRC, 'App.jsx'), 'utf8')
const login = readFileSync(join(SRC, 'pages', 'AdminLogin.jsx'), 'utf8')

test('/admin ouvre le Tableau de bord', () => {
  const bloc = app.slice(app.indexOf('<Route path="/admin" element={<AdminLayout />}>'))
  const redirection = bloc.slice(0, bloc.indexOf('/>', bloc.indexOf('<Route index')))
  assert.match(
    redirection,
    /to="\/admin\/mise-en-route"/,
    'L’adresse `/admin` ne mène plus au Tableau de bord.\nTrouvé : ' + redirection.trim().slice(-60)
  )
})

test('la connexion réussie ouvre le Tableau de bord', () => {
  assert.match(
    login,
    /navigate\('\/admin\/mise-en-route'\)/,
    'La connexion admin n’ouvre plus le Tableau de bord.'
  )
  assert.ok(
    !login.includes("navigate('/admin/logs')"),
    'La connexion repart vers Supervision → Connexions : un journal de contrôle en guise d’accueil.'
  )
})
