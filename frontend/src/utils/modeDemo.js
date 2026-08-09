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
let couple = null         // « BTS · BTS CIEL Option A » — le couple que cette base sert
let enCours = null        // la promesse partagée, tant que l'appel n'est pas revenu
const abonnes = new Set()

function demander() {
  if (connu !== null) return Promise.resolve(connu)
  if (!enCours) {
    enCours = fetch('/api/demo/etat')
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        connu = !!(d && d.mode_demo)
        couple = (d && d.couple) || null
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

// Le couple servi par cette base — « BTS · BTS CIEL Option A ». Vide tant que la réponse n'est
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
