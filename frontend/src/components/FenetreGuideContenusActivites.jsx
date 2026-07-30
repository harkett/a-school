import FenetrePro from './FenetrePro.jsx'

// « Comment ça marche » de la page « Mes contenus → Activités » (la LISTE, pas l'écran
// Activité qui a le sien). Même dispositif que les autres écrans : fenêtre déplaçable et
// étirable (coquille FenetrePro). Contenu = liste numérotée décrivant la page RÉELLE
// (règle des deux publics : on ne décrit que ce que l'écran fait vraiment) — à tenir À JOUR
// à chaque évolution de la page, dans le même geste.
const ETAPES = [
  { n: 1, titre: 'La liste (colonne de gauche)',
    desc: "Une ligne par activité : la pastille de couleur de son couple matière-niveau, son titre (l'objet demandé, sinon le type d'activité), puis le type, le niveau, le nombre de questions et avec/sans correction. Le badge date est bleu quand l'activité est récente. Cliquez une ligne : son détail s'affiche à droite." },
  { n: 2, titre: 'Les deux onglets',
    desc: "« Niveau en cours » ne montre que les activités de votre matière et niveau actuels. « Toutes mes activités » montre tout, regroupé par matière-niveau, votre couple courant épinglé en haut avec la marque « en cours »." },
  { n: 3, titre: '« Sur la plateforme »',
    desc: "Le petit encart de l'onglet Niveau en cours : combien d'activités et de profs sur la plateforme pour votre couple, et les types d'activités les plus utilisés." },
  { n: 4, titre: 'Le détail (colonne de droite)',
    desc: "Le texte source et le résultat généré de l'activité choisie. « HTML » ouvre l'aperçu mis en forme (avec Imprimer) ; « Reprendre » rouvre l'activité dans son écran pour la modifier ou la régénérer — une activité d'un autre couple demande d'abord de passer sur le profil correspondant. Le bouton sous « Nouvelle activité » cache ou réaffiche cette colonne : cachée, la liste prend toute la largeur." },
  { n: 5, titre: '« Nouvelle activité »',
    desc: "Le bouton bleu en haut à droite : l'écran Activité s'ouvre vierge. L'activité générée s'enregistre automatiquement et revient dans cette liste." },
  { n: 6, titre: 'Partager / Supprimer',
    desc: "Pas encore branchés dans Mes contenus : les deux boutons sont visibles mais inactifs (« bientôt »)." },
]

export default function FenetreGuideContenusActivites({ onFermer, onOuvrirAide }) {
  return (
    <FenetrePro titre="Comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          <strong style={{ color: '#1e293b' }}>« Mes contenus → Activités »</strong> réunit toutes vos activités :
          chaque activité générée s'y enregistre automatiquement. La liste est à gauche, le détail de
          l'activité choisie à droite.
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
