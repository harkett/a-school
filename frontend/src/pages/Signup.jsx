import { useState } from 'react'
import { Link } from 'react-router-dom'
import Attente from '../components/Attente.jsx'
import EyeIcon from '../components/EyeIcon'
import { fetchWithTimeout, lireReponse, messagePourEcran, TIMEOUT_AUTH } from '../utils/api.js'
import { showError } from '../errorDialog'

export default function Signup() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [showPwd, setShowPwd] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)


  async function handleSubmit(e) {
    e.preventDefault()
    if (password !== passwordConfirm) {
      showError('Les deux mots de passe ne sont pas identiques.\n\nRessaisissez-les à l\'identique pour créer votre compte.')
      return
    }
    setLoading(true)
    try {
      const res = await fetchWithTimeout('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          password,
          password_confirm: passwordConfirm,
        }),
      }, TIMEOUT_AUTH)   // délai d'auth (le constante était importée sans être passée)
      // Le message du serveur (« cette adresse est déjà utilisée »…) remonte tel quel s'il est
      // écrit pour un humain ; sinon c'est le message serveur générique — jamais « Erreur 500 ».
      await lireReponse(res)
      setDone(true)
    } catch (e) {
      showError(messagePourEcran(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#f0f4f8' }}>

      <header style={{ backgroundColor: 'var(--bleu)', height: 65, overflow: 'hidden', display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <img src="/Logo_aSchool_blanc.png" alt="aSchool" style={{ height: 34, width: 'auto' }} />
      </header>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 w-full max-w-md">

          {!done ? (
            <>
              <div className="flex justify-center mb-5">
                <img src="/Logo_aSchool.png" alt="aSchool" style={{ width: 160, height: 'auto' }} />
              </div>
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Créer un compte</h2>
              <p className="text-sm text-gray-500 mb-6">
                Un email de confirmation vous sera envoyé.
              </p>

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
                <div className="bg-blue-50 border border-blue-200 text-blue-800 rounded p-3 text-sm">
                  Pas besoin de choisir votre matière ni votre niveau ici : vous les
                  renseignerez juste après, dans votre profil. On commence simplement par
                  créer votre compte.
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
              <div style={{ fontSize: 34, lineHeight: 1, marginBottom: 14,
                            animation: 'aschool-sablier 1.8s ease-in-out infinite' }}>⏳</div>
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Validation du compte en attente</h2>

              {/* L'ORDRE À DONNER PASSE DEVANT LE RESTE. Le sablier bouge, la jauge défile : l'œil
                  y va d'abord, et la seule phrase qui demande quelque chose se lisait en gris, de
                  la même taille que le reste. On mettait un moment à comprendre qu'il fallait
                  ouvrir sa boîte mail — pendant lequel la page semblait travailler toute seule. */}
              <p style={{ fontSize: 17, fontWeight: 700, color: '#1F6EEB', marginBottom: 6 }}>
                Vérifiez votre boîte mail
              </p>
              <p className="text-sm text-gray-500 mb-4">
                <strong>{email}</strong><br />
                Cliquez sur le lien pour activer votre compte.<br />
                <span className="text-gray-400 text-xs">Le lien est valable 60 minutes.</span>
              </p>
              {/* LE COMPTE ATTEND, ET ÇA SE VOIT. Le sablier et la jauge disent que rien n'est
                  terminé — sans eux, cette page ressemblait à une fin de parcours, et le futur
                  professeur repartait vers la connexion sans avoir ouvert son courriel. */}
              <Attente sablier={false} />
              {/* AUCUNE PORTE VERS LA CONNEXION ICI. Le compte n'est pas encore actif : le lien
                  « Retour à la connexion » menait à un écran qui refuse — « Email non vérifié ».
                  On ouvrait une porte fermée à clé. Le seul chemin, c'est le courriel. */}

              {/* LE PANSEMENT, EN ATTENDANT LA VRAIE CORRECTION. Nos courriels partent en
                  indésirables faute de signature DKIM sur le domaine — cela se règle chez
                  l'hébergeur, pas ici. D'ici là, le professeur qui ne voit rien arriver n'a
                  aucune raison d'aller chercher dans son dossier spam : on lui dit. */}
              <div style={{ marginTop: 20, background: '#fffbeb', border: '1px solid #fde68a',
                            borderRadius: 8, padding: '10px 12px', fontSize: 12.5, color: '#92400e' }}>
                <strong>Rien reçu&nbsp;?</strong> Regardez dans vos <strong>courriers indésirables</strong> —
                le message s’y range parfois.
              </div>
            </div>
          )}

        </div>
      </div>

      <footer className="py-3 text-center text-xs text-gray-400">
        aSchool · contact@aschool.fr
      </footer>
    </div>
  )
}
