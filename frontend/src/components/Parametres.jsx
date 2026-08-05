import { useState } from 'react'
import EtapeBadge from './EtapeBadge.jsx'
import InfoGuide from './InfoGuide.jsx'
import { aideActivite } from '../utils/aideActivite.js'


// Icônes de tête posées DANS les combos (à gauche du texte). Type = quatre pavés
// (les familles d'activités), Précision = curseurs de réglage (on affine le type).
const IconType = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>
    <rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/>
  </svg>
)
const IconPrecision = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/>
    <line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/>
    <line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/>
    <line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>
  </svg>
)

export default function Parametres({ activites, params, onChange, onFeedback, verrouille = false }) {
  // Aucun repli sur activites[0] : tant qu'aucun type n'est CHOISI, `activite` est null (sinon la
  // carte se croirait remplie et « Nombre de questions » s'afficherait avant tout choix).
  const activite = activites.find(a => a.id === params.activite_type_id) || null

  // Repli automatique : la carte se replie quand elle se verrouille (phase résultat) et se déplie
  // quand elle se déverrouille (« Changer votre demande »). Le prof peut plier/déplier à la main
  // via le chevron tant que c'est verrouillé. C'est un CALCUL : le repli suit le verrou, sauf si
  // le prof a dit autre chose pour ce verrou-là — son geste tombe de lui-même au verrou suivant.
  const [replieChoisi, setReplieChoisi] = useState(null)   // { pour: verrouille, valeur } | null
  const replie = replieChoisi?.pour === verrouille ? replieChoisi.valeur : verrouille
  const setReplie = (maj) => setReplieChoisi({
    pour: verrouille,
    valeur: typeof maj === 'function' ? maj(replie) : maj,
  })

  function set(field, value) {
    onChange({ ...params, [field]: value })
  }

  function handleActivite(id) {
    const act = activites.find(a => a.id === id)
    onChange({
      ...params,
      activite_type_id: act?.id ?? null,   // identité du type = son id
      sous_type: null,   // règle appli : on ne présélectionne pas la précision, le prof la choisit
      nb: (act?.besoins || []).includes('nb') ? 5 : null,  // besoin lu du prompt du couple×type
    })
  }

  return (
    <section className="bg-white rounded border border-gray-200 p-4">
      {/* Étape ① du stepper — le numéro passe en ✓ vert dès qu'un type est choisi.
          La ligne feedback vit à CÔTÉ du titre (sa demande du 25/07 : place gagnée). */}
      <div className="mb-4" style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div className="section-title" style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <EtapeBadge n={1} fait={!!params.activite_type_id} actif={!params.activite_type_id} />
          <span style={{ display: 'inline-flex', alignItems: 'center', fontWeight: 700 }}>
            Paramètres de l'activité
            <InfoGuide {...aideActivite('parametres')} />
          </span>
          {/* Chevron plier/déplier — cerclé, à côté du « i ». Toujours visible ; grisé et inactif
              tant que la carte n'est pas verrouillée (le pliage n'a de sens qu'en phase résultat). */}
          <button
            type="button"
            disabled={!params.activite_type_id}
            onClick={() => setReplie(r => !r)}
            title={!params.activite_type_id ? "Choisissez d'abord un type d'activité" : (replie ? "Déplier les paramètres" : "Replier les paramètres")}
            style={{ marginLeft: 6, width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: params.activite_type_id ? 'pointer' : 'not-allowed', opacity: params.activite_type_id ? 1 : 0.4, padding: 0, flexShrink: 0 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ transition: 'transform 0.2s', transform: replie ? 'rotate(-90deg)' : 'none' }}>
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
        </div>
        {/* Ligne « feedback » déplacée SOUS la coche correction (27/07) pour dégager l'en-tête. */}

        {/* Récap PLIÉ : dès que la carte est repliée (à la main via le chevron, ou en phase résultat),
            on rappelle les choix EN FACE du titre, juste après le chevron — type d'activité, précision
            (si présente), et « avec correction » (si cochée). Masqué quand la carte est dépliée (les
            vrais champs sont alors visibles dessous). */}
        {replie && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', minWidth: 0 }}>
            {activite?.label && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 20, padding: '3px 10px', fontSize: 13, fontWeight: 600, color: '#334155' }}>
                <span style={{ color: 'var(--bordeaux)', display: 'inline-flex' }}><IconType /></span>
                {activite.label}
              </span>
            )}
            {params.sous_type && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 20, padding: '3px 10px', fontSize: 13, color: '#475569' }}>
                <span style={{ color: 'var(--bordeaux)', display: 'inline-flex' }}><IconPrecision /></span>
                {params.sous_type}
              </span>
            )}
            {params.avec_correction && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, background: '#e8f6ed', border: '1px solid #a7f3d0', borderRadius: 20, padding: '3px 10px', fontSize: 12.5, fontWeight: 600, color: '#166534' }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                avec correction
              </span>
            )}
          </span>
        )}
      </div>

      {/* Corps de la carte — masqué quand elle est repliée (phase résultat). */}
      {!replie && (<>
      {/* Verrouillée en phase résultat (comme la carte Texte source) : toute la grille de
          réglages est grisée et inerte d'un coup. « Changer votre demande » lève le verrou. */}
      <div className="grid grid-cols-2 gap-4" style={verrouille ? { opacity: 0.5, pointerEvents: 'none' } : undefined}>

        <div data-guide="type">
          <label className="block text-xs text-gray-500 mb-1">Type d'activité<InfoGuide {...aideActivite('type')} /></label>
          <div className="relative">
            <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--bordeaux)' }}>
              <IconType />
            </span>
            <select
              className="w-full border border-gray-300 rounded p-2 pl-9 text-sm"
              value={params.activite_type_id ?? ''}
              disabled={verrouille}
              onChange={e => handleActivite(Number(e.target.value))}
              style={{ color: params.activite_type_id ? undefined : '#94a3b8' }}
            >
              {/* Placeholder gris affiché tant que rien n'est choisi (règle appli). PAS de `disabled` :
                  une option sélectionnée disabled n'est pas affichée par Chrome/Edge, qui retombe alors
                  sur la 1re activité — c'est ce qui faisait « réapparaître » une valeur par défaut. */}
              <option value="">Choisissez un type d'activité</option>
              {activites.map(a => (
                <option key={a.id} value={a.id} style={{ color: '#1e293b' }}>{a.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Ligne « feedback » — au niveau du Type d'activité (colonne droite, 1er rang).
            Déplacée du haut (27/07) pour dégager l'en-tête. */}
        <div style={{ alignSelf: 'start', fontSize: 12, color: '#64748b', lineHeight: 1.45 }}>
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
        </div>

        {/* Précision — colonne gauche, 2e rang. GRISÉE tant qu'aucun type n'est choisi (on entre
            d'abord par le Type) ; elle revient, avec les valeurs du type, une fois celui-ci choisi. */}
        {(!params.activite_type_id || activite?.sous_types.length > 0) && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Précision<InfoGuide {...aideActivite('precision')} /></label>
            <div className="relative">
              <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--bordeaux)' }}>
                <IconPrecision />
              </span>
              <select
                className="w-full border border-gray-300 rounded p-2 pl-9 text-sm"
                value={params.sous_type || ''}
                disabled={verrouille || !params.activite_type_id}
                onChange={e => set('sous_type', e.target.value)}
                style={{ color: params.sous_type ? undefined : '#94a3b8' }}
              >
                {!params.activite_type_id
                  ? <option value="">Choisissez d'abord un type d'activité</option>
                  : <>
                      {/* Placeholder gris (même raison : pas de `disabled`, sinon Chrome affiche la 1re précision). */}
                      <option value="">Choisissez une précision</option>
                      {activite.sous_types.map(s => <option key={s} style={{ color: '#1e293b' }}>{s}</option>)}
                    </>}
              </select>
            </div>
            {params.sous_type?.toLowerCase() === 'mélange' && (
              <p className="text-xs text-gray-400 mt-1">
                <span className="font-medium text-gray-500">Cette précision comprend un mélange de :</span>{' '}
                {activite.sous_types.filter(s => s.toLowerCase() !== 'mélange').join(' · ')}
              </p>
            )}
          </div>
        )}

        {/* Coche correction — au niveau de « Précision » (colonne droite, 2e rang). */}
        <div data-guide="corrige" className="flex items-start gap-2">
          <input
            type="checkbox" id="avec-correction"
            checked={params.avec_correction}
            disabled={verrouille}
            onChange={e => set('avec_correction', e.target.checked)}
            className="mt-0.5"
          />
          <div>
            <span style={{ display: 'inline-flex', alignItems: 'center' }}>
              <label htmlFor="avec-correction" className="text-sm text-gray-700 cursor-pointer font-medium">
                Inclure une proposition de correction
              </label>
              <InfoGuide {...aideActivite('correction')} />
            </span>
            <p className="text-xs text-gray-500 mt-0.5 leading-snug">
              aSchool rédige aussi le corrigé, en même temps que l'activité.
            </p>
          </div>
        </div>

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
