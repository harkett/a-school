import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function AdminCompte() {
  const [form, setForm] = useState({ old_password: '', new_password: '', new_password_confirm: '' })
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSuccess(false)
    setSaving(true)
    try {
      const res = await fetch('/api/admin/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(form),
      })
      if (res.status === 401) { navigate('/admin/login'); return }
      const data = await res.json()
      if (!res.ok) { setError(data.detail || 'Erreur inconnue.'); return }
      setSuccess(true)
      setForm({ old_password: '', new_password: '', new_password_confirm: '' })
    } finally {
      setSaving(false)
    }
  }

  const adminUser = import.meta.env.VITE_ADMIN_USER || 'admin'

  return (
    <div style={{ maxWidth: 480 }}>
      <h2 className="text-sm font-semibold text-gray-700 mb-6">Mon compte</h2>

      <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', padding: '24px 28px' }}>
        <div style={{ marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid #f1f5f9' }}>
          <p style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>Identifiant</p>
          <p style={{ fontSize: 14, color: '#1e293b', fontWeight: 600 }}>Administrateur A-SCHOOL</p>
          <p style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>Compte unique — accès complet au backoffice</p>
        </div>

        <h3 style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', marginBottom: 16 }}>Changer le mot de passe</h3>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 500, color: '#64748b', marginBottom: 5 }}>
              Mot de passe actuel
            </label>
            <input
              type="password"
              value={form.old_password}
              onChange={e => setForm(f => ({ ...f, old_password: e.target.value }))}
              autoComplete="current-password"
              required
              style={{ width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 10px', fontSize: 13, boxSizing: 'border-box' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 500, color: '#64748b', marginBottom: 5 }}>
              Nouveau mot de passe
            </label>
            <input
              type="password"
              value={form.new_password}
              onChange={e => setForm(f => ({ ...f, new_password: e.target.value }))}
              autoComplete="new-password"
              required
              minLength={8}
              style={{ width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 10px', fontSize: 13, boxSizing: 'border-box' }}
            />
            <p style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>Minimum 8 caractères</p>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 500, color: '#64748b', marginBottom: 5 }}>
              Confirmer le nouveau mot de passe
            </label>
            <input
              type="password"
              value={form.new_password_confirm}
              onChange={e => setForm(f => ({ ...f, new_password_confirm: e.target.value }))}
              autoComplete="new-password"
              required
              style={{ width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 10px', fontSize: 13, boxSizing: 'border-box' }}
            />
          </div>

          {error && (
            <p style={{ fontSize: 12, color: '#dc2626', background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 6, padding: '8px 12px', margin: 0 }}>
              {error}
            </p>
          )}
          {success && (
            <p style={{ fontSize: 12, color: '#15803d', background: '#dcfce7', border: '1px solid #86efac', borderRadius: 6, padding: '8px 12px', margin: 0 }}>
              Mot de passe modifié avec succès.
            </p>
          )}

          <button
            type="submit"
            disabled={saving || !form.old_password || !form.new_password || !form.new_password_confirm}
            style={{
              background: '#1F6EEB', color: 'white', border: 'none', borderRadius: 7,
              padding: '9px 20px', fontSize: 13, fontWeight: 600, cursor: 'pointer',
              opacity: (saving || !form.old_password || !form.new_password || !form.new_password_confirm) ? 0.6 : 1,
              alignSelf: 'flex-start',
            }}
          >
            {saving ? 'Enregistrement…' : 'Enregistrer'}
          </button>
        </form>
      </div>

      <p style={{ fontSize: 11, color: '#94a3b8', marginTop: 12 }}>
        Le nouveau mot de passe est stocké en base de données (bcrypt). Le mot de passe du <code>.env</code> reste toujours valide comme mot de passe maître.
      </p>
    </div>
  )
}
