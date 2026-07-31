// Page « Mes contenus → Séquences » — MÊME MOTIF que les pages voisines (SeancesContenus /
// ActivitesContenus). MONDE NEUF :
//  - données : GET /api/mes-contenus (lignes « sequence », tables neuves — jamais l'ancien monde) ;
//  - détail : les séances de la séquence via GET /contenus/sequences/{id}/seances, avec leur
//    état (« à générer » = déroulé vide / « générée ») ;
//  - « Reprendre » : rouvre l'écran Séquence (reprise complète — le travail des séances se
//    fait LÀ, une à une, comme les activités dans une séance) ;
//  - Partager / Supprimer : pas encore d'équivalent monde neuf → « bientôt », inactifs ;
//  - bouton « Cacher le détail » à droite des onglets : PERMANENT (règle maison).
import { useState, useEffect, useCallback } from 'react'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_STD } from '../../utils/api.js'
import { showError } from '../../errorDialog'
import { coupleKey, grouperParCouple, parDateDesc, formatDateActivite, couleurCouple, correspondProfil } from '../../utils/activites.js'
import { aideSequences } from '../../utils/aideSequences.js'
import { TYPES_CONTENUS } from '../../utils/typesContenus.js'

// Identité du type Séquence (violet) — lue du fichier commun, appliquée en petites touches.
const TYPE_SEQ = TYPES_CONTENUS.sequence

// Icône du type : un « chemin à étapes » (départ → tracé → objectif), devant le titre de page.
// PAS la pile : c'est déjà l'icône du menu « Mes contenus » (confusion signalée le 30/07).
const IconChemin = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={TYPE_SEQ.accent} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <circle cx="6" cy="19" r="3"/>
    <path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/>
    <circle cx="18" cy="5" r="3"/>
  </svg>
)
import SplitPane from '../SplitPane.jsx'
import InfoGuide from '../InfoGuide.jsx'

const IconTrash = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
    <path d="M10 11v6"/><path d="M14 11v6"/>
    <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
  </svg>
)

const IconShare = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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

// Styles partagés du panneau de détail (colonne droite) — repris du motif des pages voisines.
const LABEL_STYLE  = { fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }
const SOURCE_STYLE = { fontSize: 13, color: '#64748b', fontStyle: 'italic', lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, padding: '10px 14px' }

export default function SequencesContenus({ onOuvrirSequence, sessionMatiere, sessionNiveau }) {
  const [sequences, setSequences] = useState([])
  const [loading, setLoading]     = useState(true)
  const [hovered, setHovered]     = useState(null)
  const [selected, setSelected]         = useState(null)  // id de la séquence affichée dans le panneau de détail
  const [profilDialog, setProfilDialog] = useState(null)  // séquence hors profil courant → modale "passez sur le profil"
  const [vue, setVue]               = useState('courant')  // 'courant' (couple du profil) | 'toutes' (groupé par couple)
  // Colonne de détail (droite) escamotée — bouton PERMANENT à droite des onglets
  // (règle maison du 30/07 : toute page liste naît avec, aucune correction ne le retire).
  const [detailCache, setDetailCache] = useState(false)
  // Lecture ratée (serveur muet, réseau coupé) : l'écran le DIT et propose « Réessayer ».
  // Une panne ne se déguise jamais en « Aucune séquence » (motif de l'Accueil).
  const [chargementRate, setChargementRate] = useState(false)

  // RELECTURE de la base = seule source de vérité de la liste. MONDE NEUF uniquement.
  const chargerSequences = useCallback(async () => {
    setChargementRate(false)
    try {
      const d = await lireReponse(await apiFetch('/api/mes-contenus', { credentials: 'include' }, TIMEOUT_STD))
      setSequences((d.contenus || []).filter(c => c.type === 'sequence'))
    } catch (e) {
      setChargementRate(true)
      showError(messagePourEcran(e))
    }
  }, [])

  useEffect(() => {
    chargerSequences().finally(() => setLoading(false))
  }, [chargerSequences])

  // « Reprendre » : on ne travaille QUE des séquences du profil courant (règle maison).
  function tenterReprendre(q) {
    if (correspondProfil(q, sessionMatiere, sessionNiveau)) onOuvrirSequence(q)
    else setProfilDialog(q)
  }

  const filtered = sequences.filter(q => {
    if (sessionMatiere && q.matiere !== sessionMatiere) return false
    if (sessionNiveau  && q.niveau  !== sessionNiveau)  return false
    return true
  }).sort(parDateDesc)   // plus récent en haut

  const labelProfil = [sessionMatiere, sessionNiveau].filter(Boolean).join(', ')

  const currentKey  = coupleKey(sessionMatiere, sessionNiveau)
  const sections    = grouperParCouple(sequences, currentKey)
  const headerCount = vue === 'courant' ? filtered.length : sequences.length
  const visibles = vue === 'courant' ? filtered : sections.flatMap(s => s.items)

  // Sélection par défaut + garde-fou : le détail montre TOUJOURS une séquence visible.
  useEffect(() => {
    if (loading) return
    if (visibles.length === 0) { if (selected !== null) setSelected(null); return }
    if (!visibles.some(q => q.id === selected)) setSelected(visibles[0].id)
  }, [loading, vue, sequences, sessionMatiere, sessionNiveau])   // eslint-disable-line react-hooks/exhaustive-deps

  const selectedSequence = sequences.find(q => q.id === selected) || null

  // Séances de la séquence sélectionnée (lecture seule ici : le TRAVAIL des séances se fait
  // dans l'écran Séquence, via « Reprendre »). null = pas encore chargées.
  const [seancesLiees, setSeancesLiees] = useState(null)
  useEffect(() => {
    if (!selected) { setSeancesLiees(null); return }
    let annule = false
    setSeancesLiees(null)
    apiFetch(`/api/contenus/sequences/${selected}/seances`, { credentials: 'include' }, TIMEOUT_STD)
      .then(lireReponse)
      .then(d => { if (!annule) setSeancesLiees(d.seances || []) })
      .catch(() => { if (!annule) setSeancesLiees([]) })
    return () => { annule = true }
  }, [selected])

  // Sous-ligne descriptive d'une séquence (nb de séances · niveau).
  const sousLigne = q => [
    `${q.nb_seances ?? 0} séance${(q.nb_seances ?? 0) > 1 ? 's' : ''}`,
    q.niveau,
  ].filter(Boolean)

  // Ligne-carte d'une séquence, réutilisée par les deux onglets. Cliquable → détail à droite.
  const SequenceRow = (q, last) => {
    const dt = formatDateActivite(q.created_at)
    const couleur = couleurCouple(coupleKey(q.matiere, q.niveau))
    const coupleLbl = [q.matiere, q.niveau].filter(Boolean).join(' — ') || 'Non classé'
    const estSel = selected === q.id
    const dateBase = dt.court ? (dt.recent ? dt.court.charAt(0).toUpperCase() + dt.court.slice(1) : dt.complet) : ''
    const dateLabel = dateBase && dt.heure ? `${dateBase} à ${dt.heure}` : dateBase
    return (
    <div
      key={q.id}
      onMouseEnter={() => setHovered(q.id)}
      onMouseLeave={() => setHovered(null)}
      onClick={() => setSelected(q.id)}
      title={dt.complet ? `Créée le ${dt.complet} à ${dt.heure}` : undefined}
      style={{
        borderBottom: last ? 'none' : '1px solid #e5e7eb',
        borderLeft: estSel ? `3px solid ${TYPE_SEQ.accent}` : '3px solid transparent',
        background: estSel ? TYPE_SEQ.fond : (hovered === q.id ? '#f3f4f6' : 'white'),
        transition: 'background 0.15s',
        cursor: 'pointer',
      }}
    >
      <div className="flex items-center gap-3 px-5 py-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span title={`Couleur du couple ${coupleLbl}`} style={{ width: 9, height: 9, borderRadius: '50%', background: couleur, flexShrink: 0, display: 'inline-block' }} />
            {/* flex-1 min-w-0 : le titre se COMPRIME (…) au lieu de sauter à la ligne sous la
                puce quand la colonne est étroite (bug signalé le 30/07). */}
            <span className="text-sm font-semibold text-gray-800 truncate flex-1 min-w-0">
              {q.titre}
            </span>
            {dateLabel && (
              <span style={{ marginLeft: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2, flexShrink: 0 }}>
                <span
                  title={dt.complet ? `Créée le ${dt.complet} à ${dt.heure}` : undefined}
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
            )}
          </div>
          <div className="flex items-center gap-1 flex-wrap mt-0.5">
            {sousLigne(q).map((morceau, i) => (
              <span key={i} className="text-xs text-gray-400">{i === 0 ? morceau : `· ${morceau}`}</span>
            ))}
          </div>
        </div>

        {/* Partager / Supprimer : pas encore d'équivalent monde neuf → « bientôt », inactifs. */}
        <div className="flex items-center gap-2 shrink-0" onClick={e => e.stopPropagation()}>
          <span
            title="Bientôt — le partage arrive dans Mes contenus"
            style={{ display: 'flex', alignItems: 'center', padding: '7px 10px', background: 'none', border: '1px solid #e2e8f0', borderRadius: 6, color: '#cbd5e1', cursor: 'not-allowed' }}
          >
            <IconShare />
          </span>
          <span
            title="Bientôt — la suppression arrive dans Mes contenus"
            style={{ display: 'flex', alignItems: 'center', padding: '7px 10px', background: 'none', border: '1px solid #e2e8f0', borderRadius: 6, color: '#cbd5e1', cursor: 'not-allowed' }}
          >
            <IconTrash />
          </span>
        </div>
      </div>
    </div>
    )
  }

  // ── Colonne GAUCHE : la liste (onglets, sections) — même motif que les pages voisines.
  const colonneListe = (
    <div className="flex flex-col gap-4">
      {vue === 'courant' && filtered.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          {filtered.map((q, i) => SequenceRow(q, i === filtered.length - 1))}
        </div>
      )}

      {vue === 'courant' && filtered.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune séquence pour {labelProfil}.</p>
          <p className="text-xs text-gray-400 mt-1">
            Vos séquences d'un autre niveau ou matière sont dans l'onglet{' '}
            <button
              onClick={() => setVue('toutes')}
              style={{ color: 'var(--bordeaux)', textDecoration: 'underline', background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontSize: 'inherit' }}
            >
              Toutes mes séquences
            </button>.
          </p>
        </div>
      )}

      {vue === 'toutes' && sections.map(sec => (
        <div key={sec.key} className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 px-1">
            <span style={{ width: 11, height: 11, borderRadius: '50%', background: couleurCouple(sec.key), flexShrink: 0, display: 'inline-block' }} />
            <span className="text-sm font-semibold text-gray-700">{sec.label}</span>
            <span style={{ fontSize: 11, color: '#6b7280', background: '#f1f5f9', borderRadius: 99, padding: '1px 8px', fontWeight: 600 }}>
              {sec.items.length}
            </span>
            {sec.key === currentKey && (
              <span style={{ fontSize: 11, color: TYPE_SEQ.accent, background: TYPE_SEQ.fond, border: `1px solid ${TYPE_SEQ.bord}`, borderRadius: 99, padding: '1px 8px', fontWeight: 600 }}>
                en cours
              </span>
            )}
          </div>
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            {sec.items.map((q, i) => SequenceRow(q, i === sec.items.length - 1))}
          </div>
        </div>
      ))}
    </div>
  )

  // ── Colonne DROITE : le détail de la séquence sélectionnée, affiché EN PERMANENCE.
  const colonneDetail = (() => {
    if (!selectedSequence) {
      return (
        <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: '#94a3b8', fontSize: 13, padding: 24 }}>
          Cliquez une séquence à gauche pour voir son détail.
        </div>
      )
    }
    const q = selectedSequence
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, boxShadow: '0 1px 2px rgba(0,0,0,0.04)', overflow: 'hidden' }}>
        {/* En-tête du détail */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, padding: '18px 22px 14px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 4 }}>
              {q.titre}
            </div>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>
              {sousLigne(q).join(' · ')}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <button onClick={() => tenterReprendre(q)}
              title="Reprendre cette séquence dans l'écran Séquence — c'est là que ses séances se travaillent, une à une"
              className="btn-primary">
              Reprendre
            </button>
          </div>
        </div>

        {/* Corps scrollable */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {q.contexte && q.contexte.trim().length > 0 && (
            <div>
              <div style={LABEL_STYLE}>Contexte<InfoGuide {...aideSequences('contexte')} /></div>
              <p style={SOURCE_STYLE}>{q.contexte}</p>
            </div>
          )}
          {q.ampleur && q.ampleur.trim().length > 0 && (
            <div>
              <div style={LABEL_STYLE}>Ampleur souhaitée</div>
              <p style={SOURCE_STYLE}>{q.ampleur}</p>
            </div>
          )}
          {Array.isArray(q.competences) && q.competences.length > 0 && (
            <div>
              <div style={LABEL_STYLE}>Compétences / attendus</div>
              <p style={SOURCE_STYLE}>{q.competences.join('\n')}</p>
            </div>
          )}
          <div>
            <div style={LABEL_STYLE}>Les séances de cette séquence<InfoGuide {...aideSequences('seances')} /></div>
            {seancesLiees === null && (
              <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>Chargement des séances…</p>
            )}
            {seancesLiees !== null && seancesLiees.length === 0 && (
              <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>Aucune séance rattachée à cette séquence.</p>
            )}
            {seancesLiees !== null && seancesLiees.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {seancesLiees.map((s, i) => (
                  <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 10, border: '1px solid #e2e8f0', borderRadius: 6, padding: '7px 10px' }}>
                    <span style={{ width: 22, height: 22, borderRadius: '50%', flexShrink: 0, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, fontVariantNumeric: 'tabular-nums', background: '#f1f5f9', border: '1px solid #e2e8f0', color: '#475569' }}>
                      {s.position ?? i + 1}
                    </span>
                    <span style={{ flex: 1, minWidth: 0, fontSize: 13, fontWeight: 600, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={s.titre}>
                      {s.titre}
                    </span>
                    {s.resultat && s.resultat.trim() ? (
                      <span title="Le déroulé de cette séance est écrit"
                        style={{ fontSize: 11, fontWeight: 600, color: '#166534', background: '#dcfce7', border: '1px solid #86efac', borderRadius: 99, padding: '2px 9px', flexShrink: 0 }}>
                        générée
                      </span>
                    ) : (
                      <span title="Le déroulé de cette séance n'est pas encore généré — reprenez la séquence pour la travailler"
                        style={{ fontSize: 11, fontWeight: 600, color: TYPE_SEQ.accent, background: TYPE_SEQ.fond, border: `1px solid ${TYPE_SEQ.bord}`, borderRadius: 99, padding: '2px 9px', flexShrink: 0 }}>
                        à générer
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  })()

  return (
    <div className="flex flex-col flex-1 min-h-0 w-full gap-3">

      {/* En-tête — même motif que les pages voisines : titre + compteur à gauche ;
          « Nouvelle séquence » à droite (« Cacher le détail » vit sur la ligne des onglets). */}
      <div className="flex items-center gap-3" style={{ flexShrink: 0, justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div className="flex items-baseline gap-3">
          <h2 className="text-lg font-semibold text-gray-800" style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}><IconChemin />Mes séquences<InfoGuide {...aideSequences('ecran')} /></h2>
          {!loading && headerCount > 0 && (
            <span style={{ fontSize: 12, color: TYPE_SEQ.accent, background: TYPE_SEQ.fond, border: `1px solid ${TYPE_SEQ.bord}`, borderRadius: 99, padding: '1px 10px', fontWeight: 600 }}>
              {headerCount} séquence{headerCount > 1 ? 's' : ''} créée{headerCount > 1 ? 's' : ''}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
          <button
            type="button"
            onClick={() => onOuvrirSequence(null)}
            title="Créer une nouvelle séquence (le plan et ses séances s'enregistrent automatiquement dans Mes contenus)"
            style={{ background: 'var(--bleu)', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Nouvelle séquence
          </button>
        </div>
      </div>

      {/* Onglets — visibles dès qu'il y a au moins une séquence */}
      {!loading && sequences.length > 0 && (
        <div style={{ display: 'flex', gap: 2, borderBottom: '1px solid #e5e7eb', flexShrink: 0 }}>
          {[['courant', 'Niveau en cours'], ['toutes', 'Toutes mes séquences']].map(([id, label]) => (
            <button
              key={id}
              onClick={() => setVue(id)}
              title={id === 'courant'
                ? (labelProfil ? `Vos séquences en ${labelProfil}` : 'Les séquences de votre matière et niveau actuels')
                : 'Toutes vos séquences, regroupées par matière et niveau'}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                fontSize: 13, padding: '6px 12px', marginBottom: -1,
                color: vue === id ? TYPE_SEQ.accent : '#6b7280',
                fontWeight: vue === id ? 600 : 400,
                borderBottom: vue === id ? `2px solid ${TYPE_SEQ.accent}` : '2px solid transparent',
              }}
            >
              {label}{id === 'toutes' ? ` (${sequences.length})` : ''}
            </button>
          ))}
          <span style={{ display: 'inline-flex', alignItems: 'center', marginLeft: 2 }}>
            <InfoGuide {...aideSequences('onglets')} />
          </span>
          {/* « Cacher le détail » : sur la ligne des onglets, complètement à droite (sa place
              depuis le 30/07 — même position sur les trois pages listes). */}
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setDetailCache(c => !c)}
            title={detailCache
              ? 'Réafficher la colonne de détail à droite'
              : 'Cacher la colonne de détail — la liste prend toute la largeur'}
            style={{ marginLeft: 'auto', alignSelf: 'center', flexShrink: 0 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {detailCache
                ? <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
                : <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>}
            </svg>
            {detailCache ? 'Afficher le détail' : 'Cacher le détail'}
          </button>
        </div>
      )}

      {loading && (
        <p className="text-sm text-gray-400 py-4">Chargement…</p>
      )}

      {/* Lecture ratée : jamais « Aucune séquence ». Le message est déjà parti en boîte de
          dialogue (règle maison) — l'écran ne garde que le bouton pour relancer. */}
      {!loading && chargementRate && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <button onClick={chargerSequences} className="btn-primary"
            title="Recharger vos séquences">
            Réessayer
          </button>
        </div>
      )}

      {!loading && !chargementRate && sequences.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune séquence pour l'instant.</p>
          <p className="text-xs text-gray-400 mt-1">Créez une séquence avec le bouton « Nouvelle séquence » pour la retrouver ici.</p>
        </div>
      )}

      {/* Deux colonnes redimensionnables : liste à gauche | détail à droite. Détail caché
          (bouton à droite des onglets) : la liste prend toute la largeur. */}
      {!loading && sequences.length > 0 && (
        <div style={{ flex: 1, minHeight: 0 }}>
          {detailCache
            ? <div className="split-pane"><div className="split-col split-col-flex">{colonneListe}</div></div>
            : <SplitPane storageKey="contenus-sequences-split-v1" defautGauche={54} gauche={colonneListe} droite={colonneDetail} />}
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
              Séquence d'un autre profil
            </div>
            <p style={{ fontSize: '13.5px', color: '#374151', margin: '0 0 18px', lineHeight: 1.6 }}>
              Cette séquence est en <strong>{profilDialog.matiere || '—'} / {profilDialog.niveau || '—'}</strong>, différente de votre profil courant (<strong>{sessionMatiere || '—'} / {sessionNiveau || '—'}</strong>). Pour la reprendre, passez d'abord sur le profil correspondant.
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

    </div>
  )
}
