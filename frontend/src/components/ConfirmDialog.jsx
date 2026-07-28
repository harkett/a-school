import { useEffect, useState } from 'react'
import { registerConfirmHandler } from '../confirmDialog'

// Dialogue de confirmation UNIQUE de l'app, monté à la racine (comme ErrorDialog) → disponible sur
// toutes les pages via showConfirm() (confirmDialog.js). Sert aux actions qui font PERDRE quelque
// chose : le prof lit clairement CE QUI change et confirme avant que ça parte. Pictogramme
// d'avertissement (ambre, pas rouge : c'est une décision, pas une erreur). Échap / clic dehors /
// « Annuler » = on ne fait rien ; seul « Continuer » déclenche l'action.
export default function ConfirmDialog() {
  const [dialog, setDialog] = useState(null)  // { titre, message, confirmLabel, cancelLabel, onConfirm, danger } | null

  useEffect(() => { registerConfirmHandler(setDialog) }, [])

  // Échap = annuler. Hook placé AVANT le return conditionnel (règle des hooks React).
  useEffect(() => {
    if (!dialog) return
    const onKey = e => { if (e.key === 'Escape') setDialog(null) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [dialog])

  if (!dialog) return null

  const annuler = () => setDialog(null)
  const confirmer = () => { const cb = dialog.onConfirm; setDialog(null); cb && cb() }
  const couleurAction = dialog.danger ? '#dc2626' : 'var(--bleu)'

  return (
    <div
      onClick={annuler}
      style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', zIndex: 2100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{ background: '#fff', borderRadius: 12, padding: '26px 24px 22px', maxWidth: 420, width: '100%', textAlign: 'center', boxShadow: '0 12px 40px rgba(0,0,0,0.25)' }}
      >
        {/* Pictogramme d'avertissement (triangle) — ambre : on prévient, on n'annonce pas une panne. */}
        <svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'block', margin: '0 auto 14px' }} aria-hidden="true">
          <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        {dialog.titre && (
          <div style={{ fontSize: 16, fontWeight: 700, color: '#0f172a', marginBottom: 10 }}>{dialog.titre}</div>
        )}
        <div style={{ fontSize: 14, color: '#334155', marginBottom: 22, lineHeight: 1.6, whiteSpace: 'pre-line' }}>
          {dialog.message}
        </div>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={annuler}
            className="btn-secondary"
            style={{ minWidth: 120, justifyContent: 'center' }}
          >
            {dialog.cancelLabel || 'Annuler'}
          </button>
          <button
            type="button"
            onClick={confirmer}
            style={{ minWidth: 120, background: couleurAction, color: '#fff', border: 'none', borderRadius: 8, padding: '9px 20px', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}
          >
            {dialog.confirmLabel || 'Continuer'}
          </button>
        </div>
      </div>
    </div>
  )
}
