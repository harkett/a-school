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
// LE TEXTE N'EST ÉCRIT QU'UNE FOIS, dans `GUIDE`. Il sert à trois sorties — la fenêtre, la page
// imprimée et le fichier HTML — et un balisage minimal (**gras**) évite d'injecter du HTML dans
// le JSX pour obtenir un mot en gras.
//
// Tout ce qui y est affirmé se vérifie dans le code : les statuts qui ouvrent la porte
// (`_STATUTS_VISITABLES`, backend/prof/demo.py), la durée du jeton (`_VALIDITE`), et la copie du
// contenu à l'entrée (`_copier_le_gabarit`). Si l'un des trois change, ce texte change avec.
import FenetrePro from './FenetrePro.jsx'
import { imprimerApercu } from '../utils/apercuHtml.js'

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

// Le même texte pour le papier et pour le fichier : les trois blocs à la suite, jamais en
// colonnes — sur une feuille, trois colonnes obligent à remonter deux fois en haut de page.
function guideEnHtml() {
  const enGras = t => t.split('**').map((x, i) => (i % 2 ? '<strong>' + x + '</strong>' : x)).join('')
  const bloc = b => '<h2>' + b.titre + '</h2><ul>'
    + b.items.map(t => '<li>' + enGras(t) + '</li>').join('')
    + '</ul>'
  return '<h1>Comment fonctionnent les démonstrations</h1><p>' + SOUS_TITRE + '</p>'
    + GUIDE.map(bloc).join('')
}

// Enregistrer la page en HTML : un fichier autonome, lisible hors de l'application, qu'on peut
// envoyer à quelqu'un qui n'a pas accès à l'administration.
function enregistrerEnHtml() {
  const page = '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
    + '<title>Démonstrations — comment ça marche</title>'
    + '<style>body{font-family:Arial,Helvetica,sans-serif;color:#1e293b;line-height:1.7;'
    + 'font-size:14px;max-width:820px;margin:32px auto;padding:0 20px}'
    + 'h1{font-size:1.45rem;color:#0f172a;margin:0 0 6px}'
    + 'h2{font-size:1.05rem;color:#0f172a;margin:1.6em 0 .4em}'
    + 'ul{margin:.4em 0 .4em 1.2em;padding:0}li{margin:.45em 0}strong{color:#0f172a}</style>'
    + '</head><body>' + guideEnHtml() + '</body></html>'
  const url = URL.createObjectURL(new Blob([page], { type: 'text/html;charset=utf-8' }))
  const a = document.createElement('a')
  a.href = url
  a.download = 'demonstrations-comment-ca-marche.html'
  document.body.appendChild(a)
  a.click()
  a.remove()
  // Le navigateur a besoin de l'URL le temps du clic ; on la rend juste après, sinon le Blob
  // reste en mémoire jusqu'au rechargement de la page.
  setTimeout(() => URL.revokeObjectURL(url), 0)
}

export default function GuideDemos({ onFermer }) {
  const lien = {
    background: 'none', border: 'none', padding: 0, fontSize: 12, color: '#1F6EEB',
    textDecoration: 'underline', cursor: 'pointer', fontFamily: 'inherit',
  }
  return (
    <FenetrePro titre="Comment fonctionnent les démonstrations" onFermer={onFermer}
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

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <button type="button" style={lien} onClick={() => imprimerApercu(guideEnHtml())}
                  title="Imprimer cette explication — ou l’enregistrer en PDF depuis la boîte d’impression">
            Imprimer
          </button>
          <button type="button" style={lien} onClick={enregistrerEnHtml}
                  title="Enregistrer un fichier HTML autonome, lisible hors de l’application">
            Enregistrer en HTML
          </button>
        </div>
      </div>
    </FenetrePro>
  )
}
