import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const MATIERES   = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']
const NIVEAUX    = ['6e', '5e', '4e', '3e', '2nde', '1ère', 'Terminale', 'Supérieur']
const LANGUES_LV = ['Anglais', 'Espagnol', 'Allemand', 'Italien', 'Portugais', 'Arabe', 'Chinois', 'Autre']

export default function MonProfil() {
  const { user, setUser } = useAuth()
  const [form, setForm] = useState({
    prenom:    user?.prenom    || '',
    nom:       user?.nom       || '',
    subject:   user?.subject   || '',
    niveau:    user?.niveau    || '',
    langue_lv: user?.langue_lv || '',
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved]   = useState(false)
  const [erreur, setErreur] = useState(null)

  function set(field, value) {
    setForm(f => ({ ...f, [field]: value }))
    setSaved(false)
  }

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setErreur(null)
    try {
      const res = await fetch('/api/user/profile', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(form),
      })
      if (!res.ok) throw new Error('Erreur lors de la sauvegarde.')
      setUser({ ...user, ...form })
      setSaved(true)
    } catch (e) {
      setErreur(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="bg-white rounded border border-gray-200 p-6" style={{ maxWidth: 480 }}>
      <div className="section-title mb-5">Mon profil</div>

      {erreur && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm mb-4">{erreur}</div>
      )}
      {saved && (
        <div className="bg-green-50 border border-green-200 text-green-700 rounded p-3 text-sm mb-4">Profil mis à jour.</div>
      )}

      <form onSubmit={handleSave} className="flex flex-col gap-4">
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
          <label className="block text-xs text-gray-500 mb-1">Matière enseignée</label>
          <select
            className="w-full border border-gray-300 rounded p-2 text-sm bg-white"
            value={form.subject}
            onChange={e => set('subject', e.target.value)}
          >
            <option value="">— Choisissez —</option>
            {MATIERES.map(m => <option key={m} value={m}>{m}</option>)}
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

        <div>
          <label className="block text-xs text-gray-500 mb-1">Niveau par défaut</label>
          <select
            className="w-full border border-gray-300 rounded p-2 text-sm bg-white"
            value={form.niveau}
            onChange={e => set('niveau', e.target.value)}
          >
            <option value="">— Choisissez —</option>
            {NIVEAUX.map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>

        <div className="flex justify-end">
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Enregistrement…' : 'Enregistrer'}
          </button>
        </div>
      </form>
    </section>
  )
}
