import { useEffect, useState } from 'react'
import { registerErrorHandler, openFeedbackFromError } from '../errorDialog'
import { registerServerHealthHandler, MSG_SERVEUR_INDISPONIBLE } from '../serverHealth'

// Modale d'erreur UNIQUE de l'app, montée à la racine → présente sur TOUTES les pages
// (connexion, inscription, admin, app connectée). Toute erreur passe par le canal unique
// showError() (errorDialog.js) OU par la détection serveur (serverHealth.js) et arrive ICI.
// Règle absolue : toute erreur = modale bloquante avec logo rouge, jamais un avertissement
// passif. C'est le point « en amont » : aucune page ne peut être oubliée, par construction.
export default function ErrorDialog() {
  // dialog = { text, feedback } | null. `feedback` : ajoute le lien « cliquez ici » qui ouvre
  // le formulaire de feedback existant (échecs techniques de génération, règle 23).
  const [dialog, setDialog] = useState(null)

  useEffect(() => {
    registerErrorHandler((text, opts = {}) => setDialog({ text, feedback: !!opts.feedback }))
    registerServerHealthHandler((degraded) => { if (degraded) setDialog({ text: MSG_SERVEUR_INDISPONIBLE, feedback: false }) })
  }, [])

  if (!dialog) return null

  const fermer = () => setDialog(null)

  // Avec le lien feedback : on coupe le texte imposé autour de « cliquez ici » et on rend ce
  // segment comme un lien. Si le repère n'est pas trouvé (message d'un autre appel), on retombe
  // proprement sur le texte simple.
  const [avant, apres] = dialog.feedback ? dialog.text.split('cliquez ici') : [dialog.text, null]

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#fff', borderRadius: '12px', padding: '28px 24px', maxWidth: '380px', width: '90%', textAlign: 'center', boxShadow: '0 8px 32px rgba(0,0,0,0.2)' }}>
        <svg width="52" height="52" viewBox="0 0 24 24" style={{ display: 'block', margin: '0 auto 16px' }} aria-hidden="true">
          <circle cx="12" cy="12" r="10" fill="#dc2626" />
          <rect x="11" y="6.5" width="2" height="7" rx="1" fill="#fff" />
          <circle cx="12" cy="16.6" r="1.25" fill="#fff" />
        </svg>
        <div style={{ fontSize: '14px', color: '#1e293b', marginBottom: '20px', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
          {dialog.feedback && apres !== null ? (
            <>
              {avant}
              <button
                type="button"
                onClick={() => { fermer(); openFeedbackFromError() }}
                style={{ background: 'none', border: 'none', padding: 0, color: '#1F6EEB', textDecoration: 'underline', cursor: 'pointer', font: 'inherit' }}
              >
                cliquez ici
              </button>
              {apres}
            </>
          ) : dialog.text}
        </div>
        <button
          onClick={fermer}
          title="Fermer ce message"
          style={{ background: 'var(--bleu)', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px 28px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}
        >
          OK
        </button>
      </div>
    </div>
  )
}
