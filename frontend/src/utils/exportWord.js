// Export Word (.docx) d'un résultat — LA porte Word, à côté de la porte HTML (apercuHtml.js)
// et de la porte PDF (exportPdf.js). Les trois lisent le même markdown, lu une seule fois par
// utils/markdown.js ; chacune le récrit dans SA langue. Word ne comprend pas le HTML : il veut
// des objets `Paragraph`, `TextRun` et `Table` — c'est pour ça qu'il a son fichier.
//
// CE QU'IL FAISAIT AVANT LE 07/08/2026 : une ligne de texte par ligne du fichier, sans rien
// interpréter. Les `#`, les `**` et les barres verticales des tableaux partaient tels quels dans
// le document — le prof recevait un .docx qui ressemblait à un fichier brut.

import {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, Header,
} from 'docx'
import { lireBlocs, morceaux } from './markdown.js'
import { PIED_ASCHOOL } from './pied.js'
import { estModeDemo, MENTION_DEMO, PHRASE_DEMO } from './modeDemo.js'

const MONOSPACE = 'Consolas'
const GRIS_CADRE = 'CBD5E1'
const GRIS_FOND  = 'F1F5F9'

// La numérotation des listes ordonnées se DÉCLARE au niveau du document (Word ne sait pas
// numéroter tout seul un paragraphe isolé) ; chaque liste rencontrée reçoit sa propre instance
// pour que la seconde reparte de 1 au lieu de continuer la première.
const REF_NUMEROTATION = 'aschool-ol'
const CONFIG_NUMEROTATION = {
  config: [{
    reference: REF_NUMEROTATION,
    levels: [{
      level: 0, format: 'decimal', text: '%1.', alignment: AlignmentType.START,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } },
    }],
  }],
}

const NIVEAUX_TITRE = [
  HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3,
  HeadingLevel.HEADING_4, HeadingLevel.HEADING_5, HeadingLevel.HEADING_6,
]

// Les morceaux d'un texte enrichi → des `TextRun` Word. Un morceau qui contient un retour à la
// ligne le rend explicitement (`break`) : sans ça, Word colle les deux lignes bout à bout.
function runs(tokens, options = {}) {
  const out = []
  for (const m of morceaux(tokens)) {
    const parts = String(m.texte).split('\n')
    parts.forEach((part, i) => {
      out.push(new TextRun({
        text: part,
        bold: m.gras || options.gras || undefined,
        italics: m.italique || options.italique || undefined,
        font: m.code ? MONOSPACE : undefined,
        color: options.couleur,
        break: i > 0 ? 1 : undefined,
      }))
    })
  }
  return out.length ? out : [new TextRun('')]
}

function cellule(cel, entete) {
  return new TableCell({
    shading: entete ? { type: ShadingType.CLEAR, fill: GRIS_FOND } : undefined,
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    children: [new Paragraph({ children: runs(cel.tokens, { gras: entete }) })],
  })
}

function tableau(bloc) {
  const bordure = { style: BorderStyle.SINGLE, size: 4, color: GRIS_CADRE }
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: { top: bordure, bottom: bordure, left: bordure, right: bordure,
               insideHorizontal: bordure, insideVertical: bordure },
    rows: [
      new TableRow({ tableHeader: true, children: bloc.header.map(c => cellule(c, true)) }),
      ...bloc.rows.map(ligne => new TableRow({ children: ligne.map(c => cellule(c, false)) })),
    ],
  })
}

// Un bloc de code : une ligne = un paragraphe monospace sur fond gris. Word n'a pas de « bloc de
// code » ; c'est cette mise en forme qui le donne à voir.
function codeParagraphes(bloc) {
  return String(bloc.text || '').split('\n').map(ligne => new Paragraph({
    shading: { type: ShadingType.CLEAR, fill: 'F8FAFC' },
    spacing: { before: 0, after: 0 },
    children: [new TextRun({ text: ligne || ' ', font: MONOSPACE, size: 19 })],
  }))
}

// Les blocs du markdown → les éléments d'un document Word. Fonction PURE : c'est elle que les
// tests interrogent, sans jamais fabriquer de fichier.
export function elementsDocx(texte, compteurListe = { n: 0 }) {
  const out = []
  for (const bloc of lireBlocs(texte)) {
    switch (bloc.type) {
      case 'heading':
        out.push(new Paragraph({ heading: NIVEAUX_TITRE[Math.min(bloc.depth, 6) - 1], children: runs(bloc.tokens) }))
        break
      case 'paragraph':
        out.push(new Paragraph({ children: runs(bloc.tokens) }))
        break
      case 'text':
        out.push(new Paragraph({ children: runs(bloc.tokens || [bloc]) }))
        break
      case 'list': {
        const instance = bloc.ordered ? compteurListe.n++ : undefined
        for (const item of bloc.items) {
          out.push(new Paragraph({
            children: runs(item.tokens),
            bullet: bloc.ordered ? undefined : { level: 0 },
            numbering: bloc.ordered ? { reference: REF_NUMEROTATION, level: 0, instance } : undefined,
          }))
        }
        break
      }
      case 'table':
        out.push(tableau(bloc))
        out.push(new Paragraph({ children: [] }))   // Word colle deux tableaux qui se suivent
        break
      case 'code':
        out.push(...codeParagraphes(bloc))
        break
      case 'blockquote':
        out.push(new Paragraph({
          indent: { left: 480 },
          border: { left: { style: BorderStyle.SINGLE, size: 12, color: GRIS_CADRE, space: 8 } },
          children: runs(bloc.tokens, { italique: true, couleur: '475569' }),
        }))
        break
      case 'hr':
        out.push(new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: GRIS_CADRE, space: 1 } },
          children: [],
        }))
        break
      case 'space':
        break
      default:
        // Tout bloc inconnu ressort en texte plutôt que de disparaître silencieusement.
        if (bloc.raw && bloc.raw.trim()) out.push(new Paragraph({ children: [new TextRun(bloc.raw.trim())] }))
    }
  }
  return out
}

// La signature obligatoire de toute sortie aSchool, en gris discret.
function pied() {
  return new Paragraph({
    spacing: { before: 400 },
    children: [new TextRun({ text: PIED_ASCHOOL, color: '999999', size: 16 })],
  })
}

// La marque d'une sortie de démonstration : un en-tête RÉPÉTÉ SUR CHAQUE PAGE.
//
// POURQUOI UN EN-TÊTE ET PAS UN VRAI FILIGRANE EN DIAGONALE. Word ne sait dessiner un filigrane
// que par un objet de dessin hérité (VML), qu'il faut écrire à la main dans le XML du document
// et que `docx` n'expose pas. Le fabriquer nous-mêmes rendrait un fichier fragile, que certaines
// versions de Word ouvrent mal. L'en-tête, lui, est du format standard : il apparaît en haut de
// chaque page, à l'écran comme au papier, et il ne peut pas être perdu en recopiant le texte.
function enteteDemo() {
  return new Header({
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: MENTION_DEMO, bold: true, color: '7C3AED', size: 32 })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: PHRASE_DEMO, color: '8B5CF6', size: 15 })],
      }),
    ],
  })
}

export async function telechargerWord(texte, nomFichier) {
  const demo = estModeDemo()
  const doc = new Document({
    numbering: CONFIG_NUMEROTATION,
    sections: [{
      properties: {},
      headers: demo ? { default: enteteDemo() } : undefined,
      children: [...elementsDocx(texte), pied()],
    }],
  })
  const blob = await Packer.toBlob(doc)
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = nomFichier || `activite_${new Date().toISOString().slice(0, 10)}.docx`
  a.click()
}
