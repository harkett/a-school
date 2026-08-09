// Export PDF d'un résultat — LA porte PDF, à côté de la porte HTML (apercuHtml.js) et de la
// porte Word (exportWord.js). Les trois lisent le même markdown, lu une seule fois par
// utils/markdown.js ; chacune le récrit dans SA langue.
//
// C'EST LA PLUS INGRATE DES TROIS, et ce n'est pas un défaut de conception : un PDF n'a ni
// paragraphes ni tableaux, seulement des traits et du texte posés à des coordonnées. Tout ce
// qu'un navigateur fait tout seul — passer à la ligne, calculer la largeur d'une colonne, ne pas
// couper une ligne de tableau en deux pages — est écrit ici, à la main. Avant le 07/08/2026, le
// PDF ne faisait rien de tout cela : il recopiait le texte ligne à ligne, `#` et barres comprises.
//
// LES DEUX FONCTIONS PURES (`largeurColonnes`, `decouperMorceaux`) sont ce que les tests
// interrogent : le reste ne peut s'observer qu'en ouvrant un PDF, ces deux-là portent les
// calculs qui se trompent.

import { lireBlocs, morceaux, texteNu } from './markdown.js'
import { PIED_ASCHOOL } from './pied.js'
import { estModeDemo, MENTION_DEMO } from './modeDemo.js'

const MARGE_X = 56, MARGE_HAUT = 56, MARGE_BAS = 52
const TAILLE_TEXTE = 11
const INTERLIGNE = 16
const TAILLES_TITRE = [17, 14.5, 12.5, 11.5, 11, 11]
const PAD_CELLULE = 5
const TAILLE_TABLEAU = 9.5

// ── Calculs purs ────────────────────────────────────────────────────────────────────────────

// Les largeurs des colonnes d'un tableau. `mesurer(texte, gras)` rend la largeur du texte dans la
// police courante — le PDF n'a pas de moteur de mise en page, c'est à nous de répartir.
// RÈGLE : chaque colonne demande la largeur de sa cellule la plus longue ; si la somme dépasse la
// place disponible, on RÉDUIT au prorata de ce qui dépasse, et jamais en dessous d'un plancher —
// sans lui, une colonne « Points » de trois caractères se retrouverait à deux pixels à côté d'une
// colonne « Critère » bavarde, et son contenu se casserait lettre par lettre.
export function largeurColonnes(entetes, lignes, largeurDispo, mesurer) {
  const n = entetes.length
  if (!n) return []
  const demandes = entetes.map((e, i) => {
    let max = mesurer(e, true)
    for (const ligne of lignes) max = Math.max(max, mesurer(ligne[i] ?? '', false))
    return max + PAD_CELLULE * 2
  })
  const total = demandes.reduce((a, b) => a + b, 0)
  if (total <= largeurDispo) {
    // On étale sur toute la largeur : un tableau étroit collé à gauche fait bâclé.
    const rab = (largeurDispo - total) / n
    return demandes.map(d => d + rab)
  }
  // Réduction au prorata, PUIS remontée des colonnes écrasées — et on recommence, parce que
  // remonter l'une reprend de la place aux autres. Le plancher d'une colonne est le plus petit
  // de : le minimum lisible, sa part égale, et ce qu'elle demandait (inutile d'élargir une
  // colonne « 4 » à 48 points).
  const plancher = i => Math.min(48, largeurDispo / n, demandes[i])
  const largeurs = demandes.slice()
  const fixes = demandes.map(() => false)
  for (let tour = 0; tour < n + 1; tour++) {
    const placeFixe = largeurs.reduce((s, l, i) => s + (fixes[i] ? l : 0), 0)
    const aRepartir = largeurDispo - placeFixe
    const totalSouple = demandes.reduce((s, d, i) => s + (fixes[i] ? 0 : d), 0)
    if (totalSouple <= 0) break
    let ecrasee = -1
    demandes.forEach((d, i) => {
      if (fixes[i]) return
      largeurs[i] = (d / totalSouple) * aRepartir
      if (largeurs[i] < plancher(i) && ecrasee < 0) ecrasee = i
    })
    if (ecrasee < 0) break
    largeurs[ecrasee] = plancher(ecrasee)
    fixes[ecrasee] = true
  }
  return largeurs
}

// Des morceaux stylés → des lignes de morceaux qui tiennent dans `largeur`.
// Le découpage se fait mot à mot en gardant le style de chaque morceau : c'est ce qui permet à
// « **Objectif :** ce que les élèves construisent » de rester gras au bon endroit même quand la
// phrase passe à la ligne. `mesurer(texte, gras, italique)` rend une largeur.
export function decouperMorceaux(liste, largeur, mesurer) {
  const lignes = [[]]
  let restant = largeur
  const nouvelleLigne = () => { lignes.push([]); restant = largeur }
  for (const m of liste) {
    for (const [iBout, bout] of String(m.texte).split('\n').entries()) {
      if (iBout > 0) nouvelleLigne()
      const mots = bout.split(/(\s+)/).filter(x => x !== '')
      for (const mot of mots) {
        const l = mesurer(mot, m.gras, m.italique)
        if (l > restant && lignes[lignes.length - 1].length) {
          if (/^\s+$/.test(mot)) { nouvelleLigne(); continue }
          nouvelleLigne()
        }
        if (/^\s+$/.test(mot) && !lignes[lignes.length - 1].length) continue   // pas d'espace en début de ligne
        lignes[lignes.length - 1].push({ ...m, texte: mot, largeur: l })
        restant -= l
      }
    }
  }
  return lignes.filter((l, i) => l.length || i === 0)
}

// Le texte tel que la police du PDF sait l'écrire.
//
// POURQUOI CETTE FONCTION EXISTE. Les polices standard de jsPDF (helvetica, courier) ne
// connaissent que le jeu WinAnsi — grosso modo l'alphabet latin occidental. Tout ce qui sort de
// là n'est pas signalé : il est écrit DE TRAVERS. Au contrôle du 07/08/2026, « Oui ! → je lève
// 128 » s'imprimait « Oui !' je lève 128 » et « −67 dBm » devenait « " 6 7dBm ». On ne peut pas
// laisser un devoir partir comme ça.
//
// LE CHOIX : transcrire plutôt qu'embarquer une police Unicode complète (+300 Ko sur chaque
// chargement de l'appli, pour quelques flèches). Ce qui n'est ni transcrit ni représentable
// devient « ? » — visible, donc corrigeable, au lieu d'un caractère faux qui passe inaperçu.
// L'aperçu écran et l'export Word, eux, gardent l'Unicode entier : ils n'ont pas cette limite.
const TRANSCRIPTIONS = {
  '→': '->', '←': '<-', '↔': '<->', '⇒': '=>', '⇐': '<=', '⇔': '<=>',
  '−': '-', '≥': '>=', '≤': '<=', '≠': '!=', '≈': '~', '∞': 'infini',
  '√': 'racine de ', '±': '+/-', '✓': '[x]', '✔': '[x]', '✗': '[ ]',
  '✘': '[ ]', '☐': '[ ]', '☑': '[x]', '■': '-', '●': '-', '▶': '>',
  '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5',
  '₆': '6', '₇': '7', '₈': '8', '₉': '9',
  '⁴': '^4', '⁵': '^5', '⁶': '^6', '⁷': '^7', '⁸': '^8', '⁹': '^9',
  '⁻': '-', '⁄': '/',
  // Espaces « spéciaux » (fine, fine insécable) : invisibles à l'œil, faux à l'impression.
  ' ': ' ', ' ': ' ',
}
// Les caractères de la plage 0x80-0x9F que WinAnsi connaît malgré leur code Unicode élevé.
const WINANSI_HAUT = '€‚ƒ„…†‡ˆ‰Š‹ŒŽ'
  + '‘’“”•–—˜™š›œžŸ'

export function pourPdf(texte) {
  let out = ''
  for (const ch of String(texte ?? '')) {
    if (TRANSCRIPTIONS[ch] !== undefined) { out += TRANSCRIPTIONS[ch]; continue }
    const code = ch.codePointAt(0)
    if (code <= 0xFF || WINANSI_HAUT.includes(ch)) { out += ch; continue }
    out += '?'
  }
  return out
}

// ── Composition ─────────────────────────────────────────────────────────────────────────────

// Le composeur tient le curseur vertical et sait tourner la page. Tout le rendu passe par lui :
// c'est le seul endroit qui décide qu'on descend, et le seul qui décide qu'on change de feuille.
function composeur(doc) {
  const largeurPage = doc.internal.pageSize.getWidth()
  const hauteurPage = doc.internal.pageSize.getHeight()
  const c = {
    doc, largeurPage, hauteurPage,
    // x0 : la marge gauche COURANTE. Elle bouge quand un bloc décale son contenu (citation) ;
    // sans elle, le trait de la citation était dessiné PAR-DESSUS la première lettre du texte.
    x0: MARGE_X,
    largeur: largeurPage - MARGE_X * 2,
    y: MARGE_HAUT,
    police(taille, gras, italique, mono) {
      doc.setFont(mono ? 'courier' : 'helvetica', gras && italique ? 'bolditalic' : gras ? 'bold' : italique ? 'italic' : 'normal')
      doc.setFontSize(taille)
    },
    mesurer(texte, taille, gras, italique, mono) {
      c.police(taille, gras, italique, mono)
      return doc.getTextWidth(texte)
    },
    place(hauteur) { return c.y + hauteur <= c.hauteurPage - MARGE_BAS },
    sautSiBesoin(hauteur) { if (!c.place(hauteur)) { doc.addPage(); c.y = MARGE_HAUT } },
    espace(h) { c.y += h },
  }
  return c
}

function poserLignes(c, liste, x, largeur, taille, interligne, couleur) {
  const lignes = decouperMorceaux(liste, largeur, (t, g, i) => c.mesurer(t, taille, g, i))
  for (const ligne of lignes) {
    c.sautSiBesoin(interligne)
    let px = x
    for (const m of ligne) {
      c.police(taille, m.gras, m.italique, m.code)
      c.doc.setTextColor(couleur ?? 30)
      c.doc.text(m.texte, px, c.y)
      px += m.largeur ?? c.doc.getTextWidth(m.texte)
    }
    c.y += interligne
  }
  c.doc.setTextColor(30)
  return lignes.length
}

function poserTableau(c, bloc) {
  const entetes = bloc.header.map(h => texteNu(h.tokens))
  const lignes = bloc.rows.map(r => r.map(cel => texteNu(cel.tokens)))
  const largeurs = largeurColonnes(entetes, lignes, c.largeur, (t, gras) => c.mesurer(t, TAILLE_TABLEAU, gras))
  const interligne = TAILLE_TABLEAU + 3.5

  // Une ligne du tableau : on découpe d'abord toutes ses cellules pour connaître sa hauteur,
  // puis on dessine le cadre, puis le texte. L'ordre compte — le fond effacerait le texte.
  const dessinerLigne = (cellules, entete) => {
    const decoupes = cellules.map((txt, i) => {
      c.police(TAILLE_TABLEAU, entete)
      return c.doc.splitTextToSize(String(txt), largeurs[i] - PAD_CELLULE * 2)
    })
    const hauteur = Math.max(...decoupes.map(d => d.length)) * interligne + PAD_CELLULE * 2
    c.sautSiBesoin(hauteur)
    let x = c.x0
    decoupes.forEach((lignesCel, i) => {
      if (entete) { c.doc.setFillColor(241, 245, 249); c.doc.rect(x, c.y, largeurs[i], hauteur, 'F') }
      c.doc.setDrawColor(203, 213, 225)
      c.doc.rect(x, c.y, largeurs[i], hauteur)
      c.police(TAILLE_TABLEAU, entete)
      c.doc.setTextColor(entete ? 15 : 40)
      lignesCel.forEach((ligne, j) => {
        c.doc.text(ligne, x + PAD_CELLULE, c.y + PAD_CELLULE + interligne * (j + 0.75))
      })
      x += largeurs[i]
    })
    c.doc.setTextColor(30)
    c.y += hauteur
  }

  c.sautSiBesoin(60)                     // ne pas laisser un en-tête de tableau seul en bas de page
  dessinerLigne(entetes, true)
  const pageDebut = c.doc.internal.getCurrentPageInfo().pageNumber
  for (const ligne of lignes) {
    const avant = c.doc.internal.getCurrentPageInfo().pageNumber
    const yAvant = c.y
    dessinerLigne(ligne, false)
    // Si la ligne a provoqué un saut, l'en-tête est resté sur la page d'avant : on le redonne.
    if (c.doc.internal.getCurrentPageInfo().pageNumber > avant && avant >= pageDebut && yAvant > MARGE_HAUT) {
      const yLigne = c.y
      c.y = MARGE_HAUT
      dessinerLigne(entetes, true)
      const decalage = c.y - MARGE_HAUT
      c.y = yLigne + decalage
    }
  }
  c.espace(8)
}

function poserBloc(c, bloc, compteur) {
  switch (bloc.type) {
    case 'heading': {
      const taille = TAILLES_TITRE[Math.min(bloc.depth, 6) - 1]
      c.espace(bloc.depth <= 2 ? 10 : 6)
      c.sautSiBesoin(taille + 8)
      poserLignes(c, morceaux(bloc.tokens).map(m => ({ ...m, gras: true })), c.x0, c.largeur, taille, taille + 5, 15)
      c.espace(3)
      break
    }
    case 'paragraph':
    case 'text':
      poserLignes(c, morceaux(bloc.tokens || [bloc]), c.x0, c.largeur, TAILLE_TEXTE, INTERLIGNE)
      c.espace(4)
      break
    case 'list': {
      let n = bloc.start || 1
      for (const item of bloc.items) {
        const puce = bloc.ordered ? `${n++}.` : '•'
        c.sautSiBesoin(INTERLIGNE)
        c.police(TAILLE_TEXTE, false)
        c.doc.text(puce, c.x0 + 6, c.y)
        poserLignes(c, morceaux(item.tokens), c.x0 + 24, c.largeur - 24, TAILLE_TEXTE, INTERLIGNE)
      }
      c.espace(4)
      break
    }
    case 'table':
      c.espace(4)
      poserTableau(c, bloc)
      break
    case 'code': {
      const lignes = String(bloc.text || '').split('\n')
      const interligne = 13
      c.espace(4)
      for (const ligne of lignes) {
        c.sautSiBesoin(interligne)
        c.doc.setFillColor(248, 250, 252)
        c.doc.rect(c.x0, c.y - interligne + 4, c.largeur, interligne, 'F')
        c.police(9.5, false, false, true)
        c.doc.setTextColor(51)
        c.doc.text(c.doc.splitTextToSize(ligne || ' ', c.largeur - 12)[0] ?? ' ', c.x0 + 6, c.y)
        c.y += interligne
      }
      c.doc.setTextColor(30)
      c.espace(6)
      break
    }
    case 'blockquote': {
      // Le contenu RECULE de 16 points ; le trait occupe la place ainsi libérée. Sans ce décalage,
      // le trait mangeait la première lettre de chaque ligne citée (constaté au contrôle du 07/08).
      const yDebut = c.y
      const x0 = c.x0, largeur = c.largeur
      c.x0 = x0 + 16
      c.largeur = largeur - 16
      for (const interne of bloc.tokens) poserBloc(c, interne, compteur)
      c.x0 = x0
      c.largeur = largeur
      c.doc.setDrawColor(203, 213, 225)
      c.doc.setLineWidth(2)
      if (c.y > yDebut) c.doc.line(x0 + 3, yDebut - INTERLIGNE + 4, x0 + 3, c.y - INTERLIGNE + 4)
      c.doc.setLineWidth(0.2)
      break
    }
    case 'hr':
      c.sautSiBesoin(18)
      c.espace(6)
      c.doc.setDrawColor(203, 213, 225)
      c.doc.line(c.x0, c.y, c.largeurPage - MARGE_X, c.y)
      c.espace(12)
      break
    case 'space':
      c.espace(4)
      break
    default:
      if (bloc.raw && bloc.raw.trim()) poserLignes(c, [{ texte: bloc.raw.trim() }], c.x0, c.largeur, TAILLE_TEXTE, INTERLIGNE)
  }
}

// Le markdown posé dans un document jsPDF déjà ouvert — SÉPARÉE du téléchargement pour qu'un
// test puisse composer un vrai document (tableaux, sauts de page compris) sans navigateur.
// Rend le nombre de pages écrites.
// Le filigrane d'une page : le mot en diagonale, en gris pâle, DERRIÈRE le texte déjà posé.
// Il s'écrit à la fin, page par page — jsPDF n'a pas de couche de fond, alors on l'écrit
// par-dessus en très clair, ce qui revient au même à l'œil sans effacer une seule lettre.
export function filigranePdf(doc, mot = MENTION_DEMO) {
  const L = doc.internal.pageSize.getWidth()
  const H = doc.internal.pageSize.getHeight()
  const nb = doc.internal.getNumberOfPages()
  for (let p = 1; p <= nb; p++) {
    doc.setPage(p)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(58)
    doc.setTextColor(124, 58, 237)
    // TRANSPARENCE plutôt qu'une couleur pâle : au premier essai, le mot en violet clair
    // effaçait le contenu des cellules qu'il traversait. Ici il s'imprime À 9 %, le texte
    // reste net dessous. `setGState` n'existe pas dans toutes les versions de jsPDF : sans lui,
    // on retombe sur une couleur très claire, qui marque moins mais n'abîme rien.
    if (typeof doc.setGState === 'function' && doc.GState) {
      doc.setGState(new doc.GState({ opacity: 0.09 }))
    } else {
      doc.setTextColor(233, 228, 252)
    }
    doc.text(mot, L / 2, H / 2, { align: 'center', angle: 26, baseline: 'middle' })
    if (typeof doc.setGState === 'function' && doc.GState) {
      doc.setGState(new doc.GState({ opacity: 1 }))
    }
  }
  doc.setTextColor(30)
}

export function composerDocument(doc, texte) {
  const c = composeur(doc)
  const compteur = { n: 0 }
  // La transcription se fait ICI, sur le texte entier, AVANT la lecture des blocs : mesures et
  // dessin voient alors exactement la même chaîne. La faire au moment d'écrire donnerait des
  // largeurs calculées sur un texte et un rendu sur un autre.
  for (const bloc of lireBlocs(pourPdf(texte))) poserBloc(c, bloc, compteur)
  return doc.internal.getNumberOfPages()
}

export async function telechargerPdf(texte, nomFichier) {
  // jsPDF chargé À LA DEMANDE (import dynamique) : son poids (~700 Ko) ne pèse que sur le clic
  // PDF, pas au démarrage de l'appli.
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF({ unit: 'pt', format: 'a4' })
  const nbPages = composerDocument(doc, texte)
  // Sortie d'une démonstration : la marque part avec le document. Un devoir d'essai qui circule
  // sans elle est indiscernable d'un vrai — c'est justement ce qu'on veut éviter.
  if (estModeDemo()) filigranePdf(doc)

  // Le pied obligatoire, sur CHAQUE page — il ne se pose qu'à la fin, quand on sait combien il y en a.
  const largeurPage = doc.internal.pageSize.getWidth()
  const hauteurPage = doc.internal.pageSize.getHeight()
  for (let p = 1; p <= nbPages; p++) {
    doc.setPage(p)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.setTextColor(153)
    doc.text(PIED_ASCHOOL, largeurPage / 2, hauteurPage - 24, { align: 'center' })
  }
  doc.save(nomFichier || `activite_${new Date().toISOString().slice(0, 10)}.pdf`)
}
