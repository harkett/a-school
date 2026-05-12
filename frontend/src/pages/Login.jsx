import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { fetchWithTimeout, TIMEOUT_AUTH } from '../utils/api.js'
import { useAuth } from '../context/AuthContext'
import EyeIcon from '../components/EyeIcon'

export default function Login() {
  const { setUser } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const deconnecteInactivite  = searchParams.get('raison') === 'inactivite'
  const deconnecteForce       = searchParams.get('raison') === 'force_deconnexion'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState(null)
  const [showPwd, setShowPwd] = useState(false)
  const [resendStatus, setResendStatus] = useState(null) // null | 'sending' | 'sent'
  const isPWA = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true


  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setErreur(null)
    const trimmed = email.trim()
    try {
      const res = await fetchWithTimeout('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: trimmed, password }),
      })
      let data = {}
      try { data = await res.json() } catch { /* corps vide */ }
      if (!res.ok) throw new Error(data.detail || 'Adresse e-mail ou mot de passe incorrect.')
      setUser(data)
      navigate('/', { replace: true })
    } catch (e) {
      setErreur(e.message)
      setResendStatus(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleResend() {
    setResendStatus('sending')
    try {
      await fetchWithTimeout('/api/auth/resend-verification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      }, TIMEOUT_AUTH)
    } catch { /* silencieux */ }
    setResendStatus('sent')
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
          <h2 className="text-lg font-semibold text-gray-800 mb-1">Connexion</h2>
          <p className="text-sm text-gray-500 mb-6">
            Accédez à votre espace aSchool.
          </p>

          {isPWA && !deconnecteForce && !deconnecteInactivite && (
            <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '10px 14px', marginBottom: '16px', fontSize: '13px', color: '#1e40af' }}>
              Première ouverture de l'application ? Connectez-vous pour démarrer — votre session restera active 30 jours.
            </div>
          )}

          {deconnecteForce && (
            <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '8px', padding: '10px 14px', marginBottom: '16px', fontSize: '13px', color: '#991b1b' }}>
              Votre session a été fermée par l'administrateur. Reconnectez-vous ou contactez l'administrateur si vous pensez qu'il s'agit d'une erreur.
            </div>
          )}

          {deconnecteInactivite && (
            <div style={{ background: '#fefce8', border: '1px solid #fde047', borderRadius: '8px', padding: '10px 14px', marginBottom: '16px', fontSize: '13px', color: '#854d0e' }}>
              Vous avez été déconnecté après une période d'inactivité. Veuillez vous reconnecter.
            </div>
          )}

          {erreur && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm mb-4">
              {erreur}
              {erreur.includes('non vérifié') && (
                <div className="mt-2 pt-2 border-t border-red-200">
                  {resendStatus === 'sent' ? (
                    <p className="text-red-600 text-xs">Email renvoyé — vérifiez votre boîte mail.</p>
                  ) : (
                    <button
                      type="button"
                      onClick={handleResend}
                      disabled={resendStatus === 'sending'}
                      className="text-xs underline text-red-600 hover:text-red-800 bg-transparent border-none cursor-pointer p-0"
                    >
                      {resendStatus === 'sending' ? 'Envoi en cours…' : 'Renvoyer l\'email de vérification'}
                    </button>
                  )}
                </div>
              )}
            </div>
          )}

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
            <div>
              <label className="block text-xs text-gray-500 mb-1">Mot de passe</label>
              <div className="relative">
                <input
                  type={showPwd ? 'text' : 'password'}
                  className="w-full border border-gray-300 rounded p-2 pr-9 text-sm"
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
                <button type="button" onClick={() => setShowPwd(v => !v)}
                  title={showPwd ? 'Masquer' : 'Afficher'}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                  <EyeIcon open={showPwd} />
                </button>
              </div>
            </div>
            <button
              type="submit"
              className="btn-primary w-full justify-center"
              disabled={loading}
            >
              {loading ? 'Connexion...' : 'Se connecter'}
            </button>
          </form>

          <p className="text-xs text-gray-400 text-center mt-4">
            <Link to="/forgot-password" className="underline text-gray-500 hover:text-gray-700">
              Mot de passe oublié ?
            </Link>
          </p>

          <p className="text-xs text-gray-400 text-center mt-2">
            Pas encore de compte ?{' '}
            <Link to="/signup" className="underline text-gray-500 hover:text-gray-700">
              Créer un compte
            </Link>
          </p>

        </div>
      </div>

      <footer className="py-3 text-center text-xs text-gray-400">
        aSchool · contact@aschool.fr
        {' · '}
        <Link to="/admin/login" style={{ color: '#e2e8f0' }} title="Administration">admin</Link>
      </footer>
    </div>
  )
}
