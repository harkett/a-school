// Briques PARTAGÉES des cartouches de « Mes contenus » (une cartouche par onglet —
// décision utilisateur du 30/07 : chaque onglet est autonome, toucher l'un ne peut pas
// abîmer l'autre ; ici ne vivent que les morceaux communs, zéro copie).
import { useEffect } from 'react'
import { corpsHtml, imprimerApercu } from '../../utils/apercuHtml.js'
import { formatDateActivite } from '../../utils/activites.js'
import ZoneResultat from '../ZoneResultat'

// ---------------------------------------------------------------------------
// Icônes (traits sobres de l'appli, une couleur par niveau du modèle)
// ---------------------------------------------------------------------------
export const IconSequenceType = ({ size = 18 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="var(--bordeaux)" strokeWidth="2">
    <polygon points="12 2 2 7 12 12 22 7 12 2"/>
    <polyline points="2 17 12 22 22 17"/>
    <polyline points="2 12 12 17 22 12"/>
  </svg>
)
export const IconSeanceType = ({ size = 18 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2">
    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
    <line x1="8" y1="11" x2="16" y2="11"/>
    <line x1="8" y1="16" x2="14" y2="16"/>
  </svg>
)
export const IconActiviteType = ({ size = 18 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
  </svg>
)
export const IconEye = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
  </svg>
)
export const IconPencil = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
  </svg>
)
export const IconCopy = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
  </svg>
)
export const IconTrash = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
  </svg>
)
export const IconPrint = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
  </svg>
)
const IconCalendar = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
    <rect x="3" y="4" width="18" height="18" rx="2"/>
    <line x1="16" y1="2" x2="16" y2="6"/>
    <line x1="8" y1="2" x2="8" y2="6"/>
    <line x1="3" y1="10" x2="21" y2="10"/>
  </svg>
)

export const LIBELLE_TYPE = { sequence: 'Séquence', seance: 'Séance', activite: 'Activité' }
export const ICONE_TYPE = { sequence: IconSequenceType, seance: IconSeanceType, activite: IconActiviteType }

// Filtre de la recherche (titre, matière, niveau, type) — le même pour toutes les cartouches.
export function filtrer(liste, recherche) {
  const q = (recherche || '').trim().toLowerCase()
  if (!q) return liste
  return liste.filter(c =>
    [c.titre, c.matiere, c.niveau, LIBELLE_TYPE[c.type]]
      .some(v => (v || '').toLowerCase().includes(q))
  )
}

// Bouton d'action de ligne (voir / modifier / dupliquer / supprimer). Grisé = pas encore
// branché (les briques suivantes) : visible mais réellement inactif, title explicite.
export function BoutonAction({ title, onClick, disabled = false, danger = false, children }) {
  return (
    <button
      type="button"
      title={title}
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      style={{
        width: 28, height: 28, borderRadius: 6, border: '1px solid #e2e8f0',
        background: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        color: disabled ? '#cbd5e1' : (danger ? '#dc2626' : '#475569'),
        cursor: disabled ? 'not-allowed' : 'pointer', padding: 0, flexShrink: 0,
      }}
    >
      {children}
    </button>
  )
}

// Badge de date — même règle que Mes activités : récent → libellé relatif capitalisé,
// ancien → date complète ; le numérique compact s'affiche dessous.
export function BadgeDate({ createdAt }) {
  const dt = formatDateActivite(createdAt)
  const dateBase = dt.court ? (dt.recent ? dt.court.charAt(0).toUpperCase() + dt.court.slice(1) : dt.complet) : ''
  const dateLabel = dateBase && dt.heure ? `${dateBase} à ${dt.heure}` : dateBase
  if (!dateLabel) return null
  return (
    <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2, flexShrink: 0 }}>
      <span
        title={dt.complet ? `Créé le ${dt.complet} à ${dt.heure}` : undefined}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          fontSize: 11, fontWeight: 600, borderRadius: 99, padding: '2px 9px',
          background: dt.recent ? '#eff6ff' : '#f1f5f9',
          color: dt.recent ? '#1d4ed8' : '#475569',
        }}
      >
        <IconCalendar />
        {dateLabel}
      </span>
      {dt.numerique && (
        <span style={{ fontSize: 10, color: '#94a3b8', fontVariantNumeric: 'tabular-nums' }}>
          {dt.numerique}-{dt.heure}
        </span>
      )}
    </span>
  )
}

// État de rangement affiché à droite d'une ligne.
export function EtatRangement({ c }) {
  if (c.type === 'sequence') {
    const n = c.nb_seances || 0
    return <span style={{ fontSize: 12.5, color: n > 0 ? '#475569' : '#94a3b8' }}>{n > 0 ? `${n} séance${n > 1 ? 's' : ''}` : 'Vide'}</span>
  }
  if (c.parent) {
    return (
      <span style={{ fontSize: 12.5, color: '#475569' }}>
        Rangée dans <span style={{ color: 'var(--bleu)', fontWeight: 600 }} title="L'ouverture du conteneur arrive avec les prochaines briques">{c.parent.titre || '—'}</span>
      </span>
    )
  }
  return <span style={{ fontSize: 12.5, color: '#94a3b8' }}>Non rangée</span>
}

// Une ligne de la bibliothèque — le MÊME dessin pour toutes les cartouches. Les actions
// varient par les callbacks : `onApercu` (œil), `onModifier` (crayon, absent = grisé).
export function LigneContenu({ c, dernier = false, estSel = false, onClick, title, onApercu, onModifier, titleModifier }) {
  const Icone = ICONE_TYPE[c.type]
  const sousTitre = [LIBELLE_TYPE[c.type], [c.matiere, c.niveau].filter(Boolean).join(' · ')].filter(Boolean).join(' — ')
  return (
    <div
      onClick={onClick}
      title={title}
      style={{
        display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
        borderBottom: dernier ? 'none' : '1px solid #f1f5f9',
        borderLeft: estSel ? '3px solid var(--bordeaux)' : '3px solid transparent',
        background: estSel ? '#fdf2f5' : '#fff',
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      <span style={{ flexShrink: 0, display: 'inline-flex' }}><Icone /></span>
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ fontSize: 13.5, fontWeight: 600, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.titre}</div>
        <div style={{ fontSize: 12, color: '#64748b' }}>{sousTitre}</div>
      </div>
      <BadgeDate createdAt={c.created_at} />
      <span style={{ flexShrink: 0 }}><EtatRangement c={c} /></span>
      {/* stopPropagation : un clic sur une action ne doit pas AUSSI ouvrir la ligne */}
      <div style={{ display: 'flex', gap: 6, flexShrink: 0 }} onClick={e => e.stopPropagation()}>
        <BoutonAction
          title={c.resultat ? 'Voir l’aperçu mis en forme' : 'Rien à afficher pour ce contenu'}
          disabled={!c.resultat}
          onClick={() => onApercu({ titre: c.titre, html: corpsHtml(c.resultat) })}
        >
          <IconEye />
        </BoutonAction>
        {onModifier ? (
          <BoutonAction title={titleModifier || 'Modifier'} onClick={onModifier}>
            <IconPencil />
          </BoutonAction>
        ) : (
          <BoutonAction title="Bientôt — la modification arrive avec les prochaines briques" disabled>
            <IconPencil />
          </BoutonAction>
        )}
        <BoutonAction title="Bientôt — la duplication arrive avec les prochaines briques" disabled>
          <IconCopy />
        </BoutonAction>
        <BoutonAction title="Bientôt — la suppression arrive avec les prochaines briques" disabled danger>
          <IconTrash />
        </BoutonAction>
      </div>
    </div>
  )
}

// Le conteneur blanc d'une liste + message quand elle est vide.
export function ListeBlanche({ children, vide, messageVide }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
      {vide ? (
        <p style={{ fontSize: 13, color: '#64748b', textAlign: 'center', padding: '28px 16px', margin: 0 }}>{messageVide}</p>
      ) : children}
    </div>
  )
}

// Panneau de DROITE d'une activité : en-tête (titre + paramètres) + le résultat rendu
// comme à la création (même ZoneResultat, exports compris).
export function DetailActivite({ detail, email }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div>
        <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b' }}>{detail.titre}</div>
        <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
          {[
            detail.activite_label,
            [detail.matiere, detail.niveau].filter(Boolean).join(' · ') || null,
            detail.sous_type,
            detail.nb ? `${detail.nb} questions` : null,
            detail.avec_correction ? 'Avec correction' : 'Sans correction',
            detail.ton === 'academique' ? 'Ton académique' : detail.ton === 'operationnel' ? 'Ton opérationnel' : null,
          ].filter(Boolean).join(' · ')}
        </div>
      </div>
      <ZoneResultat resultat={detail.resultat} loading={false} email={email} />
    </div>
  )
}

export function PlaceholderDetail({ texte }) {
  return (
    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: '#94a3b8', fontSize: 13, padding: 24 }}>
      {texte}
    </div>
  )
}

// Aperçu « HTML » — même dispositif que l'Historique (corpsHtml + imprimerApercu partagés).
// Chaque cartouche porte le sien (état local) : `apercu` = { titre, html } | null.
export function ApercuModal({ apercu, onFermer }) {
  // Échap ferme l'aperçu (même réflexe que l'Historique). Hook AVANT le return conditionnel.
  useEffect(() => {
    if (apercu === null) return
    const onEsc = e => { if (e.key === 'Escape') onFermer() }
    window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [apercu, onFermer])
  if (apercu === null) return null
  return (
    <div
      onClick={onFermer}
      style={{ position: 'fixed', inset: 0, zIndex: 2000, background: 'rgba(15,23,42,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{ background: '#fff', borderRadius: 10, maxWidth: 820, width: '100%', maxHeight: '88vh', display: 'flex', flexDirection: 'column', boxShadow: '0 20px 60px rgba(0,0,0,0.3)', overflow: 'hidden' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
          <span style={{ fontWeight: 700, color: '#0f172a', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{apercu.titre}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <button type="button" onClick={() => imprimerApercu(apercu.html)} className="btn-secondary" title="Imprimer ce contenu mis en forme">
              <IconPrint /> Imprimer
            </button>
            <button type="button" onClick={onFermer} title="Fermer l'aperçu" style={{ width: 28, height: 28, borderRadius: '50%', border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
        <div className="apercu-corps" style={{ overflowY: 'auto', padding: '22px 28px', color: '#1e293b', lineHeight: 1.7, fontSize: 15 }} dangerouslySetInnerHTML={{ __html: apercu.html }} />
        <style>{`
          .apercu-corps h1,.apercu-corps h2,.apercu-corps h3{color:#0f172a;line-height:1.3;margin:1.4em 0 .4em}
          .apercu-corps h1{font-size:1.5rem}.apercu-corps h2{font-size:1.25rem}.apercu-corps h3{font-size:1.08rem}
          .apercu-corps p{margin:.6em 0}
          .apercu-corps ul,.apercu-corps ol{margin:.6em 0 .6em 1.4em;padding:0}.apercu-corps li{margin:.3em 0}
          .apercu-corps hr{border:none;border-top:1px solid #e2e8f0;margin:1.4em 0}
          .apercu-corps strong{color:#0f172a}
        `}</style>
      </div>
    </div>
  )
}
