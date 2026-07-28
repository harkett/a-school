import { useState, useEffect } from 'react'
import { apiFetch, TIMEOUT_STD } from '../utils/api.js'
import { coupleKey, grouperParCouple, parDateDesc, formatDateActivite, couleurCouple, correspondProfil } from '../utils/activites.js'
import SplitPane from './SplitPane.jsx'

const IconTrash = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
    <path d="M10 11v6"/><path d="M14 11v6"/>
    <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
  </svg>
)

const IconShare = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
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


function StatsCommunaute({ matiere, niveau }) {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    if (!matiere && !niveau) return
    const params = new URLSearchParams()
    if (matiere) params.append('matiere', matiere)
    if (niveau)  params.append('niveau', niveau)
    fetch(`/api/stats/matiere?${params}`, { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setStats(d) })
      .catch(() => {})
  }, [matiere, niveau])

  if (!stats || stats.total_plateforme === 0) return null

  return (
    <div style={{
      background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
      padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
    }}>
      <div style={{ display: 'flex', flex: 1, gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <div>
          <span style={{ fontSize: 11, color: '#94a3b8', display: 'block' }}>Sur la plateforme</span>
          <span style={{ fontSize: 15, fontWeight: 700, color: '#1e293b' }}>{stats.total_plateforme}</span>
          <span style={{ fontSize: 11, color: '#64748b' }}> activités · {stats.nb_profs} prof{stats.nb_profs > 1 ? 's' : ''}</span>
        </div>
        {stats.top_types.length > 0 && (
          <div>
            <span style={{ fontSize: 11, color: '#94a3b8', display: 'block' }}>Types populaires</span>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 2 }}>
              {stats.top_types.map(t => (
                <span key={t.label} style={{
                  fontSize: 11, background: 'white', border: '1px solid #e2e8f0',
                  borderRadius: 99, padding: '1px 8px', color: '#475569',
                }}>
                  {t.label} <strong style={{ color: '#A63045' }}>×{t.nb}</strong>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Styles partagés du panneau de détail (colonne droite) — repris de l'ancienne modale « Plus de détails ».
const LABEL_STYLE  = { fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }
const SOURCE_STYLE = { fontSize: 13, color: '#64748b', fontStyle: 'italic', lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, padding: '10px 14px' }
const PRE_STYLE    = { whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 13, color: '#374151', lineHeight: 1.7, margin: 0, fontFamily: 'inherit' }

export default function MesActivites({ onCharger, sessionMatiere, sessionNiveau, onNavigate, userName }) {
  const isMobile = window.innerWidth < 768
  const [activites, setActivites] = useState([])
  const [loading, setLoading]     = useState(true)
  const [hovered, setHovered]     = useState(null)
  const [toggling, setToggling]         = useState(null)
  const [selected, setSelected]         = useState(null)  // id de l'activité affichée dans le panneau de détail (colonne droite)
  const [anonymeDialog, setAnonymeDialog] = useState(null)
  const [deleteDialog, setDeleteDialog] = useState(null)
  const [profilDialog, setProfilDialog] = useState(null)  // activité hors profil courant → modale "passez sur le profil"
  const [deleting, setDeleting]     = useState(null)
  const [vue, setVue]               = useState('courant')  // 'courant' (couple du profil) | 'toutes' (groupé par couple)

  useEffect(() => {
    apiFetch('/api/mes-activites', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => r.json())
      .then(data => { setActivites(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  async function supprimerActivite(id) {
    setDeleting(id)
    try {
      const res = await apiFetch(`/api/mes-activites/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      }, TIMEOUT_STD)
      if (res.ok) {
        setActivites(prev => prev.filter(a => a.id !== id))
      }
    } finally {
      setDeleting(null)
      setDeleteDialog(null)
    }
  }

  async function togglePartage(id, newValue, anonyme = false) {
    setToggling(id)
    try {
      const res = await apiFetch(`/api/mes-activites/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ partagee: newValue, anonyme }),
      })
      if (res.ok) {
        setActivites(prev => prev.map(a => a.id === id ? { ...a, partagee: newValue } : a))
      }
    } finally {
      setToggling(null)
    }
  }

  // « Reprendre » : on ne regénère QUE des activités du profil courant. Une activité d'un
  // autre couple (matière/niveau) → modale bloquante qui renvoie vers Mon profil (règle maison :
  // incohérence = on explique + on guide, jamais un marqueur passif / bouton grisé muet).
  function tenterReprendre(a) {
    if (correspondProfil(a, sessionMatiere, sessionNiveau)) onCharger(a)
    else setProfilDialog(a)
  }

  const filtered = activites.filter(a => {
    if (sessionMatiere && a.matiere !== sessionMatiere) return false
    if (sessionNiveau  && a.niveau  !== sessionNiveau)  return false
    return true
  }).sort(parDateDesc)   // plus récent en haut

  const labelProfil = [sessionMatiere, sessionNiveau].filter(Boolean).join(', ')

  // Onglet « Toutes » : sections par couple (logique pure testée dans utils/activites.test.js).
  const currentKey  = coupleKey(sessionMatiere, sessionNiveau)
  const sections    = grouperParCouple(activites, currentKey)
  const headerCount = vue === 'courant' ? filtered.length : activites.length

  // Liste réellement affichée à gauche (selon l'onglet), dans l'ordre d'affichage.
  const visibles = vue === 'courant' ? filtered : sections.flatMap(s => s.items)

  // Sélection par défaut + garde-fou : le panneau de détail montre TOUJOURS une activité visible
  // (au chargement → la plus récente ; après une suppression → la suivante ; changement d'onglet → 1ʳᵉ).
  useEffect(() => {
    if (loading) return
    if (visibles.length === 0) { if (selected !== null) setSelected(null); return }
    if (!visibles.some(a => a.id === selected)) setSelected(visibles[0].id)
  }, [loading, vue, activites, sessionMatiere, sessionNiveau])   // eslint-disable-line react-hooks/exhaustive-deps

  const selectedActivite = activites.find(a => a.id === selected) || null

  // Ligne-carte d'une activité, réutilisée par les deux onglets. Cliquable → sélectionne (détail à droite).
  const ActiviteRow = (a, last) => {
    const dt = formatDateActivite(a.created_at)
    const couleur = couleurCouple(coupleKey(a.matiere, a.niveau))
    const coupleLbl = [a.matiere, a.niveau].filter(Boolean).join(' — ') || 'Non classé'
    const estSel = selected === a.id
    // Récent → libellé relatif capitalisé ; ancien → date complète (sans « le »).
    const dateBase = dt.court ? (dt.recent ? dt.court.charAt(0).toUpperCase() + dt.court.slice(1) : dt.complet) : ''
    const dateLabel = dateBase && dt.heure ? `${dateBase} à ${dt.heure}` : dateBase
    return (
    <div
      key={a.id}
      onMouseEnter={() => setHovered(a.id)}
      onMouseLeave={() => setHovered(null)}
      onClick={() => setSelected(a.id)}
      title="Cliquer pour voir le détail à droite"
      style={{
        borderBottom: last ? 'none' : '1px solid #e5e7eb',
        borderLeft: estSel ? '3px solid var(--bordeaux)' : '3px solid transparent',
        background: estSel ? '#fdf2f5' : (hovered === a.id ? '#f3f4f6' : 'white'),
        transition: 'background 0.15s',
        cursor: 'pointer',
      }}
    >
      <div className="flex items-center gap-3 px-5 py-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span title={`Couleur du couple ${coupleLbl}`} style={{ width: 9, height: 9, borderRadius: '50%', background: couleur, flexShrink: 0, display: 'inline-block' }} />
            <span className="text-sm font-semibold text-gray-800 truncate">
              {a.objet || a.activite_label}
            </span>
            {a.partagee && (
              <span style={{ fontSize: 11, color: 'var(--bleu)', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 99, padding: '1px 8px', flexShrink: 0 }}>
                Partagé
              </span>
            )}
            {dateLabel && (
              <span
                title={dt.complet ? `Créée le ${dt.complet} à ${dt.heure}` : undefined}
                style={{
                  marginLeft: 'auto', display: 'inline-flex', alignItems: 'center', gap: 4,
                  fontSize: 11, fontWeight: 600, borderRadius: 99, padding: '2px 9px', flexShrink: 0,
                  background: dt.recent ? '#eff6ff' : '#f1f5f9',
                  color: dt.recent ? '#1d4ed8' : '#475569',
                }}
              >
                <IconCalendar />
                {dateLabel}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1 flex-wrap mt-0.5">
            <span className="text-xs text-gray-400">{a.activite_label}</span>
            <span className="text-xs text-gray-400">· {a.niveau}</span>
            {a.sous_type && <span className="text-xs text-gray-400">· {a.sous_type}</span>}
            {a.nb && <span className="text-xs text-gray-400">· {a.nb} questions</span>}
            <span className="text-xs text-gray-400">
              · {a.avec_correction ? 'Avec correction' : 'Sans correction'}
            </span>
          </div>
          {!a.objet && (
            <p className="text-xs text-gray-400 mt-0.5 truncate italic">{a.apercu}</p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0"
          style={{ opacity: (isMobile || hovered === a.id || estSel) ? 1 : 0, transition: 'opacity 0.15s' }}>
          {/* Partager — icône seule (même gabarit que la corbeille) ; la couleur porte l'état :
              bleu = partagé, gris = non partagé. « Reprendre » est dans le panneau de détail à droite. */}
          <button
            onClick={() => !a.partagee ? setAnonymeDialog(a.id) : togglePartage(a.id, false)}
            disabled={toggling === a.id}
            title={a.partagee ? 'Partagé — cliquer pour retirer de la bibliothèque partagée' : 'Partager cette activité avec vos collègues'}
            style={{
              display: 'flex', alignItems: 'center', padding: '5px 8px',
              background: 'none', border: '1px solid',
              borderColor: a.partagee ? 'var(--bleu)' : '#e5e7eb',
              borderRadius: 6,
              cursor: toggling === a.id ? 'wait' : 'pointer',
              color: a.partagee ? 'var(--bleu)' : '#9ca3af',
              transition: 'color 0.15s, border-color 0.15s',
            }}
          >
            <IconShare />
          </button>

          <button
            onClick={() => setDeleteDialog({ id: a.id, label: a.objet || a.activite_label })}
            title="Supprimer définitivement cette activité"
            style={{ display: 'flex', alignItems: 'center', padding: '5px 8px', background: 'none', border: '1px solid #fca5a5', borderRadius: 6, color: 'var(--bordeaux)', cursor: 'pointer' }}
          >
            <IconTrash />
          </button>
        </div>
      </div>
    </div>
    )
  }

  // ── Colonne GAUCHE : la liste (onglets, sections) — identique à avant, juste cliquable.
  const colonneListe = (
    <div className="flex flex-col gap-4">
      {/* Onglet « Niveau en cours » — liste filtrée sur le profil */}
      {vue === 'courant' && filtered.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          {filtered.map((a, i) => ActiviteRow(a, i === filtered.length - 1))}
        </div>
      )}

      {vue === 'courant' && filtered.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune activité pour {labelProfil}.</p>
          <p className="text-xs text-gray-400 mt-1">
            Vos activités d'un autre niveau ou matière sont dans l'onglet{' '}
            <button
              onClick={() => setVue('toutes')}
              style={{ color: 'var(--bordeaux)', textDecoration: 'underline', background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontSize: 'inherit' }}
            >
              Toutes mes activités
            </button>.
          </p>
        </div>
      )}

      {/* Onglet « Toutes mes activités » — sections par couple (courant épinglé en haut) */}
      {vue === 'toutes' && sections.map(sec => (
        <div key={sec.key} className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 px-1">
            <span style={{ width: 11, height: 11, borderRadius: '50%', background: couleurCouple(sec.key), flexShrink: 0, display: 'inline-block' }} />
            <span className="text-sm font-semibold text-gray-700">{sec.label}</span>
            <span style={{ fontSize: 11, color: '#6b7280', background: '#f1f5f9', borderRadius: 99, padding: '1px 8px', fontWeight: 600 }}>
              {sec.items.length}
            </span>
            {sec.key === currentKey && (
              <span style={{ fontSize: 11, color: 'var(--bordeaux)', background: '#fdf2f5', border: '1px solid #f4c4ce', borderRadius: 99, padding: '1px 8px', fontWeight: 600 }}>
                en cours
              </span>
            )}
          </div>
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            {sec.items.map((a, i) => ActiviteRow(a, i === sec.items.length - 1))}
          </div>
        </div>
      ))}
    </div>
  )

  // ── Colonne DROITE : le détail de l'activité sélectionnée, affiché EN PERMANENCE.
  const colonneDetail = (() => {
    if (!selectedActivite) {
      return (
        <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: '#94a3b8', fontSize: 13, padding: 24 }}>
          Cliquez une activité à gauche pour voir son détail.
        </div>
      )
    }
    const a = selectedActivite
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, boxShadow: '0 1px 2px rgba(0,0,0,0.04)', overflow: 'hidden' }}>
        {/* En-tête du détail */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, padding: '18px 22px 14px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 4 }}>
              {a.objet || a.activite_label}
            </div>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>
              {a.activite_label} · {a.niveau}
              {a.sous_type ? ` · ${a.sous_type}` : ''}
              {a.nb ? ` · ${a.nb} questions` : ''}
              {` · ${a.avec_correction ? 'Avec correction' : 'Sans correction'}`}
            </div>
          </div>
          <button onClick={() => tenterReprendre(a)}
            title="Reprendre cette activité dans le formulaire"
            className="btn-primary shrink-0">
            Reprendre
          </button>
        </div>

        {/* Corps scrollable */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {a.texte_source && a.texte_source.trim().length > 0 && (
            <div>
              <div style={LABEL_STYLE}>Texte source</div>
              <p style={SOURCE_STYLE}>{a.texte_source}</p>
            </div>
          )}
          <div>
            <div style={LABEL_STYLE}>Résultat généré</div>
            <pre style={PRE_STYLE}>{a.resultat}</pre>
          </div>
        </div>
      </div>
    )
  })()

  return (
    <div className="flex flex-col flex-1 min-h-0 w-full gap-3">

      {/* En-tête — le couple (matière/niveau) n'est PAS répété ici : il est déjà dans la barre du
          haut, et rappelé dans l'infobulle de l'onglet « Niveau en cours ». */}
      <div className="flex items-baseline gap-3" style={{ flexShrink: 0 }}>
        <h2 className="text-base font-semibold text-gray-800">Mes activités</h2>
        {!loading && headerCount > 0 && (
          <span style={{ fontSize: 12, color: 'var(--bordeaux)', background: '#fdf2f5', border: '1px solid #f4c4ce', borderRadius: 99, padding: '1px 10px', fontWeight: 600 }}>
            {headerCount} activité{headerCount > 1 ? 's' : ''} créée{headerCount > 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Onglets — visibles dès qu'il y a au moins une activité */}
      {!loading && activites.length > 0 && (
        <div style={{ display: 'flex', gap: 2, borderBottom: '1px solid #e5e7eb', flexShrink: 0 }}>
          {[['courant', 'Niveau en cours'], ['toutes', 'Toutes mes activités']].map(([id, label]) => (
            <button
              key={id}
              onClick={() => setVue(id)}
              title={id === 'courant'
                ? (labelProfil ? `Vos activités en ${labelProfil}` : 'Les activités de votre matière et niveau actuels')
                : 'Toutes vos activités, regroupées par matière et niveau'}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                fontSize: 13, padding: '6px 12px', marginBottom: -1,
                color: vue === id ? 'var(--bordeaux)' : '#6b7280',
                fontWeight: vue === id ? 600 : 400,
                borderBottom: vue === id ? '2px solid var(--bordeaux)' : '2px solid transparent',
              }}
            >
              {label}{id === 'toutes' ? ` (${activites.length})` : ''}
            </button>
          ))}
        </div>
      )}

      {/* Widget stats communauté — propre au couple courant */}
      {!loading && vue === 'courant' && <div style={{ flexShrink: 0 }}><StatsCommunaute matiere={sessionMatiere} niveau={sessionNiveau} /></div>}

      {loading && (
        <p className="text-sm text-gray-400 py-4">Chargement…</p>
      )}

      {!loading && activites.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune activité sauvegardée.</p>
          <p className="text-xs text-gray-400 mt-1">Générez une activité depuis l'Accueil pour la retrouver ici.</p>
        </div>
      )}

      {/* Deux colonnes redimensionnables, EN PERMANENCE : liste à gauche | détail à droite.
          Même composant que « Créer une activité » (poignée ajustable, largeur mémorisée, empilement
          sur écran étroit). Cf. components/SplitPane.jsx. */}
      {!loading && activites.length > 0 && (
        <div style={{ flex: 1, minHeight: 0 }}>
          <SplitPane storageKey="historique-split-v1" defautGauche={54} gauche={colonneListe} droite={colonneDetail} />
        </div>
      )}

      {/* Dialog anonymat */}
      {anonymeDialog && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={() => setAnonymeDialog(null)}
        >
          <div
            style={{ background: '#fff', borderRadius: '10px', padding: '24px 28px', maxWidth: '420px', width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ fontWeight: 700, fontSize: '15px', marginBottom: '8px', color: '#1e293b' }}>
              Comment souhaitez-vous apparaître ?
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '0 0 20px', lineHeight: 1.6 }}>
              Votre activité sera visible dans <strong>Mon réseau</strong> par vos collègues.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button
                onClick={() => { togglePartage(anonymeDialog, true, false); setAnonymeDialog(null) }}
                title="Votre nom complet sera affiché dans Mon réseau"
                style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '12px 16px', cursor: 'pointer', textAlign: 'left' }}
              >
                <div style={{ fontWeight: 600, fontSize: 13, color: '#1e293b' }}>Afficher mon nom</div>
                <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>{userName}</div>
              </button>
              <button
                onClick={() => { togglePartage(anonymeDialog, true, true); setAnonymeDialog(null) }}
                title="Votre nom ne sera pas affiché — vous apparaîtrez comme Anonyme"
                style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '12px 16px', cursor: 'pointer', textAlign: 'left' }}
              >
                <div style={{ fontWeight: 600, fontSize: 13, color: '#1e293b' }}>Rester anonyme</div>
                <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>Votre activité sera visible mais votre nom n'apparaîtra pas</div>
              </button>
            </div>
            <div style={{ marginTop: 16, textAlign: 'right' }}>
              <button
                onClick={() => setAnonymeDialog(null)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: 13, cursor: 'pointer' }}
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dialog suppression */}
      {deleteDialog && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={() => setDeleteDialog(null)}
        >
          <div
            style={{ background: '#fff', borderRadius: '10px', padding: '24px 28px', maxWidth: '420px', width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ fontWeight: 700, fontSize: '15px', marginBottom: '10px', color: '#1e293b' }}>
              Supprimer cette activité ?
            </div>
            <p style={{ fontSize: '13.5px', color: '#374151', margin: '0 0 6px', lineHeight: 1.6 }}>
              <strong>"{deleteDialog.label}"</strong>
            </p>
            <p style={{ fontSize: '13px', color: '#ef4444', margin: '0 0 20px', lineHeight: 1.5 }}>
              Cette action est irréversible — l'activité sera définitivement supprimée.
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setDeleteDialog(null)}
                style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
              >
                Annuler
              </button>
              <button
                onClick={() => supprimerActivite(deleteDialog.id)}
                disabled={deleting === deleteDialog.id}
                title="Confirmer la suppression définitive de cette activité"
                style={{ background: 'var(--bordeaux)', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: deleting ? 'wait' : 'pointer' }}
              >
                {deleting === deleteDialog.id ? 'Suppression…' : 'Supprimer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {profilDialog && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={() => setProfilDialog(null)}
        >
          <div
            style={{ background: '#fff', borderRadius: '10px', padding: '24px 28px', maxWidth: '440px', width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ fontWeight: 700, fontSize: '15px', marginBottom: '10px', color: '#1e293b' }}>
              Activité d'un autre profil
            </div>
            <p style={{ fontSize: '13.5px', color: '#374151', margin: '0 0 18px', lineHeight: 1.6 }}>
              Cette activité est en <strong>{profilDialog.matiere || '—'} / {profilDialog.niveau || '—'}</strong>, différente de votre profil courant (<strong>{sessionMatiere || '—'} / {sessionNiveau || '—'}</strong>). Pour la reprendre, passez d'abord sur le profil correspondant.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setProfilDialog(null)}
                title="Fermer"
                style={{ background: 'var(--bleu)', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}

      {!loading && vue === 'courant' && (
        <p className="text-xs text-gray-400 text-center mt-1" style={{ flexShrink: 0 }}>
          Vous enseignez plusieurs matières ?{' '}
          <button
            onClick={() => onNavigate?.('mon-profil')}
            style={{ color: 'var(--bordeaux)', textDecoration: 'underline', background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontSize: 'inherit' }}
          >
            Changez votre matière dans le profil
          </button>{' '}
          pour voir les activités correspondantes.
        </p>
      )}
    </div>
  )
}
