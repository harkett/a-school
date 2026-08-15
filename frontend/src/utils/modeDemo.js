// Le MODE DÉMONSTRATION côté navigateur : la réponse, et la marque qui en découle.
//
// Sommes-nous dans une instance de démonstration ? UNE seule réponse, UNE seule requête.
//
// POURQUOI UN HOOK PARTAGÉ. Deux pièces posent la même question — le bandeau du bas et le
// filigrane de fond — et il y en aura d'autres. Chacune avec son `fetch` ferait deux appels pour
// une réponse qui ne change jamais pendant la visite, et surtout deux vérités possibles si l'une
// répond et pas l'autre. La réponse est donc mémorisée ICI, au niveau du module : la première
// pièce montée déclenche l'appel, les suivantes s'y accrochent.
//
// LA PRUDENCE DU DÉFAUT : `false`. Une absence de réponse ne doit JAMAIS faire croire qu'on est
// en démonstration — un prof qui croirait travailler dans un bac à sable alors qu'il est dans le
// vrai ferait des dégâts irréversibles. Le doute penche du côté du réel.

import { useEffect, useState } from 'react'

let connu = null          // true / false une fois la réponse reçue
let couple = null         // « cycle · niveau » — le couple que cette base sert
let enCours = null        // la promesse partagée, tant que l'appel n'est pas revenu
const abonnes = new Set()

// ── L'ONGLET DU NAVIGATEUR ───────────────────────────────────────────────────────────────────
// POURQUOI MARQUER L'ONGLET, ALORS QUE LA PAGE L'EST DÉJÀ. Le bandeau du bas et le filigrane
// sont DANS la page : ils ne disent rien quand l'onglet est au second plan. Or c'est là que la
// confusion arrive — une session prof et une démonstration ouvertes côte à côte, deux onglets
// nommés « aSchool », et rien pour les distinguer avant d'avoir cliqué dedans.
//
// LE FOND D'UN ONGLET N'EST PAS MODIFIABLE : aucun navigateur ne l'expose à la page. Les deux
// seules prises sont le TITRE et l'ICÔNE. On se sert des deux, et pas d'une seule : le titre dit
// QUELLE démonstration, l'icône fait que ça se voit sans lire — un onglet rétréci ne montre plus
// que son icône.

// Le violet est celui du bandeau et du filigrane (#6d28d9), pas une troisième couleur : la marque
// de l'onglet et celle de la page doivent se reconnaître l'une l'autre.
const ICONE_DEMO = 'data:image/svg+xml,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">' +
  '<rect width="32" height="32" rx="7" fill="#6d28d9"/>' +
  '<text x="16" y="24" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" ' +
  'font-size="21" font-weight="700" fill="#ffffff">D</text>' +
  '</svg>'
)

// « BTS · BTS Machin » → « BTS Machin » : le cycle précède le niveau et se répète presque
// toujours dans son nom ; un onglet ne montre que ses premiers caractères, et « BTS · BTS… »
// les gaspillerait à dire deux fois la même chose. Plusieurs couples restent séparés par « / ».
function niveauxDe(valeur) {
  return valeur.split(' / ').map(p => p.split(' · ').pop().trim()).filter(Boolean).join(' / ')
}

// LA DÉMONSTRATION D'ABORD, LE NOM DU PRODUIT ENSUITE. Un onglet étroit coupe la fin : ce qui doit
// survivre au rognage, c'est « DÉMO », puis le couple. « aSchool » ferme la marche — on sait déjà
// où on est, la question est de savoir dans LAQUELLE des deux instances.
function marquerOnglet() {
  const niveaux = couple ? niveauxDe(couple) : ''
  document.title = niveaux ? `DÉMO · ${niveaux} — aSchool` : 'DÉMO — aSchool'

  // On RÉUTILISE la balise d'index.html plutôt que d'en ajouter une : deux `rel="icon"` laissent
  // le navigateur choisir, et Chrome garde volontiers la première — l'icône rose serait restée.
  let lien = document.querySelector('link[rel="icon"]')
  if (!lien) {
    lien = document.createElement('link')
    lien.rel = 'icon'
    document.head.appendChild(lien)
  }
  lien.type = 'image/svg+xml'
  lien.href = ICONE_DEMO
}

function demander() {
  if (connu !== null) return Promise.resolve(connu)
  if (!enCours) {
    enCours = fetch('/api/demo/etat')
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        connu = !!(d && d.mode_demo)
        couple = (d && d.couple) || null
        // La marque de l'onglet se pose ICI et nulle part ailleurs : c'est le seul endroit qui
        // connaisse la réponse, et il n'exige aucun composant monté — l'onglet est donc juste
        // même sur un écran qui n'affiche ni bandeau ni filigrane.
        if (connu) marquerOnglet()
        abonnes.forEach(poser => poser(connu))
        return connu
      })
      .catch(() => {
        // Pas de réponse : on ne fige rien (`connu` reste null) pour qu'un rechargement puisse
        // redemander, et on ne prétend surtout pas être en démonstration.
        enCours = null
        return false
      })
  }
  return enCours
}

export function useModeDemo() {
  const [demo, setDemo] = useState(connu === true)
  useEffect(() => {
    let vivant = true
    const poser = valeur => { if (vivant) setDemo(valeur) }
    abonnes.add(poser)
    demander().then(poser)
    return () => { vivant = false; abonnes.delete(poser) }
  }, [])
  return demo
}

// Le couple servi par cette base — « cycle · niveau ». Vide tant que la réponse n'est
// pas revenue, et vide aussi quand la base n'a aucun référentiel découpé : le bandeau garde alors
// sa phrase seule plutôt que d'afficher un trou.
export function coupleDemo() {
  return couple
}

// La réponse SANS passer par un hook — pour les sorties (PDF, Word, impression), qui sont des
// fonctions ordinaires et non des composants React. Rend `false` tant que la réponse n'est pas
// revenue : même prudence que le hook, le doute penche du côté du réel.
export function estModeDemo() {
  return connu === true
}

// La marque, écrite une fois et portée par toutes les sorties.
export const MENTION_DEMO = 'DÉMONSTRATION'
export const PHRASE_DEMO =
  'Document produit dans une base de démonstration — il ne provient pas de vos vrais contenus.'

// La tuile du filigrane, en SVG : le mot incliné, dessiné une fois. Partagée par le fond d'écran
// et par la page d'impression, pour que l'écran et le papier portent exactement la même marque.
// L'opacité et la taille sont le RÉGLAGE de tout le filigrane : plus discret qu'à l'origine
// (7 % et 48 px), assez pour tenir sur une capture d'écran sans se mettre entre le prof et son
// texte. La tuile s'espace en même temps qu'elle s'allège — un mot pâle mais serré resterait un
// quadrillage.
export const TUILE_DEMO = encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="420">' +
  '<text x="380" y="210" transform="rotate(-24 380 210)" text-anchor="middle" ' +
  'font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="600" ' +
  'letter-spacing="8" fill="#6d28d9" fill-opacity="0.035">' + MENTION_DEMO + '</text>' +
  '</svg>'
)
