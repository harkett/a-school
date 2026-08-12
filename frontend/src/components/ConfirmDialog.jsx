import { useEffect, useRef, useState } from 'react'
import { registerConfirmHandler } from '../confirmDialog'

// Dialogue de confirmation UNIQUE de l'app, monté à la racine (comme ErrorDialog) → disponible sur
// toutes les pages via showConfirm() (confirmDialog.js). Sert aux actions qui font PERDRE quelque
// chose : le prof lit clairement CE QUI change et confirme avant que ça parte.
//
// MÊME BOÎTE que ErrorDialog, le patron « vraie boîte de dialogue » de la maison : barre de titre
// avec pictogramme, titre et croix de fermeture ; corps aligné à gauche (un paragraphe centré ne se
// lit pas) ; pied sur fond doux avec les boutons à droite, l'action principale la plus à droite.
//
// QUATRE sorties sans confirmer — la croix, « Annuler », Échap, le clic en dehors — et toutes
// passent par `fermerSansConfirmer`. C'est vital : sans ce rappel, `demanderConfirmation`
// (confirmDialog.js) ne se résoudrait jamais et la fonction qui l'attend resterait figée.

// Les mots qui disent la dépense, en rouge dans le corps du message : « FACTURÉ » se lit alors
// avant le reste, au lieu de se fondre dans le paragraphe. Le message reste une simple chaîne
// côté appelant — aucun balisage à apprendre, aucune façon nouvelle d'écrire un message.
const MOTS_DEPENSE = /(FACTURÉ\S*|PAYANT\S*|DEUX appels)/g

function enRouge(message) {
  if (typeof message !== 'string') return message
  // Le groupe capturant fait tomber les mots trouvés aux index IMPAIRS du découpage : pas de
  // second test à faire, donc pas de `lastIndex` à réarmer entre deux appels.
  return message.split(MOTS_DEPENSE).map((bout, i) => (
    i % 2 === 1
      ? <strong key={i} style={{ color: '#dc2626' }}>{bout}</strong>
      : <span key={i}>{bout}</span>
  ))
}

export default function ConfirmDialog() {
  // { titre, message, confirmLabel, cancelLabel, onConfirm, onCancel, danger, icone } | null
  const [dialog, setDialog] = useState(null)
  const actionRef = useRef(null)

  useEffect(() => { registerConfirmHandler(setDialog) }, [])

  const fermerSansConfirmer = () => {
    // Avec un bouton unique, il n'y a pas de « sans confirmer » : les trois sorties douces
    // (croix, Échap, clic dehors) valent alors accusé de réception, comme le bouton lui-même.
    const cb = dialog?.boutonUnique ? dialog?.onConfirm : dialog?.onCancel
    setDialog(null)
    cb && cb()
  }

  // Ouverture : focus sur l'action (Entrée confirme) ; Échap annule. Hooks placés AVANT le return
  // conditionnel (règle des hooks React).
  useEffect(() => {
    if (!dialog) return
    actionRef.current?.focus()
    const onKey = e => { if (e.key === 'Escape') fermerSansConfirmer() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [dialog])   // eslint-disable-line react-hooks/exhaustive-deps

  if (!dialog) return null

  const annuler = fermerSansConfirmer
  const confirmer = () => { const cb = dialog.onConfirm; setDialog(null); cb && cb() }
  const couleurAction = dialog.danger ? '#dc2626' : 'var(--bleu)'

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      onClick={annuler}
      style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', zIndex: 2100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{ background: '#fff', borderRadius: 12, maxWidth: 460, width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.3)', overflow: 'hidden' }}
      >

        {/* ── Barre de titre : pictogramme + titre + croix de fermeture ── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '13px 16px', borderBottom: '1px solid #e2e8f0' }}>
          {/* Par défaut : avertissement (triangle) ambre — on prévient, on n'annonce pas une panne.
              `icone: 'interdit'` : sens interdit rouge, pour ce qui est déjà connu / déjà fait. */}
          {dialog.icone === 'interdit' ? (
            <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" style={{ flexShrink: 0 }}>
              <circle cx="12" cy="12" r="10" fill="#dc2626" />
              <rect x="6" y="10.75" width="12" height="2.5" rx="1.25" fill="#fff" />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>
              <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          )}
          <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a', flex: 1 }}>
            {dialog.titre || 'Confirmation'}
          </span>
          <button
            type="button"
            onClick={annuler}
            title="Fermer sans rien changer"
            aria-label="Fermer"
            style={{ width: 28, height: 28, borderRadius: '50%', border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        {/* ── Corps : le message, aligné à gauche, lisible (les \n sont respectés) ── */}
        <div style={{ padding: '18px 20px', fontSize: 14, color: '#334155', lineHeight: 1.65, whiteSpace: 'pre-line', textAlign: 'left' }}>
          {dialog.payant ? enRouge(dialog.message) : dialog.message}

          {/* `payant` : le rappel de la voie à 0 €, écrit UNE fois ici. Chaque clic payant a sa
              jumelle gratuite (l'admin exécute le prompt de son côté) — la lui redire au moment
              où il s'apprête à payer, c'est le seul moment où ça lui sert. */}
          {dialog.payant && (
            <div style={{ marginTop: 14, padding: '10px 12px', borderRadius: 8,
              background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', fontSize: 13 }}>
              <strong>Pour rester à 0 €</strong> — annulez, prenez le prompt de cette étape et
              exécutez-le vous-même auprès d'un agent externe, sur votre abonnement
              (aujourd'hui Sonnet avec un abonnement Max ; cela peut changer), puis rapportez le
              résultat ici. Vous obtenez la même chose sans que l'application appelle.
            </div>
          )}
        </div>

        {/* ── Pied : les boutons, à droite, sur fond doux — l'action principale la plus à droite ── */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 10, padding: '12px 16px', borderTop: '1px solid #e2e8f0', background: '#f8fafc' }}>
          {/* `boutonUnique` : un seul bouton, quand il n'y a rien à refuser (un prof prévenu
              d'une mise à jour ne peut pas la décliner — un « Annuler » lui laisserait croire le
              contraire). Additive : sans l'option, les deux boutons, comme avant. Échap et le
              clic en dehors se comportent alors comme ce bouton (ils confirment). */}
          {!dialog.boutonUnique && (
            <button
              type="button"
              onClick={annuler}
              title="Fermer sans rien changer"
              style={{ background: '#fff', color: '#475569', border: '1px solid #cbd5e1', borderRadius: 8, padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
            >
              {dialog.cancelLabel || 'Annuler'}
            </button>
          )}
          <button
            ref={actionRef}
            type="button"
            onClick={confirmer}
            style={{ background: couleurAction, color: '#fff', border: 'none', borderRadius: 8, padding: '8px 24px', fontSize: 13, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}
          >
            {dialog.confirmLabel || 'Continuer'}
          </button>
        </div>
      </div>
    </div>
  )
}
