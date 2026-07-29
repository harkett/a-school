// Écran « Mes contenus » — la bibliothèque unique du prof (modèle playlist :
// séquence ⊃ séances ⊃ activités, parent toujours facultatif).
// Brique 1 (socle) : liste à plat de TOUS les contenus mélangés, onglets avec compteurs,
// recherche, « + Créer », état de rangement par ligne, aperçu HTML et suppression.
//
// État serveur : React Query, LOCAL à ce sous-ensemble (décision de chantier — le reste de
// l'appli migrera dans un chantier dédié). La liste n'est JAMAIS patchée à la main : toute
// écriture invalide la requête et la base est relue.
import { useEffect, useMemo, useState } from 'react'
import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_STD } from '../utils/api.js'
import { corpsHtml, imprimerApercu } from '../utils/apercuHtml.js'
import { showError } from '../errorDialog'

// ---------------------------------------------------------------------------
// Icônes (traits sobres de l'appli, une couleur par niveau du modèle)
// ---------------------------------------------------------------------------
const IconSequenceType = ({ size = 18 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="var(--bordeaux)" strokeWidth="2">
    <polygon points="12 2 2 7 12 12 22 7 12 2"/>
    <polyline points="2 17 12 22 22 17"/>
    <polyline points="2 12 12 17 22 12"/>
  </svg>
)
const IconSeanceType = ({ size = 18 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2">
    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
    <line x1="8" y1="11" x2="16" y2="11"/>
    <line x1="8" y1="16" x2="14" y2="16"/>
  </svg>
)
const IconActiviteType = ({ size = 18 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
  </svg>
)
const IconEye = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
  </svg>
)
const IconPencil = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
  </svg>
)
const IconCopy = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
  </svg>
)
const IconTrash = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
  </svg>
)
const IconPrint = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
  </svg>
)
const IconSearch = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
)

const LIBELLE_TYPE = { sequence: 'Séquence', seance: 'Séance', activite: 'Activité' }
const ICONE_TYPE = { sequence: IconSequenceType, seance: IconSeanceType, activite: IconActiviteType }

const ONGLETS = [
  ['tout', 'Tout', 'tout'],
  ['sequence', 'Séquences', 'sequences'],
  ['seance', 'Séances', 'seances'],
  ['activite', 'Activités', 'activites'],
]

// Bouton d'action de ligne (voir / modifier / dupliquer / supprimer). Grisé = pas encore
// branché (les briques suivantes) : visible mais réellement inactif, title explicite.
function BoutonAction({ title, onClick, disabled = false, danger = false, children }) {
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

function EcranMesContenus({ onNavigate }) {
  const qc = useQueryClient()
  const [onglet, setOnglet] = useState('tout')
  const [recherche, setRecherche] = useState('')
  const [menuCreer, setMenuCreer] = useState(false)
  const [apercu, setApercu] = useState(null)        // { titre, html } | null
  const [suppression, setSuppression] = useState(null)  // ligne à supprimer (confirmation) | null

  // LA source de vérité : la base, relue par React Query (jamais de liste patchée à la main).
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['mes-contenus'],
    queryFn: async () => lireReponse(await apiFetch('/api/mes-contenus', {}, TIMEOUT_STD)),
  })

  // Suppression d'une ACTIVITÉ (seul type présent en brique 1) : l'endpoint existant, puis
  // invalidation → React Query relit la base.
  const supprimer = useMutation({
    mutationFn: async (ligne) =>
      lireReponse(await apiFetch(`/api/mes-activites/${ligne.id}`, { method: 'DELETE' }, TIMEOUT_STD)),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['mes-contenus'] }),
    onError: (err) => showError(messagePourEcran(err)),
    onSettled: () => setSuppression(null),
  })

  // Échap ferme l'aperçu HTML (même réflexe que l'Historique).
  useEffect(() => {
    if (apercu === null) return
    const onEsc = e => { if (e.key === 'Escape') setApercu(null) }
    window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [apercu])

  const contenus = data?.contenus || []
  const compteurs = data?.compteurs || { tout: 0, sequences: 0, seances: 0, activites: 0 }

  const visibles = useMemo(() => {
    const q = recherche.trim().toLowerCase()
    return contenus.filter(c => {
      if (onglet !== 'tout' && c.type !== onglet) return false
      if (!q) return true
      return [c.titre, c.matiere, c.niveau, LIBELLE_TYPE[c.type]]
        .some(v => (v || '').toLowerCase().includes(q))
    })
  }, [contenus, onglet, recherche])

  // État de rangement affiché à droite d'une ligne.
  function etatRangement(c) {
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* En-tête : titre + recherche */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <h2 style={{ fontSize: 17, fontWeight: 700, color: '#1e293b', margin: 0 }}>Mes contenus</h2>
        <div style={{ position: 'relative' }}>
          <span style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', display: 'inline-flex' }}><IconSearch /></span>
          <input
            type="search"
            value={recherche}
            onChange={e => setRecherche(e.target.value)}
            placeholder="Rechercher…"
            title="Rechercher dans vos contenus (titre, matière, niveau, type)"
            style={{ padding: '7px 12px 7px 30px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 13, width: 220, background: '#fff' }}
          />
        </div>
      </div>

      {/* Onglets avec compteurs + « Créer » */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ display: 'inline-flex', border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden', background: '#fff' }}>
          {ONGLETS.map(([id, label, cle], i) => (
            <button
              key={id}
              type="button"
              onClick={() => setOnglet(id)}
              title={`Afficher : ${label.toLowerCase()}`}
              style={{
                padding: '7px 14px', fontSize: 13, border: 'none', cursor: 'pointer',
                borderLeft: i > 0 ? '1px solid #e2e8f0' : 'none',
                background: onglet === id ? 'var(--bordeaux)' : '#fff',
                color: onglet === id ? '#fff' : '#475569',
                fontWeight: onglet === id ? 600 : 400,
              }}
            >
              {label} ({compteurs[cle]})
            </button>
          ))}
        </div>

        <div style={{ position: 'relative' }}>
          <button
            type="button"
            onClick={() => setMenuCreer(o => !o)}
            title="Créer un nouveau contenu"
            style={{ background: 'var(--bleu)', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Créer
          </button>
          {menuCreer && (
            <>
              {/* voile invisible : un clic ailleurs referme le menu */}
              <div style={{ position: 'fixed', inset: 0, zIndex: 40 }} onClick={() => setMenuCreer(false)} />
              <div style={{ position: 'absolute', right: 0, top: 'calc(100% + 6px)', zIndex: 41, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, boxShadow: '0 8px 24px rgba(0,0,0,0.12)', minWidth: 200, padding: 6, display: 'flex', flexDirection: 'column' }}>
                <button
                  type="button"
                  onClick={() => { setMenuCreer(false); onNavigate('creer-activite') }}
                  title="Créer une activité (l'outil existant)"
                  style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', fontSize: 13, color: '#1e293b', background: 'none', border: 'none', borderRadius: 6, cursor: 'pointer', textAlign: 'left' }}
                >
                  <IconActiviteType size={15} /> Une activité
                </button>
                <span title="Bientôt — l'outil Séance rejoint Mes contenus à la prochaine brique" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', fontSize: 13, color: '#b4bac3', cursor: 'not-allowed' }}>
                  <IconSeanceType size={15} /> Une séance
                  <span style={{ marginLeft: 'auto', fontSize: 9, fontWeight: 600, color: '#94a3b8', background: '#f1f5f9', borderRadius: 99, padding: '1px 6px' }}>bientôt</span>
                </span>
                <span title="Bientôt — la séquence (conteneur de séances) arrive avec les prochaines briques" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', fontSize: 13, color: '#b4bac3', cursor: 'not-allowed' }}>
                  <IconSequenceType size={15} /> Une séquence
                  <span style={{ marginLeft: 'auto', fontSize: 9, fontWeight: 600, color: '#94a3b8', background: '#f1f5f9', borderRadius: 99, padding: '1px 6px' }}>bientôt</span>
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* La liste à plat */}
      <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
        {isLoading && (
          <p style={{ fontSize: 13, color: '#64748b', textAlign: 'center', padding: '28px 16px', margin: 0 }}>Chargement de vos contenus…</p>
        )}
        {isError && (
          <p style={{ fontSize: 13, color: '#dc2626', textAlign: 'center', padding: '28px 16px', margin: 0, whiteSpace: 'pre-wrap' }}>{messagePourEcran(error)}</p>
        )}
        {!isLoading && !isError && contenus.length === 0 && (
          <div style={{ textAlign: 'center', padding: '32px 16px' }}>
            <p style={{ fontSize: 13.5, color: '#475569', margin: '0 0 4px', fontWeight: 600 }}>Votre bibliothèque est vide pour l'instant.</p>
            <p style={{ fontSize: 12.5, color: '#94a3b8', margin: 0 }}>Vos activités, séances et séquences apparaîtront ici.</p>
          </div>
        )}
        {!isLoading && !isError && contenus.length > 0 && visibles.length === 0 && (
          <p style={{ fontSize: 13, color: '#64748b', textAlign: 'center', padding: '28px 16px', margin: 0 }}>Aucun contenu ne correspond à votre recherche.</p>
        )}
        {visibles.map((c, i) => {
          const Icone = ICONE_TYPE[c.type]
          const sousTitre = [LIBELLE_TYPE[c.type], [c.matiere, c.niveau].filter(Boolean).join(' · ')].filter(Boolean).join(' — ')
          const dateCreation = c.created_at ? new Date(c.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }) : null
          return (
            <div
              key={`${c.type}-${c.id}`}
              title={dateCreation ? `Créé le ${dateCreation}` : undefined}
              style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
                borderBottom: i < visibles.length - 1 ? '1px solid #f1f5f9' : 'none',
              }}
            >
              <span style={{ flexShrink: 0, display: 'inline-flex' }}><Icone /></span>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{ fontSize: 13.5, fontWeight: 600, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.titre}</div>
                <div style={{ fontSize: 12, color: '#64748b' }}>{sousTitre}</div>
              </div>
              <span style={{ flexShrink: 0 }}>{etatRangement(c)}</span>
              <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                <BoutonAction
                  title={c.resultat ? 'Voir l’aperçu mis en forme' : 'Rien à afficher pour ce contenu'}
                  disabled={!c.resultat}
                  onClick={() => setApercu({ titre: c.titre, html: corpsHtml(c.resultat) })}
                >
                  <IconEye />
                </BoutonAction>
                <BoutonAction title="Bientôt — la modification arrive avec les prochaines briques" disabled>
                  <IconPencil />
                </BoutonAction>
                <BoutonAction title="Bientôt — la duplication arrive avec les prochaines briques" disabled>
                  <IconCopy />
                </BoutonAction>
                <BoutonAction
                  title={c.type === 'activite' ? 'Supprimer cette activité' : 'Bientôt — la suppression arrive avec les prochaines briques'}
                  disabled={c.type !== 'activite'}
                  danger
                  onClick={() => setSuppression(c)}
                >
                  <IconTrash />
                </BoutonAction>
              </div>
            </div>
          )
        })}
      </div>

      {/* Confirmation de suppression — règle maison : jamais de suppression au clic direct. */}
      {suppression && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={() => { if (!supprimer.isPending) setSuppression(null) }}
        >
          <div
            style={{ background: '#fff', borderRadius: '10px', padding: '24px 28px', maxWidth: '420px', width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ fontWeight: 700, fontSize: '15px', marginBottom: '10px', color: '#1e293b' }}>
              Supprimer cette activité ?
            </div>
            <p style={{ fontSize: '13.5px', color: '#374151', margin: '0 0 6px', lineHeight: 1.6 }}>
              <strong>"{suppression.titre}"</strong>
            </p>
            <p style={{ fontSize: '13px', color: '#ef4444', margin: '0 0 20px', lineHeight: 1.5 }}>
              Cette action est irréversible — l'activité sera définitivement supprimée.
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setSuppression(null)}
                disabled={supprimer.isPending}
                style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
              >
                Annuler
              </button>
              <button
                onClick={() => supprimer.mutate(suppression)}
                disabled={supprimer.isPending}
                title="Confirmer la suppression définitive"
                style={{ background: 'var(--bordeaux)', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: supprimer.isPending ? 'wait' : 'pointer' }}
              >
                {supprimer.isPending ? 'Suppression…' : 'Supprimer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Aperçu « HTML » — même dispositif que l'Historique (corpsHtml + imprimerApercu partagés). */}
      {apercu !== null && (
        <div
          onClick={() => setApercu(null)}
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
                <button type="button" onClick={() => setApercu(null)} title="Fermer l'aperçu" style={{ width: 28, height: 28, borderRadius: '50%', border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}>
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
      )}

    </div>
  )
}

// React Query volontairement LOCAL au sous-ensemble « Mes contenus » : un client dédié ici,
// pas de provider global — le reste de l'appli migrera dans le chantier React Query dédié.
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

export default function MesContenus({ onNavigate }) {
  return (
    <QueryClientProvider client={queryClient}>
      <EcranMesContenus onNavigate={onNavigate} />
    </QueryClientProvider>
  )
}
