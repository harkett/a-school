const NIVEAUX = ['6e', '5e', '4e', '3e', '2nde', '1ère', 'Terminale', 'Supérieur']

const IconGenerer = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
  </svg>
)

export default function Parametres({ activites, params, onChange, onGenerer, loading, hasResultat, canGenerer }) {
  const activite = activites.find(a => a.key === params.activite_key) || activites[0]

  function set(field, value) {
    onChange({ ...params, [field]: value })
  }

  function handleActivite(key) {
    const act = activites.find(a => a.key === key)
    onChange({
      ...params,
      activite_key: key,
      sous_type: act?.sous_types[0] || null,
      nb: act?.params.includes('nb') ? 5 : null,
    })
  }

  return (
    <section className="bg-white rounded border border-gray-200 p-4">
      <div className="section-title mb-4">Paramètres de l'activité</div>
      <div className="grid grid-cols-2 gap-4">

        <div>
          <label className="block text-xs text-gray-500 mb-1">Niveau de la classe</label>
          <select
            className="w-full border border-gray-300 rounded p-2 text-sm"
            value={params.niveau}
            onChange={e => set('niveau', e.target.value)}
          >
            {NIVEAUX.map(n => <option key={n}>{n}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Type d'activité</label>
          <select
            className="w-full border border-gray-300 rounded p-2 text-sm"
            value={params.activite_key}
            onChange={e => handleActivite(e.target.value)}
          >
            {activites.map(a => (
              <option key={a.key} value={a.key}>{a.label}</option>
            ))}
          </select>
        </div>

        {activite?.sous_types.length > 0 && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Précision</label>
            <select
              className="w-full border border-gray-300 rounded p-2 text-sm"
              value={params.sous_type || ''}
              onChange={e => set('sous_type', e.target.value)}
            >
              {activite.sous_types.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
        )}

        {activite?.params.includes('nb') && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Nombre de questions</label>
            <input
              type="number" min="1" max="20"
              className="w-full border border-gray-300 rounded p-2 text-sm"
              value={params.nb || 5}
              onChange={e => set('nb', parseInt(e.target.value))}
            />
          </div>
        )}
      </div>

      <div className="mt-4 flex items-start gap-2">
        <input
          type="checkbox" id="avec-correction"
          checked={params.avec_correction}
          onChange={e => set('avec_correction', e.target.checked)}
          className="mt-0.5"
        />
        <div>
          <label htmlFor="avec-correction" className="text-sm text-gray-700 cursor-pointer font-medium">
            Inclure une proposition de correction
          </label>
          <p className="text-xs text-gray-400 mt-0.5">
            A-SCHOOL génère une réponse-type après chaque question, que le professeur adapte à sa classe.
          </p>
        </div>
      </div>

      {!hasResultat && (
        <div className="mt-5 flex justify-end">
          <button
            className="btn-primary"
            onClick={onGenerer}
            disabled={loading || !canGenerer}
            title={!canGenerer ? 'Saisissez un texte source pour générer une activité' : 'Lancer la génération de l\'activité avec A-SCHOOL'}
          >
            <IconGenerer />
            {loading ? 'Génération en cours...' : 'Générer l\'activité'}
          </button>
        </div>
      )}
    </section>
  )
}
