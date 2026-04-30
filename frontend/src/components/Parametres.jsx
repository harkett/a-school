import { useState } from 'react'

const NIVEAUX  = ['6e', '5e', '4e', '3e', '2nde', '1ère', 'Terminale', 'Supérieur']
const MATIERES = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']

const IconGenerer = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
  </svg>
)

export default function Parametres({ activites, params, onChange, onGenerer, loading, hasResultat, canGenerer, onFeedback, sessionMatiere, onMatiereChange }) {
  const activite = activites.find(a => a.key === params.activite_key) || activites[0]
  const [showAjuster, setShowAjuster] = useState(false)
  const [ajustTemp, setAjustTemp] = useState({ matiere: sessionMatiere, niveau: params.niveau })

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

  function ouvrirAjuster() {
    setAjustTemp({ matiere: sessionMatiere, niveau: params.niveau })
    setShowAjuster(true)
  }

  function validerAjust() {
    onMatiereChange(ajustTemp.matiere)
    onChange({ ...params, niveau: ajustTemp.niveau })
    setShowAjuster(false)
  }

  return (
    <section className="bg-white rounded border border-gray-200 p-4">
      <div className="section-title mb-4">Paramètres de l'activité</div>

      {/* Récapitulatif profil */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '6px',
        padding: '8px 12px', marginBottom: '16px', gap: '12px',
      }}>
        <span className="text-sm text-gray-700">
          <span className="font-medium">{sessionMatiere}</span>
          <span className="text-gray-400 mx-2">·</span>
          <span>{params.niveau}</span>
        </span>
        <button
          type="button"
          onClick={ouvrirAjuster}
          title="Modifier la matière et le niveau pour cette activité uniquement — votre profil reste inchangé"
          style={{
            background: 'none', border: '1px solid #d1d5db', borderRadius: '5px',
            padding: '3px 10px', fontSize: '12px', color: '#374151',
            cursor: 'pointer', whiteSpace: 'nowrap', flexShrink: 0,
          }}
        >
          Ajuster pour cette activité
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">

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
            {params.sous_type?.toLowerCase() === 'mélange' && (
              <p className="text-xs text-gray-400 mt-1">
                <span className="font-medium text-gray-500">Combinera :</span>{' '}
                {activite.sous_types.filter(s => s.toLowerCase() !== 'mélange').join(' · ')}
              </p>
            )}
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

      {params.niveau === 'Supérieur' && (
        <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div className="text-sm font-semibold text-blue-800 mb-1">Niveau Supérieur — fonctionnalité en cours de développement</div>
          <p className="text-xs text-blue-700 leading-relaxed">
            A-SCHOOL peut déjà générer des activités adaptées à ce niveau, mais cette option n'est pas encore complètement développée.
            La version complète proposera des activités spécifiques au supérieur : synthèse de documents, fiche de TD, commentaire composé CPGE,
            plan de dissertation, annotation de corpus, préparation Grand Oral post-bac, et bien plus.
          </p>
        </div>
      )}

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

      <div className="mt-4 rounded border border-gray-200 bg-gray-50 px-4 py-3 flex items-start gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6b7280" strokeWidth="2" className="mt-0.5 shrink-0">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <p className="text-xs text-gray-500 leading-relaxed">
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
        </p>
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

      {/* Modale — Ajuster pour cette activité */}
      {showAjuster && (
        <div
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 500,
          }}
          onClick={e => { if (e.target === e.currentTarget) setShowAjuster(false) }}
        >
          <div style={{
            background: '#fff', borderRadius: '10px', padding: '24px',
            width: '360px', maxWidth: '92vw', boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
            display: 'flex', flexDirection: 'column', gap: '16px',
          }}>
            <div>
              <div className="text-sm font-semibold text-gray-800">Ajuster pour cette activité</div>
              <div className="text-xs text-gray-400 mt-0.5">Votre profil reste inchangé.</div>
            </div>

            <div className="flex flex-col gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Matière</label>
                <select
                  className="w-full border border-gray-300 rounded p-2 text-sm"
                  value={ajustTemp.matiere}
                  onChange={e => setAjustTemp(t => ({ ...t, matiere: e.target.value }))}
                >
                  {MATIERES.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Niveau de la classe</label>
                <select
                  className="w-full border border-gray-300 rounded p-2 text-sm"
                  value={ajustTemp.niveau}
                  onChange={e => setAjustTemp(t => ({ ...t, niveau: e.target.value }))}
                >
                  {NIVEAUX.map(n => <option key={n}>{n}</option>)}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-2">
              <button
                type="button"
                onClick={() => setShowAjuster(false)}
                title="Annuler — revenir aux paramètres actuels"
                style={{
                  padding: '7px 16px', fontSize: '13px', borderRadius: '6px',
                  border: '1px solid #d1d5db', background: '#fff', color: '#374151', cursor: 'pointer',
                }}
              >
                Annuler
              </button>
              <button
                type="button"
                onClick={validerAjust}
                title="Valider les ajustements pour cette activité"
                style={{
                  padding: '7px 16px', fontSize: '13px', borderRadius: '6px',
                  border: 'none', background: 'var(--bleu)', color: '#fff', cursor: 'pointer', fontWeight: 600,
                }}
              >
                Valider
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
