import { useState } from 'react'
import { fetchWithTimeout } from '../utils/api.js'
import FenetrePro from './FenetrePro.jsx'

const CATEGORIES = [
  { key: 'bug',        label: 'Problème' },
  { key: 'suggestion', label: 'Suggestion' },
  { key: 'question',   label: 'Question' },
]

// Formulaire d'envoi de feedback dans LA fenêtre de l'appli (FenetrePro : déplaçable,
// étirable, sans voile — le prof continue de voir l'écran dont il parle). Le feedback
// emporte tout seul son CONTEXTE (« Depuis : écran … · couple ») : affiché ici en clair,
// envoyé dans sa propre case en base, jamais mélangé au message du prof.
export default function Feedback({ onClose, contexte }) {
  const [category, setCategory] = useState('')
  const [message, setMessage]   = useState('')
  const [loading, setLoading]   = useState(false)
  const [done, setDone]         = useState(false)
  const [error, setError]       = useState('')

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
        body: JSON.stringify({ type: 'feedback', message: message.trim(), category,
                               contexte: contexte || null }),
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
    <FenetrePro titre="Envoyer un feedback" onFermer={onClose} largeur={560} hauteur={520}
                minWidth={380} minHeight={340} zIndex={460}>
      {done ? (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
                      justifyContent: 'center', gap: 6, padding: 24 }}>
          <p className="text-gray-700 font-medium">Merci pour votre retour !</p>
          <p className="text-sm text-gray-400 mb-4">Votre message a bien été transmis.</p>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded text-sm font-medium"
            style={{ background: 'var(--bleu)', border: 'none', cursor: 'pointer', color: 'white' }}
          >
            Fermer
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit}
              style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column',
                       gap: 14, padding: '16px 20px', overflowY: 'auto' }}>
          {contexte && (
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6,
                          padding: '7px 12px', fontSize: 12, color: '#64748b', lineHeight: 1.5 }}
                 title="Cette information part avec votre message — vous n'avez pas à décrire où vous êtes.">
              <strong style={{ color: '#475569' }}>Depuis :</strong> {contexte}
            </div>
          )}

          <div>
            <label className="block text-sm text-gray-600 mb-2">Type</label>
            <div className="flex gap-2">
              {CATEGORIES.map(c => (
                <button
                  key={c.key}
                  type="button"
                  onClick={() => setCategory(c.key)}
                  title={`Catégorie : ${c.label}`}
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

          <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            <label className="block text-sm text-gray-600 mb-1">Message</label>
            {/* La zone grandit avec la fenêtre : étirez la fenêtre, le message respire. */}
            <textarea
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="Décrivez votre retour, problème ou suggestion…"
              maxLength={2000}
              className="w-full border border-gray-200 rounded px-3 py-2 text-sm text-gray-700 focus:outline-none focus:border-blue-400"
              style={{ flex: 1, minHeight: 90, resize: 'none' }}
            />
            <p className="text-xs text-gray-400 text-right mt-0.5">{message.length}/2000</p>
          </div>

          {error && <p className="text-sm text-red-500" style={{ margin: 0 }}>{error}</p>}

          <div className="flex justify-end gap-2" style={{ flexShrink: 0 }}>
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
              title={!canSubmit ? 'Choisissez un type et écrivez votre message avant d\'envoyer' : 'Envoyer votre feedback à l\'équipe aSchool'}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
              {loading ? 'Envoi…' : 'Envoyer'}
            </button>
          </div>
        </form>
      )}
    </FenetrePro>
  )
}
