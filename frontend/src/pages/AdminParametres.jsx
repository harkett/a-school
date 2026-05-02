import { useEffect, useState } from 'react'

const VARIABLES = ['{prenom}', '{email}']

export default function AdminParametres() {
  const [form, setForm] = useState({ welcome_email_subject: '', welcome_email_body: '' })
  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)
  const [testing, setTesting]   = useState(false)
  const [message, setMessage]   = useState(null) // { type: 'ok'|'err', text }

  useEffect(() => {
    fetch('/api/admin/settings', { credentials: 'include' })
      .then(r => r.json())
      .then(data => setForm({
        welcome_email_subject: data.welcome_email_subject || '',
        welcome_email_body:    data.welcome_email_body    || '',
      }))
      .finally(() => setLoading(false))
  }, [])

  async function save() {
    setSaving(true)
    setMessage(null)
    try {
      const res = await fetch('/api/admin/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(form),
      })
      const data = await res.json().catch(() => ({}))
      setMessage(res.ok
        ? { type: 'ok',  text: 'Paramètres enregistrés.' }
        : { type: 'err', text: data.detail || 'Erreur lors de l\'enregistrement.' }
      )
    } catch {
      setMessage({ type: 'err', text: 'Erreur réseau — vérifiez que le backend tourne.' })
    } finally {
      setSaving(false)
    }
  }

  async function sendTest() {
    setTesting(true)
    setMessage(null)
    try {
      const res = await fetch('/api/admin/settings/test-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          welcome_email_subject: form.welcome_email_subject,
          welcome_email_body:    form.welcome_email_body,
        }),
      })
      const data = await res.json().catch(() => ({}))
      setMessage(res.ok
        ? { type: 'ok',  text: 'Test réussi — email envoyé à contact@aschool.fr.' }
        : { type: 'err', text: data.detail || 'Erreur envoi email de test.' }
      )
    } catch {
      setMessage({ type: 'err', text: 'Erreur réseau — vérifiez que le backend tourne.' })
    } finally {
      setTesting(false)
    }
  }

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  return (
    <div style={{ maxWidth: 640 }}>
      <h2 className="text-sm font-semibold text-gray-700 mb-1">Paramètres</h2>
      <p className="text-xs text-gray-400 mb-6">
        Configurez l'email de bienvenue envoyé automatiquement à chaque nouvel inscrit.
      </p>

      <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">

        {/* Objet */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Objet de l'email
          </label>
          <input
            type="text"
            value={form.welcome_email_subject}
            onChange={e => setForm(f => ({ ...f, welcome_email_subject: e.target.value }))}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            placeholder="Bienvenue sur A-SCHOOL !"
          />
        </div>

        {/* Corps */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Corps du message
          </label>
          <textarea
            value={form.welcome_email_body}
            onChange={e => setForm(f => ({ ...f, welcome_email_body: e.target.value }))}
            rows={12}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono"
            placeholder="Bonjour {prenom},…"
            style={{ resize: 'vertical', lineHeight: 1.6 }}
          />
          <p className="text-xs text-gray-400 mt-1">
            Variables disponibles :{' '}
            {VARIABLES.map(v => (
              <code key={v} style={{ background: '#f1f5f9', borderRadius: 4, padding: '1px 5px', marginRight: 4, fontSize: 11 }}>{v}</code>
            ))}
            — remplacées automatiquement à l'envoi.
          </p>
        </div>

        {/* Aperçu */}
        <div style={{ background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0', padding: '12px 16px' }}>
          <p className="text-xs font-medium text-gray-500 mb-2">Aperçu rendu</p>
          <p className="text-xs text-gray-400 mb-1">
            <strong>Objet :</strong> {form.welcome_email_subject || '—'}
          </p>
          <pre className="text-xs text-gray-600 whitespace-pre-wrap leading-relaxed" style={{ fontFamily: 'inherit' }}>
            {(form.welcome_email_body || '')
              .replace('{prenom}', 'Marie')
              .replace('{email}', 'marie@college.fr')}
          </pre>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-3 pt-1">
          <div className="flex gap-3">
            <button
              onClick={save}
              disabled={saving}
              title="Enregistrer les paramètres"
              style={{
                background: '#1F6EEB', color: 'white', border: 'none',
                borderRadius: 7, padding: '8px 20px', fontSize: 13,
                fontWeight: 500, cursor: 'pointer', opacity: saving ? 0.6 : 1,
              }}
            >
              {saving ? 'Enregistrement…' : 'Enregistrer'}
            </button>
            <button
              onClick={sendTest}
              disabled={testing}
              title="Envoyer un email de test à contact@aschool.fr pour vérifier la config SMTP"
              style={{
                background: 'white', color: '#374151',
                border: '1px solid #d1d5db', borderRadius: 7,
                padding: '8px 20px', fontSize: 13, fontWeight: 500,
                cursor: 'pointer', opacity: testing ? 0.6 : 1,
              }}
            >
              {testing ? 'Envoi en cours…' : 'Envoyer un test'}
            </button>
          </div>
          {message && (
            <div style={{
              background: message.type === 'ok' ? '#f0fdf4' : '#fef2f2',
              border: `1px solid ${message.type === 'ok' ? '#bbf7d0' : '#fecaca'}`,
              color:  message.type === 'ok' ? '#166534' : '#dc2626',
              borderRadius: 8, padding: '10px 14px', fontSize: 13,
            }}>
              {message.text}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
