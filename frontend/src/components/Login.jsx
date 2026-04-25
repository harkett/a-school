import { useState } from 'react'

export default function Login({ onVerified, tokenError }) {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState(tokenError || null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!email.trim()) return
    setLoading(true)
    setErreur(null)
    try {
      const res = await fetch('/api/auth/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || `Erreur ${res.status}`)
      }
      setSent(true)
    } catch (e) {
      setErreur(e.message || 'Erreur réseau — vérifiez que le serveur est lancé.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#f0f4f8' }}>

      <header className="flex items-center px-6 py-4" style={{ backgroundColor: 'var(--bleu)' }}>
        <span className="text-white font-bold text-xl tracking-tight">
          <span style={{ color: 'var(--bordeaux)' }}>A</span>-SCHOOL
        </span>
        <span className="text-white text-base ml-3" style={{ opacity: 0.75 }}>
          | Générateur d'activités pédagogiques
        </span>
      </header>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 w-full max-w-md">

          {!sent ? (
            <>
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Connexion</h2>
              <p className="text-sm text-gray-500 mb-6">
                Saisissez votre adresse e-mail pour recevoir un lien de connexion.
              </p>

              {erreur && (
                <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm mb-4">
                  {erreur}
                </div>
              )}

              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Adresse e-mail</label>
                  <input
                    type="email"
                    className="w-full border border-gray-300 rounded p-2 text-sm"
                    placeholder="votre.email@etablissement.fr"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    autoFocus
                    required
                  />
                </div>
                <button
                  type="submit"
                  className="btn-primary w-full justify-center"
                  disabled={loading}
                >
                  {loading ? 'Envoi en cours...' : 'Recevoir mon lien de connexion'}
                </button>
              </form>
            </>
          ) : (
            <div className="text-center py-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#1F6EEB" strokeWidth="1.5" className="mx-auto mb-4">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Lien envoyé !</h2>
              <p className="text-sm text-gray-500">
                Vérifiez votre boîte mail à <strong>{email}</strong>.<br />
                Le lien est valable <strong>15 minutes</strong>.
              </p>
              <button
                className="text-xs text-gray-400 mt-6 underline"
                onClick={() => { setSent(false); setEmail('') }}
              >
                Utiliser une autre adresse
              </button>
            </div>
          )}
        </div>
      </div>

      <footer className="py-3 text-center text-xs text-gray-400">
        A-SCHOOL · harketti@afia.fr
      </footer>
    </div>
  )
}
