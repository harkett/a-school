import { useState } from 'react'

// Couple de travail (matière · niveau) + « Changer la classe ou la matière » — affiché dans la
// barre du haut de l'écran Créer, à gauche du bouton Générer. La modale relit les listes EN BASE
// à CHAQUE ouverture (get /api/programmes) ; Valider écrit le couple de SESSION seulement — le
// profil du prof n'est jamais modifié.
export default function CoupleBandeau({ sessionMatiere, niveau, profilMatiere, profilNiveau, onValider, onRevenirProfil }) {
  const [showAjuster, setShowAjuster] = useState(false)
  const [ajustTemp, setAjustTemp] = useState({ matiere: sessionMatiere, niveau })
  const [niveauxParCycle, setNiveauxParCycle] = useState([])
  const [matieresParNiveau, setMatieresParNiveau] = useState([])  // [{niveau, matieres:[{id,nom}]}] — filtre la matière par le niveau

  function ouvrirAjuster() {
    setAjustTemp({ matiere: sessionMatiere, niveau })
    setShowAjuster(true)
    // Listes relues EN BASE à CHAQUE ouverture (get frais) — jamais servies d'un chargement périmé.
    fetch('/api/programmes', { credentials: 'include' })
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) { setNiveauxParCycle(d.niveaux_par_cycle || []); setMatieresParNiveau(d.matieres_par_niveau || []) } })
      .catch(() => {})
  }

  // Le prof travaille-t-il hors de son couple de profil ? (comparaison pure, rien de stocké)
  const coupleAjuste = sessionMatiere !== profilMatiere || niveau !== profilNiveau

  function validerAjust() {
    onValider(ajustTemp.matiere, ajustTemp.niveau)
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
  // qui contient le niveau courant, filtré sur les niveaux disponibles. Zéro dur : le cycle est déduit, pas écrit.
  const cycleCourant = niveauxParCycle.find(g => g.niveaux.some(n => n.nom === niveau))
  const niveauxDuCycle = cycleCourant
    ? [{ ...cycleCourant, niveaux: cycleCourant.niveaux.filter(n => n.refDisponible !== false) }]
    : []

  return (
    <>
      <span className="text-sm text-gray-700" style={{ whiteSpace: 'nowrap' }}>
        <span className="font-medium">{sessionMatiere}</span>
        <span className="text-gray-400 mx-2">·</span>
        <span>{niveau}</span>
      </span>
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
        Changer niveau et/ou matière
      </button>

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
    </>
  )
}
