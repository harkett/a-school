import { useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

const CATEGORIES = [
  { key: 'bug',        label: 'Problème' },
  { key: 'suggestion', label: 'Suggestion' },
  { key: 'question',   label: 'Question' },
]

export default function Feedback({ onClose }) {
  const [category, setCategory] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const canSubmit = category && message.trim().length >= 5

  async function handleSubmit(e) {
    e.preventDefault()
    if (!canSubmit) return
    setLoading(true)
    setError('')
    try {
      const res = await fetchWithTimeout('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ type: 'feedback', message: message.trim(), rating: 0, category }),
      })
      if (!res.ok) throw new Error()
      setDone(true)
    } catch {
      setError('Une erreur est survenue. Réessayez.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/icon.png" alt="" style={{ width: 24, height: 24, borderRadius: 5 }} />
            <h2 className="text-base font-semibold text-gray-800">Envoyer un feedback</h2>
          </div>
          <button
            onClick={onClose}
            title="Fermer"
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            style={{ background: 'none', border: 'none', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>

        {done ? (
          <div className="px-6 py-10 text-center">
            <p className="text-gray-700 font-medium mb-1">Merci pour votre retour !</p>
            <p className="text-sm text-gray-400 mb-6">Votre message a bien été transmis.</p>
            <button
              onClick={onClose}
              className="px-5 py-2 rounded text-sm font-medium"
              style={{ background: 'var(--bleu)', border: 'none', cursor: 'pointer', color: 'white' }}
            >
              Fermer
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="px-6 py-5 flex flex-col gap-4">

            <div>
              <label className="block text-sm text-gray-600 mb-2">Type</label>
              <div className="flex gap-2">
                {CATEGORIES.map(c => (
                  <button
                    key={c.key}
                    type="button"
                    onClick={() => setCategory(c.key)}
                    className="px-4 py-1.5 rounded-full text-sm font-medium border transition-colors"
                    style={
                      category === c.key
                        ? { background: 'var(--bleu)', color: 'white', border: '1px solid var(--bleu)' }
                        : { background: 'white', color: '#6b7280', border: '1px solid #e5e7eb', cursor: 'pointer' }
                    }
                  >
                    {c.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">Message</label>
              <textarea
                value={message}
                onChange={e => setMessage(e.target.value)}
                placeholder="Décrivez votre retour, problème ou suggestion…"
                rows={4}
                maxLength={2000}
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm text-gray-700 resize-none focus:outline-none focus:border-blue-400"
              />
              <p className="text-xs text-gray-400 text-right mt-0.5">{message.length}/2000</p>
            </div>

            {error && <p className="text-sm text-red-500">{error}</p>}

            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 rounded"
                style={{ background: 'none', border: '1px solid #e5e7eb', cursor: 'pointer' }}
              >
                Annuler
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={!canSubmit || loading}
                title={!canSubmit ? 'Remplissez le message avant d\'envoyer' : 'Envoyer votre feedback à l\'équipe A-SCHOOL'}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                {loading ? 'Envoi…' : 'Envoyer'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
