// Aperçu « HTML » d'une activité : formateur texte brut → HTML + impression de l'aperçu mis en forme.
// PARTAGÉ (zéro copie) entre le résultat de « Créer une activité » (ZoneResultat) et le détail de
// l'Historique (MesActivites) — un seul formateur, une seule impression, aucune divergence possible.
//
// Le corps produit est du HTML SÛR : texte échappé + nos seules balises (h1-3, strong/em, ul/ol/li,
// p, hr), donc injectable via dangerouslySetInnerHTML sans risque.

function echapperHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function enligne(s) {
  // gras puis italique, sur du texte DÉJÀ échappé (les astérisques ne sont pas échappés)
  return s
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>')
}

// Texte brut → HTML propre : titres #, gras **, italique *, listes numérotées / à puces, séparateurs.
export function corpsHtml(texte) {
  const lignes = String(texte || '').replace(/\r\n/g, '\n').split('\n')
  const out = []
  let liste = null   // 'ul' | 'ol' | null : liste en cours d'ouverture
  const fermer = () => { if (liste) { out.push(`</${liste}>`); liste = null } }
  for (const brut of lignes) {
    const t = brut.trim()
    if (t === '') { fermer(); continue }
    if (/^-{3,}$/.test(t)) { fermer(); out.push('<hr>'); continue }
    let m
    if ((m = t.match(/^(#{1,3})\s+(.*)$/))) { fermer(); const n = m[1].length; out.push(`<h${n}>${enligne(echapperHtml(m[2]))}</h${n}>`); continue }
    if ((m = t.match(/^\d+[.)]\s+(.*)$/)))  { if (liste !== 'ol') { fermer(); out.push('<ol>'); liste = 'ol' } out.push(`<li>${enligne(echapperHtml(m[1]))}</li>`); continue }
    if ((m = t.match(/^[-*•]\s+(.*)$/)))    { if (liste !== 'ul') { fermer(); out.push('<ul>'); liste = 'ul' } out.push(`<li>${enligne(echapperHtml(m[1]))}</li>`); continue }
    fermer()
    out.push(`<p>${enligne(echapperHtml(t))}</p>`)
  }
  fermer()
  return out.join('\n')
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
  doc.write(`<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Activité aSchool</title>
    <style>
      @page{margin:18mm}
      body{font-family:Arial,Helvetica,sans-serif;color:#1e293b;line-height:1.7;font-size:13px;margin:0}
      h1,h2,h3{color:#0f172a;line-height:1.3;margin:1.3em 0 .35em}
      h1{font-size:1.5rem}h2{font-size:1.25rem}h3{font-size:1.08rem}
      p{margin:.55em 0}
      ul,ol{margin:.55em 0 .55em 1.4em;padding:0}li{margin:.28em 0}
      hr{border:none;border-top:1px solid #cbd5e1;margin:1.3em 0}
      strong{color:#0f172a}
      .pied-aschool{margin-top:2.5em;padding-top:8px;border-top:1px solid #e5e7eb;text-align:center;font-size:10px;color:#9ca3af}
    </style></head>
    <body>${corps}<div class="pied-aschool">Généré avec aSchool — aschool.fr</div></body></html>`)
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
