import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { apiFetch, TIMEOUT_STD } from '../utils/api.js'
import { matieresDuNiveau, matiereIncoherente, profilPretAValider, niveauxRefDisponibles, niveauDisponible } from '../utils/profil.js'
import { showError } from '../errorDialog.js'

const LANGUES_LV = ['Anglais', 'Espagnol', 'Allemand', 'Italien', 'Portugais', 'Arabe', 'Chinois', 'Autre']

// Message de la modale bloquante quand niveau et matière ne vont pas ensemble.
// Langage prof : dit le PROBLÈME puis l'ACTION attendue. `cas` distingue l'ouverture
// (profil déjà incohérent) du changement de niveau (incohérence qu'on vient de créer).
function messageIncoherence(cas, niveau, matiere) {
  const probleme = cas === 'ouverture'
    ? `Votre profil associe la matière « ${matiere} » au niveau « ${niveau} ».\nCe niveau ne propose pas cette matière.`
    : `Vous venez de passer au niveau « ${niveau} ».\nLa matière « ${matiere} » n'y est pas enseignée.`
  return `${probleme}\n\nChoisissez la matière que vous enseignez à ce niveau, puis enregistrez.`
}

// Modale quand le niveau du profil hérité n'est plus disponible (pas de référentiel, donc caché).
function messageNiveauIndisponible(niveau) {
  return `Votre niveau « ${niveau} » n'est pas (ou plus) disponible.\n\n`
    + `Choisissez un niveau disponible, indiquez votre matière, puis enregistrez.`
}

export default function MonProfil({ onNavigate }) {
  const { user, setUser } = useAuth()
  const [form, setForm] = useState({
    prenom:    user?.prenom    || '',
    nom:       user?.nom       || '',
    subject:   user?.subject   || '',
    niveau:    user?.niveau    || '',
    langue_lv: user?.langue_lv || '',
    mobile:    user?.mobile    || '',
  })
  const [saving, setSaving] = useState(false)
  const [erreur, setErreur] = useState(null)
  const [niveauxParCycle, setNiveauxParCycle]     = useState([])
  const [matieresParCycle, setMatieresParCycle]   = useState([])   // repli « tout groupé » sans niveau
  const [matieresParNiveau, setMatieresParNiveau] = useState([])   // scope fin = programme du niveau

  useEffect(() => {
    apiFetch('/api/programmes', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(data => {
        if (!data) return
        const niveaux   = data.niveaux_par_cycle || []
        const parNiveau = data.matieres_par_niveau || []
        setNiveauxParCycle(niveaux)
        setMatieresParCycle(data.matieres_par_cycle || [])
        setMatieresParNiveau(parNiveau)
        // Déclencheur 1 (priorité) : niveau du profil hérité devenu INDISPONIBLE (non disponible,
        // donc caché — ex. Master) → on vide niveau + matière, le prof doit tout re-choisir.
        if (form.niveau && !niveauDisponible(niveaux, form.niveau)) {
          showError(messageNiveauIndisponible(form.niveau))
          setForm(f => ({ ...f, niveau: '', subject: '' }))
        // Déclencheur 2 : niveau OK mais matière incohérente (ex. Français + un niveau réel).
        } else if (matiereIncoherente(parNiveau, form.niveau, form.subject)) {
          showError(messageIncoherence('ouverture', form.niveau, form.subject))
          setForm(f => ({ ...f, subject: '' }))
        }
      })
      .catch(() => {})
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps -- check à l'ouverture, sur le profil initial

  // Matière en cascade sur le NIVEAU choisi (helper pur testé : utils/profil.js).
  // null = pas de niveau / niveau inconnu → on montre tout, groupé par cycle (repli).
  const matieresNiveau    = matieresDuNiveau(matieresParNiveau, form.niveau)
  const matieresAffichees = matieresNiveau ?? matieresParCycle.flatMap(g => g.matieres)
  const peutValider       = profilPretAValider(matieresParNiveau, form.niveau, form.subject)

  function set(field, value) {
    setForm(f => ({ ...f, [field]: value }))
  }

  // Changer de niveau peut rendre la matière incohérente (matière hors du programme du
  // nouveau niveau) → modale bloquante + matière vidée (le prof DOIT en rechoisir une).
  // (Les niveaux non disponibles ne sont pas dans la liste → impossible d'en choisir un ici.)
  function changerNiveau(value) {
    const incoherent = matiereIncoherente(matieresParNiveau, value, form.subject)
    if (incoherent) showError(messageIncoherence('changement', value, form.subject))
    setForm(f => ({ ...f, niveau: value, subject: incoherent ? '' : f.subject }))
  }

  async function handleValider(e) {
    e.preventDefault()
    setSaving(true)
    setErreur(null)
    try {
      const res = await apiFetch('/api/user/profile', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(form),
      })
      if (!res.ok) throw new Error('Erreur lors de la sauvegarde.')
      setUser({ ...user, ...form })
      onNavigate('accueil')
    } catch (e) {
      setErreur(e.message)
      setSaving(false)
    }
  }

  return (
    <section className="bg-white rounded border border-gray-200 p-6" style={{ maxWidth: 480 }}>
      <div className="section-title mb-5">Mon profil</div>

      {erreur && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm mb-4">{erreur}</div>
      )}

      <form onSubmit={handleValider} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Prénom</label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded p-2 text-sm"
              value={form.prenom}
              onChange={e => set('prenom', e.target.value)}
              placeholder="Votre prénom"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Nom</label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded p-2 text-sm"
              value={form.nom}
              onChange={e => set('nom', e.target.value)}
              placeholder="Votre nom"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">E-mail</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded p-2 text-sm"
            value={user?.email || ''}
            readOnly
            style={{ background: '#f8fafc', color: '#94a3b8' }}
          />
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">
            Mobile <span className="text-gray-400">(optionnel)</span>
          </label>
          <input
            type="tel"
            className="w-full border border-gray-300 rounded p-2 text-sm"
            value={form.mobile}
            onChange={e => set('mobile', e.target.value)}
            placeholder="06 00 00 00 00"
          />
        </div>

        {/* Niveau d'abord : il détermine le cycle, donc la liste des matières. */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Niveau par défaut</label>
          <select
            className="w-full border border-gray-300 rounded p-2 text-sm bg-white"
            value={form.niveau}
            onChange={e => changerNiveau(e.target.value)}
          >
            <option value="">— Choisissez —</option>
            {niveauxRefDisponibles(niveauxParCycle).map(grp => (
              <optgroup key={grp.cycle} label={grp.cycle}>
                {grp.niveaux.map(n => <option key={n.id} value={n.nom}>{n.nom}</option>)}
              </optgroup>
            ))}
          </select>
        </div>

        {/* Matière : filtrée sur le NIVEAU choisi (sinon tout, groupé par cycle). */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Matière enseignée</label>
          <select
            className="w-full border border-gray-300 rounded p-2 text-sm bg-white"
            value={form.subject}
            onChange={e => set('subject', e.target.value)}
          >
            <option value="">— Choisissez —</option>
            {matieresNiveau
              ? matieresNiveau.map(m => <option key={m.id} value={m.nom}>{m.nom}</option>)
              : matieresParCycle.map(grp => (
                  <optgroup key={grp.cycle} label={grp.cycle}>
                    {grp.matieres.map(m => <option key={m.id} value={m.nom}>{m.nom}</option>)}
                  </optgroup>
                ))}
          </select>
        </div>

        {form.subject === 'Langues Vivantes (LV)' && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Langue enseignée</label>
            <select
              className="w-full border border-gray-300 rounded p-2 text-sm bg-white"
              value={form.langue_lv}
              onChange={e => set('langue_lv', e.target.value)}
            >
              <option value="">— Précisez la langue —</option>
              {LANGUES_LV.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-1">
          <button
            type="button"
            title="Annuler les modifications et revenir à l'accueil"
            onClick={() => onNavigate('accueil')}
            className="btn-secondary"
            disabled={saving}
          >
            Annuler
          </button>
          <button
            type="submit"
            title={peutValider
              ? "Enregistrer le profil et revenir à l'accueil"
              : "Choisissez une matière correspondant à votre niveau pour pouvoir enregistrer"}
            className="btn-primary"
            disabled={saving || !peutValider}
          >
            {saving ? 'Enregistrement…' : 'Valider'}
          </button>
        </div>
      </form>
    </section>
  )
}
