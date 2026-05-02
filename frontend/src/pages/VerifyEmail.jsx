import { useState, useEffect, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

export default function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [status, setStatus] = useState('loading')
  const [message, setMessage] = useState('')
  const called = useRef(false)

  const [resendEmail, setResendEmail] = useState('')
  const [resendStatus, setResendStatus] = useState(null) // null | 'sending' | 'sent'

  async function handleResend(e) {
    e.preventDefault()
    setResendStatus('sending')
    try {
      await fetch('/api/auth/resend-verification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resendEmail.trim() }),
      })
    } catch { /* silencieux */ }
    setResendStatus('sent')
  }

  useEffect(() => {
    if (called.current) return
    called.current = true
    if (!token) {
      setStatus('error')
      setMessage('Lien de vérification manquant.')
      return
    }
    fetch(`/api/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then(async r => {
        let data = {}
        try { data = await r.json() } catch { /* empty */ }
        if (r.ok) setStatus('ok')
        else { setStatus('error'); setMessage(data.detail || 'Lien invalide ou expiré.') }
      })
      .catch(() => { setStatus('error'); setMessage('Erreur réseau — réessayez.') })
  }, [token])

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
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 w-full max-w-md text-center">

          {status === 'loading' && (
            <p className="text-sm text-gray-400">Activation en cours…</p>
          )}

          {status === 'ok' && (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 24 24"
                fill="none" stroke="#16a34a" strokeWidth="1.5" className="mx-auto mb-4">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Compte activé !</h2>
              <p className="text-sm text-gray-500 mb-6">
                Votre adresse email a été vérifiée. Vous pouvez maintenant vous connecter.
              </p>
              <Link to="/login" className="btn-primary">
                Se connecter
              </Link>
            </>
          )}

          {status === 'error' && (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 24 24"
                fill="none" stroke="#dc2626" strokeWidth="1.5" className="mx-auto mb-4">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Lien invalide ou expiré</h2>
              <p className="text-sm text-gray-500 mb-6">{message}</p>

              {resendStatus === 'sent' ? (
                <p className="text-sm text-green-600 mb-4">
                  Email renvoyé — vérifiez votre boîte mail.
                </p>
              ) : (
                <form onSubmit={handleResend} className="text-left mb-6">
                  <p className="text-xs text-gray-500 mb-2 text-center">
                    Recevez un nouveau lien de vérification :
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      inputMode="email"
                      className="flex-1 border border-gray-300 rounded p-2 text-sm"
                      placeholder="votre.adresse@domaine.fr"
                      value={resendEmail}
                      onChange={e => setResendEmail(e.target.value)}
                      pattern="[^@\s]+@[^@\s]+\.[^@\s]+"
                      title="Adresse e-mail valide requise"
                      required
                    />
                    <button
                      type="submit"
                      disabled={resendStatus === 'sending'}
                      className="btn-primary"
                      style={{ whiteSpace: 'nowrap' }}
                    >
                      {resendStatus === 'sending' ? 'Envoi…' : 'Renvoyer'}
                    </button>
                  </div>
                </form>
              )}

              <Link to="/login" className="text-xs text-gray-400 underline">
                Retour à la connexion
              </Link>
            </>
          )}

        </div>
      </div>

      <footer className="py-3 text-center text-xs text-gray-400">
        A-SCHOOL · harketti@afia.fr
      </footer>
    </div>
  )
}
