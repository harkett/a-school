// « Comment ça marche » des démonstrations — fenêtre destinée à L'ADMIN, et à personne d'autre.
//
// Elle répond aux trois questions de celui qui arrive sur l'écran Démos sans avoir fabriqué les
// démonstrations : qu'est-ce que c'est, qu'est-ce que CET écran commande, et que voit le prof à
// l'autre bout. Les trois blocs sont dans cet ordre parce que c'est l'ordre des questions.
//
// POURQUOI UNE FENÊTRE ET NON UN PANNEAU DÉPLIÉ DANS L'ÉCRAN. Une explication qui pousse le
// tableau vers le bas se lit une fois puis se referme ; une fenêtre se déplace, se garde ouverte
// à côté pendant qu'on remplit une fiche, s'imprime et s'emporte. Elle réutilise `FenetrePro`,
// la coquille unique de l'application — déplaçable par sa barre de titre, étirable par le coin.
//
// LE TEXTE N'EST ÉCRIT QU'UNE FOIS, dans `GUIDE`. Il sert à la fenêtre ET à la page HTML qu'on
// ouvre dans un onglet, et un balisage minimal (**gras**) évite d'injecter du HTML dans le JSX
// pour obtenir un mot en gras. L'impression n'a pas de bouton : elle se fait depuis l'onglet.
//
// Tout ce qui y est affirmé se vérifie dans le code : les statuts qui ouvrent la porte
// (`_STATUTS_VISITABLES`, backend/prof/demo.py), la durée du jeton (`_VALIDITE`), et la copie du
// contenu à l'entrée (`_copier_le_gabarit`). Si l'un des trois change, ce texte change avec.
import { useState } from 'react'
import FenetrePro from './FenetrePro.jsx'
import { imprimerApercu } from '../utils/apercuHtml.js'

// Le globe de l'aperçu mis en forme, et l'imprimante — les mêmes que dans Mes contenus.
const IconGlobe = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
  </svg>
)

const IconPrint = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
  </svg>
)

const SOUS_TITRE = 'Une démonstration est une base à part, avec sa propre instance. '
  + 'Cet écran tient sa fiche ; il ne l’ouvre jamais.'

const GUIDE = [
  { titre: 'Ce qu’est une démonstration', items: [
    'Une base PostgreSQL **séparée**, une par référentiel, avec son propre serveur et son propre écran. La base réelle n’est jamais touchée.',
    'Elle contient un référentiel déjà découpé et vectorisé — copié tel quel depuis le réel, sans rien recalculer — et un **compte modèle**, connexion coupée, qui porte le contenu d’exemple.',
    'Elle ne se fabrique pas depuis cet écran : la base se crée et se remplit à la main, puis on vient déclarer sa fiche ici.',
  ] },
  { titre: 'Côté admin — ce que cet écran commande', items: [
    'Il tient la **fiche**, jamais les données. Il n’ouvre aucune autre base : les compteurs se saisissent, ils ne se calculent pas.',
    'Cinq statuts, du vide au livrable : À faire → En cours → Fabriquée → Testée → Validée. **Seules « Testée » et « Validée » ouvrent la porte aux profs** — ce qui n’a pas été relu n’est proposé à personne.',
    'L’**adresse** branche la fiche sur son instance. Sans elle, l’entrée du menu prof reste grisée, même en statut Validée.',
    '**Visiter** ouvre n’importe quelle démonstration avec l’identité admin, quel que soit son couple et son statut. C’est par là qu’on la relit avant de la passer en « Testée ».',
    '**Retirer** efface la fiche, pas la base : celle-ci survit et se détruit à la main.',
  ] },
  { titre: 'Côté prof — ce qu’il voit', items: [
    'Une entrée **« Démonstration »** dans son menu, active seulement s’il existe une démonstration relue **pour son niveau**.',
    'Il part avec un jeton signé, valable **cinq minutes**, qui porte son identité : il arrive connecté, sans second mot de passe à retenir.',
    'À son arrivée, le contenu du compte modèle est **recopié à son nom**. Chacun a sa copie : ce qu’il modifie ou supprime ne touche ni le modèle ni les autres visiteurs.',
    'Le filigrane **DÉMONSTRATION** marque l’écran, l’impression, le Word et le PDF — une page sortie de là ne peut pas se confondre avec une vraie.',
    'Rien de ce qu’il y fait ne remonte dans la base réelle.',
  ] },
]

// **gras** → <b> à l'écran. Découpage sur les paires d'astérisques : les rangs impairs sont gras.
function gras(texte) {
  return texte.split('**').map((bout, i) => (
    i % 2 ? <b key={i} style={{ color: '#0f172a' }}>{bout}</b> : <span key={i}>{bout}</span>
  ))
}

// Le même texte pour la page ouverte en onglet : les trois blocs à la suite, jamais en colonnes
// — à l'impression, trois colonnes obligeraient à remonter deux fois en haut de page.
function guideEnHtml() {
  const enGras = t => t.split('**').map((x, i) => (i % 2 ? '<strong>' + x + '</strong>' : x)).join('')
  const bloc = b => '<h2>' + b.titre + '</h2><ul>'
    + b.items.map(t => '<li>' + enGras(t) + '</li>').join('')
    + '</ul>'
  return '<h1>Comment fonctionnent les démonstrations</h1><p>' + SOUS_TITRE + '</p>'
    + GUIDE.map(bloc).join('')
}

// Norme maison, valable pour les deux fenêtres : un bouton porte son icône et sa bulle d'aide,
// à hauteur fixe. Posé dans la barre de titre, donc sur le bleu : fond transparent, trait blanc.
const boutonBarre = {
  display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
  height: 26, padding: '0 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
  border: '1px solid rgba(255,255,255,0.55)', background: 'rgba(255,255,255,0.12)',
  color: '#fff', cursor: 'pointer', fontFamily: 'inherit',
}

// L'aperçu mis en forme : une fenêtre flottante de plus, posée au-dessus de la première
// (`zIndex` plus haut), avec son bouton « Imprimer » dans sa barre de titre. C'est la même page
// que celle qu'on imprime — `guideEnHtml()` sert les deux, il n'y a pas deux versions du texte.
//
// `dangerouslySetInnerHTML` est sans risque ici : le HTML vient de `GUIDE`, écrit dans ce
// fichier, jamais d'une saisie ni d'un fournisseur d'IA. La classe `.apercu-corps` (index.css)
// lui donne la mise en forme de tous les aperçus de l'application.
function ApercuHtmlGuide({ onFermer }) {
  const html = guideEnHtml()
  const actions = (
    <button type="button" style={boutonBarre} onClick={() => imprimerApercu(html)}
            title="Imprimer cette page — ou l’enregistrer en PDF depuis la boîte d’impression">
      <IconPrint />Imprimer
    </button>
  )
  return (
    <FenetrePro titre="Comment ça marche — aperçu mis en forme" onFermer={onFermer} actions={actions}
                largeur={Math.min(760, window.innerWidth - 60)} hauteur="min(80vh, 720px)" zIndex={470}>
      <div className="apercu-corps"
           style={{ overflowY: 'auto', padding: '22px 28px', color: '#1e293b', lineHeight: 1.7, fontSize: 14.5 }}
           dangerouslySetInnerHTML={{ __html: html }} />
    </FenetrePro>
  )
}

export default function GuideDemos({ onFermer }) {
  // L'aperçu HTML est une SECONDE fenêtre, par-dessus la première — jamais un onglet du
  // navigateur : dans cette application, un HTML s'ouvre en fenêtre flottante, partout.
  const [apercu, setApercu] = useState(false)

  const actions = (
    <button type="button" style={boutonBarre} onClick={() => setApercu(true)}
            title="Voir cette explication mise en forme, dans une fenêtre à part">
      <IconGlobe />Ouvrir en HTML
    </button>
  )
  return (
    <>
    {apercu && <ApercuHtmlGuide onFermer={() => setApercu(false)} />}
    <FenetrePro titre="Comment fonctionnent les démonstrations" onFermer={onFermer} actions={actions}
                largeur={Math.min(880, window.innerWidth - 40)} hauteur="min(78vh, 700px)">
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 14 }}>
        <p style={{ margin: 0, fontSize: 12, color: '#94a3b8', lineHeight: 1.5 }}>{SOUS_TITRE}</p>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20 }}>
          {GUIDE.map(b => (
            <div key={b.titre} style={{ flex: '1 1 240px', minWidth: 0 }}>
              <p style={{ fontSize: 12.5, fontWeight: 700, color: '#0f172a', margin: '0 0 6px' }}>{b.titre}</p>
              <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12, lineHeight: 1.65, color: '#475569' }}>
                {b.items.map((t, i) => <li key={i} style={{ marginBottom: 4 }}>{gras(t)}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </FenetrePro>
    </>
  )
}
