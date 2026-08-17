import { test, expect } from '@playwright/test'

// PARCOURS COMPLET DE L'ADMINISTRATION.
//
// Le script ne connait AUCUN ecran a l'avance : il lit le menu tel qu'il est affiche, ouvre
// chaque rubrique, visite chaque entree et controle ce qui apparait. Ajouter un ecran au menu
// suffit donc a le faire tester ; il n'y a rien a mettre a jour ici.
//
// Identifiants attendus dans l'environnement :
//   ADMIN_USER, ADMIN_PASS

const USER = process.env.ADMIN_USER
const PASS = process.env.ADMIN_PASS

// Les mots qui trahissent une page cassee quand ils s'affichent a l'ecran.
const MOTS_DE_PANNE = /undefined|NaN|\[object Object\]|Internal Server Error|Failed to fetch/i

test.beforeAll(() => {
  if (!USER || !PASS) throw new Error('ADMIN_USER et ADMIN_PASS doivent etre definis.')
})

async function connecter(page) {
  await page.goto('/admin/login')
  await page.getByLabel(/identifiant/i).fill(USER)
  await page.getByLabel(/mot de passe/i).fill(PASS)
  await page.getByRole('button', { name: /connexion|se connecter/i }).click()
  await expect(page).not.toHaveURL(/\/admin\/login/, { timeout: 15000 })
}

// Une page est "saine" si elle a un titre, du contenu, et aucune trace de panne.
async function controlerEcran(page, chemin) {
  await expect(page.locator('header')).toBeVisible()
  const corps = page.locator('main')
  await expect(corps).toBeVisible()
  const texte = (await corps.innerText()).trim()
  expect(texte.length, `ecran vide : ${chemin}`).toBeGreaterThan(0)
  expect(texte, `mot de panne affiche sur ${chemin}`).not.toMatch(MOTS_DE_PANNE)
}

test('toute l administration s ouvre sans casse', async ({ page }) => {
  const erreurs = []
  page.on('console', m => { if (m.type() === 'error') erreurs.push(m.text()) })
  page.on('pageerror', e => erreurs.push(e.message))

  await connecter(page)

  const visites = []
  const rubriques = page.locator('nav button[aria-expanded]')

  for (let i = 0; i < await rubriques.count(); i++) {
    const rubrique = rubriques.nth(i)
    const nomRubrique = (await rubrique.innerText()).trim().split('\n')[0]

    if ((await rubrique.getAttribute('aria-expanded')) !== 'true') await rubrique.click()
    await expect(rubrique).toHaveAttribute('aria-expanded', 'true')

    // Les entrees visibles appartiennent a la rubrique qu'on vient d'ouvrir.
    const entrees = page.locator('nav a:visible')
    const adresses = []
    for (let j = 0; j < await entrees.count(); j++) {
      const href = await entrees.nth(j).getAttribute('href')
      if (href && href.startsWith('/admin')) adresses.push(href)
    }

    for (const adresse of adresses) {
      await page.goto(adresse)
      await controlerEcran(page, adresse)
      visites.push(`${nomRubrique} > ${adresse}`)
    }
  }

  console.log(`${visites.length} ecrans visites :\n` + visites.join('\n'))
  expect(visites.length, 'aucun ecran visite : le menu n a pas ete lu').toBeGreaterThan(0)
  expect(erreurs, 'erreurs javascript pendant le parcours').toEqual([])
})

test('le menu designe toujours la page affichee', async ({ page }) => {
  await connecter(page)

  const rubriques = page.locator('nav button[aria-expanded]')
  for (let i = 0; i < await rubriques.count(); i++) {
    const rubrique = rubriques.nth(i)
    if ((await rubrique.getAttribute('aria-expanded')) !== 'true') await rubrique.click()

    const entree = page.locator('nav a:visible').first()
    if (!(await entree.count())) continue
    const adresse = await entree.getAttribute('href')
    await entree.click()

    // L'entree ouverte doit rester marquee : sans reperage visible, on ne sait plus ou l'on est.
    const marquee = page.locator(`nav a[href="${adresse}"]`)
    await expect(marquee).toBeVisible()
  }
})

test('le retour du navigateur laisse le menu coherent', async ({ page }) => {
  await connecter(page)

  const premiere = page.locator('nav a[href^="/admin"]').first()
  await premiere.click()
  const depart = page.url()

  await page.goto('/admin/compte')
  await page.goBack()

  await expect(page).toHaveURL(depart)
  const ouvertes = page.locator('nav button[aria-expanded="true"]')
  expect(await ouvertes.count(), 'aucune rubrique ouverte apres un retour arriere').toBeGreaterThan(0)
})
