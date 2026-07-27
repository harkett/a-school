import { GUIDE_CREER } from '../utils/aideCreer.js'
import FenetrePro from './FenetrePro.jsx'

// Regroupement des explications par CARTOUCHE de l'écran (mêmes numéros et mêmes titres que
// les cartouches 1→5). On NE duplique pas les textes : on lit `phrase` du catalogue unique
// aideCreer.js (via `cles`). La cartouche 5 (Analyse) n'a pas encore d'entrée au catalogue —
// pour ne pas toucher la visite guidée ni le centre d'aide — donc son texte est fourni ici (`local`).
const CARTOUCHES = [
  { n: 1, titre: "Paramètres de l'activité",           cles: ['type', 'corrige'] },
  { n: 2, titre: 'Texte source',                        cles: ['boutons', 'texte'] },
  { n: 3, titre: 'Générer',                             cles: ['generer'] },
  { n: 4, titre: 'Résultat généré',                     cles: ['resultat'] },
  { n: 5, titre: 'Analyse et amélioration du résultat', cles: [],
    local: "Trois analyses de l'activité générée, chacune dans son onglet : Ambiguïté, Consigne et Équité." },
]
const phraseDe = cle => (GUIDE_CREER.find(e => e.cle === cle) || {}).phrase

// « Comment ça marche » (l'idée de l'utilisateur, 25/07) : une fenêtre déplaçable et
// étirable (coquille FenetrePro), pas un onglet qui remplace l'écran — le prof la pose où
// il veut et garde le mode d'emploi sous les yeux pendant qu'il remplit le vrai formulaire.
// Les étapes lisent le catalogue unique (utils/aideCreer.js — les mêmes phrases que les
// bulles et le centre d'aide). L'exemple ne se fabrique PLUS ici (décision du 25/07 : un
// appel IA n'a pas sa place dans un mode d'emploi, c'était trop lourd) — on renvoie au
// bouton « Document d'exemple » de la zone de texte, seul endroit qui fabrique un exemple.
export default function FenetreGuide({ onFermer, onRevoirGuide, onOuvrirAide }) {
  return (
    <FenetrePro titre="Comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        {/* Intro : le bandeau classe/matière, au-dessus des cartouches sur l'écran. */}
        {phraseDe('couple') && (
          <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>{phraseDe('couple')}</p>
        )}
        {/* Les étapes, regroupées par cartouche (mêmes numéros/titres que l'écran). Textes lus
            dans le catalogue unique aideCreer.js — les mêmes phrases que les bulles de la visite. */}
        <ol style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {CARTOUCHES.map(c => {
            const phrases = c.cles.map(phraseDe).filter(Boolean)
            if (c.local) phrases.push(c.local)
            return (
              <li key={c.n} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <span style={{ flexShrink: 0, width: 20, height: 20, borderRadius: '50%', background: 'var(--bleu)',
                               color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex',
                               alignItems: 'center', justifyContent: 'center', marginTop: 1 }}>{c.n}</span>
                <span style={{ fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
                  <strong style={{ color: '#1e293b' }}>{c.titre}</strong>
                  {phrases.map((p, i) => (
                    <span key={i} style={{ display: 'block', marginTop: 3 }}>{p}</span>
                  ))}
                </span>
              </li>
            )
          })}
        </ol>

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />

        {/* L'exemple ne se fabrique plus ici : on pointe vers le bouton qui le fait. */}
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          Pour voir un exemple adapté à votre classe, cliquez sur <strong>« Document d'exemple »</strong>, au-dessus de la zone de texte.
        </p>

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={onRevoirGuide}
            title="Relancer la visite guidée : chaque élément de l'écran s'explique, à sa place"
            style={{ background: 'none', border: 'none', padding: 0, fontSize: 12, color: '#1F6EEB',
                     textDecoration: 'underline', cursor: 'pointer', fontFamily: 'inherit' }}
          >
            Revoir le guide de l'écran
          </button>
          <button
            type="button"
            onClick={() => onOuvrirAide()}
            title="Ouvrir le centre d'aide (fiches complètes)"
            style={{ background: 'none', border: 'none', padding: 0, fontSize: 12, color: '#1F6EEB',
                     textDecoration: 'underline', cursor: 'pointer', fontFamily: 'inherit' }}
          >
            Ouvrir le centre d'aide
          </button>
        </div>
      </div>
    </FenetrePro>
  )
}
