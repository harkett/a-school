import FenetrePro from './FenetrePro.jsx'

// « Comment ça marche » de la page « Mes contenus → Séances » (la LISTE, pas l'écran
// Séance qui a le sien — FenetreGuideSeance). Même dispositif que les autres écrans :
// fenêtre déplaçable et étirable (coquille FenetrePro). Contenu = liste numérotée décrivant
// la page RÉELLE (règle des deux publics) — à tenir À JOUR à chaque évolution de la page.
const ETAPES = [
  { n: 1, titre: 'La liste (colonne de gauche)',
    desc: "Une ligne par séance : la pastille de couleur de son couple matière-niveau, le thème en titre, puis le mode choisi à la génération, le niveau et la durée. Le badge date est bleu quand la séance est récente. Cliquez une ligne : son détail s'affiche à droite." },
  { n: 2, titre: 'Les deux onglets',
    desc: "« Niveau en cours » ne montre que les séances de votre matière et niveau actuels. « Toutes mes séances » montre tout, regroupé par matière-niveau, votre couple courant épinglé en haut avec la marque « en cours »." },
  { n: 3, titre: 'Le détail (colonne de droite)',
    desc: "Le contexte que vous aviez fourni, les activités rattachées à la séance (« Ouvrir » recharge l'activité dans son écran ; rattacher ou détacher se fait dans l'écran Séance, via « Reprendre ») et le déroulé généré. « HTML » ouvre l'aperçu mis en forme (avec Imprimer) ; « Reprendre » rouvre la séance dans son écran pour la modifier ou la régénérer — une séance d'un autre couple demande d'abord de passer sur le profil correspondant. Le bouton « Cacher le détail », à droite des onglets, cache ou réaffiche cette colonne : cachée, la liste prend toute la largeur." },
  { n: 4, titre: '« Nouvelle séance »',
    desc: "Le bouton bleu en haut à droite : l'écran Séance s'ouvre vierge. La séance générée s'enregistre automatiquement et revient dans cette liste." },
  { n: 5, titre: 'Partager / Supprimer',
    desc: "Pas encore branchés dans Mes contenus : les deux boutons sont visibles mais inactifs (« bientôt »)." },
]

export default function FenetreGuideContenusSeances({ onFermer, onOuvrirAide }) {
  return (
    <FenetrePro titre="Mes séances — comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          <strong style={{ color: '#1e293b' }}>« Mes séances »</strong> réunit toutes vos séances :
          chaque séance générée s'y enregistre automatiquement. La liste est à gauche, le détail de la
          séance choisie à droite.
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
