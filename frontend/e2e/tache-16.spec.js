import { test, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

// RECETTE DE LA NOTE 16 — « Referentiels : la matiere sur l'unite, et le depot par arrete ».
//
// CE FICHIER NE SERT QU'A CETTE NOTE. Il ne parcourt pas l'application : il eprouve les cinq
// gestes ecrits dans la section « LA RECETTE » de la note, et rien d'autre. Le jour ou la note
// se coche, c'est lui qui tourne — un script commun ne dirait rien de CE travail-la.
//
// IL EST ROUGE TANT QUE LE CHANTIER N'EST PAS FAIT, et c'est sa raison d'etre : il est ecrit
// AVANT la structure, il en est le contrat. Les libelles qu'il attend sont ceux que l'ecran
// devra porter — ils sont rassembles dans `MOTS`, en un seul endroit.
//
// AUCUN APPEL PAYANT, ET RIEN DE DETRUIT. Le depot est joue jusqu'a l'annonce de ce qui sera
// refait, puis RETIRE : la lecture du PDF (nombre de pages, recherche du niveau) ne coute rien,
// et la decoupe — la seule etape qui appelle un modele — n'est jamais lancee. Le document est
// fabrique ici meme, en memoire : aucune trace sur le disque, aucune unite touchee.
//
// Identifiants attendus dans l'environnement :
//   ADMIN_USER, ADMIN_PASS

const USER = process.env.ADMIN_USER
const PASS = process.env.ADMIN_PASS

function echapper(texte) {
  return String(texte).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// LES LIBELLES DE L'ECRAN, EN UN SEUL ENDROIT. Le jour ou un titre change de mot, c'est une
// ligne a corriger ici, pas dix dans le fichier. Tout est insensible a la casse : un accent ou
// une majuscule qui bouge ne doit pas faire echouer une recette.
const MOTS = {
  catalogues:    /catalogues/i,
  decoupe:       /découpe/i,
  matieres:      /matières de ce référentiel/i,
  documents:     /documents du référentiel/i,
  niveaux:       /niveaux desservis/i,
  // Le compteur de la cartouche « Decoupe » : c'est LUI qui porte le verdict du chantier.
  // « 0 sans matiere » est la forme attendue ; tout autre chiffre est un referentiel oublie.
  sansMatiere:   /(\d+)\s+sans\s+matière/i,
  // Ce que porte une unite de cadre : la portee « formation », affichee en clair.
  portee:        /tout le référentiel/i,
  matiereDe:     (nom) => new RegExp('matière\\s*:\\s*' + echapper(nom), 'i'),
  filtreMatiere: /filtrer par matière/i,
  toutesMatieres: 'Toutes les matières',
  ajouterArrete: /ajouter un arrêté/i,
  matiereDuDoc:  /matière du document/i,
  enVigueur:     /en vigueur depuis/i,
  annonceRefaite: /seront refaites|unités de cette matière/i,
  retirer:       /retirer/i,
  valider:       /valider le référentiel/i,
  enregistrer:   /enregistrer/i,
  deplier:       /déplier|réduire/i,
}

// Les mots qui trahissent un ecran casse quand ils s'affichent tels quels.
// `NaN` est a part : sensible a la casse et entre limites de mots, sans quoi il matche
// « fiNANce » ou « connaissance » — un test qui crie au loup se desapprend en trois jours.
const MOTS_DE_PANNE = /undefined|\[object Object\]|Internal Server Error|Failed to fetch/i
const PANNE_NAN = /\bNaN\b/

test.describe.configure({ mode: 'serial' })   // les cinq gestes forment une histoire : elle a un ordre

// UNE SEULE CONNEXION POUR TOUT LE FICHIER, gardee dans un fichier d'etat que chaque scenario
// recharge. Ce n'est pas une optimisation : /admin/login est plafonne a DIX tentatives par
// heure, et cinq scenarios qui se connectent chacun de leur cote atteignent la limite des la
// deuxieme execution de la journee — l'echec accuse alors une protection qui fonctionne.
const ETAT_SESSION = 'test-results/.session-tache-16.json'

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
  await expect(page.locator('nav button[aria-expanded]').first()).toBeVisible({ timeout: 15000 })
}

// ── LES OUTILS DE L'ECRAN ────────────────────────────────────────────────────────────────────

// UNE CARTOUCHE, DESIGNEE PAR SON TITRE. Toutes les cartouches de la maison ont la meme forme :
// une carte blanche arrondie dont le premier element est un `h2`. On vise donc la carte QUI
// CONTIENT le titre — pas un rang, pas une position : ajouter une cartouche au-dessus ne casse
// rien.
function cartouche(page, titre) {
  return page.locator('div.rounded-xl')
    .filter({ has: page.getByRole('heading', { name: titre }) }).first()
}

function titreDecoupe(page) {
  return cartouche(page, MOTS.decoupe).getByRole('heading', { name: MOTS.decoupe }).first()
}

// ON ATTEND LA LISTE, PAS SON TITRE. « Catalogues (6) » s'affiche AVANT que la liste soit
// revenue du serveur — a ce moment-la il est ecrit « Catalogues (0) », et le titre matche tout
// aussi bien. Le premier passage a compte zero referentiel et conclu qu'il n'y avait rien a
// eprouver, sur un ecran qui en portait six.
async function ouvrirReferentiels(page) {
  await page.goto('/admin/referentiels')
  await expect(lignesCatalogue(page).first(),
    'aucun referentiel dans la colonne des catalogues : il n y a rien a eprouver')
    .toBeVisible({ timeout: 15000 })
}

// LES CATALOGUES TELS QU'ILS SONT AFFICHES — jamais une liste ecrite ici. Le chantier porte sur
// TOUS les referentiels ; en nommer six dans le script, c'est oublier le septieme le jour ou il
// arrive, et croire la recette verte alors qu'elle n'a rien regarde.
//
// ON NE GARDE QUE LES BOUTONS QUI PORTENT « cycle · niveau ». La ligne en compte deux — ouvrir,
// et transferer vers une autre installation — et le second n'a pas de texte : l'ecarter par son
// libelle ne marche pas, et le parcours cliquait une fois sur deux sur un transfert.
function lignesCatalogue(page) {
  return page.locator('aside').filter({ hasText: MOTS.catalogues }).first()
    .locator('button').filter({ hasText: /·/ })
}

// LA CARTOUCHE « DECOUPE » EST REPLIEE une fois le referentiel monte : son compteur vit dans le
// titre, qui reste lisible replie — c'est justement l'interet de replier. On ne la deroule que
// pour regarder les lignes.
async function deroulerDecoupe(page) {
  const carte = cartouche(page, MOTS.decoupe)
  const bouton = carte.getByRole('button', { name: MOTS.deplier }).first()
  if (await bouton.count()) {
    const nom = (await bouton.textContent()) || ''
    if (/déplier/i.test(nom)) await bouton.click()
  }
  return carte
}

async function ecranSain(page) {
  const texte = await page.locator('body').innerText()
  expect(texte).not.toMatch(MOTS_DE_PANNE)
  expect(texte).not.toMatch(PANNE_NAN)
}

// ── 1. LE VERDICT DU CHANTIER : AUCUNE UNITE ORPHELINE, NULLE PART ───────────────────────────
//
// « Le chantier est fini quand une requete le dit : aucune unite sans matiere ni portee
// explicite. » Ce compteur EST cette requete, rendue lisible : il vit dans le titre de la
// cartouche, donc sous les yeux, et non dans un outil que personne n'ouvre.

test('aucune unite ne reste sans matiere, sur tous les catalogues', async ({ page }) => {
  await ouvrirReferentiels(page)
  const lignes = lignesCatalogue(page)
  const combien = await lignes.count()
  expect(combien, 'aucun referentiel a l ecran : il n y a rien a eprouver').toBeGreaterThan(0)

  for (let i = 0; i < combien; i++) {
    const nom = ((await lignes.nth(i).textContent()) || '').trim()
    await lignes.nth(i).click()
    const titre = titreDecoupe(page)
    await expect(titre, 'la cartouche Decoupe ne s ouvre pas : ' + nom).toBeVisible({ timeout: 15000 })

    const texte = (await titre.textContent()) || ''
    const compte = texte.match(MOTS.sansMatiere)
    expect(compte, 'le titre de la decoupe n annonce pas les unites sans matiere : ' + nom + ' — ' + texte).not.toBeNull()
    expect(Number(compte[1]), compte[1] + ' unite(s) sans matiere : ' + nom).toBe(0)
    await ecranSain(page)
  }
})

// ── 2. CHAQUE UNITE DIT D'OU ELLE VIENT, ET LA LISTE SE FILTRE ───────────────────────────────
//
// Le compteur ci-dessus prouve qu'aucune etiquette ne manque ; celui-ci prouve qu'elle SERT —
// un filtre qui laisse passer une unite d'une autre matiere ramenerait au prof de maths du
// francais, exactement ce que le chantier vient corriger.

test('la liste des unites se filtre par matiere, et les textes de cadre restent', async ({ page }) => {
  await ouvrirReferentiels(page)
  await lignesCatalogue(page).first().click()

  // Deux matieres du referentiel : celle qu'on demande, et celle qui ne doit plus apparaitre.
  const lignesMatieres = cartouche(page, MOTS.matieres).getByRole('listitem')
  await expect(lignesMatieres.first()).toBeVisible({ timeout: 15000 })
  const noms = []
  for (let i = 0; i < Math.min(await lignesMatieres.count(), 2); i++) {
    noms.push(((await lignesMatieres.nth(i).textContent()) || '').trim())
  }
  expect(noms.length, 'il faut deux matieres pour eprouver un filtre').toBe(2)

  const carte = await deroulerDecoupe(page)
  await carte.getByLabel(MOTS.filtreMatiere).selectOption({ label: noms[0] })

  await expect(carte.getByText(MOTS.matiereDe(noms[0])).first()).toBeVisible()
  await expect(carte.getByText(MOTS.matiereDe(noms[1]))).toHaveCount(0)

  // LES TEXTES DE CADRE NE SE FILTRENT PAS. Socle commun, competences travaillees : ils portent
  // la portee « formation » et le moteur les ajoute a toute generation, quelle que soit la
  // matiere. Les voir disparaitre d'un filtre, c'est les perdre en production.
  await carte.getByLabel(MOTS.filtreMatiere).selectOption({ label: MOTS.toutesMatieres })
  await expect(carte.getByText(MOTS.portee).first()).toBeVisible()
  await ecranSain(page)
})

// ── 3. UN DOCUMENT PAR ARRETE, AVEC SA PLAGE ─────────────────────────────────────────────────
//
// Le referentiel ne garde plus un bloc unique de texte epure : un morceau par document depose.
// C'est ce qui permet d'en remplacer un seul — et la plage de validite est ce qui remplace
// l'ecrasement : l'ancienne version se ferme, la nouvelle s'ouvre.

test('les documents se listent un par arrete, avec leur matiere et leur plage', async ({ page }) => {
  await ouvrirReferentiels(page)
  await lignesCatalogue(page).first().click()

  const carte = cartouche(page, MOTS.documents)
  await expect(carte).toBeVisible({ timeout: 15000 })

  const documents = carte.getByRole('listitem')
  await expect(documents.first()).toBeVisible()
  const combien = await documents.count()
  for (let i = 0; i < combien; i++) {
    const ligne = ((await documents.nth(i).textContent()) || '').trim()
    // Chaque document dit trois choses : ce qu'il couvre, depuis quand, et jusqu'a quand. La fin
    // reste vide tant que le texte est en vigueur — un document ferme, lui, porte sa date.
    expect(ligne, 'document sans matiere annoncee : ' + ligne).toMatch(/matière/i)
    expect(ligne, 'document sans plage de validite : ' + ligne).toMatch(MOTS.enVigueur)
  }
  await ecranSain(page)
})

// ── 4. LE DEPOT SE RATTACHE A UNE MATIERE, ET L'ANNULER NE LAISSE RIEN ───────────────────────
//
// « Un depot = un document = une matiere. » Un arrete depose sans matiere n'aurait aucune unite
// a remplacer : la decoupe refaite ecraserait tout le referentiel — la panne meme que ce
// chantier supprime. Le bouton reste donc ferme tant que la matiere manque.
//
// ON S'ARRETE AVANT DE VALIDER. Le scenario prouve le rattachement et l'annonce, puis retire le
// document : rien n'est ecrit, aucune unite n'est refaite, aucun modele n'est appele.

test('un arrete se depose sur une matiere, et le retirer laisse le referentiel intact', async ({ page }) => {
  await ouvrirReferentiels(page)
  const premier = lignesCatalogue(page).first()
  // LE LIBELLE PEUT NOMMER PLUSIEURS NIVEAUX (« Crèche · Bébés (0-1 an), Moyens-Grands (1-3 ans) ») :
  // on prend le premier, un vrai nom de niveau, celui que le controle du couple ira chercher.
  const niveau = ((await premier.textContent()) || '').split('·').pop().split(',')[0].trim()
  await premier.click()

  const avant = ((await titreDecoupe(page).textContent()) || '').trim()

  const carte = cartouche(page, MOTS.documents)
  await carte.getByRole('button', { name: MOTS.ajouterArrete }).click()

  // LE DOCUMENT EST FABRIQUE ICI, avec le nom du niveau dedans : sans lui, le controle du couple
  // refuse le fichier — et il aurait raison, un arrete qui ne nomme pas son niveau n'est pas
  // l'arrete de ce referentiel.
  await page.locator('input[type="file"]').setInputFiles({
    name: 'arrete-de-recette.pdf',
    mimeType: 'application/pdf',
    buffer: pdfMinimal(['Arrete de recette - ' + niveau, 'Document fabrique par la recette, jamais valide.']),
  })

  // Tant que la matiere n'est pas choisie, la validation est fermee.
  const valider = carte.getByRole('button', { name: MOTS.valider })
  await expect(valider, 'un document part sans matiere : rien ne dit quelles unites refaire').toBeDisabled()

  const choixMatiere = carte.getByLabel(MOTS.matiereDuDoc)
  await expect(choixMatiere).toBeVisible()
  await choixMatiere.selectOption({ index: 1 })
  await expect(valider).toBeEnabled()

  // L'ANNONCE : ce qui sera refait, et ce qui ne bougera pas. Sans elle, l'admin valide sans
  // savoir ce qu'il remplace.
  await expect(carte.getByText(MOTS.annonceRefaite)).toBeVisible()

  await carte.getByRole('button', { name: MOTS.retirer }).first().click()
  const apres = ((await titreDecoupe(page).textContent()) || '').trim()
  expect(apres, 'retirer le document a change la decoupe : il ne devait rien toucher').toBe(avant)
  await ecranSain(page)
})

// ── 5. LES NIVEAUX DESSERVIS SE CHOISISSENT A L'ECRAN ────────────────────────────────────────
//
// `referentiel_niveaux` n'avait aucun ecran (dette assumee le 15/08/2026) : un referentiel de
// cycle se remplissait a la main, en base. Ce qui se prouve ici, c'est que le choix TIENNE —
// un ecran qui accepte le clic et oublie au rechargement est pire que pas d'ecran.

test('les niveaux desservis se cochent, et le choix tient au rechargement', async ({ page }) => {
  await ouvrirReferentiels(page)
  await lignesCatalogue(page).first().click()

  const carte = cartouche(page, MOTS.niveaux)
  await expect(carte).toBeVisible({ timeout: 15000 })

  const cases = carte.getByRole('checkbox')
  await expect(cases.first()).toBeVisible()
  const etatDepart = await cases.first().isChecked()

  await cases.first().setChecked(!etatDepart)
  await carte.getByRole('button', { name: MOTS.enregistrer }).click()

  await page.reload()
  await expect(cartouche(page, MOTS.niveaux).getByRole('checkbox').first())
    .toBeChecked({ checked: !etatDepart, timeout: 15000 })

  // ON REMET LE REFERENTIEL COMME ON L'A TROUVE. Une recette qui laisse un niveau coche derriere
  // elle change ce que voient les profs — elle eprouverait l'application en la deformant.
  const revenue = cartouche(page, MOTS.niveaux)
  await revenue.getByRole('checkbox').first().setChecked(etatDepart)
  await revenue.getByRole('button', { name: MOTS.enregistrer }).click()
  await ecranSain(page)
})

// ── LE DOCUMENT DE RECETTE ───────────────────────────────────────────────────────────────────
//
// UN VRAI PDF, ECRIT A LA MAIN. Le depot lit le fichier pour en compter les pages et y chercher
// le nom du niveau : un fichier bidon serait rejete, et le scenario n'aurait rien prouve. Il en
// faut donc un valide — une page, une police standard, un flux de texte non compresse, lisible
// par n'importe quel extracteur.
//
// AUCUNE DEPENDANCE, AUCUN FICHIER SUR LE DISQUE. Ajouter une bibliotheque de fabrication de PDF
// a la recette, c'est une mise a jour de plus a suivre pour trois cents octets de texte ; le
// document vit en memoire et meurt avec le scenario.
function pdfMinimal(lignes) {
  // LA POLICE STANDARD NE CONNAIT QUE WINANSI. Un tiret cadratin ou une apostrophe
  // typographique — deux caracteres que les intitules portent souvent — en ressortent en
  // « (cid:20) » : le nom du niveau devient introuvable, et le controle du couple refuse un
  // document parfaitement bon. On les ramene donc a leur equivalent simple avant d'ecrire.
  const lisible = (t) => t.replace(/[—–]/g, '-').replace(/[’‘]/g, "'").replace(/[“”]/g, '"')
  const texte = lignes.map(lisible).map((l, i) =>
    'BT /F1 12 Tf 60 ' + (760 - i * 20) + ' Td (' + l.replace(/([\\()])/g, '\\$1') + ') Tj ET').join('\n')
  const flux = texte + '\n'

  const objets = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',
    '<< /Length ' + Buffer.byteLength(flux, 'latin1') + ' >>\nstream\n' + flux + 'endstream',
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
  ]

  // LES DECALAGES SE COMPTENT EN OCTETS, PAS EN CARACTERES. Un titre accentue — et les niveaux
  // en portent — pese deux octets en UTF-8 : une table xref comptee en caracteres decalerait
  // tout le fichier et le rendrait illisible. D'ou `latin1` de bout en bout.
  let corps = '%PDF-1.4\n'
  const decalages = []
  objets.forEach((o, i) => {
    decalages.push(Buffer.byteLength(corps, 'latin1'))
    corps += (i + 1) + ' 0 obj\n' + o + '\nendobj\n'
  })

  const xref = Buffer.byteLength(corps, 'latin1')
  corps += 'xref\n0 ' + (objets.length + 1) + '\n0000000000 65535 f \n'
  for (const d of decalages) corps += String(d).padStart(10, '0') + ' 00000 n \n'
  corps += 'trailer\n<< /Size ' + (objets.length + 1) + ' /Root 1 0 R >>\nstartxref\n' + xref + '\n%%EOF\n'

  return Buffer.from(corps, 'latin1')
}
