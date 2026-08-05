import { useEffect, useRef, useState } from 'react'
import { registerErrorHandler, openFeedbackFromError } from '../errorDialog'
import { registerServerHealthHandler, MSG_SERVEUR_INDISPONIBLE } from '../serverHealth'

// Modale d'erreur UNIQUE de l'app, montée à la racine → présente sur TOUTES les pages
// (connexion, inscription, admin, app connectée). Toute erreur passe par le canal unique
// showError() (errorDialog.js) OU par la détection serveur (serverHealth.js) et arrive ICI.
// Règle absolue : toute erreur = modale bloquante, jamais un avertissement passif.
// HABIT « vraie boîte de dialogue » (demande utilisateur du 30/07) : barre de titre avec
// icône + croix de fermeture, corps aligné à gauche, pied avec les boutons à droite —
// comme n'importe quelle application sérieuse. Échap ferme, OK a le focus (Entrée ferme).
export default function ErrorDialog() {
  // dialog = { text, feedback, ref } | null. `feedback` : le segment « cliquez ici » du texte
  // devient un lien + un bouton « Nous le signaler » au pied (échecs techniques, règle 23).
  const [dialog, setDialog] = useState(null)
  const okRef = useRef(null)

  useEffect(() => {
    registerErrorHandler((text, opts = {}) => setDialog({
      text, feedback: !!opts.feedback, ref: opts.ref || null,
      danger: !!opts.danger, titre: opts.titre || '',
    }))
    registerServerHealthHandler((degraded) => { if (degraded) setDialog({
      text: MSG_SERVEUR_INDISPONIBLE, feedback: false, ref: null, danger: true, titre: '' }) })
  }, [])

  // Ouverture : focus sur OK (Entrée ferme) ; Échap ferme aussi — les gestes standard.
  useEffect(() => {
    if (!dialog) return
    okRef.current?.focus()
    const onEsc = e => { if (e.key === 'Escape') setDialog(null) }
    window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [dialog])

  if (!dialog) return null

  const fermer = () => setDialog(null)
  const signaler = () => { fermer(); openFeedbackFromError(dialog.ref) }

  // Avec le lien feedback : on coupe le texte imposé autour de « cliquez ici » et on rend ce
  // segment comme un lien. Si le repère n'est pas trouvé (message d'un autre appel), on retombe
  // proprement sur le texte simple.
  const [avant, apres] = dialog.feedback ? dialog.text.split('cliquez ici') : [dialog.text, null]

  // TON de la boîte : bandeau BLEU par défaut (un message à lire), ROUGE quand c'est grave
  // (showError(msg, { danger: true }) ou serveur indisponible). Le bandeau est plein, avec son
  // titre et sa croix en blanc — le patron d'une vraie application.
  const accent = dialog.danger ? '#dc2626' : 'var(--bleu)'
  const titre = dialog.titre || (dialog.danger ? 'Attention' : 'Information')

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}
    >
      <div style={{ background: '#fff', borderRadius: 12, maxWidth: 460, width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.3)', overflow: 'hidden' }}>

        {/* ── Bandeau de titre PLEIN (bleu, ou rouge si c'est grave) : icône + titre + croix ── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', background: accent }}>
          <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="10" fill="#fff" />
            <rect x="11" y={dialog.danger ? 6.5 : 10.5} width="2" height="7" rx="1" fill={accent} />
            <circle cx="12" cy={dialog.danger ? 16.6 : 7.4} r="1.25" fill={accent} />
          </svg>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#fff', flex: 1 }}>{titre}</span>
          <button
            type="button"
            onClick={fermer}
            title="Fermer ce message"
            aria-label="Fermer"
            style={{ width: 28, height: 28, borderRadius: '50%', border: '1px solid rgba(255,255,255,0.45)', background: 'transparent', color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        {/* ── Corps : le message, aligné à gauche, lisible ── */}
        <div style={{ padding: '18px 20px', fontSize: 14, color: '#334155', lineHeight: 1.65, whiteSpace: 'pre-line', textAlign: 'left' }}>
          {dialog.feedback && apres !== null ? (
            <>
              {avant}
              <button
                type="button"
                onClick={signaler}
                style={{ background: 'none', border: 'none', padding: 0, color: '#1F6EEB', textDecoration: 'underline', cursor: 'pointer', font: 'inherit' }}
              >
                cliquez ici
              </button>
              {apres}
            </>
          ) : dialog.text}
          {dialog.ref && (
            <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 12 }}>
              Référence : <strong style={{ color: '#64748b', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>{dialog.ref}</strong>
            </div>
          )}
        </div>

        {/* ── Pied : les boutons, à droite, sur fond doux ── */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 10, padding: '12px 16px', borderTop: '1px solid #e2e8f0', background: '#f8fafc' }}>
          {dialog.feedback && (
            <button
              type="button"
              onClick={signaler}
              title="Ouvrir le formulaire de retour pour nous signaler ce problème"
              style={{ background: '#fff', color: '#475569', border: '1px solid #cbd5e1', borderRadius: 8, padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
            >
              Nous le signaler
            </button>
          )}
          <button
            ref={okRef}
            type="button"
            onClick={fermer}
            title="Fermer ce message"
            style={{ background: accent, color: '#fff', border: 'none', borderRadius: 8, padding: '8px 24px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
          >
            OK
          </button>
        </div>

      </div>
    </div>
  )
}
