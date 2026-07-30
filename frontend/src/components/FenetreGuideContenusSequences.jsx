import FenetrePro from './FenetrePro.jsx'

// « Comment ça marche » de la page « Mes contenus → Séquences » (la LISTE, pas l'écran
// Séquence qui a le sien — FenetreGuideSequence). Même dispositif que les pages voisines.
// Contenu = liste numérotée décrivant la page RÉELLE — à tenir À JOUR avec la page.
const ETAPES = [
  { n: 1, titre: 'La liste (colonne de gauche)',
    desc: "Une ligne par séquence : la pastille de couleur de son couple matière-niveau, l'objectif en titre, puis le nombre de séances et le niveau. Le badge date est bleu quand la séquence est récente. Cliquez une ligne : son détail s'affiche à droite." },
  { n: 2, titre: 'Les deux onglets',
    desc: "« Niveau en cours » ne montre que les séquences de votre matière et niveau actuels. « Toutes mes séquences » montre tout, regroupé par matière-niveau, votre couple courant épinglé en haut." },
  { n: 3, titre: 'Le détail (colonne de droite)',
    desc: "L'objectif, le contexte et les précisions que vous aviez fournis, puis les séances de la séquence dans l'ordre du plan, chacune avec son état : « à générer » (déroulé pas encore écrit) ou « générée ». Le bouton « Cacher le détail », à droite des onglets, cache ou réaffiche cette colonne : cachée, la liste prend toute la largeur." },
  { n: 4, titre: '« Reprendre »',
    desc: "Rouvre la séquence dans son écran : c'est LÀ que ses séances se travaillent, une à une — ouvrir une séance du plan, générer son déroulé, y accrocher des activités, puis revenir à la séquence pour enchaîner la suivante. Une séquence d'un autre couple demande d'abord de passer sur le profil correspondant." },
  { n: 5, titre: '« Nouvelle séquence »',
    desc: "Le bouton bleu en haut à droite : l'écran Séquence s'ouvre vierge. Le plan généré et ses séances s'enregistrent automatiquement et reviennent dans cette liste." },
  { n: 6, titre: 'Partager / Supprimer',
    desc: "Pas encore branchés dans Mes contenus : les deux boutons sont visibles mais inactifs (« bientôt »)." },
]

export default function FenetreGuideContenusSequences({ onFermer, onOuvrirAide }) {
  return (
    <FenetrePro titre="Mes séquences — comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          <strong style={{ color: '#1e293b' }}>« Mes séquences »</strong> réunit toutes vos
          séquences : un objectif + la suite ordonnée des séances qui y mènent. La liste est à gauche,
          le détail de la séquence choisie à droite.
        </p>

        <ol style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {ETAPES.map(e => (
            <li key={e.n} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <span style={{ flexShrink: 0, width: 20, height: 20, borderRadius: '50%', background: 'var(--bleu)',
                             color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex',
                             alignItems: 'center', justifyContent: 'center', marginTop: 1 }}>{e.n}</span>
              <span style={{ fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
                <strong style={{ color: '#1e293b' }}>{e.titre}</strong>
                <span style={{ display: 'block', marginTop: 3 }}>{e.desc}</span>
              </span>
            </li>
          ))}
        </ol>

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
