import { useQuery } from '@tanstack/react-query'
import FenetrePro from './FenetrePro.jsx'
import { apiFetch, lireReponse, TIMEOUT_STD } from '../utils/api.js'

// « Comment ça marche » de l'écran « Détecter les ambiguïtés ». Même dispositif que les autres
// guides (FenetreGuideSeance, FenetreGuideSequence…) : une fenêtre déplaçable et étirable posée
// À CÔTÉ de l'écran, pas un onglet qui cache le formulaire — c'est ce qui a fait sortir l'aide
// de la barre d'onglets de cet écran.
const ETAPES = [
  { n: 1, titre: 'Apportez votre énoncé',
    desc: "Un exercice, une série de questions ou une consigne isolée. Cinq façons de remplir la zone : au clavier, ou par les boutons en haut à droite — Fichier TXT, Image/Scan (une photo de votre sujet papier), PDF, Dicter (vous parlez, aSchool écrit). Quand le texte ne vient pas du clavier, une ligne sous la zone rappelle d'où il vient." },
  { n: 2, titre: '« Utiliser un exemple » — pour découvrir l\'outil',
    desc: "Ce bouton charge un énoncé tout prêt de VOTRE matière, dans lequel des défauts ont été glissés volontairement : de quoi voir ce que l'outil sait faire sans avoir à chercher un sujet. Il n'apparaît que si votre couple matière-niveau en a un — aSchool n'invente jamais d'exemple à la volée." },
  { n: 3, titre: 'Cochez ce qu\'aSchool doit chercher',
    desc: "Les types d'ambiguïté sont des cases à cocher — aucune n'est cochée au départ, et vous en cochez autant que vous voulez. Survolez-en une pour lire ce qu'elle repère. C'est ce qui distingue cet outil d'une relecture tous azimuts : aSchool ne remonte QUE les types demandés, donc aucune remarque hors sujet à écarter, et il les traite un par un au lieu de s'arrêter au premier défaut vu." },
  { n: 4, titre: 'Autre — votre propre point de vigilance',
    desc: "La dernière case ouvre un champ où vous écrivez, en une ligne, ce que vous voulez faire vérifier en plus (par exemple : vérifie le vocabulaire inclusif). aSchool le traite comme un critère de vigilance supplémentaire ; ce qu'il trouve à ce titre revient sous l'étiquette « Autre »." },
  { n: 5, titre: 'Lancez l\'analyse',
    desc: "Le bouton « Analyser l'énoncé », en haut à droite, reste gris tant qu'il manque quelque chose — survolez-le, sa bulle dit lequel des trois motifs bloque : rien de coché, « Autre » coché sans texte, ou zone vide. La matière et le niveau, eux, viennent de votre profil : ils s'affichent dans le bandeau du haut." },
  { n: 6, titre: 'Lisez le rapport',
    desc: "Un verdict global sur la clarté de l'énoncé, puis une carte par ambiguïté : l'extrait exact en cause, son type, le risque concret pour l'élève, et une reformulation corrigée prête à copier dans votre exercice. Un type coché qui ne donne aucune carte, c'est qu'il n'y avait rien à signaler. « Nouvel énoncé » repart de zéro." },
]

export default function FenetreGuideAmbiguites({ onFermer, onOuvrirAide }) {
  // Les types listés plus bas viennent de la base, comme les cases de l'écran : même clé de
  // cache que celle de Ambiguites.jsx, donc aucune requête de plus, et jamais deux listes
  // qui divergent.
  const { data: criteres = [] } = useQuery({
    queryKey: ['ambiguites', 'criteres'],
    queryFn: async () => {
      const d = await lireReponse(await apiFetch('/api/ambiguites/criteres', { credentials: 'include' }, TIMEOUT_STD))
      return Array.isArray(d) ? d : []
    },
  })

  return (
    <FenetrePro titre="Comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          <strong style={{ color: '#1e293b' }}>« Détecter les ambiguïtés »</strong> relit votre énoncé à la loupe :
          il repère les formulations qui prêtent à confusion et, pour chacune, vous propose une reformulation
          corrigée. Un énoncé mal formulé, et l'élève bute sur la consigne au lieu de l'exercice.
          Rien n'est enregistré : cet outil rend un résultat, c'est tout.
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

        {criteres.length > 0 && (
          <>
            <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
            <div>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: '#1e293b', marginBottom: 6 }}>
                Les types proposés
              </div>
              <ul style={{ margin: 0, paddingLeft: 16, listStyleType: 'disc', display: 'flex',
                           flexDirection: 'column', gap: 4, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
                {criteres.map(c => (
                  <li key={c.code}>
                    <strong style={{ color: '#1e293b' }}>{c.label}</strong>
                    {c.description ? ` — ${c.description}` : ' — le point que vous écrivez vous-même'}
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}

        <p style={{ margin: 0, fontSize: 12, color: '#64748b', lineHeight: 1.5, fontStyle: 'italic' }}>
          À utiliser avant de distribuer un contrôle ou un devoir maison : une consigne claire réduit les
          questions pendant l'épreuve.
        </p>

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
