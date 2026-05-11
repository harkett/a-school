import { useState } from 'react'

const STARS = [1, 2, 3, 4, 5]
const LABELS = { 1: 'Décevant', 2: 'Passable', 3: 'Correct', 4: 'Bien', 5: 'Excellent !' }

export default function Notation({ onClose }) {
  const [rating, setRating]   = useState(0)
  const [hover, setHover]     = useState(0)
  const [comment, setComment] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone]       = useState(false)
  const [error, setError]     = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!rating) return
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          type: 'notation',
          rating,
          message: comment.trim() || '—',
          category: null,
        }),
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
      <div className="bg-white rounded-lg shadow-xl w-full max-w-sm mx-4">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/icon.png" alt="" style={{ width: 24, height: 24, borderRadius: 5 }} />
            <h2 className="text-base font-semibold text-gray-800">Notez A-SCHOOL</h2>
          </div>
          <button
            onClick={onClose}
            title="Fermer"
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: '#9ca3af' }}
          >
            ✕
          </button>
        </div>

        {done ? (
          <div className="px-6 py-10 text-center">
            <div style={{ fontSize: 32, color: '#f59e0b', marginBottom: 12 }}>
              {'★'.repeat(rating)}{'☆'.repeat(5 - rating)}
            </div>
            <p className="text-gray-700 font-medium mb-1">Merci pour votre note !</p>
            <p className="text-sm text-gray-400 mb-6">Votre retour nous aide à améliorer A-SCHOOL.</p>
            <button
              onClick={onClose}
              style={{ background: 'var(--bleu)', border: 'none', borderRadius: 6, padding: '8px 24px', color: 'white', cursor: 'pointer', fontSize: 14 }}
            >
              Fermer
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="px-6 py-5 flex flex-col gap-4">

            <div className="text-center">
              <div className="flex justify-center gap-1 mb-1">
                {STARS.map(s => (
                  <button
                    key={s}
                    type="button"
                    title={LABELS[s]}
                    onMouseEnter={() => setHover(s)}
                    onMouseLeave={() => setHover(0)}
                    onClick={() => setRating(s)}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      fontSize: 36,
                      color: s <= (hover || rating) ? '#f59e0b' : '#e5e7eb',
                      transition: 'color 0.1s',
                    }}
                  >
                    ★
                  </button>
                ))}
              </div>
              <p className="text-sm text-gray-400 h-5">
                {(hover || rating) ? LABELS[hover || rating] : ''}
              </p>
            </div>

            <div>
              <label className="block text-sm text-gray-500 mb-1">
                Un mot sur votre expérience ? <span className="text-gray-300">(optionnel)</span>
              </label>
              <textarea
                value={comment}
                onChange={e => setComment(e.target.value)}
                placeholder="Ce que vous aimez, ce qui pourrait être amélioré…"
                rows={3}
                maxLength={500}
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm text-gray-700 resize-none focus:outline-none focus:border-blue-400"
              />
            </div>

            {error && <p className="text-sm text-red-500">{error}</p>}

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                style={{ background: 'none', border: '1px solid #e5e7eb', borderRadius: 6, padding: '7px 16px', cursor: 'pointer', fontSize: 13, color: '#6b7280' }}
              >
                Annuler
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={!rating || loading}
                title={!rating ? 'Sélectionnez une note avant d\'envoyer' : 'Envoyer votre note à l\'équipe A-SCHOOL'}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                {loading ? 'Envoi…' : 'Envoyer ma note'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
