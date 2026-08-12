import FenetrePro from './FenetrePro.jsx'
import { GUIDE_CONSIGNE } from '../utils/aideConsigne.js'
import { AXES_CONSIGNE } from '../utils/axesConsigne.js'

// « Comment ça marche » de l'écran « Analyser une consigne ». Même dispositif que les autres
// guides (FenetreGuideAmbiguites, FenetreGuideSeance…) : une fenêtre déplaçable et étirable posée
// À CÔTÉ de l'écran, pas un onglet qui cache le formulaire.
//
// ELLE N'ÉCRIT AUCUN TEXTE : elle lit le catalogue de l'écran (utils/aideConsigne.js), celui-là
// même que les « i » affichent, et les cinq axes à leur source unique (utils/axesConsigne.js).
// L'écran portait jusqu'au 12/08/2026 un onglet « Comment ça marche » qui recopiait tout — et sa
// liste d'axes avait déjà divergé de celle du prompt. Une explication, une place.
export default function FenetreGuideConsigne({ onFermer, onOuvrirAide }) {
  return (
    <FenetrePro titre="Comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          <strong style={{ color: '#1e293b' }}>« Analyser une consigne »</strong> prend UNE consigne isolée
          — l'instruction que vous adressez à l'élève — et la juge sur cinq axes didactiques, puis vous la
          rend réécrite. Une consigne mal formulée, et l'élève bute sur l'instruction au lieu de l'exercice.
          <span style={{ display: 'block', marginTop: 6 }}>
            L'écran tient en deux colonnes : votre consigne à gauche, le rapport à droite.
            Rien n'est enregistré — cet outil rend un rapport, c'est tout.
          </span>
        </p>

        <ol style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {GUIDE_CONSIGNE.map((e, i) => (
            <li key={e.cle} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <span style={{ flexShrink: 0, width: 20, height: 20, borderRadius: '50%', background: 'var(--bleu)',
                             color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex',
                             alignItems: 'center', justifyContent: 'center', marginTop: 1 }}>{i + 1}</span>
              <span style={{ fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
                <strong style={{ color: '#1e293b' }}>{e.titre}</strong>
                {/* Le texte long du catalogue — ses paragraphes sont séparés par des lignes vides,
                    rendues telles quelles (`pre-line`) plutôt que recopiées en balises ici. */}
                <span style={{ display: 'block', marginTop: 3, whiteSpace: 'pre-line' }}>{e.long}</span>
              </span>
            </li>
          ))}
        </ol>

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
        <div>
          <div style={{ fontSize: 12.5, fontWeight: 700, color: '#1e293b', marginBottom: 6 }}>
            Les cinq axes
          </div>
          <ul style={{ margin: 0, paddingLeft: 16, listStyleType: 'disc', display: 'flex',
                       flexDirection: 'column', gap: 4, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
            {AXES_CONSIGNE.map(a => (
              <li key={a.label}>
                <strong style={{ color: '#1e293b' }}>{a.label}</strong> — {a.description}
              </li>
            ))}
          </ul>
        </div>

        <div style={{ background: '#f8fafc', borderRadius: 6, padding: '10px 14px', borderLeft: '3px solid #cbd5e1' }}>
          <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>
            <strong style={{ color: '#475569' }}>Différence avec « Détecter les ambiguïtés »</strong><br />
            Le détecteur d'ambiguïtés relit un énoncé ENTIER (plusieurs questions) et vous laisse cocher ce
            qu'il doit chercher. L'analyseur de consignes se concentre sur UNE consigne : il va plus loin sur
            la précision didactique, la charge cognitive et la structure de l'instruction elle-même, et il
            vous en rend une version réécrite.
          </div>
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />

        <button
          type="button"
          onClick={() => onOuvrirAide()}
          title="Ouvrir le centre d'aide (fiches complètes)"
          style={{ alignSelf: 'flex-start', background: 'none', border: 'none', padding: 0, fontSize: 12,
                   color: '#1F6EEB', textDecoration: 'underline', cursor: 'pointer', fontFamily: 'inherit' }}
        >
          Ouvrir le centre d'aide
        </button>
      </div>
    </FenetrePro>
  )
}
