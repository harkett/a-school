// LE MENU ADMIN S'UTILISE SANS SOURIS.
//
// LE DÉFAUT QU'ON A EU (16/08/2026) : l'en-tête de chaque rubrique (IA, Supervision, Système…)
// était un `<div onClick>`. La tabulation le sautait : au clavier seul, aucune rubrique ne
// pouvait s'ouvrir — et comme leurs écrans ne sont atteignables QUE par les sous-entrées d'une
// rubrique dépliée, la moitié du back-office devenait inaccessible.
//
// LA RÉPARATION : un vrai `<button>`. Focus, Entrée et Espace viennent avec la balise, il n'y a
// rien à écrire. `aria-expanded` dit « replié / déplié » aux lecteurs d'écran.
//
// CE QUE CE TEST ATTRAPE : le retour d'un `<div>` cliquable à la place du bouton, la perte
// d'`aria-expanded`, et la disparition de l'anneau de focus visible sur fond sombre.
//
// CE QU'IL N'ATTRAPE PAS : un `tabIndex={-1}` glissé ailleurs, ou un CSS qui masque l'anneau
// depuis un autre fichier. Le front tourne sur `node --test`, sans jsdom : on lit la SOURCE.
//
// Lancer : npm test  (ou  node --test src/menu-admin-au-clavier.test.js)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const SRC = dirname(fileURLToPath(import.meta.url))
const layout = readFileSync(join(SRC, 'components', 'AdminLayout.jsx'), 'utf8')
const css = readFileSync(join(SRC, 'index.css'), 'utf8')

// Le bloc de l'en-tête de rubrique : de sa balise ouvrante jusqu'à la bascule de l'accordéon.
// On part de la bascule, qui ne bougera pas, et on remonte à la balise qui la porte.
function enTeteRubrique() {
  const bascule = layout.indexOf('setOpenGroup(isOpen ? null : item.label)')
  assert.notEqual(bascule, -1, "L'en-tête de rubrique est introuvable dans AdminLayout.jsx")
  const debut = layout.lastIndexOf('<', bascule)
  return layout.slice(debut, bascule + 600)
}

test("l'en-tête de rubrique est un bouton, pas un bloc cliquable", () => {
  const bloc = enTeteRubrique()
  assert.match(
    bloc,
    /^<button\b/,
    "L'en-tête de rubrique du menu admin n'est plus un <button> : la tabulation le saute, et les\n" +
    'rubriques deviennent impossibles à ouvrir sans souris.\n' +
    'Trouvé : ' + bloc.slice(0, 80)
  )
  assert.match(bloc, /type="button"/, 'Sans type="button", le bouton soumettrait un formulaire parent.')
})

test("l'état replié / déplié est annoncé", () => {
  assert.match(
    enTeteRubrique(),
    /aria-expanded=\{[^}]*isOpen\}/,
    "aria-expanded a disparu : un lecteur d'écran ne sait plus si la rubrique est ouverte."
  )
})

test("l'anneau de focus reste visible sur la barre sombre", () => {
  assert.match(
    css,
    /\.admin-categorie:focus-visible[\s\S]{0,120}outline:/,
    "La règle de focus du menu admin a disparu d'index.css : au clavier, on tabule à l'aveugle\n" +
    "sur le fond bleu nuit de la barre latérale."
  )
  assert.match(
    layout,
    /className="admin-categorie"/,
    'Le bouton de rubrique a perdu sa classe : la règle de focus ne le vise plus.'
  )
  assert.match(
    layout,
    /<nav className="admin-nav"/,
    'La barre de navigation a perdu sa classe : les sous-entrées n’ont plus d’anneau de focus.'
  )
})
