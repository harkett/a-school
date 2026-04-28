import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const MATIERES = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']
const NIVEAUX  = ['6e', '5e', '4e', '3e', '2nde', '1ère', 'Terminale', 'Supérieur']

const IconMail = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
    <polyline points="22,6 12,13 2,6"/>
  </svg>
)

const IconEdit = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
  </svg>
)

const IconTrash = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
    <path d="M10 11v6M14 11v6"/>
    <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
  </svg>
)

export default function AdminProfils() {
  const [users, setUsers]           = useState([])
  const [loading, setLoading]       = useState(true)
  const [filterText, setFilterText] = useState('')
  const [filterMatiere, setFilterMatiere] = useState('')
  const [editing, setEditing]       = useState(null)
  const [editForm, setEditForm]     = useState({})
  const [saving, setSaving]         = useState(false)
  const [deleting, setDeleting]     = useState(null)
  const [emailModal, setEmailModal] = useState(null) // { email, prenom }
  const [emailForm, setEmailForm]   = useState({ subject: '', body: '' })
  const [sending, setSending]       = useState(false)
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

  async function openEmailModal(u) {
    const res = await fetch('/api/admin/settings', { credentials: 'include' })
    const settings = await res.json()
    setEmailForm({
      subject: settings.welcome_email_subject || '',
      body:    settings.welcome_email_body    || '',
    })
    setEmailModal({ email: u.email, prenom: u.prenom })
  }

  async function sendEmail() {
    setSending(true)
    try {
      const res = await fetch(`/api/admin/user/${encodeURIComponent(emailModal.email)}/send-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(emailForm),
      })
      if (res.ok) setEmailModal(null)
    } finally {
      setSending(false)
    }
  }

  async function deleteUser(email) {
    if (!window.confirm(`Supprimer définitivement le compte de ${email} ?\n\nToutes ses données (activités, feedbacks, tokens) seront effacées.`)) return
    setDeleting(email)
    try {
      const res = await fetch(`/api/admin/user/${encodeURIComponent(email)}`, {
        method: 'DELETE',
        credentials: 'include',
      })
      if (res.ok) setUsers(users.filter(u => u.email !== email))
    } finally {
      setDeleting(null)
    }
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
        <div className="rounded-lg border border-gray-200">
          <table className="w-full text-sm table-fixed">
            <colgroup>
              <col style={{ width: '18%' }} />
              <col style={{ width: '22%' }} />
              <col style={{ width: '16%' }} />
              <col style={{ width: '10%' }} />
              <col style={{ width: '12%' }} />
              <col style={{ width: '14%' }} />
              <col style={{ width: '8%' }} />
            </colgroup>
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-3 py-3 font-medium">Profil</th>
                <th className="px-3 py-3 font-medium">Email</th>
                <th className="px-3 py-3 font-medium">Matière</th>
                <th className="px-3 py-3 font-medium" title="Niveau par défaut choisi par le prof">Niveau</th>
                <th className="px-3 py-3 font-medium">Inscrit le</th>
                <th className="px-3 py-3 font-medium">Dernière connexion</th>
                <th className="px-3 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map(u => editing === u.email ? (
                <tr key={u.email} style={{ background: '#eff6ff' }}>
                  <td className="px-3 py-2">
                    <div className="flex gap-1">
                      <input value={editForm.prenom} onChange={e => setEditForm(f => ({ ...f, prenom: e.target.value }))}
                        className="border border-gray-300 rounded px-2 py-1 text-sm w-1/2" placeholder="Prénom" />
                      <input value={editForm.nom} onChange={e => setEditForm(f => ({ ...f, nom: e.target.value }))}
                        className="border border-gray-300 rounded px-2 py-1 text-sm w-1/2" placeholder="Nom" />
                    </div>
                  </td>
                  <td className="px-3 py-2 text-gray-400 text-xs truncate">{u.email}</td>
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
                    <div className="flex gap-1">
                      <button
                        onClick={() => saveEdit(u.email)}
                        disabled={saving}
                        title="Enregistrer les modifications"
                        style={{ background: '#1F6EEB', color: 'white', border: 'none', borderRadius: 6, padding: '4px 10px', fontSize: 11, cursor: 'pointer', opacity: saving ? 0.6 : 1, whiteSpace: 'nowrap' }}
                      >
                        {saving ? '…' : 'OK'}
                      </button>
                      <button
                        onClick={() => setEditing(null)}
                        title="Annuler"
                        style={{ background: 'white', color: '#374151', border: '1px solid #d1d5db', borderRadius: 6, padding: '4px 8px', fontSize: 11, cursor: 'pointer' }}
                      >
                        ✕
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (
                <tr key={u.email} className="hover:bg-gray-50 transition-colors">
                  <td className="px-3 py-3 text-gray-700 truncate">
                    {(u.prenom || u.nom)
                      ? <span>{u.prenom} {u.nom}</span>
                      : <span className="text-gray-300">—</span>}
                  </td>
                  <td className="px-3 py-3 text-gray-500 truncate" title={u.email}>{u.email}</td>
                  <td className="px-3 py-3 text-gray-700 truncate">{u.subject || <span className="text-gray-300">—</span>}</td>
                  <td className="px-3 py-3 text-gray-700">{u.niveau || <span className="text-gray-300">—</span>}</td>
                  <td className="px-3 py-3 text-gray-400 text-xs">{u.created_at}</td>
                  <td className="px-3 py-3 text-gray-400 text-xs">{u.last_login}</td>
                  <td className="px-3 py-3">
                    <div className="flex gap-1 justify-end">
                      <button
                        onClick={() => startEdit(u)}
                        title="Éditer le profil"
                        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, background: 'white', color: '#374151', border: '1px solid #d1d5db', borderRadius: 6, cursor: 'pointer' }}
                      >
                        <IconEdit />
                      </button>
                      <button
                        onClick={() => openEmailModal(u)}
                        title="Envoyer un email à ce prof"
                        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, background: 'white', color: '#1F6EEB', border: '1px solid #bfdbfe', borderRadius: 6, cursor: 'pointer' }}
                      >
                        <IconMail />
                      </button>
                      <button
                        onClick={() => deleteUser(u.email)}
                        disabled={deleting === u.email}
                        title="Supprimer ce compte"
                        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, background: 'white', color: '#dc2626', border: '1px solid #fca5a5', borderRadius: 6, cursor: 'pointer', opacity: deleting === u.email ? 0.5 : 1 }}
                      >
                        {deleting === u.email ? '…' : <IconTrash />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal email */}
      {emailModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
          <div style={{ background: 'white', borderRadius: 12, padding: 28, width: '100%', maxWidth: 520, boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
            <h3 style={{ margin: '0 0 4px', fontSize: 15, fontWeight: 600, color: '#1e293b' }}>
              Envoyer un email
            </h3>
            <p style={{ margin: '0 0 20px', fontSize: 12, color: '#94a3b8' }}>
              Destinataire : <strong>{emailModal.email}</strong>
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 500, color: '#64748b', marginBottom: 4 }}>Objet</label>
                <input
                  type="text"
                  value={emailForm.subject}
                  onChange={e => setEmailForm(f => ({ ...f, subject: e.target.value }))}
                  style={{ width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '7px 10px', fontSize: 13, boxSizing: 'border-box' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 500, color: '#64748b', marginBottom: 4 }}>Message</label>
                <textarea
                  value={emailForm.body}
                  onChange={e => setEmailForm(f => ({ ...f, body: e.target.value }))}
                  rows={8}
                  style={{ width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '7px 10px', fontSize: 13, resize: 'vertical', lineHeight: 1.6, boxSizing: 'border-box', fontFamily: 'inherit' }}
                />
                <p style={{ fontSize: 11, color: '#94a3b8', margin: '4px 0 0' }}>
                  Variables : <code style={{ background: '#f1f5f9', borderRadius: 3, padding: '1px 4px' }}>{'{prenom}'}</code>{' '}
                  <code style={{ background: '#f1f5f9', borderRadius: 3, padding: '1px 4px' }}>{'{email}'}</code>
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, marginTop: 20, justifyContent: 'flex-end' }}>
              <button
                onClick={() => setEmailModal(null)}
                style={{ background: 'white', color: '#374151', border: '1px solid #d1d5db', borderRadius: 7, padding: '8px 18px', fontSize: 13, cursor: 'pointer' }}
              >
                Annuler
              </button>
              <button
                onClick={sendEmail}
                disabled={sending || !emailForm.subject.trim() || !emailForm.body.trim()}
                style={{ background: '#1F6EEB', color: 'white', border: 'none', borderRadius: 7, padding: '8px 18px', fontSize: 13, fontWeight: 500, cursor: 'pointer', opacity: (sending || !emailForm.subject.trim() || !emailForm.body.trim()) ? 0.6 : 1 }}
              >
                {sending ? 'Envoi…' : 'Envoyer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
