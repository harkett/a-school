import { useState } from 'react'
import { Link } from 'react-router-dom'
import EyeIcon from '../components/EyeIcon'

export default function Signup() {
  const [email, setEmail] = useState('')
  const [subject, setSubject] = useState('')
  const [langueLv, setLangueLv] = useState('')
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
          langue_lv: subject === 'Langues Vivantes (LV)' ? langueLv : '',
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

      <header className="flex items-center gap-3 px-6 py-4" style={{ backgroundColor: 'var(--bleu)' }}>
        <img src="/icon.png" alt="A-SCHOOL" style={{ width: 34, height: 34, borderRadius: 8, flexShrink: 0 }} />
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
              <div className="flex justify-center mb-5">
                <img src="/logo.png" alt="A-SCHOOL" style={{ width: 160, height: 'auto' }} />
              </div>
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
                    onChange={e => { setSubject(e.target.value); setLangueLv('') }}
                    required
                  >
                    <option value="" disabled>— Choisissez une matière —</option>
                    <option value="Français">Français</option>
                    <option value="Histoire-Géographie">Histoire-Géographie</option>
                    <option value="Mathématiques">Mathématiques</option>
                    <option value="Physique-Chimie">Physique-Chimie</option>
                    <option value="SVT">SVT</option>
                    <option value="SES">SES</option>
                    <option value="NSI">NSI</option>
                    <option value="Philosophie">Philosophie</option>
                    <option value="Langues Vivantes (LV)">Langues Vivantes (LV)</option>
                    <option value="Technologie">Technologie</option>
                    <option value="Arts">Arts</option>
                    <option value="EPS">EPS</option>
                  </select>
                </div>

                {subject === 'Langues Vivantes (LV)' && (
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Langue enseignée :</label>
                    <select
                      className="w-full border border-gray-300 rounded p-2 text-sm bg-white"
                      value={langueLv}
                      onChange={e => setLangueLv(e.target.value)}
                      required
                    >
                      <option value="" disabled>— Précisez la langue —</option>
                      <option value="Anglais">Anglais</option>
                      <option value="Espagnol">Espagnol</option>
                      <option value="Allemand">Allemand</option>
                      <option value="Italien">Italien</option>
                      <option value="Portugais">Portugais</option>
                      <option value="Arabe">Arabe</option>
                      <option value="Chinois">Chinois</option>
                      <option value="Autre">Autre</option>
                    </select>
                  </div>
                )}
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
        A-SCHOOL · contact@aschool.fr
      </footer>
    </div>
  )
}
