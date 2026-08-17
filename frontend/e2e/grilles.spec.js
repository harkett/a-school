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
//   l'application en ligne  — `npm run dev`, ou lancée par Scripts\recette.ps1
//
// UN APPEL PAYANT. Le scénario complet fait une VRAIE génération : il coûte un appel au
// fournisseur d'IA. C'est le prix d'une recette qui prouve quelque chose — un modèle moqué ne
// dirait pas si le tableau s'affiche. Le second scénario, lui, ne coûte rien : il joue la voie
// sans IA (grille vide, remplie à la main) et couvre tout le reste du parcours.
//
// LES LIBELLÉS SONT RASSEMBLÉS DANS `MOTS`, en tête et en un seul endroit : le jour où un
// bouton change de nom, c'est UNE ligne à corriger, pas dix dans le fichier. Chaque libellé est
// une expression régulière insensible à la casse — un accent ou une majuscule qui change ne
// doit pas faire échouer une recette.

const USER = process.env.PROF_USER
const PASS = process.env.PROF_PASS

const MOTS = {
  menuEvals:    /mes évals/i,
  menuGrilles:  /^grilles$/i,
  generer:      /générer la grille/i,
  creerVide:    /créer une grille vide/i,
  dupliquer:    /dupliquer/i,
  imprimer:     /imprimer/i,
  supprimer:    /supprimer/i,
  ajouterCritere: /ajouter un critère/i,
  titreGrille:  /titre de la grille/i,
  demande:      /exposé|décrivez|évaluer/i,
}

// La demande envoyée au modèle. Volontairement banale et courte : la recette prouve que la
// chaîne fonctionne, pas que le modèle est inspiré — et une demande courte coûte moins cher.
const DEMANDE = "Exposé oral de cinq minutes présentant un travail réalisé en classe."

// Les mots qui trahissent un écran cassé quand ils s'affichent tels quels au professeur.
const MOTS_DE_PANNE = /undefined|NaN|\[object Object\]|Internal Server Error|Failed to fetch/i

// La génération passe par un modèle : plusieurs dizaines de secondes. Ce délai n'est pas de la
// tolérance à la lenteur, c'est la durée réelle d'un appel.
const ATTENTE_GENERATION = 120_000

test.describe.configure({ mode: 'serial' })   // le parcours est une histoire : elle a un ordre

test.beforeAll(() => {
  if (!USER || !PASS) throw new Error('PROF_USER et PROF_PASS doivent être définis.')
})

async function connecter(page) {
  await page.goto('/login')
  await page.getByLabel(/adresse e-mail/i).fill(USER)
  await page.getByLabel(/mot de passe/i).fill(PASS)
  await page.getByRole('button', { name: /se connecter/i }).click()
  await expect(page).not.toHaveURL(/\/login/, { timeout: 20_000 })
}

// Le menu mène à la LISTE des grilles, pas à un éditeur : c'est de là que tout part.
async function ouvrirLaListe(page) {
  const evals = page.getByRole('button', { name: MOTS.menuEvals }).first()
  if (await evals.count()) await evals.click()

  const entree = page.getByRole('button', { name: MOTS.menuGrilles }).first()
  await expect(entree, 'l’entrée « Grilles » du menu est absente').toHaveCount(1)
  // Dégrisée : tant qu'elle porte `disabled`, la fonctionnalité n'est pas livrée — et une
  // recette qui « passe » sur un menu grisé ne prouve rien.
  await expect(entree, 'l’entrée « Grilles » est encore grisée').toBeEnabled()
  await entree.click()
  await expect(page.getByRole('button', { name: MOTS.generer }),
               'la liste des grilles ne s’ouvre pas').toBeVisible({ timeout: 20_000 })
}

// Une page saine : du contenu, et aucun mot de panne affiché au professeur.
async function ecranSain(page, etape) {
  const texte = (await page.locator('#root').innerText()).trim()
  expect(texte.length, `écran vide à l’étape : ${etape}`).toBeGreaterThan(0)
  expect(texte, `mot de panne affiché à l’étape : ${etape}`).not.toMatch(MOTS_DE_PANNE)
}

// LE TABLEAU, CONTRÔLÉ POUR CE QU'IL CONTIENT. Les cases sont des zones de saisie : leur
// contenu est une VALEUR, pas du texte affiché — le lire avec innerText renverrait toujours du
// vide et la recette passerait sur une grille creuse.
async function lireTableau(page) {
  const tableau = page.locator('table').first()
  await expect(tableau, 'aucun tableau à l’écran').toBeVisible({ timeout: ATTENTE_GENERATION })

  const lignes = tableau.locator('tbody tr')
  const cases  = tableau.locator('tbody td textarea')
  const valeurs = []
  for (let i = 0; i < await cases.count(); i++) valeurs.push((await cases.nth(i).inputValue()).trim())

  return { tableau, nbCriteres: await lignes.count(), valeurs, cases }
}

test('la grille se génère, se retouche, se retrouve, se duplique et se supprime', async ({ page }) => {
  const erreurs = []
  page.on('console', m => { if (m.type() === 'error') erreurs.push(m.text()) })
  page.on('pageerror', e => erreurs.push(e.message))

  // ── 1. Entrer et demander la grille ──────────────────────────────────────────────────
  await connecter(page)
  await ouvrirLaListe(page)
  await ecranSain(page, 'ouverture de la liste')

  await page.getByRole('textbox').first().fill(DEMANDE)
  await page.getByRole('button', { name: MOTS.generer }).click()

  // ── 2. Contrôler CE QUI EST ÉCRIT, pas seulement que quelque chose est apparu ─────────
  // Une grille est un tableau : des critères en lignes, des niveaux de maîtrise en colonnes, et
  // un descripteur dans chaque croisement. Un tableau qui s'affiche avec des cases vides est un
  // écran qui marche et une fonctionnalité qui ne sert à rien.
  const { nbCriteres, valeurs, cases } = await lireTableau(page)

  expect(nbCriteres, 'la grille doit porter de 4 à 6 critères').toBeGreaterThanOrEqual(4)
  expect(nbCriteres, 'la grille doit porter de 4 à 6 critères').toBeLessThanOrEqual(6)
  expect(valeurs.length, 'aucune case dans le tableau').toBeGreaterThan(0)
  const vides = valeurs.filter(v => v.length === 0).length
  expect(vides, `${vides} case(s) vide(s) dans la grille générée`).toBe(0)

  // Le titre sert à retrouver la grille dans la liste : c'est un champ, pas un titre de page.
  const champTitre = page.getByPlaceholder(MOTS.titreGrille)
  const titre = (await champTitre.inputValue()).trim()
  expect(titre.length, 'la grille générée n’a pas de titre').toBeGreaterThan(0)

  // ── 3. Retoucher, et vérifier que ça TIENT ───────────────────────────────────────────
  // Le vrai test de l'enregistrement n'est pas qu'un message s'affiche : c'est que la
  // modification survive à un rechargement complet. Il n'y a pas de bouton « Enregistrer » —
  // le champ part au blur, l'écran relit la grille ensuite.
  const marque = 'Retouche de recette ' + Math.abs(titre.length * 7919)
  await cases.first().fill(marque)
  await cases.first().blur()

  await page.waitForTimeout(1200)   // le temps de l'écriture et de la relecture
  await page.reload()
  await expect(page.getByPlaceholder(MOTS.titreGrille),
               'l’éditeur ne se rouvre pas après rechargement').toBeVisible({ timeout: 20_000 })

  const apres = await lireTableau(page)
  expect(apres.valeurs, 'la retouche n’a pas été enregistrée').toContain(marque)
  await ecranSain(page, 'après retouche')

  // ── 4. La retrouver dans la liste ────────────────────────────────────────────────────
  await ouvrirLaListe(page)
  const dansLaListe = page.getByRole('button', { name: new RegExp(`ouvrir .*${escape(titre)}`, 'i') })
  await expect(dansLaListe.first(), 'la grille n’apparaît pas dans la liste').toBeVisible({ timeout: 20_000 })
  const avant = await dansLaListe.count()

  // ── 5. Dupliquer — la copie doit porter le CONTENU, pas seulement le nom ──────────────
  await dansLaListe.first().click()
  await page.getByRole('button', { name: MOTS.dupliquer }).click()

  // On atterrit sur la copie : elle doit déjà contenir la retouche.
  const copie = await lireTableau(page)
  expect(copie.valeurs, 'la copie ne porte pas le contenu de l’originale').toContain(marque)

  await ouvrirLaListe(page)
  await expect(async () => {
    expect(await page.getByRole('button', { name: new RegExp(`ouvrir .*${escape(titre)}`, 'i') }).count())
      .toBeGreaterThan(avant)
  }).toPass({ timeout: 20_000 })

  // ── 6. Supprimer — et vérifier que ça disparaît VRAIMENT ─────────────────────────────
  await page.getByRole('button', { name: new RegExp(`ouvrir .*${escape(titre)}`, 'i') }).first().click()
  await page.getByRole('button', { name: MOTS.supprimer }).click()
  // La maison a un canal unique de confirmation : le bouton de la modale porte le mot du geste.
  await page.getByRole('button', { name: /^supprimer$/i }).last().click()

  await ouvrirLaListe(page)
  await expect(async () => {
    expect(await page.getByRole('button', { name: new RegExp(`ouvrir .*${escape(titre)}`, 'i') }).count())
      .toBeLessThanOrEqual(avant)
  }).toPass({ timeout: 20_000 })

  // ── 7. Rien n'a cassé en chemin ──────────────────────────────────────────────────────
  await ecranSain(page, 'fin du parcours')
  expect(erreurs, 'erreurs JavaScript pendant le parcours').toEqual([])
})

// LA VOIE SANS IA, et elle ne coûte rien. Une grille vide se crée, se remplit à la main, et se
// supprime : si la génération est indisponible un jour, cette moitié-là doit continuer de
// fonctionner — c'est la promesse de « Créer une grille vide ».
test('une grille vide se crée, se remplit à la main et se supprime', async ({ page }) => {
  const erreurs = []
  page.on('pageerror', e => erreurs.push(e.message))

  await connecter(page)
  await ouvrirLaListe(page)

  const titre = 'Recette sans IA ' + (await page.title()).length + Date.now().toString().slice(-5)
  await page.getByPlaceholder(MOTS.titreGrille).first().fill(titre)
  await page.getByRole('button', { name: MOTS.creerVide }).click()

  await expect(page.getByRole('button', { name: MOTS.ajouterCritere }),
               'l’éditeur ne s’ouvre pas sur une grille vide').toBeVisible({ timeout: 20_000 })

  await page.getByRole('button', { name: MOTS.ajouterCritere }).click()
  const { cases } = await lireTableau(page)
  expect(await cases.count(), 'un critère ajouté ne crée aucune case').toBeGreaterThan(0)

  const texte = 'Descripteur écrit à la main'
  await cases.first().fill(texte)
  await cases.first().blur()
  await page.waitForTimeout(1200)
  await page.reload()

  const apres = await lireTableau(page)
  expect(apres.valeurs, 'la saisie manuelle n’a pas été enregistrée').toContain(texte)

  await page.getByRole('button', { name: MOTS.supprimer }).click()
  await page.getByRole('button', { name: /^supprimer$/i }).last().click()

  await ouvrirLaListe(page)
  await expect(page.getByText(titre, { exact: false }),
               'la grille supprimée est encore dans la liste').toHaveCount(0, { timeout: 20_000 })

  expect(erreurs, 'erreurs JavaScript pendant le parcours').toEqual([])
})

// Le titre généré peut contenir des caractères que les expressions régulières interprètent.
function escape(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') }
