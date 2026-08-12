import { useQuery } from '@tanstack/react-query'
import FenetrePro from './FenetrePro.jsx'
import { apiFetch, lireReponse, TIMEOUT_STD } from '../utils/api.js'
import { GUIDE_AMBIGUITES } from '../utils/aideAmbiguites.js'

// « Comment ça marche » de l'écran « Analyser un texte pour détecter les ambiguïtés ». Même
// dispositif que les autres guides (FenetreGuideSeance, FenetreGuideSequence…) : une fenêtre
// déplaçable et étirable posée À CÔTÉ de l'écran, pas un onglet qui cache le formulaire.
//
// ELLE N'ÉCRIT AUCUN TEXTE : elle lit le catalogue de l'écran (utils/aideAmbiguites.js), celui-là
// même que les « i » affichent. Elle portait jusqu'au 12/08/2026 ses propres étapes en dur — elles
// décrivaient un écran qui n'existait plus (une seule colonne, un bouton d'exemple supprimé), et
// personne ne pouvait le voir en corrigeant les bulles. Une explication, une place.
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
          <strong style={{ color: '#1e293b' }}>« Analyser un texte pour détecter les ambiguïtés »</strong> relit
          votre énoncé à la loupe : il repère les formulations qui prêtent à confusion et, pour chacune, vous
          propose une reformulation corrigée. Un énoncé mal formulé, et l'élève bute sur la consigne au lieu
          de l'exercice.
          <span style={{ display: 'block', marginTop: 6 }}>
            L'écran tient en deux colonnes : votre énoncé à gauche, le rapport à droite.
            Rien n'est enregistré — cet outil rend un rapport, c'est tout.
          </span>
        </p>

        <ol style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {GUIDE_AMBIGUITES.map((e, i) => (
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
