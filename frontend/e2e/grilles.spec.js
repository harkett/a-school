import { test, expect } from '@playwright/test'

// RECETTE DES GRILLES — LA BARRIÈRE AVANT LA LIVRAISON.
//
// Ce fichier ne vérifie pas du code : il JOUE la fonctionnalité dans un vrai navigateur, comme
// un professeur le ferait, et il échoue si une seule étape ne se passe pas. Tant qu'il est
// rouge, la migration de livraison ne part pas — donc aucune ligne n'arrive dans l'encart de
// l'administration, et aucune annonce ne parvient aux professeurs. Le rouge ne concerne que le
// développement : c'est lui qui corrige, l'administration n'a rien à décider là-dessus.
//
// POURQUOI CE N'EST PAS UN TEST DE PLUS. Les tests serveur prouvent que les routes répondent ;
// ils ne disent pas qu'un bouton existe, qu'un champ se remplit, ni qu'une modification survit
// à un rechargement. C'est exactement là que se logent les fonctionnalités « finies » qu'on
// découvre cassées trois semaines plus tard.
//
// CE QU'IL EXIGE POUR TOURNER :
//   PROF_USER / PROF_PASS   — un compte professeur réel, avec un niveau (donc un référentiel :
//                             sans lui, aucune génération n'est possible)
//   l'application en ligne  — `npm run dev`, ou lancée par Scripts\tester-admin.ps1
//
// LES LIBELLÉS SONT RASSEMBLÉS DANS `MOTS`, en un seul endroit et volontairement en tête : les
// écrans des grilles sont écrits par une autre session, et le jour où un bouton s'appellera
// « Créer une grille » au lieu de « Nouvelle grille », c'est UNE ligne à corriger ici, pas dix
// dans le fichier. Chaque libellé est une expression régulière insensible à la casse — un
// accent ou une majuscule qui change ne doit pas faire échouer une recette.

const USER = process.env.PROF_USER
const PASS = process.env.PROF_PASS

const MOTS = {
  menuEvals:      /mes évals/i,
  menuGrilles:    /grilles/i,
  nouvelle:       /nouvelle grille|créer une grille|nouvelle/i,
  demande:        /décrivez|votre demande|ce que vous voulez évaluer|sujet/i,
  generer:        /générer/i,
  dupliquer:      /dupliquer/i,
  supprimer:      /supprimer/i,
  confirmer:      /^(supprimer|confirmer|oui)$/i,
  titre:          /titre/i,
}

// La demande envoyée au modèle. Volontairement banale et courte : la recette prouve que la
// chaîne fonctionne, pas que le modèle est inspiré — et une demande courte coûte moins cher.
const DEMANDE = "Exposé oral de cinq minutes présentant un travail réalisé en classe."

// Les mots qui trahissent un écran cassé quand ils s'affichent tels quels au professeur.
const MOTS_DE_PANNE = /undefined|NaN|\[object Object\]|Internal Server Error|Failed to fetch/i

test.describe.configure({ mode: 'serial' })   // le parcours est une histoire : elle a un ordre

test.beforeAll(() => {
  if (!USER || !PASS) throw new Error('PROF_USER et PROF_PASS doivent être définis.')
})

// La génération passe par un modèle : elle peut prendre plusieurs dizaines de secondes. Ce
// délai n'est pas de la tolérance à la lenteur, c'est la durée réelle d'un appel.
const ATTENTE_GENERATION = 120_000

async function connecter(page) {
  await page.goto('/login')
  await page.getByLabel(/adresse e-mail/i).fill(USER)
  await page.getByLabel(/mot de passe/i).fill(PASS)
  await page.getByRole('button', { name: /se connecter/i }).click()
  await expect(page).not.toHaveURL(/\/login/, { timeout: 20_000 })
}

async function ouvrirLesGrilles(page) {
  // L'entrée doit être DÉGRISÉE : tant qu'elle porte l'attribut `disabled`, la fonctionnalité
  // n'est pas livrée — et une recette qui « passe » sur un menu grisé ne prouve rien.
  const evals = page.getByRole('button', { name: MOTS.menuEvals })
  if (await evals.count()) await evals.first().click()

  const entree = page.getByRole('button', { name: MOTS.menuGrilles }).first()
  await expect(entree, 'l’entrée « Grilles » du menu est absente').toHaveCount(1)
  await expect(entree, 'l’entrée « Grilles » est encore grisée').toBeEnabled()
  await entree.click()
}

// Une page saine : du contenu, et aucun mot de panne affiché au professeur.
async function ecranSain(page, etape) {
  const corps = page.locator('main, #root')
  const texte = (await corps.first().innerText()).trim()
  expect(texte.length, `écran vide à l’étape : ${etape}`).toBeGreaterThan(0)
  expect(texte, `mot de panne affiché à l’étape : ${etape}`).not.toMatch(MOTS_DE_PANNE)
}

test('une grille se crée, se génère, se retouche, se retrouve, se duplique et se supprime', async ({ page }) => {
  const erreurs = []
  page.on('console', m => { if (m.type() === 'error') erreurs.push(m.text()) })
  page.on('pageerror', e => erreurs.push(e.message))

  // ── 1. Entrer ────────────────────────────────────────────────────────────────────────
  await connecter(page)
  await ouvrirLesGrilles(page)
  await ecranSain(page, 'ouverture des grilles')

  // ── 2. Créer et faire écrire la grille ───────────────────────────────────────────────
  const nouvelle = page.getByRole('button', { name: MOTS.nouvelle }).first()
  if (await nouvelle.count()) await nouvelle.click()

  const demande = page.getByRole('textbox').first()
  await expect(demande, 'aucun champ pour décrire la grille').toBeVisible()
  await demande.fill(DEMANDE)

  await page.getByRole('button', { name: MOTS.generer }).first().click()

  // ── 3. Contrôler CE QUI EST ÉCRIT, pas seulement que quelque chose est apparu ─────────
  // Une grille est un tableau : des critères en lignes, des niveaux de maîtrise en colonnes,
  // et un descripteur dans chaque croisement. Un tableau qui s'affiche avec des cases vides
  // est un écran qui marche et une fonctionnalité qui ne sert à rien.
  const tableau = page.locator('table').first()
  await expect(tableau, 'aucun tableau après la génération').toBeVisible({ timeout: ATTENTE_GENERATION })

  const colonnes = tableau.locator('thead th')
  const lignes   = tableau.locator('tbody tr')
  await expect(lignes, 'moins de quatre critères').not.toHaveCount(0)
  expect(await lignes.count(), 'la grille doit porter de 4 à 6 critères').toBeGreaterThanOrEqual(4)
  expect(await lignes.count(), 'la grille doit porter de 4 à 6 critères').toBeLessThanOrEqual(6)
  expect(await colonnes.count(), 'aucun niveau de maîtrise en colonne').toBeGreaterThan(1)

  // Aucune case du tableau ne doit être vide : le descripteur est ce que le professeur lit et
  // ce que l'élève doit comprendre.
  const cases = tableau.locator('tbody td')
  for (let i = 0; i < await cases.count(); i++) {
    const contenu = (await cases.nth(i).innerText()).trim()
    expect(contenu.length, `case vide dans la grille (case n° ${i + 1})`).toBeGreaterThan(0)
  }

  // Le titre de la grille, pour la retrouver plus loin sans dépendre d'un identifiant.
  const titre = (await page.locator('h1, h2, h3').first().innerText()).trim()
  expect(titre.length, 'la grille générée n’a pas de titre').toBeGreaterThan(0)

  // ── 4. Retoucher, et vérifier que ça TIENT ───────────────────────────────────────────
  // Le vrai test de l'enregistrement n'est pas qu'un message de confirmation s'affiche : c'est
  // que la modification survive à un rechargement complet de la page.
  const premiereCase = cases.first()
  const marque = 'Retouche de recette ' + titre.slice(0, 6)
  await premiereCase.click()

  const champ = page.locator('textarea:visible, input[type="text"]:visible').first()
  await expect(champ, 'une case ne s’ouvre pas à la retouche').toBeVisible()
  await champ.fill(marque)
  await champ.blur()

  await page.reload()
  await expect(page.getByText(marque), 'la retouche n’a pas été enregistrée').toBeVisible({ timeout: 20_000 })
  await ecranSain(page, 'après retouche')

  // ── 5. La retrouver dans la liste ────────────────────────────────────────────────────
  await ouvrirLesGrilles(page)
  const dansLaListe = page.getByText(titre, { exact: false })
  await expect(dansLaListe.first(), 'la grille n’apparaît pas dans la liste').toBeVisible({ timeout: 20_000 })

  // ── 6. Dupliquer — la copie doit porter le même contenu, pas seulement le même nom ────
  const avant = await page.getByText(titre, { exact: false }).count()
  await page.getByRole('button', { name: MOTS.dupliquer }).first().click()
  await expect(async () => {
    expect(await page.getByText(titre, { exact: false }).count()).toBeGreaterThan(avant)
  }).toPass({ timeout: 20_000 })

  await page.getByText(titre, { exact: false }).last().click()
  await expect(page.getByText(marque), 'la copie ne porte pas le contenu de l’originale').toBeVisible({ timeout: 20_000 })

  // ── 7. Supprimer — et vérifier que ça disparaît VRAIMENT ─────────────────────────────
  await page.getByRole('button', { name: MOTS.supprimer }).first().click()
  const confirmation = page.getByRole('button', { name: MOTS.confirmer })
  if (await confirmation.count()) await confirmation.first().click()

  await ouvrirLesGrilles(page)
  await expect(async () => {
    expect(await page.getByText(titre, { exact: false }).count()).toBeLessThan(avant + 1)
  }).toPass({ timeout: 20_000 })

  // ── 8. Rien n'a cassé en chemin ──────────────────────────────────────────────────────
  await ecranSain(page, 'fin du parcours')
  expect(erreurs, 'erreurs JavaScript pendant le parcours').toEqual([])
})
