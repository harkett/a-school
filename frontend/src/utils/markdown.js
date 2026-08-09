// LA lecture du markdown — une seule, partagée par TOUTES les sorties.
//
// POURQUOI CE FICHIER EXISTE. Une activité générée est du markdown : titres, gras, listes,
// tableaux, blocs de code, citations. Elle ressort par six portes qui ne parlent pas la même
// langue : l'aperçu écran et l'impression veulent du HTML, Word veut des objets `Paragraph` et
// `Table`, le PDF veut des lignes placées à la main, le .txt veut le brut. Sans ce fichier,
// chaque porte se remettrait à deviner ce qu'est un tableau — quatre analyseurs maison, quatre
// occasions de diverger, et c'est exactement ce qui avait produit le défaut du 07/08/2026 :
// l'ancien formateur ignorait `|`, ``` et `>`, et 38 activités sur 41 sortaient en tubes.
//
// LA RÈGLE : on LIT le markdown ici, une fois, avec `marked` ; chaque porte RÉCRIT ces blocs à
// sa façon. Ce qui est partagé, c'est la compréhension du texte ; ce qui reste propre à chacun,
// c'est la mise en page — une page Word et une page écran ne se fabriquent pas pareil.
//
// POURQUOI UNE BIBLIOTHÈQUE ET PAS VINGT LIGNES À NOUS. Convertir du markdown est un problème
// résolu depuis quinze ans. Le nôtre ne serait testé que sur les cas auxquels on pense ; `marked`
// a rencontré les autres — cellule contenant une barre verticale, tableau sans séparateur, bloc
// de code non refermé. La dépendance est enfermée ICI : `marked` n'est importé nulle part
// ailleurs, et le jour où il faudrait en changer, c'est ce fichier seul qui bouge.

import { marked } from 'marked'

// `breaks: true` — DÉLIBÉRÉ, et ce n'est pas le défaut de markdown. En markdown strict, deux
// lignes qui se suivent forment un seul paragraphe : il faut une ligne vide pour en changer.
// Nos activités sont écrites (par l'IA comme à la main) avec des retours à la ligne simples qui
// veulent dire « à la ligne ». L'ancien formateur les respectait ; sans cette option, la mise en
// forme se serait resserrée du jour au lendemain sur tout l'existant.
// `gfm: true` — c'est ce qui apporte les tableaux `|` : ils ne font pas partie du markdown d'origine.
marked.use({ gfm: true, breaks: true })

// Le texte → la liste de ses blocs, dans l'ordre. Chaque bloc porte son `type` :
//   heading (avec depth 1-6) · paragraph · list (ordered, items) · table (header, rows, align)
//   code (text, lang) · blockquote (tokens) · hr · space
// Les blocs qui contiennent du texte enrichi portent leurs `tokens` — voir `morceaux()`.
export function lireBlocs(texte) {
  return marked.lexer(String(texte || '').replace(/\r\n/g, '\n'))
}

// Le markdown → le HTML, pour les portes qui en veulent (aperçu écran, impression).
// Le nettoyage NE se fait PAS ici : il appartient à celui qui injecte dans la page (apercuHtml.js).
export function versHtml(texte) {
  return marked.parse(String(texte || '').replace(/\r\n/g, '\n'))
}

// Le texte enrichi d'un bloc → des morceaux plats, pour les portes qui ne savent pas imbriquer
// (Word et PDF placent des bouts de texte, ils ne comprennent pas un arbre).
// Rend : [{ texte, gras, italique, code }] — un morceau par changement de style.
export function morceaux(tokens, herite = { gras: false, italique: false, code: false }) {
  const out = []
  for (const t of tokens || []) {
    if (t.type === 'strong')      { out.push(...morceaux(t.tokens, { ...herite, gras: true })); continue }
    if (t.type === 'em')          { out.push(...morceaux(t.tokens, { ...herite, italique: true })); continue }
    if (t.type === 'codespan')    { out.push({ texte: t.text, ...herite, code: true }); continue }
    if (t.type === 'br')          { out.push({ texte: '\n', ...herite }); continue }
    if (t.type === 'link')        { out.push(...morceaux(t.tokens, herite)); continue }
    if (t.type === 'del')         { out.push(...morceaux(t.tokens, herite)); continue }
    if (t.tokens && t.tokens.length) { out.push(...morceaux(t.tokens, herite)); continue }
    if (t.text != null)           { out.push({ texte: t.text, ...herite }) }
  }
  return out
}

// Le texte NU d'un bloc ou d'une cellule (sans aucun style) — le PDF mesure des chaînes, pas des styles.
export function texteNu(tokens) {
  return morceaux(tokens).map(m => m.texte).join('')
}
