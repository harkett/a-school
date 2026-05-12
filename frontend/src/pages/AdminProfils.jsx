import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

const MATIERES = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']
const NIVEAUX  = ['6e', '5e', '4e', '3e', '2nde', '1ère', 'Terminale', 'Supérieur']

const IconMail  = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
const IconEdit  = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
const IconTrash = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
const IconKey   = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
const IconPower = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg>
const IconCheck = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>

function SortTh({ label, sKey, current, dir, onSort, style }) {
  const active = current === sKey
  return (
    <th
      onClick={() => onSort(sKey)}
      className="px-3 py-3 font-medium"
      style={{ cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap', ...style }}
      title={`Trier par ${label}`}
    >
      {label}{active ? (dir === 'asc' ? ' ↑' : ' ↓') : ' ·'}
    </th>
  )
}

export default function AdminProfils() {
  const [users, setUsers]           = useState([])
  const [loading, setLoading]       = useState(true)
  const [filterText, setFilterText] = useState('')
  const [filterMatiere, setFilterMatiere] = useState('')
  const [filterStatut, setFilterStatut]   = useState('tous')
  const [sortKey, setSortKey]       = useState('created_at')
  const [sortDir, setSortDir]       = useState('desc')
  const [editing, setEditing]       = useState(null)
  const [editForm, setEditForm]     = useState({})
  const [saving, setSaving]         = useState(false)
  const [deleting, setDeleting]     = useState(null)
  const [resetting, setResetting]   = useState(null)
  const [toggling, setToggling]     = useState(null)
  const [verifying, setVerifying]   = useState(null)
  const [emailModal, setEmailModal] = useState(null)
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

  function handleSort(key) {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const filtered = users.filter(u => {
    const text = filterText.toLowerCase()
    const matchText = !text ||
      u.email.toLowerCase().includes(text) ||
      (u.prenom || '').toLowerCase().includes(text) ||
      (u.nom || '').toLowerCase().includes(text)
    const matchMatiere = !filterMatiere || u.subject === filterMatiere
    const matchStatut  = filterStatut === 'tous'
      || (filterStatut === 'actifs'        ? (u.is_verified && u.is_active)
      : filterStatut === 'inactifs'        ? (u.is_verified && !u.is_active)
      : filterStatut === 'non_verifies'    ? !u.is_verified
      : true)
    return matchText && matchMatiere && matchStatut
  })

  const displayed = [...filtered].sort((a, b) => {
    if (sortKey === 'nb_activites') {
      const diff = (a.nb_activites || 0) - (b.nb_activites || 0)
      return sortDir === 'asc' ? diff : -diff
    }
    let va = String(a[sortKey] ?? '')
    let vb = String(b[sortKey] ?? '')
    if (va === '—') va = ''
    if (vb === '—') vb = ''
    const cmp = va.localeCompare(vb, 'fr')
    return sortDir === 'asc' ? cmp : -cmp
  })

  function startEdit(u) {
    setEditing(u.email)
    setEditForm({ prenom: u.prenom, nom: u.nom, subject: u.subject, niveau: u.niveau })
  }

  async function openEmailModal(u) {
    const res = await fetchWithTimeout('/api/admin/settings', { credentials: 'include' })
    const settings = await res.json()
    setEmailForm({ subject: settings.welcome_email_subject || '', body: settings.welcome_email_body || '' })
    setEmailModal({ email: u.email, prenom: u.prenom })
  }

  async function sendEmail() {
    setSending(true)
    try {
      const res = await fetchWithTimeout(`/api/admin/user/${encodeURIComponent(emailModal.email)}/send-email`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        credentials: 'include', body: JSON.stringify(emailForm),
      })
      if (res.ok) setEmailModal(null)
    } finally { setSending(false) }
  }

  async function saveEdit(email) {
    setSaving(true)
    try {
      const res = await fetchWithTimeout(`/api/admin/user/${encodeURIComponent(email)}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        credentials: 'include', body: JSON.stringify(editForm),
      })
      if (res.ok) { setUsers(users.map(u => u.email === email ? { ...u, ...editForm } : u)); setEditing(null) }
    } finally { setSaving(false) }
  }

  async function deleteUser(email) {
    if (!window.confirm(`Supprimer définitivement le compte de ${email} ?\n\nToutes ses données (activités, feedbacks, tokens) seront effacées.`)) return
    setDeleting(email)
    try {
      const res = await fetchWithTimeout(`/api/admin/user/${encodeURIComponent(email)}`, { method: 'DELETE', credentials: 'include' })
      if (res.ok) setUsers(users.filter(u => u.email !== email))
    } finally { setDeleting(null) }
  }

  async function resetPassword(email) {
    if (!window.confirm(`Envoyer un lien de réinitialisation de mot de passe à ${email} ?`)) return
    setResetting(email)
    try {
      await fetchWithTimeout(`/api/admin/user/${encodeURIComponent(email)}/reset-password`, { method: 'POST', credentials: 'include' })
    } finally { setResetting(null) }
  }

  async function verifyUser(email) {
    setVerifying(email)
    try {
      const res = await fetchWithTimeout(`/api/admin/user/${encodeURIComponent(email)}/verify`, { method: 'POST', credentials: 'include' })
      if (res.ok) setUsers(users.map(u => u.email === email ? { ...u, is_verified: true, is_active: true } : u))
    } finally { setVerifying(null) }
  }

  async function toggleActive(email) {
    setToggling(email)
    try {
      const res = await fetchWithTimeout(`/api/admin/user/${encodeURIComponent(email)}/toggle-active`, { method: 'PATCH', credentials: 'include' })
      const data = await res.json()
      if (res.ok) setUsers(users.map(u => u.email === email ? { ...u, is_active: data.is_active } : u))
    } finally { setToggling(null) }
  }

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  const nbInactifs    = users.filter(u => u.is_verified && !u.is_active).length
  const nbNonVerifies = users.filter(u => !u.is_verified).length

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h2 className="text-sm font-semibold text-gray-700">
          Profils profs
          <span className="ml-2 text-xs font-normal text-gray-400">({displayed.length} / {users.length})</span>
          {nbInactifs > 0 && (
            <span style={{ marginLeft: 8, padding: '2px 8px', borderRadius: 99, fontSize: 11, background: '#fee2e2', color: '#dc2626', fontWeight: 700 }}>
              {nbInactifs} désactivé{nbInactifs > 1 ? 's' : ''}
            </span>
          )}
          {nbNonVerifies > 0 && (
            <span style={{ marginLeft: 6, padding: '2px 8px', borderRadius: 99, fontSize: 11, background: '#fef9c3', color: '#a16207', fontWeight: 700 }}>
              {nbNonVerifies} non vérifié{nbNonVerifies > 1 ? 's' : ''}
            </span>
          )}
        </h2>
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        <input
          type="text"
          placeholder="Nom, prénom ou email…"
          value={filterText}
          onChange={e => setFilterText(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm flex-1 min-w-32"
        />
        <select value={filterMatiere} onChange={e => setFilterMatiere(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm bg-white">
          <option value="">Toutes les matières</option>
          {MATIERES.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
        <select value={filterStatut} onChange={e => setFilterStatut(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm bg-white">
          <option value="tous">Tous</option>
          <option value="actifs">Actifs</option>
          <option value="inactifs">Désactivés</option>
          <option value="non_verifies">Non vérifiés</option>
        </select>
      </div>

      {displayed.length === 0 ? (
        <p className="text-sm text-gray-400">Aucun prof trouvé.</p>
      ) : (
        <div className="rounded-lg border border-gray-200" style={{ overflow: 'hidden' }}>
          <table className="w-full text-sm table-fixed">
            <colgroup>
              <col style={{ width: '14%' }} />
              <col style={{ width: '19%' }} />
              <col style={{ width: '13%' }} />
              <col style={{ width: '8%' }} />
              <col style={{ width: '7%' }} />
              <col style={{ width: '9%' }} />
              <col style={{ width: '12%' }} />
              <col style={{ width: '18%' }} />
            </colgroup>
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide border-b border-gray-200">
                <SortTh label="Profil"      sKey="prenom"       current={sortKey} dir={sortDir} onSort={handleSort} />
                <SortTh label="Email"       sKey="email"        current={sortKey} dir={sortDir} onSort={handleSort} />
                <SortTh label="Matière"     sKey="subject"      current={sortKey} dir={sortDir} onSort={handleSort} />
                <SortTh label="Niveau"      sKey="niveau"       current={sortKey} dir={sortDir} onSort={handleSort} />
                <SortTh label="Activités"   sKey="nb_activites" current={sortKey} dir={sortDir} onSort={handleSort} style={{ textAlign: 'center' }} />
                <SortTh label="Inscrit"     sKey="created_at"   current={sortKey} dir={sortDir} onSort={handleSort} />
                <SortTh label="Dernière co" sKey="last_login"   current={sortKey} dir={sortDir} onSort={handleSort} />
                <th className="px-3 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {displayed.map(u => editing === u.email ? (
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
                  <td className="px-3 py-2 text-gray-400 text-xs text-center">{u.nb_activites ?? 0}</td>
                  <td className="px-3 py-2 text-gray-400 text-xs">{u.created_at}</td>
                  <td className="px-3 py-2 text-gray-400 text-xs">{u.last_login}</td>
                  <td className="px-3 py-2">
                    <div className="flex gap-1">
                      <button onClick={() => saveEdit(u.email)} disabled={saving} title="Enregistrer"
                        style={{ background: '#1F6EEB', color: 'white', border: 'none', borderRadius: 6, padding: '4px 10px', fontSize: 11, cursor: 'pointer', opacity: saving ? 0.6 : 1 }}>
                        {saving ? '…' : 'OK'}
                      </button>
                      <button onClick={() => setEditing(null)} title="Annuler"
                        style={{ background: 'white', color: '#374151', border: '1px solid #d1d5db', borderRadius: 6, padding: '4px 8px', fontSize: 11, cursor: 'pointer' }}>
                        ✕
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (
                <tr key={u.email}
                  style={{ background: !u.is_verified ? '#fefce8' : !u.is_active ? '#fff5f5' : undefined }}
                  className="hover:bg-gray-50 transition-colors">
                  <td className="px-3 py-3 truncate">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {!u.is_verified && (
                        <span style={{ padding: '1px 5px', borderRadius: 3, fontSize: 9, fontWeight: 700, background: '#fef9c3', color: '#92400e', flexShrink: 0, textTransform: 'uppercase', letterSpacing: '0.3px' }}>Non vérifié</span>
                      )}
                      {u.is_verified && !u.is_active && (
                        <span style={{ padding: '1px 5px', borderRadius: 3, fontSize: 9, fontWeight: 700, background: '#fee2e2', color: '#dc2626', flexShrink: 0, textTransform: 'uppercase', letterSpacing: '0.3px' }}>Off</span>
                      )}
                      <span style={{ color: u.is_verified && u.is_active ? '#374151' : '#9ca3af' }}>
                        {(u.prenom || u.nom) ? `${u.prenom} ${u.nom}`.trim() : <span style={{ color: '#d1d5db' }}>—</span>}
                      </span>
                    </div>
                  </td>
                  <td className="px-3 py-3 text-gray-500 truncate" title={u.email}>{u.email}</td>
                  <td className="px-3 py-3 text-gray-700 truncate">{u.subject || <span style={{ color: '#d1d5db' }}>—</span>}</td>
                  <td className="px-3 py-3 text-gray-700">{u.niveau || <span style={{ color: '#d1d5db' }}>—</span>}</td>
                  <td className="px-3 py-3 text-center">
                    <span style={{ fontSize: 12, fontWeight: u.nb_activites > 0 ? 600 : 400, color: u.nb_activites > 0 ? '#1d4ed8' : '#d1d5db' }}>
                      {u.nb_activites ?? 0}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-gray-400 text-xs">{u.created_at}</td>
                  <td className="px-3 py-3 text-gray-400 text-xs">{u.last_login}</td>
                  <td className="px-3 py-3">
                    <div className="flex gap-1 justify-end">
                      {!u.is_verified ? (
                        <>
                          <button onClick={() => verifyUser(u.email)} disabled={verifying === u.email}
                            title="Valider manuellement ce compte (bypass email)"
                            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 26, height: 26, background: '#f0fdf4', color: '#15803d', border: '1px solid #bbf7d0', borderRadius: 5, cursor: 'pointer', opacity: verifying === u.email ? 0.5 : 1 }}>
                            {verifying === u.email ? '…' : <IconCheck />}
                          </button>
                          <button onClick={() => openEmailModal(u)} title="Envoyer un email à ce prof"
                            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 26, height: 26, background: 'white', color: '#1F6EEB', border: '1px solid #bfdbfe', borderRadius: 5, cursor: 'pointer' }}>
                            <IconMail />
                          </button>
                          <button onClick={() => deleteUser(u.email)} disabled={deleting === u.email} title="Supprimer ce compte définitivement"
                            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 26, height: 26, background: 'white', color: '#dc2626', border: '1px solid #fca5a5', borderRadius: 5, cursor: 'pointer', opacity: deleting === u.email ? 0.5 : 1 }}>
                            {deleting === u.email ? '…' : <IconTrash />}
                          </button>
                        </>
                      ) : (
                        <>
                          <button onClick={() => startEdit(u)} title="Éditer le profil"
                            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 26, height: 26, background: 'white', color: '#374151', border: '1px solid #d1d5db', borderRadius: 5, cursor: 'pointer' }}>
                            <IconEdit />
                          </button>
                          <button onClick={() => resetPassword(u.email)} disabled={resetting === u.email} title="Envoyer un lien de réinitialisation du mot de passe"
                            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 26, height: 26, background: 'white', color: '#7c3aed', border: '1px solid #ddd6fe', borderRadius: 5, cursor: 'pointer', opacity: resetting === u.email ? 0.5 : 1 }}>
                            {resetting === u.email ? '…' : <IconKey />}
                          </button>
                          <button onClick={() => toggleActive(u.email)} disabled={toggling === u.email} title={u.is_active ? 'Désactiver ce compte' : 'Réactiver ce compte'}
                            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 26, height: 26, background: 'white', color: u.is_active ? '#d97706' : '#15803d', border: `1px solid ${u.is_active ? '#fde68a' : '#bbf7d0'}`, borderRadius: 5, cursor: 'pointer', opacity: toggling === u.email ? 0.5 : 1 }}>
                            {toggling === u.email ? '…' : <IconPower />}
                          </button>
                          <button onClick={() => openEmailModal(u)} title="Envoyer un email à ce prof"
                            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 26, height: 26, background: 'white', color: '#1F6EEB', border: '1px solid #bfdbfe', borderRadius: 5, cursor: 'pointer' }}>
                            <IconMail />
                          </button>
                          <button onClick={() => deleteUser(u.email)} disabled={deleting === u.email} title="Supprimer ce compte définitivement"
                            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 26, height: 26, background: 'white', color: '#dc2626', border: '1px solid #fca5a5', borderRadius: 5, cursor: 'pointer', opacity: deleting === u.email ? 0.5 : 1 }}>
                            {deleting === u.email ? '…' : <IconTrash />}
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {emailModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
          <div style={{ background: 'white', borderRadius: 12, padding: 28, width: '100%', maxWidth: 520, boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
            <h3 style={{ margin: '0 0 4px', fontSize: 15, fontWeight: 600, color: '#1e293b' }}>Envoyer un email</h3>
            <p style={{ margin: '0 0 20px', fontSize: 12, color: '#94a3b8' }}>Destinataire : <strong>{emailModal.email}</strong></p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 500, color: '#64748b', marginBottom: 4 }}>Objet</label>
                <input type="text" value={emailForm.subject} onChange={e => setEmailForm(f => ({ ...f, subject: e.target.value }))}
                  style={{ width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '7px 10px', fontSize: 13, boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 500, color: '#64748b', marginBottom: 4 }}>Message</label>
                <textarea value={emailForm.body} onChange={e => setEmailForm(f => ({ ...f, body: e.target.value }))} rows={8}
                  style={{ width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '7px 10px', fontSize: 13, resize: 'vertical', lineHeight: 1.6, boxSizing: 'border-box', fontFamily: 'inherit' }} />
                <p style={{ fontSize: 11, color: '#94a3b8', margin: '4px 0 0' }}>
                  Variables : <code style={{ background: '#f1f5f9', borderRadius: 3, padding: '1px 4px' }}>{'{prenom}'}</code>{' '}
                  <code style={{ background: '#f1f5f9', borderRadius: 3, padding: '1px 4px' }}>{'{email}'}</code>
                </p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10, marginTop: 20, justifyContent: 'flex-end' }}>
              <button onClick={() => setEmailModal(null)}
                style={{ background: 'white', color: '#374151', border: '1px solid #d1d5db', borderRadius: 7, padding: '8px 18px', fontSize: 13, cursor: 'pointer' }}>
                Annuler
              </button>
              <button onClick={sendEmail} disabled={sending || !emailForm.subject.trim() || !emailForm.body.trim()}
                style={{ background: '#1F6EEB', color: 'white', border: 'none', borderRadius: 7, padding: '8px 18px', fontSize: 13, fontWeight: 500, cursor: 'pointer', opacity: (sending || !emailForm.subject.trim() || !emailForm.body.trim()) ? 0.6 : 1 }}>
                {sending ? 'Envoi…' : 'Envoyer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
