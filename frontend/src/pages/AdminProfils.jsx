import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const MATIERES = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']
const NIVEAUX  = ['6e', '5e', '4e', '3e', '2nde', '1ère', 'Terminale', 'Supérieur']

export default function AdminProfils() {
  const [users, setUsers]           = useState([])
  const [loading, setLoading]       = useState(true)
  const [filterText, setFilterText] = useState('')
  const [filterMatiere, setFilterMatiere] = useState('')
  const [editing, setEditing]       = useState(null)
  const [editForm, setEditForm]     = useState({})
  const [saving, setSaving]         = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/users', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        return r.json()
      })
      .then(data => { if (data) setUsers(data) })
      .finally(() => setLoading(false))
  }, [navigate])

  const filtered = users.filter(u => {
    const text = filterText.toLowerCase()
    const matchText = !text ||
      u.email.toLowerCase().includes(text) ||
      u.prenom.toLowerCase().includes(text) ||
      u.nom.toLowerCase().includes(text)
    const matchMatiere = !filterMatiere || u.subject === filterMatiere
    return matchText && matchMatiere
  })

  function startEdit(u) {
    setEditing(u.email)
    setEditForm({ prenom: u.prenom, nom: u.nom, subject: u.subject, niveau: u.niveau })
  }

  async function saveEdit(email) {
    setSaving(true)
    try {
      const res = await fetch(`/api/admin/user/${encodeURIComponent(email)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(editForm),
      })
      if (res.ok) {
        setUsers(users.map(u => u.email === email ? { ...u, ...editForm } : u))
        setEditing(null)
      }
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-700 mb-4">
        Profils profs
        <span className="ml-2 text-xs font-normal text-gray-400">({filtered.length} / {users.length})</span>
      </h2>

      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Rechercher par nom, prénom ou email…"
          value={filterText}
          onChange={e => setFilterText(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm flex-1"
        />
        <select
          value={filterMatiere}
          onChange={e => setFilterMatiere(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm bg-white"
        >
          <option value="">Toutes les matières</option>
          {MATIERES.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-gray-400">Aucun prof trouvé.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-4 py-3 font-medium">Prénom</th>
                <th className="px-4 py-3 font-medium">Nom</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Matière</th>
                <th className="px-4 py-3 font-medium" title="Niveau par défaut choisi par le prof dans son profil — peut être modifié à chaque génération">Niveau défaut ↓</th>
                <th className="px-4 py-3 font-medium">Inscrit le</th>
                <th className="px-4 py-3 font-medium">Dernière connexion</th>
                <th className="px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map(u => editing === u.email ? (
                <tr key={u.email} style={{ background: '#eff6ff' }}>
                  <td className="px-3 py-2">
                    <input value={editForm.prenom} onChange={e => setEditForm(f => ({ ...f, prenom: e.target.value }))}
                      className="border border-gray-300 rounded px-2 py-1 text-sm w-full" placeholder="Prénom" />
                  </td>
                  <td className="px-3 py-2">
                    <input value={editForm.nom} onChange={e => setEditForm(f => ({ ...f, nom: e.target.value }))}
                      className="border border-gray-300 rounded px-2 py-1 text-sm w-full" placeholder="Nom" />
                  </td>
                  <td className="px-3 py-2 text-gray-400 text-xs">{u.email}</td>
                  <td className="px-3 py-2">
                    <select value={editForm.subject} onChange={e => setEditForm(f => ({ ...f, subject: e.target.value }))}
                      className="border border-gray-300 rounded px-2 py-1 text-sm w-full bg-white">
                      <option value="">—</option>
                      {MATIERES.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <select value={editForm.niveau} onChange={e => setEditForm(f => ({ ...f, niveau: e.target.value }))}
                      className="border border-gray-300 rounded px-2 py-1 text-sm w-full bg-white">
                      <option value="">—</option>
                      {NIVEAUX.map(n => <option key={n} value={n}>{n}</option>)}
                    </select>
                  </td>
                  <td className="px-3 py-2 text-gray-400 text-xs">{u.created_at}</td>
                  <td className="px-3 py-2 text-gray-400 text-xs">{u.last_login}</td>
                  <td className="px-3 py-2">
                    <div className="flex gap-2">
                      <button
                        onClick={() => saveEdit(u.email)}
                        disabled={saving}
                        title="Enregistrer les modifications"
                        style={{ background: '#1F6EEB', color: 'white', border: 'none', borderRadius: 6, padding: '4px 12px', fontSize: 12, cursor: 'pointer', opacity: saving ? 0.6 : 1 }}
                      >
                        {saving ? '…' : 'Enregistrer'}
                      </button>
                      <button
                        onClick={() => setEditing(null)}
                        title="Annuler"
                        style={{ background: 'white', color: '#374151', border: '1px solid #d1d5db', borderRadius: 6, padding: '4px 12px', fontSize: 12, cursor: 'pointer' }}
                      >
                        Annuler
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (
                <tr key={u.email} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-gray-700">{u.prenom || <span className="text-gray-300">—</span>}</td>
                  <td className="px-4 py-3 text-gray-700">{u.nom || <span className="text-gray-300">—</span>}</td>
                  <td className="px-4 py-3 text-gray-500">{u.email}</td>
                  <td className="px-4 py-3 text-gray-700">{u.subject || <span className="text-gray-300">—</span>}</td>
                  <td className="px-4 py-3 text-gray-700">{u.niveau || <span className="text-gray-300">—</span>}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{u.created_at}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{u.last_login}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => startEdit(u)}
                      title="Éditer le profil de ce prof"
                      style={{ background: 'white', color: '#374151', border: '1px solid #d1d5db', borderRadius: 6, padding: '4px 12px', fontSize: 12, cursor: 'pointer' }}
                    >
                      Éditer
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
