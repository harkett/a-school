import { useState } from 'react'
import { Link } from 'react-router-dom'

const EyeIcon = ({ open }) => open ? (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
  </svg>
) : (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
    <line x1="1" y1="1" x2="23" y2="23"/>
  </svg>
)

export default function Signup() {
  const [email, setEmail] = useState('')
  const [subject, setSubject] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState(null)
  const [done, setDone] = useState(false)
  const [showPwd, setShowPwd] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)


  async function handleSubmit(e) {
    e.preventDefault()
    if (password !== passwordConfirm) {
      setErreur('Les mots de passe ne correspondent pas.')
      return
    }
    setLoading(true)
    setErreur(null)
    try {
      const res = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          subject,
          password,
          password_confirm: passwordConfirm,
        }),
      })
      let data = {}
      try { data = await res.json() } catch { /* corps vide */ }
      if (!res.ok) throw new Error(data.detail || `Erreur ${res.status}`)
      setDone(true)
    } catch (e) {
      setErreur(e.message)
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

          {!done ? (
            <>
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Créer un compte</h2>
              <p className="text-sm text-gray-500 mb-6">
                Un email de confirmation vous sera envoyé.
              </p>

              {erreur && (
                <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm mb-4">
                  {erreur}
                </div>
              )}

              <form onSubmit={handleSubmit} autoComplete="off" className="flex flex-col gap-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Adresse e-mail</label>
                  <input
                    type="text"
                    inputMode="email"
                    className="w-full border border-gray-300 rounded p-2 text-sm"
                    placeholder="votre.adresse@domaine.fr"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    autoComplete="off"
                    autoFocus
                    pattern="[^@\s]+@[^@\s]+\.[^@\s]+"
                    title="Adresse e-mail valide requise"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Vous êtes professeur de :</label>
                  <select
                    className="w-full border border-gray-300 rounded p-2 text-sm bg-white"
                    value={subject}
                    onChange={e => setSubject(e.target.value)}
                    required
                  >
                    <option value="" disabled>— Choisissez une matière —</option>
                    <option value="francais">Français</option>
                    <option value="histoire_geo">Histoire-Géographie</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    Mot de passe <span className="text-gray-400">(8 caractères minimum)</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showPwd ? 'text' : 'password'}
                      className="w-full border border-gray-300 rounded p-2 pr-9 text-sm"
                      placeholder="••••••••"
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      autoComplete="new-password"
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
                      type={showConfirm ? 'text' : 'password'}
                      className="w-full border border-gray-300 rounded p-2 pr-9 text-sm"
                      placeholder="••••••••"
                      value={passwordConfirm}
                      onChange={e => setPasswordConfirm(e.target.value)}
                      autoComplete="new-password"
                      required
                    />
                    <button type="button" onClick={() => setShowConfirm(v => !v)}
                      title={showConfirm ? 'Masquer' : 'Afficher'}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                      <EyeIcon open={showConfirm} />
                    </button>
                  </div>
                </div>
                <button
                  type="submit"
                  className="btn-primary w-full justify-center"
                  disabled={loading}
                >
                  {loading ? 'Création...' : 'Créer mon compte'}
                </button>
              </form>

              <p className="text-xs text-gray-400 text-center mt-6">
                Déjà un compte ?{' '}
                <Link to="/login" className="underline text-gray-500 hover:text-gray-700">
                  Se connecter
                </Link>
              </p>
            </>
          ) : (
            <div className="text-center py-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24"
                fill="none" stroke="#1F6EEB" strokeWidth="1.5" className="mx-auto mb-4">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Email envoyé !</h2>
              <p className="text-sm text-gray-500">
                Vérifiez votre boîte mail à <strong>{email}</strong>.<br />
                Cliquez sur le lien pour activer votre compte.<br />
                <span className="text-gray-400 text-xs">Le lien est valable 60 minutes.</span>
              </p>
              <Link
                to="/login"
                className="text-xs text-gray-400 mt-6 underline block"
              >
                Retour à la connexion
              </Link>
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
