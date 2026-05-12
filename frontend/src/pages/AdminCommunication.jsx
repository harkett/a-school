import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchWithTimeout, TIMEOUT_GROQ, TIMEOUT_STD } from '../utils/api.js'

const MATIERES = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']

export default function AdminCommunication() {
  const [users, setUsers]               = useState([])
  const [loading, setLoading]           = useState(true)
  const [selected, setSelected]         = useState(new Set())
  const [filterText, setFilterText]     = useState('')
  const [filterMatiere, setFilterMatiere] = useState('')
  const [filterStatut, setFilterStatut] = useState('actifs')
  const [subject, setSubject]           = useState('')
  const [body, setBody]                 = useState('')
  const [sending, setSending]           = useState(false)
  const [result, setResult]             = useState(null)
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
      (u.prenom || '').toLowerCase().includes(text) ||
      (u.nom || '').toLowerCase().includes(text)
    const matchMatiere = !filterMatiere || u.subject === filterMatiere
    const matchStatut  = filterStatut === 'tous' || (filterStatut === 'actifs' ? u.is_active : !u.is_active)
    return matchText && matchMatiere && matchStatut
  })

  const filteredEmails     = filtered.map(u => u.email)
  const allFilteredSelected = filteredEmails.length > 0 && filteredEmails.every(e => selected.has(e))

  function toggleOne(email) {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(email)) next.delete(email)
      else next.add(email)
      return next
    })
  }

  function toggleAll() {
    setSelected(prev => {
      const next = new Set(prev)
      if (allFilteredSelected) filteredEmails.forEach(e => next.delete(e))
      else filteredEmails.forEach(e => next.add(e))
      return next
    })
  }

  async function send() {
    if (!subject.trim() || !body.trim() || selected.size === 0) return
    setSending(true)
    setResult(null)
    try {
      const res = await fetchWithTimeout('/api/admin/mail-groupe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ emails: [...selected], subject, body }),
      })
      const data = await res.json()
      setResult(data)
    } finally {
      setSending(false)
    }
  }

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  const canSend = selected.size > 0 && subject.trim() && body.trim()

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-sm font-semibold text-gray-700">Mail groupé</h2>
      </div>

      {/* Compose */}
      <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', padding: 24, marginBottom: 24 }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 13, fontWeight: 600, color: '#1e293b' }}>Composer le message</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 500, color: '#64748b', marginBottom: 4 }}>Objet</label>
            <input
              type="text"
              value={subject}
              onChange={e => setSubject(e.target.value)}
              placeholder="Objet du message…"
              style={{ width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '7px 10px', fontSize: 13, boxSizing: 'border-box' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 500, color: '#64748b', marginBottom: 4 }}>Message</label>
            <textarea
              value={body}
              onChange={e => setBody(e.target.value)}
              rows={7}
              placeholder="Votre message…"
              style={{ width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '7px 10px', fontSize: 13, resize: 'vertical', lineHeight: 1.6, boxSizing: 'border-box', fontFamily: 'inherit' }}
            />
            <p style={{ fontSize: 11, color: '#94a3b8', margin: '4px 0 0' }}>
              Variables :{' '}
              <code style={{ background: '#f1f5f9', borderRadius: 3, padding: '1px 4px' }}>{'{prenom}'}</code>{' '}
              <code style={{ background: '#f1f5f9', borderRadius: 3, padding: '1px 4px' }}>{'{email}'}</code>
            </p>
          </div>
        </div>
      </div>

      {/* Destinataires */}
      <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
          <h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
            Destinataires
            {selected.size > 0 && (
              <span style={{ marginLeft: 8, padding: '2px 8px', borderRadius: 99, fontSize: 11, background: '#dbeafe', color: '#1d4ed8', fontWeight: 700 }}>
                {selected.size} sélectionné{selected.size > 1 ? 's' : ''}
              </span>
            )}
          </h3>
          <button
            onClick={send}
            disabled={sending || !canSend}
            title={!canSend ? 'Remplissez l\'objet, le message et sélectionnez au moins un prof' : `Envoyer à ${selected.size} prof${selected.size > 1 ? 's' : ''}`}
            style={{
              background: '#1F6EEB', color: 'white !important', border: 'none', borderRadius: 7,
              padding: '8px 18px', fontSize: 13, fontWeight: 500, cursor: canSend && !sending ? 'pointer' : 'not-allowed',
              opacity: (sending || !canSend) ? 0.5 : 1,
            }}
          >
            {sending ? 'Envoi en cours…' : `Envoyer à ${selected.size} prof${selected.size > 1 ? 's' : ''}`}
          </button>
        </div>

        {result && (
          <div style={{
            marginBottom: 16, padding: '10px 14px', borderRadius: 7,
            background: result.errors.length === 0 ? '#f0fdf4' : '#fff7ed',
            border: `1px solid ${result.errors.length === 0 ? '#bbf7d0' : '#fed7aa'}`,
            fontSize: 13, color: result.errors.length === 0 ? '#15803d' : '#c2410c',
          }}>
            {result.sent} email{result.sent > 1 ? 's' : ''} envoyé{result.sent > 1 ? 's' : ''} sur {result.total}.
            {result.errors.length > 0 && ` ${result.errors.length} erreur(s) : ${result.errors.join(', ')}`}
          </div>
        )}

        <div className="flex gap-2 mb-3 flex-wrap">
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
          </select>
        </div>

        {filtered.length === 0 ? (
          <p className="text-sm text-gray-400">Aucun prof trouvé.</p>
        ) : (
          <div className="rounded-lg border border-gray-200" style={{ overflow: 'hidden' }}>
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide border-b border-gray-200">
                  <th className="px-3 py-3" style={{ width: 40 }}>
                    <input
                      type="checkbox"
                      checked={allFilteredSelected}
                      onChange={toggleAll}
                      title={allFilteredSelected ? 'Tout désélectionner' : 'Tout sélectionner'}
                      style={{ cursor: 'pointer' }}
                    />
                  </th>
                  <th className="px-3 py-3">Profil</th>
                  <th className="px-3 py-3">Email</th>
                  <th className="px-3 py-3">Matière</th>
                  <th className="px-3 py-3">Niveau</th>
                  <th className="px-3 py-3">Statut</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map(u => (
                  <tr
                    key={u.email}
                    onClick={() => toggleOne(u.email)}
                    style={{
                      background: selected.has(u.email) ? '#eff6ff' : (u.is_active ? undefined : '#fff5f5'),
                      cursor: 'pointer',
                    }}
                    className="hover:bg-blue-50 transition-colors"
                  >
                    <td className="px-3 py-3" style={{ width: 40 }} onClick={e => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selected.has(u.email)}
                        onChange={() => toggleOne(u.email)}
                        style={{ cursor: 'pointer' }}
                      />
                    </td>
                    <td className="px-3 py-3">
                      <span style={{ color: u.is_active ? '#374151' : '#9ca3af', fontSize: 13 }}>
                        {(u.prenom || u.nom)
                          ? `${u.prenom || ''} ${u.nom || ''}`.trim()
                          : <span style={{ color: '#d1d5db' }}>—</span>}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-gray-500 text-xs" style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {u.email}
                    </td>
                    <td className="px-3 py-3 text-gray-700 text-xs">{u.subject || <span style={{ color: '#d1d5db' }}>—</span>}</td>
                    <td className="px-3 py-3 text-gray-700 text-xs">{u.niveau || <span style={{ color: '#d1d5db' }}>—</span>}</td>
                    <td className="px-3 py-3">
                      <span style={{
                        padding: '2px 7px', borderRadius: 99, fontSize: 11, fontWeight: 600,
                        background: u.is_active ? '#f0fdf4' : '#fee2e2',
                        color: u.is_active ? '#15803d' : '#dc2626',
                      }}>
                        {u.is_active ? 'Actif' : 'Désactivé'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
