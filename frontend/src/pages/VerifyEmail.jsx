import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchWithTimeout, TIMEOUT_AUTH } from '../utils/api.js'
import Attente from '../components/Attente.jsx'

export default function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [resendEmail, setResendEmail] = useState('')
  const [resendStatus, setResendStatus] = useState(null) // null | 'sending' | 'sent'

  async function handleResend(e) {
    e.preventDefault()
    setResendStatus('sending')
    try {
      await fetchWithTimeout('/api/auth/resend-verification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resendEmail.trim() }),
      })
    } catch { /* silencieux */ }
    setResendStatus('sent')
  }

  // L'activation est UN appel, joué une seule fois : react-query en tient le résultat, et sa
  // clé porte le jeton — c'est lui qui dit quand c'est un autre lien, pas un drapeau à la main.
  // Sans jeton, il n'y a rien à demander au serveur : le verdict est immédiat.
  const { data: verdict = { status: 'loading', message: '' } } = useQuery({
    queryKey: ['verify-email', token],
    enabled: !!token,
    queryFn: async () => {
      try {
        // `credentials` explicite : c'est le cookie posé à l'inscription qui voyage ici, et
        // c'est lui qui décide si la session s'ouvre. Le laisser au comportement par défaut du
        // navigateur reviendrait à parier sur un réglage qu'on ne maîtrise pas.
        const r = await fetchWithTimeout(`/api/auth/verify-email?token=${encodeURIComponent(token)}`,
                                         { credentials: 'include' }, TIMEOUT_AUTH)
        let data = {}
        try { data = await r.json() } catch { /* corps vide ou illisible : le code HTTP suffit */ }
        return r.ok ? { status: data.connecte ? 'entree' : 'ok', message: '' }
                    : { status: 'error', message: data.detail || 'Lien invalide ou expiré.' }
      } catch {
        return { status: 'error', message: 'Erreur réseau — réessayez.' }
      }
    },
  })
  const { status, message } = token ? verdict : { status: 'error', message: 'Lien de vérification manquant.' }

  // LE COMPTE EST OUVERT ET LA SESSION AUSSI : on entre, sans écran intermédiaire à cliquer.
  // Rechargement complet plutôt que navigation interne — l'application relit sa session au
  // démarrage, et c'est le seul moyen sûr qu'elle parte avec les cookies qu'on vient de poser.
  useEffect(() => {
    if (status !== 'entree') return
    const t = setTimeout(() => window.location.replace('/'), 900)
    return () => clearTimeout(t)
  }, [status])

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#f0f4f8' }}>

      <header style={{ backgroundColor: 'var(--bleu)', height: 65, overflow: 'hidden', display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <img src="/Logo_aSchool_blanc.png" alt="aSchool" style={{ height: 34, width: 'auto' }} />
      </header>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 w-full max-w-md text-center">

          <div className="flex justify-center mb-5">
            <img src="/Logo_aSchool.png" alt="aSchool" style={{ width: 160, height: 'auto' }} />
          </div>

          {status === 'loading' && <Attente texte="Activation en cours…" />}

          {/* Le compte vient de s'ouvrir sur le navigateur qui s'est inscrit : rien à cliquer,
              l'application s'ouvre. La phrase dit ce qui se passe pendant la seconde d'attente. */}
          {status === 'entree' && <Attente texte="Compte activé — ouverture de votre espace…" />}

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
                <>
                  <p className="text-sm text-green-600 mb-2">
                    Email renvoyé — <strong>vérifiez votre boîte mail</strong>.
                  </p>
                  {/* Même situation qu'après l'inscription : quelqu'un attend un courriel qui
                      peut tomber en indésirables. Le dire ici aussi, sinon il attend pour rien. */}
                  <p className="text-xs mb-4" style={{ color: '#92400e' }}>
                    Pensez à regarder dans vos courriers indésirables.
                  </p>
                </>
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
        aSchool · contact@aschool.fr
      </footer>
    </div>
  )
}
