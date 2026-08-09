// Aperçu « HTML » d'une activité ou d'une séance : markdown → HTML + impression mise en forme.
// PARTAGÉ (zéro copie) entre le résultat de « Créer une activité » (ZoneResultat), l'écran Séance
// et les deux listes de l'Historique — un seul rendu, une seule impression, aucune divergence.
//
// LA LECTURE DU MARKDOWN N'EST PAS ICI : elle est dans utils/markdown.js, faite une seule fois
// pour toutes les sorties (écran, impression, Word, PDF). Ce fichier ne fait que la porte HTML.
// Avant le 07/08/2026, il portait ses propres règles écrites à la main : il ignorait les tableaux,
// les blocs de code et les citations, qui sortaient en barres verticales et en chevrons — dans
// l'aperçu comme sur le papier.
//
// LE HTML EST NETTOYÉ AVANT D'ÊTRE INJECTÉ. Le texte vient d'un fournisseur d'IA ou de ce que le
// prof a collé : il peut contenir du HTML, et `marked` le laisse passer (c'est son rôle, pas de
// juger). `DOMPurify` retire tout ce qui pourrait s'exécuter — balises de script, attributs
// d'événement, adresses `javascript:` — et rend un fragment sûr pour dangerouslySetInnerHTML.

import DOMPurify from 'dompurify'
import { PIED_ASCHOOL, piedHtml } from './pied.js'
import { versHtml } from './markdown.js'
import { estModeDemo, PHRASE_DEMO, TUILE_DEMO } from './modeDemo.js'

// Les styles de la mise en forme, en UN SEUL endroit — ils habillent l'aperçu à l'écran (via la
// classe .apercu-corps, définie dans index.css) ET la page d'impression (ci-dessous). Un tableau
// sans bordures ni cellules espacées reste illisible : rendre la balise ne suffit pas.
const STYLE_IMPRESSION = `
  @page{margin:18mm}
  body{font-family:Arial,Helvetica,sans-serif;color:#1e293b;line-height:1.7;font-size:13px;margin:0}
  h1,h2,h3,h4,h5,h6{color:#0f172a;line-height:1.3;margin:1.3em 0 .35em;page-break-after:avoid}
  h1{font-size:1.5rem}h2{font-size:1.25rem}h3{font-size:1.08rem}
  h4{font-size:1rem}h5,h6{font-size:.95rem}
  p{margin:.55em 0}
  ul,ol{margin:.55em 0 .55em 1.4em;padding:0}li{margin:.28em 0}
  hr{border:none;border-top:1px solid #cbd5e1;margin:1.3em 0}
  strong{color:#0f172a}
  table{border-collapse:collapse;width:100%;margin:.9em 0;font-size:12px;page-break-inside:avoid}
  th,td{border:1px solid #cbd5e1;padding:5px 8px;text-align:left;vertical-align:top}
  th{background:#f1f5f9;color:#0f172a;font-weight:700}
  pre{background:#f8fafc;border:1px solid #e2e8f0;border-radius:4px;padding:9px 11px;margin:.9em 0;
      white-space:pre-wrap;word-break:break-word;font-family:Consolas,Monaco,monospace;font-size:11.5px}
  code{font-family:Consolas,Monaco,monospace;font-size:.92em;background:#f1f5f9;padding:1px 4px;border-radius:3px}
  pre code{background:none;padding:0}
  blockquote{margin:.9em 0;padding:.2em 0 .2em .9em;border-left:3px solid #cbd5e1;color:#475569;font-style:italic}
`

// Le markdown → du HTML SÛR. Le nettoyage est fait ici, une fois, pour tous les appelants.
//
// PAS DE REPLI SILENCIEUX. `DOMPurify` a besoin d'un vrai navigateur (il s'appuie sur le DOM) :
// hors navigateur, il n'expose même pas `sanitize`. Rendre le HTML non filtré « en attendant »
// serait une faille invisible — on refuse bruyamment. En production ce chemin n'existe pas :
// cette fonction n'est appelée que depuis un écran ouvert.
export function corpsHtml(texte) {
  if (!DOMPurify.isSupported) {
    throw new Error("corpsHtml exige un navigateur : DOMPurify ne peut pas nettoyer le HTML sans DOM.")
  }
  return DOMPurify.sanitize(versHtml(texte))
}

// Impression de l'APERÇU mis en forme : le HTML formaté est écrit dans une iframe cachée avec une
// feuille de style d'impression, puis l'impression est lancée DEPUIS cette iframe — le prof reste
// sur aSchool (aucun nouvel onglet) et c'est la mise en forme qui part à l'imprimante, pas le brut.
export function imprimerApercu(corps) {
  const iframe = document.createElement('iframe')
  iframe.setAttribute('aria-hidden', 'true')
  iframe.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0'
  document.body.appendChild(iframe)
  const doc = iframe.contentWindow.document
  doc.open()
  // FILIGRANE — la feuille sortie d'une démonstration doit se reconnaître à l'œil, comme l'écran.
  // Posé sur le `body` en image répétée ET demandé à l'impression (`print-color-adjust`), sans
  // quoi la plupart des navigateurs suppriment les fonds pour économiser l'encre : la page
  // partirait blanche, et un devoir d'essai serait impossible à distinguer d'un vrai.
  const filigrane = estModeDemo() ? `
    body{background-image:url("data:image/svg+xml,${TUILE_DEMO}");background-repeat:repeat;
         -webkit-print-color-adjust:exact;print-color-adjust:exact}
    .mention-demo{margin:0 0 14px;padding:6px 10px;border:1px solid #ddd6fe;border-radius:4px;
                  background:#f5f3ff;color:#5b21b6;font-size:11px;font-weight:700;text-align:center}
  ` : ''
  const mention = estModeDemo()
    ? `<p class="mention-demo">${PHRASE_DEMO}</p>` : ''
  doc.write(`<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Activité aSchool</title>
    <style>${STYLE_IMPRESSION}${filigrane}</style></head>
    <body>${mention}${corps}${piedHtml()}</body></html>`)
  doc.close()
  const win = iframe.contentWindow
  const nettoyer = () => setTimeout(() => {
    try { document.body.removeChild(iframe) } catch { /* déjà retiré (double appel onafterprint + filet) : rien à faire */ }
  }, 500)
  win.onafterprint = nettoyer
  win.focus()
  win.print()
  setTimeout(nettoyer, 60000)   // filet de sécurité si onafterprint ne se déclenche pas
}

// Le corps d'un document AVEC sa signature — c'est cette forme-là qui s'affiche dans l'aperçu et
// qui part à l'imprimante. `corpsHtml` seul reste disponible pour les usages qui ne sortent pas.
export function documentHtml(texte) {
  return corpsHtml(texte) + piedHtml()
}

export { PIED_ASCHOOL }
