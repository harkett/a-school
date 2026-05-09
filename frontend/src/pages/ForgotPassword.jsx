import { useState } from 'react'
import { Link } from 'react-router-dom'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    try {
      await fetch('/api/auth/request-reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      })
    } catch { /* silencieux */ }
    setSent(true)
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#f0f4f8' }}>

      <header style={{ backgroundColor: 'var(--bleu)', height: 65, overflow: 'hidden', display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <img src="/Logo_aSchool_blanc.png" alt="aSchool" style={{ height: 140, width: 'auto' }} />
      </header>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 w-full max-w-md">

          <div className="flex justify-center mb-5">
            <img src="/Logo_aSchool.png" alt="aSchool" style={{ width: 160, height: 'auto' }} />
          </div>

          {sent ? (
            <div className="text-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 24 24"
                fill="none" stroke="#16a34a" strokeWidth="1.5" className="mx-auto mb-4">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Email envoyé</h2>
              <p className="text-sm text-gray-500 mb-6">
                Si un compte existe avec cette adresse, un lien de réinitialisation vous a été envoyé.
                Vérifiez votre boîte mail (et vos spams).
              </p>
              <Link to="/login" className="text-sm text-blue-600 underline hover:text-blue-800">
                Retour à la connexion
              </Link>
            </div>
          ) : (
            <>
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Mot de passe oublié</h2>
              <p className="text-sm text-gray-500 mb-6">
                Saisissez votre adresse email — nous vous enverrons un lien pour choisir un nouveau mot de passe.
              </p>

              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Adresse e-mail</label>
                  <input
                    type="text"
                    inputMode="email"
                    className="w-full border border-gray-300 rounded p-2 text-sm"
                    placeholder="votre.adresse@domaine.fr"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    autoComplete="email"
                    autoFocus
                    pattern="[^@\s]+@[^@\s]+\.[^@\s]+"
                    title="Adresse e-mail valide requise"
                    required
                  />
                </div>
                <button
                  type="submit"
                  className="btn-primary w-full justify-center"
                  disabled={loading}
                >
                  {loading ? 'Envoi en cours…' : 'Envoyer le lien'}
                </button>
              </form>

              <p className="text-xs text-gray-400 text-center mt-6">
                <Link to="/login" className="underline text-gray-500 hover:text-gray-700">
                  Retour à la connexion
                </Link>
              </p>
            </>
          )}

        </div>
      </div>

      <footer className="py-3 text-center text-xs text-gray-400">
        A-SCHOOL · contact@aschool.fr
      </footer>
    </div>
  )
}
