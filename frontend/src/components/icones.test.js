// Les icônes ne se recopient plus d'un fichier à l'autre.
//
// CE QUE CE TEST ATTRAPE, et pourquoi il existe : une icône utilisée en JSX sans être
// définie ni importée ne casse NI le build NI les autres tests — c'est une variable libre,
// elle n'explose qu'à l'écran, chez le prof. Le second test gèle le nombre de noms encore
// définis dans plusieurs fichiers : le copier-coller d'icônes est ce qui avait produit du
// code mort (une copie de Spinner jamais utilisée) et des divergences muettes (la même
// icône dessinée différemment selon l'écran).
//
// CE QU'IL N'ATTRAPE PAS : que deux icônes de MÊME nom dessinent la même chose. Les deux
// doublons gelés ci-dessous sont justement des dessins différents, gardés exprès.
//
// Lancer : npm test  (ou  node --test src/components/icones.test.js)
import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join, relative } from 'node:path'

const SRC = join(dirname(fileURLToPath(import.meta.url)), '..')

// Deux noms recouvrent deux DESSINS différents ; les fusionner changerait l'écran.
//   IconMail — bouts de traits arrondis côté admin, francs côté prof ;
//   IconUser — 15 px et traits arrondis dans l'Aide, 14 px francs dans la Sidebar.
// Toute NOUVELLE entrée ici est une copie de plus : elle se corrige, elle ne s'ajoute pas.
const DOUBLONS_GELES = ['IconMail', 'IconUser']

function fichiersJsx(dossier) {
  return readdirSync(dossier).flatMap((nom) => {
    const chemin = join(dossier, nom)
    if (statSync(chemin).isDirectory()) return fichiersJsx(chemin)
    return nom.endsWith('.jsx') ? [chemin] : []
  })
}

const FICHIERS = fichiersJsx(SRC).map((f) => ({ chemin: f, texte: readFileSync(f, 'utf8') }))

test('toute icône utilisée est définie sur place ou importée', () => {
  const manquantes = []
  for (const { chemin, texte } of FICHIERS) {
    const utilisees = new Set([...texte.matchAll(/<(Icon[A-Za-z]+|Spinner)[\s/>]/g)].map((m) => m[1]))
    for (const nom of utilisees) {
      const definie = new RegExp(`^(export )?(const|function)\\s+${nom}\\s*[=(]`, 'm').test(texte)
      const importee = new RegExp(`^import .*\\b${nom}\\b.*from `, 'm').test(texte)
      if (!definie && !importee) manquantes.push(`${relative(SRC, chemin)} : <${nom}>`)
    }
  }
  assert.deepEqual(
    manquantes,
    [],
    `Icônes utilisées sans être définies ni importées — elles n'explosent qu'à l'écran : ${manquantes.join(', ')}`,
  )
})

test('aucune icône ne réapparaît dans deux fichiers', () => {
  const parNom = new Map()
  for (const { chemin, texte } of FICHIERS) {
    if (chemin.endsWith('icones.jsx')) continue
    for (const m of texte.matchAll(/^(?:const|function)\s+(Icon[A-Za-z]+|Spinner)\s*[=(]/gm)) {
      parNom.set(m[1], [...(parNom.get(m[1]) || []), relative(SRC, chemin)])
    }
  }
  const doublons = [...parNom.entries()].filter(([, f]) => f.length > 1).map(([n]) => n).sort()
  assert.deepEqual(
    doublons,
    [...DOUBLONS_GELES].sort(),
    'Une icône est de nouveau définie dans plusieurs fichiers. Elle a sa place dans '
      + 'components/icones.jsx — sauf si son dessin diffère vraiment, auquel cas elle rejoint '
      + 'DOUBLONS_GELES en haut de ce test, avec la raison.',
  )
})
