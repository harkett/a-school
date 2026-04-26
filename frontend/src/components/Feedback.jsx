import { useState } from 'react'

const STARS = [1, 2, 3, 4, 5]

export default function Feedback({ onClose }) {
  const [message, setMessage] = useState('')
  const [rating, setRating] = useState(0)
  const [hover, setHover] = useState(0)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const canSubmit = message.trim().length >= 5 && rating > 0

  async function handleSubmit(e) {
    e.preventDefault()
    if (!canSubmit) return
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message: message.trim(), rating }),
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
          <h2 className="text-base font-semibold text-gray-800">Envoyer un feedback</h2>
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
              className="px-5 py-2 rounded text-sm font-medium text-white"
              style={{ background: 'var(--bleu)', border: 'none', cursor: 'pointer' }}
            >
              Fermer
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="px-6 py-5 flex flex-col gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Note</label>
              <div className="flex gap-1">
                {STARS.map(s => (
                  <button
                    key={s}
                    type="button"
                    title={`${s} étoile${s > 1 ? 's' : ''}`}
                    onMouseEnter={() => setHover(s)}
                    onMouseLeave={() => setHover(0)}
                    onClick={() => setRating(s)}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      fontSize: 24,
                      color: s <= (hover || rating) ? '#f59e0b' : '#d1d5db',
                    }}
                  >
                    ★
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
                disabled={!canSubmit || loading}
                title="Envoyer votre feedback"
                className="px-5 py-2 text-sm font-medium text-white rounded"
                style={{
                  background: canSubmit && !loading ? 'var(--bleu)' : '#9ca3af',
                  border: 'none',
                  cursor: canSubmit && !loading ? 'pointer' : 'not-allowed',
                  color: 'white',
                }}
              >
                {loading ? 'Envoi…' : 'Envoyer'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
