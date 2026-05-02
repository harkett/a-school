import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import EyeIcon from '../components/EyeIcon'

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') || ''

  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [showPwdConfirm, setShowPwdConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('form') // 'form' | 'success' | 'error'
  const [erreur, setErreur] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (password !== passwordConfirm) {
      setErreur('Les mots de passe ne correspondent pas.')
      return
    }
    setLoading(true)
    setErreur(null)
    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password, password_confirm: passwordConfirm }),
      })
      let data = {}
      try { data = await res.json() } catch { /* corps vide */ }
      if (res.ok) {
        setStatus('success')
      } else {
        setErreur(data.detail || 'Une erreur est survenue.')
        if (data.detail?.includes('expiré') || data.detail?.includes('invalide')) {
          setStatus('error')
        }
      }
    } catch {
      setErreur('Erreur réseau — réessayez.')
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

          {status === 'success' && (
            <div className="text-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 24 24"
                fill="none" stroke="#16a34a" strokeWidth="1.5" className="mx-auto mb-4">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Mot de passe modifié</h2>
              <p className="text-sm text-gray-500 mb-6">
                Votre mot de passe a été mis à jour. Vous pouvez maintenant vous connecter.
              </p>
              <Link to="/login" className="btn-primary">
                Se connecter
              </Link>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 24 24"
                fill="none" stroke="#dc2626" strokeWidth="1.5" className="mx-auto mb-4">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Lien invalide ou expiré</h2>
              <p className="text-sm text-gray-500 mb-6">
                Ce lien de réinitialisation n'est plus valable. Faites une nouvelle demande.
              </p>
              <Link to="/forgot-password" className="btn-primary">
                Nouvelle demande
              </Link>
              <p className="text-xs text-gray-400 mt-4">
                <Link to="/login" className="underline text-gray-500 hover:text-gray-700">
                  Retour à la connexion
                </Link>
              </p>
            </div>
          )}

          {status === 'form' && (
            <>
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Nouveau mot de passe</h2>
              <p className="text-sm text-gray-500 mb-6">
                Choisissez un nouveau mot de passe (8 caractères minimum).
              </p>

              {erreur && (
                <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm mb-4">
                  {erreur}
                </div>
              )}

              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Nouveau mot de passe</label>
                  <div className="relative">
                    <input
                      type={showPwd ? 'text' : 'password'}
                      className="w-full border border-gray-300 rounded p-2 pr-9 text-sm"
                      placeholder="••••••••"
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      autoComplete="new-password"
                      autoFocus
                      minLength={8}
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
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Confirmer le mot de passe</label>
                  <div className="relative">
                    <input
                      type={showPwdConfirm ? 'text' : 'password'}
                      className="w-full border border-gray-300 rounded p-2 pr-9 text-sm"
                      placeholder="••••••••"
                      value={passwordConfirm}
                      onChange={e => setPasswordConfirm(e.target.value)}
                      autoComplete="new-password"
                      minLength={8}
                      required
                    />
                    <button type="button" onClick={() => setShowPwdConfirm(v => !v)}
                      title={showPwdConfirm ? 'Masquer' : 'Afficher'}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                      <EyeIcon open={showPwdConfirm} />
                    </button>
                  </div>
                </div>
                <button
                  type="submit"
                  className="btn-primary w-full justify-center"
                  disabled={loading}
                >
                  {loading ? 'Enregistrement…' : 'Enregistrer le mot de passe'}
                </button>
              </form>
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
