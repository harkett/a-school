import { test, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

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
// UN SEUL APPEL PAYANT, ET C'EST LE PREMIER SCÉNARIO. Il fait une VRAIE génération : c'est le
// prix d'une recette qui prouve quelque chose — un modèle moqué ne dirait pas si le tableau
// s'affiche. Le second, lui, ne coûte RIEN : il travaille sur une grille DÉJÀ EXISTANTE, celle
// que le premier vient de laisser. Il n'y a pas d'autre façon de créer une grille — la voie
// « grille vide » a existé un temps et a été retirée le 17/08/2026.
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
  nouvelle:     /nouvelle grille/i,
  ouvrir:       /^ouvrir$/i,
  mesGrilles:   /mes grilles/i,
  dupliquer:    /dupliquer/i,
  imprimer:     /imprimer/i,
  supprimer:    /supprimer/i,
  ajouterCritere: /ajouter un critère/i,
  titreGrille:  /titre de la grille/i,
  demande:      /exposé|décrivez|évaluer/i,
  proposerIdee: /propose-moi une idée/i,
  theme:        /les réseaux/i,
  annuler:      /^annuler$/i,
}

// La demande envoyée au modèle. Volontairement banale et courte : la recette prouve que la
// chaîne fonctionne, pas que le modèle est inspiré — et une demande courte coûte moins cher.
const DEMANDE = "Exposé oral de cinq minutes présentant un travail réalisé en classe."

// Les mots qui trahissent un écran cassé quand ils s'affichent tels quels au professeur.
// Les mots qui trahissent une page cassee quand ils s'affichent a l'ecran.
//
// `NaN` EST A PART : sensible a la casse, et entre limites de mots. Sans les deux, il matche
// « fiNANce », « connaissance », « maiNteNANt » — la recette a echoue sur un niveau nomme
// « Master Finance », donc sur un ecran parfaitement sain. Un test qui crie au loup se
// desapprend en trois jours.
const MOTS_DE_PANNE = /undefined|\[object Object\]|Internal Server Error|Failed to fetch/i
const PANNE_NAN = /\bNaN\b/

// La génération passe par un modèle : plusieurs dizaines de secondes. Ce délai n'est pas de la
// tolérance à la lenteur, c'est la durée réelle d'un appel.
const ATTENTE_GENERATION = 120_000

test.describe.configure({ mode: 'serial' })   // le parcours est une histoire : elle a un ordre

// UNE SEULE CONNEXION POUR LES DEUX SCENARIOS, gardee dans un fichier d'etat. La connexion du
// professeur est plafonnee, comme celle de l'administration : deux scenarios qui se connectent
// chacun de leur cote atteignent la limite des la deuxieme execution de la journee, et le
// second echoue sur une protection qui fonctionne — pas sur un defaut des grilles.
const ETAT_SESSION = 'test-results/.session-prof.json'

fs.mkdirSync(path.dirname(ETAT_SESSION), { recursive: true })
if (!fs.existsSync(ETAT_SESSION)) {
  fs.writeFileSync(ETAT_SESSION, JSON.stringify({ cookies: [], origins: [] }))
}

test.beforeAll(async ({ browser }) => {
  if (!USER || !PASS) throw new Error('PROF_USER et PROF_PASS doivent être définis.')
  const page = await browser.newPage()
  await connecter(page)
  await page.context().storageState({ path: ETAT_SESSION })
  await page.close()
})

test.use({ storageState: ETAT_SESSION })

async function connecter(page) {
  await page.goto('/login')
  await page.getByLabel(/adresse e-mail/i).fill(USER)
  await page.getByLabel(/mot de passe/i).fill(PASS)
  await page.getByRole('button', { name: /se connecter/i }).click()
  await expect(page).not.toHaveURL(/\/login/, { timeout: 20_000 })
}

// Le menu mène à la LISTE des grilles, pas à un éditeur ni à un formulaire : c'est de là que
// tout part. La liste se reconnaît à son bouton « Nouvelle grille » — la demande, elle, vit sur
// un ÉCRAN À PART (cadre maison : « Nouvelle … » ouvre un écran, il ne déplie pas un panneau).
async function ouvrirLaListe(page) {
  // ON NE DEPLIE QUE SI C'EST REPLIE. « Mes évals » est un accordéon : cliquer dessus alors
  // qu'il est déjà ouvert le REFERME, et l'entrée « Grilles » disparaît — le scénario annonçait
  // alors une entrée absente sur un menu parfaitement sain.
  const entreeVisible = page.getByRole('link', { name: MOTS.menuGrilles }).first()
  if (!(await entreeVisible.isVisible().catch(() => false))) {
    const evals = page.getByRole('button', { name: MOTS.menuEvals }).first()
    if (await evals.count()) await evals.click()
  }

  // LES SOUS-ENTREES SONT DES LIENS, pas des boutons (Sidebar.jsx : `subNavItem` rend un <a>).
  // Une entree PAS ENCORE LIVREE, elle, est un <span> grise — c'est ce qui permet a la ligne
  // suivante de distinguer « absente » de « annoncee mais inactive ».
  const entree = page.getByRole('link', { name: MOTS.menuGrilles }).first()
  await expect(entree, 'l’entrée « Grilles » du menu est absente').toHaveCount(1)
  // Dégrisée : tant qu'elle porte `disabled`, la fonctionnalité n'est pas livrée — et une
  // recette qui « passe » sur un menu grisé ne prouve rien.
  await expect(entree, 'l’entrée « Grilles » est encore grisée').toBeEnabled()
  await entree.click()
  await expect(page.getByRole('button', { name: MOTS.nouvelle }),
               'la liste des grilles ne s’ouvre pas').toBeVisible({ timeout: 20_000 })
}

// L'écran de création. LA LISTE DOIT AVOIR DISPARU : c'est tout l'objet de la correction du
// 17/08/2026 — le formulaire était déplié en tête de liste, ce qui ne se fait nulle part.
async function ouvrirLaCreation(page) {
  await page.getByRole('button', { name: MOTS.nouvelle }).click()
  await expect(page.getByRole('button', { name: MOTS.generer }),
               'l’écran de création ne s’ouvre pas').toBeVisible({ timeout: 20_000 })
  await expect(page.getByRole('button', { name: MOTS.nouvelle }),
               'la liste est encore visible derrière l’écran de création').toHaveCount(0)
}

// Ouvrir une grille de la liste dans l'ÉDITEUR : on la choisit, puis « Ouvrir » — le geste de
// « Reprendre » sur une activité. Le détail de droite LIT, il ne modifie pas.
async function ouvrirDansEditeur(page, ligne) {
  await ligne.click()
  await page.getByRole('button', { name: MOTS.ouvrir }).click()
  await expect(page.getByRole('button', { name: MOTS.ajouterCritere }),
               'l’éditeur ne s’ouvre pas').toBeVisible({ timeout: 20_000 })
}

// Une page saine : du contenu, et aucun mot de panne affiché au professeur.
async function ecranSain(page, etape) {
  const texte = (await page.locator('#root').innerText()).trim()
  expect(texte.length, `écran vide à l’étape : ${etape}`).toBeGreaterThan(0)
  expect(texte, `mot de panne affiché à l’étape : ${etape}`).not.toMatch(MOTS_DE_PANNE)
  expect(texte, `NaN affiché à l’étape : ${etape}`).not.toMatch(PANNE_NAN)
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
  // CINQ MINUTES, et non les trente secondes du reglage general : ce scenario enchaine une
  // generation par le modele, une dizaine de retouches et deux allers-retours vers la liste.
  // Le plafond commun est taille pour un scenario qui fait un geste.
  test.setTimeout(300000)

  // CE QU'ON COMPTE COMME UNE PANNE : une exception JavaScript, ou une reponse serveur en
  // erreur AVEC son adresse. Le message de console ne dit pas quelle requete a echoue, donc il
  // ne se corrige pas — et un test qu'on ne peut pas corriger finit par etre ignore.
  //
  // DEUX ROUTES SONT ECARTEES : /api/auth/me et /api/auth/refresh. Sur l'ecran de connexion, le
  // front demande qui est connecte AVANT de savoir s'il l'est — la reponse est 401, et c'est la
  // reponse juste. Les compter ferait echouer le scenario sur son premier ecran.
  const IGNOREES = [/\/api\/auth\/me/, /\/api\/auth\/refresh/]
  const erreurs = []
  page.on('pageerror', e => erreurs.push(`exception : ${e.message}`))
  page.on('response', r => {
    if (r.status() < 400) return
    if (IGNOREES.some(re => re.test(r.url()))) return
    erreurs.push(`${r.status()} ${r.url().replace(/^https?:\/\/[^/]+/, '')}`)
  })

  // ── 1. Entrer et demander la grille ──────────────────────────────────────────────────
  // ON ATTEND LE MENU. La session est deja ouverte (fichier d'etat), mais le menu arrive au
  // rendu suivant : chercher « Grilles » tout de suite le declare absent d'un menu qui n'est
  // simplement pas encore la.
  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('button', { name: MOTS.menuEvals }).first(),
               'le menu du professeur ne s’affiche pas').toBeVisible({ timeout: 20_000 })
  await ouvrirLaListe(page)
  await ecranSain(page, 'ouverture de la liste')

  await ouvrirLaCreation(page)

  // « PROPOSE-MOI UNE IDÉE » — ouvert, éprouvé, refermé, SANS APPELER LE MODÈLE. Ce bouton fait
  // un appel payant : la recette vérifie donc ce qui ne coûte rien et qui casse le plus souvent
  // — la fenêtre s'ouvre, elle refuse de partir sans thème, et Annuler ne laisse aucune trace
  // dans la zone. La chaîne complète, elle, est prouvée côté serveur (tests/test_grilles.py).
  await page.getByRole('button', { name: MOTS.proposerIdee }).click()
  const champTheme = page.getByPlaceholder(MOTS.theme)
  await expect(champTheme, 'la fenêtre « Propose-moi une idée » ne s’ouvre pas').toBeVisible()
  const boutonIdee = page.getByRole('button', { name: MOTS.proposerIdee }).last()
  await expect(boutonIdee, 'le bouton part alors que le thème est vide').toBeDisabled()
  await page.getByRole('button', { name: MOTS.annuler }).click()
  await expect(champTheme, 'Annuler ne ferme pas la fenêtre').toBeHidden()

  const zone = page.getByRole('textbox').first()
  expect((await zone.inputValue()).trim(), 'Annuler a écrit dans la zone').toBe('')

  await zone.fill(DEMANDE)
  await page.getByRole('button', { name: MOTS.generer }).click()

  // La grille écrite, on REVIENT À LA LISTE — elle y est. C'est de là qu'on l'ouvre.
  await expect(page.getByRole('button', { name: MOTS.nouvelle }),
               'on ne revient pas à la liste après la génération').toBeVisible({ timeout: ATTENTE_GENERATION })
  const nouvelleLigne = page.getByRole('button', { name: /critères? ×/i }).first()
  await expect(nouvelleLigne, 'la grille générée n’apparaît pas dans la liste').toBeVisible({ timeout: 20_000 })
  await ouvrirDansEditeur(page, nouvelleLigne)

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

  // ON QUITTE ET ON REVIENT — c'est la preuve d'enregistrement, et la seule qui vaille ici.
  // Un `reload()` ramènerait à l'accueil : l'application du professeur n'a qu'UNE adresse, tous
  // ses écrans sont des pages internes. Sortir vers la liste puis rouvrir la grille la fait
  // relire depuis le serveur, ce qui est exactement ce qu'on veut vérifier.
  await page.waitForTimeout(1200)   // le temps de l'écriture et de la relecture
  await ouvrirLaListe(page)
  const relue = page.getByRole('button', { name: /critères? ×/i }).first()
  await expect(relue, 'la grille n’est plus dans la liste').toBeVisible({ timeout: 20_000 })
  await ouvrirDansEditeur(page, relue)

  const apres = await lireTableau(page)
  expect(apres.valeurs, 'la retouche n’a pas été enregistrée').toContain(marque)
  await ecranSain(page, 'après retouche')

  // ── 4. La retrouver dans la liste ────────────────────────────────────────────────────
  await ouvrirLaListe(page)
  // La ligne de liste porte le TITRE de la grille : depuis le cadre liste + détail, un clic la
  // sélectionne et le détail s'affiche à droite — le mot « ouvrir » n'est plus dans son nom.
  const dansLaListe = page.getByRole('button', { name: new RegExp(escape(titre), 'i') })
  await expect(dansLaListe.first(), 'la grille n’apparaît pas dans la liste').toBeVisible({ timeout: 20_000 })
  const avant = await dansLaListe.count()

  // ── 5. Dupliquer — la copie doit porter le CONTENU, pas seulement le nom ──────────────
  await ouvrirDansEditeur(page, dansLaListe.first())
  await page.getByRole('button', { name: MOTS.dupliquer }).click()

  // On atterrit sur la copie : elle doit déjà contenir la retouche.
  const copie = await lireTableau(page)
  expect(copie.valeurs, 'la copie ne porte pas le contenu de l’originale').toContain(marque)

  await ouvrirLaListe(page)
  await expect(async () => {
    expect(await page.getByRole('button', { name: new RegExp(escape(titre), 'i') }).count())
      .toBeGreaterThan(avant)
  }).toPass({ timeout: 20_000 })

  // ── 6. Supprimer LA COPIE — et vérifier que ça disparaît VRAIMENT ────────────────────
  // La copie, et pas l'originale : le second scénario a besoin d'une grille en base pour jouer
  // la voie sans IA. S'il n'en trouve pas, il s'exclut et la recette ne joue qu'un scénario
  // sur deux — sans rien dire d'autre qu'une ligne « skipped ».
  const copie1 = page.getByRole('button', { name: /\(copie\)/i }).first()
  await expect(copie1, 'la copie n’apparaît pas dans la liste').toBeVisible({ timeout: 20_000 })
  await ouvrirDansEditeur(page, copie1)
  await page.getByRole('button', { name: MOTS.supprimer }).click()

  // La maison a un canal unique de confirmation (ConfirmDialog.jsx, `role="alertdialog"`) : on
  // vise le bouton DANS le dialogue. Un `.last()` sur toute la page attrapait parfois celui de
  // l'éditeur, déjà cliqué, et attendait indéfiniment qu'il redevienne stable.
  const boite = page.getByRole('alertdialog')
  await expect(boite, 'la confirmation de suppression ne s’ouvre pas').toBeVisible({ timeout: 10_000 })
  await boite.getByRole('button', { name: /^supprimer$/i }).click()
  await expect(boite, 'la confirmation reste ouverte après le clic').toBeHidden({ timeout: 15_000 })

  await ouvrirLaListe(page)
  await expect(page.getByRole('button', { name: /\(copie\)/i }),
               'la copie est toujours là après suppression').toHaveCount(0, { timeout: 20_000 })

  // ── 7. Rien n'a cassé en chemin ──────────────────────────────────────────────────────
  await ecranSain(page, 'fin du parcours')
  expect(erreurs, 'erreurs JavaScript pendant le parcours').toEqual([])
})

// RETOUCHER UNE GRILLE EXISTANTE — ET CE SCÉNARIO NE COÛTE RIEN.
//
// Il ne crée aucune grille : il travaille sur celles qui sont déjà là. C'est le geste le plus
// fréquent du professeur (il génère une fois, il retouche vingt), et c'est aussi ce qui permet
// de passer la recette autant de fois qu'on veut sans payer un appel à chaque coup.
//
// IL Y A UNE SEULE FAÇON DE CRÉER UNE GRILLE : la génération. Ce scénario jouait avant la voie
// « grille vide », retirée le 17/08/2026 — un tableau nu à remplir case par case n'est pas un
// service, le professeur a déjà un tableur.
test('une grille existante se retouche case, colonne et poids, puis se supprime', async ({ page }) => {
  // CINQ MINUTES, et non les trente secondes du reglage general : ce scenario enchaine une
  // generation par le modele, une dizaine de retouches et deux allers-retours vers la liste.
  // Le plafond commun est taille pour un scenario qui fait un geste.
  test.setTimeout(300000)

  const erreurs = []
  page.on('pageerror', e => erreurs.push(e.message))

  // ON ATTEND LE MENU. La session est deja ouverte (fichier d'etat), mais le menu arrive au
  // rendu suivant : chercher « Grilles » tout de suite le declare absent d'un menu qui n'est
  // simplement pas encore la.
  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('button', { name: MOTS.menuEvals }).first(),
               'le menu du professeur ne s’affiche pas').toBeVisible({ timeout: 20_000 })
  await ouvrirLaListe(page)

  // Aucune grille en base : il n'y a rien à retoucher, et ce scénario ne doit pas en fabriquer
  // une (il deviendrait payant). On le dit et on s'arrête — le premier scénario en laisse une.
  // ON ATTEND LA LISTE AVANT DE LA DECLARER VIDE. Les lignes arrivent apres le bouton
  // « Nouvelle grille » : compter tout de suite renvoyait zero, et le scenario s'excluait alors
  // qu'il y avait des grilles a l'ecran une seconde plus tard.
  const lignes = page.getByRole('button', { name: /critères? ×/i })
  // `isVisible()` NE REESSAIE PAS — il repond sur l'instant, et son option `timeout` est sans
  // effet. C'est `waitFor` qui attend. La nuance a fait s'exclure ce scenario alors que trois
  // grilles etaient a l'ecran une seconde plus tard.
  const listeVide = await lignes.first()
    .waitFor({ state: 'visible', timeout: 10_000 })
    .then(() => false)
    .catch(() => true)
  test.skip(listeVide, 'aucune grille en base : lancez d’abord le scénario de génération')

  await ouvrirDansEditeur(page, lignes.first())
  await ecranSain(page, 'ouverture de l’éditeur')

  const champTitre = page.getByPlaceholder(MOTS.titreGrille)
  const titre = (await champTitre.inputValue()).trim()

  // ── 1. UNE CASE ──────────────────────────────────────────────────────────────────────
  const { cases } = await lireTableau(page)
  expect(await cases.count(), 'la grille ouverte n’a aucune case').toBeGreaterThan(0)

  const marque = 'Retouche sans IA ' + Date.now().toString().slice(-6)
  await cases.first().fill(marque)
  await cases.first().blur()

  // ── 2. UNE COLONNE — son libellé, qui est commun à tous les critères ─────────────────
  const colonne = page.locator('table thead input[type="text"]').first()
  const nomColonne = 'Palier ' + Date.now().toString().slice(-4)
  await colonne.fill(nomColonne)
  await colonne.blur()

  // ── 3. UN POIDS — c'est lui qui fait bouger la note maximale ─────────────────────────
  const poids = page.locator('table tbody input[type="number"]').first()
  await expect(poids, 'le poids d’un critère n’est pas un champ numérique').toBeVisible()
  await poids.fill('3')
  await poids.blur()

  // ── 4. TOUT ÇA DOIT SURVIVRE À UN RECHARGEMENT ───────────────────────────────────────
  // Il n'y a pas de bouton « Enregistrer » : chaque champ part au blur. Le seul contrôle qui
  // vaille est donc celui-ci — un message à l'écran ne prouverait rien.
  await page.waitForTimeout(1500)
  await ouvrirLaListe(page)
  const relue = page.getByRole('button', { name: /critères? ×/i }).first()
  await expect(relue, 'la grille n’est plus dans la liste').toBeVisible({ timeout: 20_000 })
  await ouvrirDansEditeur(page, relue)

  const apres = await lireTableau(page)
  expect(apres.valeurs, 'la case retouchée n’a pas été enregistrée').toContain(marque)
  await expect(page.locator('table thead input[type="text"]').first(),
               'le libellé de colonne n’a pas été enregistré').toHaveValue(nomColonne)
  await expect(page.locator('table tbody input[type="number"]').first(),
               'le poids n’a pas été enregistré').toHaveValue('3')
  await ecranSain(page, 'après retouches')

  // ── 5. SUPPRIMER — et vérifier que ça disparaît VRAIMENT ─────────────────────────────
  await page.getByRole('button', { name: MOTS.supprimer }).click()
  // La maison a un canal unique de confirmation : le bouton de la modale porte le mot du geste.
  // ON CIBLE DANS LA MODALE, pas `.last()` sur toute la page : la boîte de confirmation est
  // montée AVANT les écrans (App.jsx), donc son bouton est le PREMIER du document et `.last()`
  // retombait sur celui de l'écran, que la modale recouvrait — clic éternellement intercepté.
  await page.getByRole('alertdialog').getByRole('button', { name: /^supprimer$/i }).click()

  await ouvrirLaListe(page)
  await expect(page.getByText(titre, { exact: false }),
               'la grille supprimée est encore dans la liste').toHaveCount(0, { timeout: 20_000 })

  expect(erreurs, 'erreurs JavaScript pendant le parcours').toEqual([])
})

// Le titre généré peut contenir des caractères que les expressions régulières interprètent.
function escape(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') }
