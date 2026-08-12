import FenetrePro from './FenetrePro.jsx'
import { GUIDE_EQUITE } from '../utils/aideEquite.js'
import Aschool from './Aschool.jsx'

// « Comment ça marche » de l'écran « Équité d'une évaluation ». Même dispositif que les autres
// guides (FenetreGuideAmbiguites, FenetreGuideConsigne…) : une fenêtre déplaçable et étirable
// posée À CÔTÉ de l'écran, pas un onglet qui cache le formulaire.
//
// ELLE N'ÉCRIT AUCUN TEXTE : elle lit le catalogue de l'écran (utils/aideEquite.js), celui-là même
// que les « i » affichent. Une explication, une place.
//
// LA LISTE DES BIAIS N'EST PAS ICI, et c'est volontaire : elle vit EN BASE (`equite_criteres`) et
// se lit sur l'écran, chaque case portant sa description au survol. La recopier dans le guide en
// aurait fait une seconde vérité, qui aurait divergé au premier biais ajouté ou renommé — c'est
// exactement ce qui était arrivé à la liste d'axes de l'ex-onglet des consignes.
export default function FenetreGuideEquite({ onFermer, onOuvrirAide }) {
  return (
    <FenetrePro titre="Comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          <strong style={{ color: '#1e293b' }}>« Équité d'une évaluation »</strong> relit un sujet complet
          et cherche ce qu'il demande <em>en plus</em> de la compétence évaluée — et qui n'est pas également
          disponible à tous vos élèves. Un savoir qui n'a pas été enseigné, une expérience de vie supposée,
          un ordinateur à la maison, une longueur de lecture qui prend le pas sur la matière.
          <span style={{ display: 'block', marginTop: 6 }}>
            L'écran tient en deux colonnes : votre évaluation à gauche, le rapport à droite.
            Rien n'est enregistré — cet outil rend un rapport, c'est tout.
          </span>
        </p>

        {/* Le cadre qui compte : la question que le professeur se pose en découvrant la liste. La
            poser ici, en tête et non en note de bas de page, évite qu'il conclue à un oubli. */}
        <div style={{ background: '#fffbeb', borderRadius: 6, padding: '10px 14px',
                      borderLeft: '3px solid #fcd34d' }}>
          <div style={{ fontSize: 12, color: '#78350f', lineHeight: 1.5 }}>
            <strong style={{ color: '#92400e' }}>Les biais du sujet, pas ceux de la correction</strong><br />
            L'effet de halo, les écarts entre deux correcteurs, la sévérité qui dérive au fil du paquet :
            ce sont les biais les mieux établis de l'évaluation scolaire, et aucun ne se voit dans un
            sujet. Ils demandent plusieurs copies, plusieurs correcteurs, ou du temps. <Aschool /> ne les
            cherche donc pas et ne prétendra jamais les avoir trouvés. L'entrée
            <strong> « Et l'effet de halo ? »</strong> ci-dessous dit ce qui les réduit vraiment.
          </div>
        </div>

        <ol style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {GUIDE_EQUITE.map((e, i) => (
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

        <div style={{ background: '#f8fafc', borderRadius: 6, padding: '10px 14px', borderLeft: '3px solid #cbd5e1' }}>
          <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>
            <strong style={{ color: '#475569' }}>Différence avec les deux autres analyses</strong><br />
            « Détecter les ambiguïtés » demande <em>est-ce compréhensible ?</em> et « Analyser une consigne »
            <em> est-ce bien formulé ?</em>. Celui-ci demande autre chose : <em>tous mes élèves partent-ils
            d'aussi loin ?</em> Une évaluation peut être parfaitement claire et rester inéquitable — c'est
            même le cas le plus fréquent.
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
