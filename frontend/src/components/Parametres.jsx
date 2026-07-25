import { useState, useEffect } from 'react'
import EtapeBadge from './EtapeBadge.jsx'

const IconGenerer = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
  </svg>
)

export default function Parametres({ activites, params, onChange, onGenerer, loading, hasResultat, canGenerer, onFeedback, verrouille = false }) {
  const activite = activites.find(a => a.id === params.activite_type_id) || activites[0]

  // Repli automatique : la carte se replie quand elle se verrouille (phase résultat) et se déplie
  // quand elle se déverrouille (« Changer votre demande »). Le prof peut plier/déplier à la main
  // via le chevron tant que c'est verrouillé.
  const [replie, setReplie] = useState(false)
  useEffect(() => { setReplie(verrouille) }, [verrouille])

  function set(field, value) {
    onChange({ ...params, [field]: value })
  }

  function handleActivite(id) {
    const act = activites.find(a => a.id === id)
    onChange({
      ...params,
      activite_type_id: act?.id ?? null,   // identité du type = son id
      sous_type: act?.sous_types[0] || null,
      nb: (act?.besoins || []).includes('nb') ? 5 : null,  // besoin lu du prompt du couple×type
    })
  }

  return (
    <section className="bg-white rounded border border-gray-200 p-4">
      {/* Étape ① du stepper — le numéro passe en ✓ vert dès qu'un type est choisi.
          La ligne feedback vit à CÔTÉ du titre (sa demande du 25/07 : place gagnée). */}
      <div className="mb-4" style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div className="section-title" style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <EtapeBadge n={1} fait={!!params.activite_type_id} />
          Paramètres de l'activité
        </div>
        {!replie && (
          <span style={{ flex: 1, minWidth: 240, fontSize: 12, color: '#64748b', lineHeight: 1.45 }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" style={{ display: 'inline', verticalAlign: '-2px', marginRight: 5 }}>
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            Vous ne trouvez pas l'activité dont vous avez besoin ?{' '}
            <button
              type="button"
              onClick={onFeedback}
              title="Ouvrir le formulaire de feedback pour signaler une activité manquante"
              className="underline text-gray-600 hover:text-gray-800 cursor-pointer"
              style={{ background: 'none', border: 'none', padding: 0, font: 'inherit' }}
            >
              Signalez-la via le Feedback
            </button>
            {' '}— nous l'ajouterons pour vous et pour tous les profs.
          </span>
        )}
        {/* Chevron plier/déplier : visible seulement quand la carte est verrouillée (phase résultat). */}
        {verrouille && (
          <button
            type="button"
            onClick={() => setReplie(r => !r)}
            title={replie ? "Déplier les paramètres" : "Replier les paramètres"}
            style={{ marginLeft: 'auto', flexShrink: 0, background: 'none', border: 'none', cursor: 'pointer', padding: 4, color: '#64748b', display: 'flex', alignItems: 'center' }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ transition: 'transform 0.2s', transform: replie ? 'rotate(-90deg)' : 'none' }}>
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
        )}
      </div>

      {/* Corps de la carte — masqué quand elle est repliée (phase résultat). */}
      {!replie && (<>
      {/* Verrouillée en phase résultat (comme la carte Texte source) : toute la grille de
          réglages est grisée et inerte d'un coup. « Changer votre demande » lève le verrou. */}
      <div className="grid grid-cols-2 gap-4" style={verrouille ? { opacity: 0.5, pointerEvents: 'none' } : undefined}>

        <div data-guide="type">
          <label className="block text-xs text-gray-500 mb-1">Type d'activité</label>
          <select
            className="w-full border border-gray-300 rounded p-2 text-sm"
            value={params.activite_type_id ?? ''}
            disabled={verrouille}
            onChange={e => handleActivite(Number(e.target.value))}
          >
            {activites.map(a => (
              <option key={a.id} value={a.id}>{a.label}</option>
            ))}
          </select>
        </div>

        {/* À la place de Précision : la coche correction, à droite du Type */}
        <div data-guide="corrige" className="flex items-start gap-2">
          <input
            type="checkbox" id="avec-correction"
            checked={params.avec_correction}
            disabled={verrouille}
            onChange={e => set('avec_correction', e.target.checked)}
            className="mt-0.5"
          />
          <div>
            <label htmlFor="avec-correction" className="text-sm text-gray-700 cursor-pointer font-medium">
              Inclure une proposition de correction
            </label>
            <p className="text-xs text-gray-400 mt-0.5">
              aSchool génère une réponse-type après chaque question, que le professeur adapte à sa classe.
            </p>
          </div>
        </div>

        {/* Précision SOUS le Type d'activité (2e rang de la grille) */}
        {activite?.sous_types.length > 0 && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Précision</label>
            <select
              className="w-full border border-gray-300 rounded p-2 text-sm"
              value={params.sous_type || ''}
              disabled={verrouille}
              onChange={e => set('sous_type', e.target.value)}
            >
              {activite.sous_types.map(s => <option key={s}>{s}</option>)}
            </select>
            {params.sous_type?.toLowerCase() === 'mélange' && (
              <p className="text-xs text-gray-400 mt-1">
                <span className="font-medium text-gray-500">Cette précision comprend un mélange de :</span>{' '}
                {activite.sous_types.filter(s => s.toLowerCase() !== 'mélange').join(' · ')}
              </p>
            )}
          </div>
        )}

        {(activite?.besoins || []).includes('nb') && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Nombre de questions</label>
            <input
              type="number" min="1" max="20"
              className="w-full border border-gray-300 rounded p-2 text-sm"
              value={params.nb || 5}
              disabled={verrouille}
              onChange={e => set('nb', parseInt(e.target.value))}
            />
          </div>
        )}
      </div>

      {params.niveau === 'Supérieur' && (
        <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div className="text-sm font-semibold text-blue-800 mb-1">Niveau Supérieur — fonctionnalité en cours de développement</div>
          <p className="text-xs text-blue-700 leading-relaxed">
            aSchool peut déjà générer des activités adaptées à ce niveau, mais cette option n'est pas encore complètement développée.
            La version complète proposera des activités spécifiques au supérieur : synthèse de documents, fiche de TD, commentaire composé CPGE,
            plan de dissertation, annotation de corpus, préparation Grand Oral post-bac, et bien plus.
          </p>
        </div>
      )}
      </>)}

    </section>
  )
}
