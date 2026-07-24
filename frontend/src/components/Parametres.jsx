import { useState } from 'react'

const IconGenerer = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
  </svg>
)

export default function Parametres({ activites, params, accentType, onChange, onGenerer, loading, hasResultat, canGenerer, onFeedback, sessionMatiere, onMatiereChange, profilMatiere, profilNiveau, onRevenirProfil }) {
  const activite = activites.find(a => a.id === params.activite_type_id) || activites[0]
  const [showAjuster, setShowAjuster] = useState(false)
  const [ajustTemp, setAjustTemp] = useState({ matiere: sessionMatiere, niveau: params.niveau })
  const [niveauxParCycle, setNiveauxParCycle] = useState([])
  const [matieresParNiveau, setMatieresParNiveau] = useState([])  // [{niveau, matieres:[{id,nom}]}] — filtre la matière par le niveau

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

  function ouvrirAjuster() {
    setAjustTemp({ matiere: sessionMatiere, niveau: params.niveau })
    setShowAjuster(true)
    // Listes relues EN BASE à CHAQUE ouverture (get frais) — jamais servies d'un chargement périmé.
    fetch('/api/programmes', { credentials: 'include' })
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) { setNiveauxParCycle(d.niveaux_par_cycle || []); setMatieresParNiveau(d.matieres_par_niveau || []) } })
      .catch(() => {})
  }

  // Le prof travaille-t-il hors de son couple de profil ? (comparaison pure, rien de stocké)
  const coupleAjuste = sessionMatiere !== profilMatiere || params.niveau !== profilNiveau

  function validerAjust() {
    onMatiereChange(ajustTemp.matiere)
    onChange({ ...params, niveau: ajustTemp.niveau })
    setShowAjuster(false)
  }

  // Matières réellement rattachées au niveau choisi (get base, zéro copie) — la matière DÉPEND du niveau.
  const matieresDuNiveauAjust = (matieresParNiveau.find(x => x.niveau === ajustTemp.niveau)?.matieres) || []
  // Couple valide = un niveau + une matière qui existe POUR ce niveau. Sinon Valider reste grisé (on n'écrit rien).
  const coupleAjustValide = !!ajustTemp.niveau && matieresDuNiveauAjust.some(m => m.nom === ajustTemp.matiere)

  // Changer le niveau peut invalider la matière courante → on la vide si elle n'existe pas pour ce niveau.
  function choisirNiveauAjust(nom) {
    const mats = (matieresParNiveau.find(x => x.niveau === nom)?.matieres) || []
    setAjustTemp(t => ({ niveau: nom, matiere: mats.some(m => m.nom === t.matiere) ? t.matiere : '' }))
  }

  // On ne SORT PAS du cycle : le menu Niveau ne propose que les niveaux du cycle du niveau courant du prof.
  // Le lien cycle→niveaux vient de la base (/api/programmes → niveaux_par_cycle) ; on garde le SEUL groupe
  // qui contient params.niveau, filtré sur les niveaux disponibles. Zéro dur : le cycle est déduit, pas écrit.
  const cycleCourant = niveauxParCycle.find(g => g.niveaux.some(n => n.nom === params.niveau))
  const niveauxDuCycle = cycleCourant
    ? [{ ...cycleCourant, niveaux: cycleCourant.niveaux.filter(n => n.refDisponible !== false) }]
    : []

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
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
          {coupleAjuste && (
            <button
              type="button"
              onClick={onRevenirProfil}
              title="Revenir à la classe et à la matière de votre profil."
              style={{
                background: 'none', border: 'none', padding: 0, fontSize: '12px',
                color: '#64748b', textDecoration: 'underline', cursor: 'pointer', whiteSpace: 'nowrap',
              }}
            >
              Revenir à mon profil
            </button>
          )}
          <button
            type="button"
            onClick={ouvrirAjuster}
            title="Générer cette activité pour une autre classe de votre cycle ou une autre matière — votre profil n'est pas modifié."
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '6px',
              background: '#eff6ff', border: '1px solid #1F6EEB', borderRadius: '6px',
              padding: '6px 12px', fontSize: '13px', color: '#1F6EEB', fontWeight: 600,
              cursor: 'pointer', whiteSpace: 'nowrap', flexShrink: 0,
            }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>
            </svg>
            Changer la classe ou la matière
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">

        <div style={{
          outline: accentType ? '2px solid #1F6EEB' : '2px solid transparent',
          outlineOffset: '3px', borderRadius: 6, transition: 'outline-color 0.25s ease',
        }}>
          <label className="block text-xs text-gray-500 mb-1">Type d'activité</label>
          <select
            className="w-full border border-gray-300 rounded p-2 text-sm"
            value={params.activite_type_id ?? ''}
            onChange={e => handleActivite(Number(e.target.value))}
          >
            {activites.map(a => (
              <option key={a.id} value={a.id}>{a.label}</option>
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
            aSchool génère une réponse-type après chaque question, que le professeur adapte à sa classe.
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
              <div className="text-sm font-semibold text-gray-800">Changer la classe ou la matière</div>
              <div className="text-xs text-gray-400 mt-0.5">Pour cette activité seulement — votre profil reste inchangé.</div>
            </div>

            <div className="flex flex-col gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Niveau de la classe</label>
                <select
                  className="w-full border border-gray-300 rounded p-2 text-sm"
                  value={ajustTemp.niveau}
                  onChange={e => choisirNiveauAjust(e.target.value)}
                >
                  <option value="">— choisir un niveau —</option>
                  {niveauxDuCycle.map(grp => (
                    <optgroup key={grp.cycle} label={grp.cycle}>
                      {grp.niveaux.map(n => <option key={n.id} value={n.nom}>{n.nom}</option>)}
                    </optgroup>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Matière</label>
                <select
                  className="w-full border border-gray-300 rounded p-2 text-sm"
                  value={ajustTemp.matiere}
                  onChange={e => setAjustTemp(t => ({ ...t, matiere: e.target.value }))}
                  disabled={!ajustTemp.niveau}
                >
                  <option value="">{ajustTemp.niveau ? '— choisir une matière —' : '— choisis d’abord un niveau —'}</option>
                  {matieresDuNiveauAjust.map(m => <option key={m.id} value={m.nom}>{m.nom}</option>)}
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
                disabled={!coupleAjustValide}
                title={coupleAjustValide ? 'Valider les ajustements pour cette activité' : 'Choisis un niveau et une matière valides'}
                style={{
                  padding: '7px 16px', fontSize: '13px', borderRadius: '6px',
                  border: 'none', background: coupleAjustValide ? 'var(--bleu)' : '#cbd5e1',
                  color: '#fff', cursor: coupleAjustValide ? 'pointer' : 'not-allowed', fontWeight: 600,
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
