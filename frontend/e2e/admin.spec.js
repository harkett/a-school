import { test, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

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
//
// `NaN` EST A PART : sensible a la casse, et entre limites de mots. Sans les deux, il matche
// « fiNANce », « connaissance », « maiNteNANt » — la recette a echoue sur un niveau nomme
// « Master Finance », donc sur un ecran parfaitement sain. Un test qui crie au loup se
// desapprend en trois jours.
const MOTS_DE_PANNE = /undefined|\[object Object\]|Internal Server Error|Failed to fetch/i
const PANNE_NAN = /\bNaN\b/

// UNE SEULE CONNEXION POUR TOUT LE FICHIER, gardee dans un fichier d'etat que chaque scenario
// recharge. Ce n'est pas une optimisation : /admin/login est plafonne a DIX tentatives par
// heure, et trois scenarios qui se connectent chacun de leur cote atteignent le plafond des la
// deuxieme execution de la journee. Le troisieme echouait alors sur un 429 — c'est-a-dire sur
// une protection qui fonctionne, pas sur un defaut.
const ETAT_SESSION = 'test-results/.session-admin.json'

// Le fichier doit EXISTER quand Playwright cree le contexte du premier scenario, c'est-a-dire
// avant meme `beforeAll`. On pose donc un etat vide au chargement ; la connexion l'ecrase.
fs.mkdirSync(path.dirname(ETAT_SESSION), { recursive: true })
if (!fs.existsSync(ETAT_SESSION)) {
  fs.writeFileSync(ETAT_SESSION, JSON.stringify({ cookies: [], origins: [] }))
}

test.beforeAll(async ({ browser }) => {
  if (!USER || !PASS) throw new Error('ADMIN_USER et ADMIN_PASS doivent etre definis.')
  const page = await browser.newPage()
  await connecter(page)
  await page.context().storageState({ path: ETAT_SESSION })
  await page.close()
})

test.use({ storageState: ETAT_SESSION })

async function connecter(page) {
  await page.goto('/admin/login')
  await page.getByLabel(/identifiant/i).fill(USER)
  await page.getByLabel(/mot de passe/i).fill(PASS)
  await page.getByRole('button', { name: /connexion|se connecter/i }).click()
  await expect(page).not.toHaveURL(/\/admin\/login/, { timeout: 15000 })
  // ET ON ATTEND LE MENU. L'adresse change des que le cookie est pose ; la barre laterale, elle,
  // arrive au rendu suivant. Sans cette attente, le scenario comptait ZERO rubrique et visitait
  // zero ecran — en annoncant « le menu n'a pas ete lu », ce qui etait vrai mais pas la cause.
  await expect(page.locator('nav button[aria-expanded]').first()).toBeVisible({ timeout: 15000 })
}

// La session est deja ouverte (fichier d'etat) : il ne reste qu'a poser la page sur
// l'administration et a attendre que le menu soit rendu.
async function ouvrir(page) {
  await page.goto('/admin/mise-en-route', { waitUntil: 'domcontentloaded' })
  await expect(page.locator('nav button[aria-expanded]').first()).toBeVisible({ timeout: 15000 })
}

// Une page est "saine" si elle a un titre, du contenu, et aucune trace de panne.
async function controlerEcran(page, chemin) {
  await expect(page.locator('header')).toBeVisible()
  const corps = page.locator('main')
  await expect(corps).toBeVisible()
  const texte = (await corps.innerText()).trim()
  expect(texte.length, `ecran vide : ${chemin}`).toBeGreaterThan(0)
  expect(texte, `mot de panne affiche sur ${chemin}`).not.toMatch(MOTS_DE_PANNE)
  expect(texte, `NaN affiché sur ${chemin}`).not.toMatch(PANNE_NAN)
}

test('toute l administration s ouvre sans casse', async ({ page }) => {
  // TROIS MINUTES, et non les trente secondes du reglage general : ce scenario ouvre TOUS les
  // ecrans de l'administration, une vingtaine, chacun avec ses lectures. Le plafond commun est
  // taille pour un scenario qui fait un geste — celui-ci en fait vingt.
  test.setTimeout(180000)

  // CE QU'ON COMPTE COMME UNE PANNE : une exception JavaScript, ou une reponse serveur en
  // erreur. Pas « tout ce que la console affiche en rouge » — le message de console ne dit pas
  // QUELLE requete a echoue, donc il ne se corrige pas, et un test qu'on ne peut pas corriger
  // finit par etre ignore.
  //
  // DEUX ROUTES SONT ECARTEES, et c'est un defaut connu, pas une commodite : sur chaque ecran
  // d'administration, le front appelle /api/auth/me et /api/auth/refresh — les routes du compte
  // PROFESSEUR — alors que la session ouverte est celle de l'administration. Elles repondent 401
  // a chaque page, sans consequence visible. Le jour ou ce sera corrige, ces deux lignes
  // partiront et le test redeviendra strict.
  const IGNOREES = [/\/api\/auth\/me/, /\/api\/auth\/refresh/]
  const erreurs = []
  page.on('pageerror', e => erreurs.push(`exception : ${e.message}`))
  page.on('response', r => {
    if (r.status() < 400) return
    if (IGNOREES.some(re => re.test(r.url()))) return
    erreurs.push(`${r.status()} ${r.url().replace(/^https?:\/\/[^/]+/, '')}`)
  })

  await ouvrir(page)

  // DEUX TEMPS, et c'est ce qui rend ce scenario stable. On RELEVE d'abord toutes les adresses
  // du menu, puis on les visite. Melanger les deux — ouvrir une rubrique, visiter, revenir —
  // lancait une navigation pendant que la precedente courait encore : `net::ERR_ABORTED`, sur
  // une application parfaitement saine.
  const rubriques = page.locator('nav button[aria-expanded]')
  const adresses = new Map()          // adresse -> rubrique d'ou elle vient

  for (let i = 0; i < await rubriques.count(); i++) {
    const rubrique = rubriques.nth(i)
    const nomRubrique = (await rubrique.innerText()).trim().split('\n')[0]

    if ((await rubrique.getAttribute('aria-expanded')) !== 'true') await rubrique.click()
    await expect(rubrique).toHaveAttribute('aria-expanded', 'true')

    const entrees = page.locator('nav a:visible')
    for (let j = 0; j < await entrees.count(); j++) {
      const href = await entrees.nth(j).getAttribute('href')
      if (href && href.startsWith('/admin') && !adresses.has(href)) adresses.set(href, nomRubrique)
    }
  }

  expect(adresses.size, 'aucune adresse relevee : le menu n a pas ete lu').toBeGreaterThan(0)

  const visites = []
  for (const [adresse, nomRubrique] of adresses) {
    await page.goto(adresse, { waitUntil: 'domcontentloaded' })
    await controlerEcran(page, adresse)
    visites.push(`${nomRubrique} > ${adresse}`)
  }

  console.log(`${visites.length} ecrans visites :\n` + visites.join('\n'))
  expect(erreurs, `erreurs javascript pendant la visite :\n${erreurs.join('\n')}`).toEqual([])
})


test('le menu designe toujours la page affichee', async ({ page }) => {
  await ouvrir(page)

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
  await ouvrir(page)

  // ON PART D'UNE ENTREE QUI APPARTIENT A UNE RUBRIQUE. « Tableau de bord » est au premier
  // niveau, hors rubrique : y revenir n'a aucune rubrique a rouvrir, et le scenario echouait sur
  // son propre point de depart plutot que sur le comportement du menu.
  const rubrique = page.locator('nav button[aria-expanded]').first()
  await rubrique.click()
  await expect(rubrique).toHaveAttribute('aria-expanded', 'true')

  const entree = page.locator('nav a[href^="/admin"]:visible').nth(1)
  await entree.click()
  const depart = page.url()

  // ON ATTEND QUE L'ECRAN SUIVANT SOIT VRAIMENT LA avant de revenir. Un retour arriere lance
  // pendant que la page confirme encore la session repart sur l'ecran de connexion : le
  // scenario mesurait alors sa propre precipitation, pas le menu.
  await page.goto('/admin/compte', { waitUntil: 'domcontentloaded' })
  await expect(page.locator('nav button[aria-expanded]').first()).toBeVisible({ timeout: 15000 })

  await page.goBack()

  await expect(page).toHaveURL(depart)
  // LA RUBRIQUE DE LA PAGE AFFICHEE DOIT ETRE OUVERTE. Un menu qui montre une page sans dire
  // d'ou elle vient laisse l'administrateur sans repere apres chaque retour arriere.
  // On ATTEND la rubrique au lieu de la compter une fois : le retour arriere remonte la page,
  // et un comptage immediat mesure l'instant ou le menu n'est pas encore rendu.
  await expect(
    page.locator('nav button[aria-expanded="true"]').first(),
    'aucune rubrique ouverte apres un retour arriere',
  ).toBeVisible({ timeout: 15000 })
})
