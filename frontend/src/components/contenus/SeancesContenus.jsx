// Page « Mes contenus → Séances » — MÊME MOTIF que la page Activités voisine
// (contenus/ActivitesContenus.jsx), demandée par l'utilisateur le 30/07. MONDE NEUF :
//  - données : GET /api/mes-contenus (lignes « seance », tables neuves — jamais l'ancien monde) ;
//  - « Reprendre » : rouvre l'écran Séance du monde neuf (reprise complète, règle 0) ;
//  - Partager / Supprimer : pas encore d'équivalent côté monde neuf → boutons visibles
//    mais « bientôt » (réellement inactifs), comme le veut le motif maison.
import { useState, useEffect, useCallback } from 'react'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_STD } from '../../utils/api.js'
import { showError } from '../../errorDialog'
import ConfirmerSuppression from './ConfirmerSuppression.jsx'
import { coupleKey, grouperParCouple, parDateDesc, formatDateActivite, couleurCouple, correspondProfil } from '../../utils/activites.js'
import { corpsHtml, imprimerApercu } from '../../utils/apercuHtml.js'
import { aideSeances } from '../../utils/aideSeances.js'
import SplitPane from '../SplitPane.jsx'
import InfoGuide from '../InfoGuide.jsx'
import { TYPES_CONTENUS } from '../../utils/typesContenus.js'

// Identité du type Séance (vert émeraude) — fichier commun, appliquée en petites touches
// (mêmes endroits que le violet de la page Séquences : titre, pastille, liseré, onglets).
const TYPE_SEA = TYPES_CONTENUS.seance

// Icône du type : une « horloge » (un temps qui se déroule), devant le titre de page.
const IconHorloge = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={TYPE_SEA.accent} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
  </svg>
)

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

const IconGlobe = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
  </svg>
)

const IconPrint = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
  </svg>
)

// Libellés des modes — mêmes que l'écran Séance (SeanceEcran.jsx), pour la sous-ligne.
const MODE_LABELS = {
  standard: 'Séance standard',
  remediation: 'Remédiation',
  approfondissement: 'Approfondissement',
  autonomie: 'Autonomie guidée',
}

// Styles partagés du panneau de détail (colonne droite) — repris du motif Activités.
const LABEL_STYLE  = { fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }
const SOURCE_STYLE = { fontSize: 13, color: '#64748b', fontStyle: 'italic', lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, padding: '10px 14px' }
const PRE_STYLE    = { whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 13, color: '#374151', lineHeight: 1.7, margin: 0, fontFamily: 'inherit' }

export default function SeancesContenus({ onOuvrirSeance, onOuvrirActivite, sessionMatiere, sessionNiveau }) {
  const [seances, setSeances]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [hovered, setHovered]   = useState(null)
  const [selected, setSelected]         = useState(null)  // id de la séance affichée dans le panneau de détail (colonne droite)
  const [apercuHtml, setApercuHtml]     = useState(null)  // aperçu HTML mis en forme (modale) : chaîne = ouvert, null = fermé ; éphémère
  const [profilDialog, setProfilDialog] = useState(null)  // séance hors profil courant → modale "passez sur le profil"
  const [vue, setVue]               = useState('courant')  // 'courant' (couple du profil) | 'toutes' (groupé par couple)
  // Colonne de détail (droite) escamotée — bouton PERMANENT à droite des onglets
  // (demande utilisateur répétée du 30/07 : ce bouton ne se retire JAMAIS de cette page).
  const [detailCache, setDetailCache] = useState(false)
  // Lecture ratée (serveur muet, réseau coupé) : l'écran le DIT et propose « Réessayer ».
  // Une panne ne se déguise jamais en « Aucune séance » (motif de l'Accueil).
  const [chargementRate, setChargementRate] = useState(false)
  const [aSupprimer, setASupprimer] = useState(null)   // séance en attente de confirmation

  // RELECTURE de la base = seule source de vérité de la liste. MONDE NEUF uniquement :
  // les lignes « seance » de /api/mes-contenus (jamais l'ancien monde).
  const chargerSeances = useCallback(async () => {
    setChargementRate(false)
    try {
      const d = await lireReponse(await apiFetch('/api/mes-contenus', { credentials: 'include' }, TIMEOUT_STD))
      const lignes = (d.contenus || []).filter(c => c.type === 'seance')
      // Même forme de ligne que le motif Activités : l'aperçu (quand pas de titre) vient du contexte.
      setSeances(lignes.map(c => ({ ...c, apercu: (c.contexte || '').slice(0, 120) })))
    } catch (e) {
      setChargementRate(true)
      showError(messagePourEcran(e))
    }
  }, [])

  useEffect(() => {
    chargerSeances().finally(() => setLoading(false))
  }, [chargerSeances])

  // Échap ferme l'aperçu HTML.
  useEffect(() => {
    if (apercuHtml === null) return
    const onEsc = e => { if (e.key === 'Escape') setApercuHtml(null) }
    window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [apercuHtml])

  // « Reprendre » : on ne regénère QUE des séances du profil courant. Une séance d'un
  // autre couple (matière/niveau) → modale bloquante qui renvoie vers Mon profil (règle maison).
  function tenterReprendre(s) {
    if (correspondProfil(s, sessionMatiere, sessionNiveau)) onOuvrirSeance(s)
    else setProfilDialog(s)
  }

  const filtered = seances.filter(s => {
    if (sessionMatiere && s.matiere !== sessionMatiere) return false
    if (sessionNiveau  && s.niveau  !== sessionNiveau)  return false
    return true
  }).sort(parDateDesc)   // plus récent en haut

  const labelProfil = [sessionMatiere, sessionNiveau].filter(Boolean).join(', ')

  // Onglet « Toutes » : sections par couple (logique pure partagée utils/activites.js).
  const currentKey  = coupleKey(sessionMatiere, sessionNiveau)
  const sections    = grouperParCouple(seances, currentKey)
  const headerCount = vue === 'courant' ? filtered.length : seances.length

  // Liste réellement affichée à gauche (selon l'onglet), dans l'ordre d'affichage.
  const visibles = vue === 'courant' ? filtered : sections.flatMap(s => s.items)

  // Sélection par défaut + garde-fou : le panneau de détail montre TOUJOURS une séance visible.
  useEffect(() => {
    if (loading) return
    if (visibles.length === 0) { if (selected !== null) setSelected(null); return }
    if (!visibles.some(s => s.id === selected)) setSelected(visibles[0].id)
  }, [loading, vue, seances, sessionMatiere, sessionNiveau])   // eslint-disable-line react-hooks/exhaustive-deps

  const selectedSeance = seances.find(s => s.id === selected) || null

  // Activités RATTACHÉES à la séance sélectionnée (lecture seule ici : le rattachement se
  // gère dans l'écran Séance). null = pas encore chargées. Même filet silencieux que la
  // liste (chargerSeances) : un échec laisse le bloc vide, la sélection suivante relira.
  const [activitesLiees, setActivitesLiees] = useState(null)
  useEffect(() => {
    if (!selected) { setActivitesLiees(null); return }
    let annule = false
    setActivitesLiees(null)
    apiFetch(`/api/contenus/seances/${selected}/activites`, { credentials: 'include' }, TIMEOUT_STD)
      .then(lireReponse)
      .then(d => { if (!annule) setActivitesLiees(d.activites || []) })
      .catch(() => { if (!annule) setActivitesLiees([]) })
    return () => { annule = true }
  }, [selected])

  // Sous-ligne descriptive d'une séance (mode · niveau · durée) — équivalent de la ligne
  // « type · niveau · nb questions » du motif Activités.
  const sousLigne = s => [MODE_LABELS[s.mode] || s.mode, s.niveau, s.duree ? `${s.duree} min` : null].filter(Boolean)

  // Ligne-carte d'une séance, réutilisée par les deux onglets. Cliquable → sélectionne (détail à droite).
  const SeanceRow = (s, last) => {
    const dt = formatDateActivite(s.created_at)
    const couleur = couleurCouple(coupleKey(s.matiere, s.niveau))
    const coupleLbl = [s.matiere, s.niveau].filter(Boolean).join(' — ') || 'Non classé'
    const estSel = selected === s.id
    // Récent → libellé relatif capitalisé ; ancien → date complète (sans « le »).
    const dateBase = dt.court ? (dt.recent ? dt.court.charAt(0).toUpperCase() + dt.court.slice(1) : dt.complet) : ''
    const dateLabel = dateBase && dt.heure ? `${dateBase} à ${dt.heure}` : dateBase
    return (
    <div
      key={s.id}
      onMouseEnter={() => setHovered(s.id)}
      onMouseLeave={() => setHovered(null)}
      onClick={() => setSelected(s.id)}
      title={dt.complet ? `Créée le ${dt.complet} à ${dt.heure}` : undefined}
      style={{
        borderBottom: last ? 'none' : '1px solid #e5e7eb',
        borderLeft: estSel ? `3px solid ${TYPE_SEA.accent}` : '3px solid transparent',
        background: estSel ? TYPE_SEA.fond : (hovered === s.id ? '#f3f4f6' : 'white'),
        transition: 'background 0.15s',
        cursor: 'pointer',
      }}
    >
      <div className="flex items-center gap-3 px-5 py-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span title={`Couleur du couple ${coupleLbl}`} style={{ width: 9, height: 9, borderRadius: '50%', background: couleur, flexShrink: 0, display: 'inline-block' }} />
            <span className="text-sm font-semibold text-gray-800 truncate">
              {s.titre}
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
            {sousLigne(s).map((morceau, i) => (
              <span key={i} className="text-xs text-gray-400">{i === 0 ? morceau : `· ${morceau}`}</span>
            ))}
          </div>
          {!s.titre && (
            <p className="text-xs text-gray-400 mt-0.5 truncate italic">{s.apercu}</p>
          )}
        </div>

        {/* Actions toujours visibles. Partager / Supprimer : pas encore d'équivalent monde
            neuf → visibles mais « bientôt », réellement inactifs (motif maison). */}
        <div className="flex items-center gap-2 shrink-0" onClick={e => e.stopPropagation()}>
          <span
            title="Bientôt — le partage arrive dans Mes contenus"
            style={{ display: 'flex', alignItems: 'center', padding: '7px 10px', background: 'none', border: '1px solid #e2e8f0', borderRadius: 6, color: '#cbd5e1', cursor: 'not-allowed' }}
          >
            <IconShare />
          </span>
          <button
            type="button"
            onClick={() => setASupprimer(s)}
            title="Supprimer cette séance — ses activités, elles, seront conservées"
            style={{ display: 'flex', alignItems: 'center', padding: '7px 10px', background: 'none', border: '1px solid #e2e8f0', borderRadius: 6, color: '#94a3b8', cursor: 'pointer' }}
          >
            <IconTrash />
          </button>
        </div>
      </div>
    </div>
    )
  }

  // ── Colonne GAUCHE : la liste (onglets, sections) — même motif que la page Activités.
  const colonneListe = (
    <div className="flex flex-col gap-4">
      {/* Onglet « Niveau en cours » — liste filtrée sur le profil */}
      {vue === 'courant' && filtered.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          {filtered.map((s, i) => SeanceRow(s, i === filtered.length - 1))}
        </div>
      )}

      {vue === 'courant' && filtered.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune séance pour {labelProfil}.</p>
          <p className="text-xs text-gray-400 mt-1">
            Vos séances d'un autre niveau ou matière sont dans l'onglet{' '}
            <button
              onClick={() => setVue('toutes')}
              style={{ color: 'var(--bordeaux)', textDecoration: 'underline', background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontSize: 'inherit' }}
            >
              Toutes mes séances
            </button>.
          </p>
        </div>
      )}

      {/* Onglet « Toutes mes séances » — sections par couple (courant épinglé en haut) */}
      {vue === 'toutes' && sections.map(sec => (
        <div key={sec.key} className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 px-1">
            <span style={{ width: 11, height: 11, borderRadius: '50%', background: couleurCouple(sec.key), flexShrink: 0, display: 'inline-block' }} />
            <span className="text-sm font-semibold text-gray-700">{sec.label}</span>
            <span style={{ fontSize: 11, color: '#6b7280', background: '#f1f5f9', borderRadius: 99, padding: '1px 8px', fontWeight: 600 }}>
              {sec.items.length}
            </span>
            {sec.key === currentKey && (
              <span style={{ fontSize: 11, color: TYPE_SEA.accent, background: TYPE_SEA.fond, border: `1px solid ${TYPE_SEA.bord}`, borderRadius: 99, padding: '1px 8px', fontWeight: 600 }}>
                en cours
              </span>
            )}
          </div>
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            {sec.items.map((s, i) => SeanceRow(s, i === sec.items.length - 1))}
          </div>
        </div>
      ))}
    </div>
  )

  // ── Colonne DROITE : le détail de la séance sélectionnée, affiché EN PERMANENCE.
  const colonneDetail = (() => {
    if (!selectedSeance) {
      return (
        <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: '#94a3b8', fontSize: 13, padding: 24 }}>
          Cliquez une séance à gauche pour voir son détail.
        </div>
      )
    }
    const s = selectedSeance
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, boxShadow: '0 1px 2px rgba(0,0,0,0.04)', overflow: 'hidden' }}>
        {/* En-tête du détail */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, padding: '18px 22px 14px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 4 }}>
              {s.titre}
            </div>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>
              {sousLigne(s).join(' · ')}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <button onClick={() => setApercuHtml(corpsHtml(s.resultat))}
              title="Voir la séance mise en forme (aperçu, sans quitter aSchool)"
              className="btn-secondary">
              <IconGlobe /> HTML
            </button>
            <button onClick={() => tenterReprendre(s)}
              title="Reprendre cette séance dans l'écran Séance (modifier, régénérer)"
              className="btn-primary">
              Reprendre
            </button>
          </div>
        </div>

        {/* Corps scrollable */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {s.contexte && s.contexte.trim().length > 0 && (
            <div>
              <div style={LABEL_STYLE}>Contexte<InfoGuide {...aideSeances('contexte')} /></div>
              <p style={SOURCE_STYLE}>{s.contexte}</p>
            </div>
          )}
          {/* Activités rattachées à cette séance — lecture + ouvrir (le rattachement se
              gère dans l'écran Séance, via « Reprendre »). */}
          {activitesLiees !== null && activitesLiees.length > 0 && (
            <div>
              <div style={LABEL_STYLE}>Activités de cette séance<InfoGuide {...aideSeances('activites')} /></div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {activitesLiees.map(a => (
                  <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 8, border: '1px solid #e2e8f0', borderRadius: 6, padding: '7px 10px' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {a.titre}
                      </div>
                      <div style={{ fontSize: 11, color: '#94a3b8' }}>
                        {a.activite_label}{a.sous_type ? ` · ${a.sous_type}` : ''}{a.nb ? ` · ${a.nb} questions` : ''}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => onOuvrirActivite(a)}
                      title="Rouvrir cette activité dans son écran (modifier, régénérer)"
                    >
                      Ouvrir
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div>
            <div style={LABEL_STYLE}>Déroulé généré<InfoGuide {...aideSeances('resultat')} /></div>
            <pre style={PRE_STYLE}>{s.resultat}</pre>
          </div>
        </div>
      </div>
    )
  })()

  return (
    <div className="flex flex-col flex-1 min-h-0 w-full gap-3">

      {/* En-tête — même motif que la page Activités + bouton bleu « Nouvelle séance »
          en haut à droite : ouvre l'écran Séance du monde neuf. */}
      <div className="flex items-center gap-3" style={{ flexShrink: 0, justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div className="flex items-baseline gap-3">
          <h2 className="text-lg font-semibold text-gray-800" style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}><IconHorloge />Mes séances<InfoGuide {...aideSeances('ecran')} /></h2>
          {!loading && headerCount > 0 && (
            <span style={{ fontSize: 12, color: TYPE_SEA.accent, background: TYPE_SEA.fond, border: `1px solid ${TYPE_SEA.bord}`, borderRadius: 99, padding: '1px 10px', fontWeight: 600 }}>
              {headerCount} séance{headerCount > 1 ? 's' : ''} créée{headerCount > 1 ? 's' : ''}
            </span>
          )}
        </div>
        {/* « Nouvelle séance » + JUSTE DESSOUS le bouton qui cache/réaffiche la colonne de
            détail (droite) — bouton PERMANENT (demande répétée du 30/07), même motif que
            « Cacher le déroulé » de l'écran Séance. */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
          <button
            type="button"
            onClick={() => onOuvrirSeance(null)}
            title="Créer une nouvelle séance (enregistrement automatique dans Mes contenus)"
            style={{ background: 'var(--bleu)', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Nouvelle séance
          </button>
        </div>
      </div>

      {/* Onglets — visibles dès qu'il y a au moins une séance */}
      {!loading && seances.length > 0 && (
        <div style={{ display: 'flex', gap: 2, borderBottom: '1px solid #e5e7eb', flexShrink: 0 }}>
          {[['courant', 'Niveau en cours'], ['toutes', 'Toutes mes séances']].map(([id, label]) => (
            <button
              key={id}
              onClick={() => setVue(id)}
              title={id === 'courant'
                ? (labelProfil ? `Vos séances en ${labelProfil}` : 'Les séances de votre matière et niveau actuels')
                : 'Toutes vos séances, regroupées par matière et niveau'}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                fontSize: 13, padding: '6px 12px', marginBottom: -1,
                color: vue === id ? TYPE_SEA.accent : '#6b7280',
                fontWeight: vue === id ? 600 : 400,
                borderBottom: vue === id ? `2px solid ${TYPE_SEA.accent}` : '2px solid transparent',
              }}
            >
              {label}{id === 'toutes' ? ` (${seances.length})` : ''}
            </button>
          ))}
          <span style={{ display: 'inline-flex', alignItems: 'center', marginLeft: 2 }}>
            <InfoGuide {...aideSeances('onglets')} />
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

      {/* Lecture ratée : jamais « Aucune séance ». Le message est déjà parti en boîte de
          dialogue (règle maison) — l'écran ne garde que le bouton pour relancer. */}
      {!loading && chargementRate && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <button onClick={chargerSeances} className="btn-primary"
            title="Recharger vos séances">
            Réessayer
          </button>
        </div>
      )}

      {!loading && !chargementRate && seances.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune séance pour l'instant.</p>
          <p className="text-xs text-gray-400 mt-1">Créez une séance avec le bouton « Nouvelle séance » pour la retrouver ici.</p>
        </div>
      )}

      {/* Deux colonnes redimensionnables : liste à gauche | détail à droite. Détail caché
          (bouton à droite des onglets) : la liste prend toute la largeur. */}
      {!loading && seances.length > 0 && (
        <div style={{ flex: 1, minHeight: 0 }}>
          {detailCache
            ? <div className="split-pane"><div className="split-col split-col-flex">{colonneListe}</div></div>
            : <SplitPane storageKey="contenus-seances-split-v1" defautGauche={54} gauche={colonneListe} droite={colonneDetail} />}
        </div>
      )}

      {/* Suppression : la confirmation demande au serveur ce qui meurt (l'historique) et ce
          qui survit (les activités, qui repassent en « non rangées »), puis la liste est RELUE
          en base — jamais un retrait optimiste de l'état local. */}
      {aSupprimer && (
        <ConfirmerSuppression
          base={`/api/contenus/seances/${aSupprimer.id}`}
          type="seance"
          titre={aSupprimer.titre}
          onAnnuler={() => setASupprimer(null)}
          onSupprime={() => { setASupprimer(null); chargerSeances() }}
        />
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
              Séance d'un autre profil
            </div>
            <p style={{ fontSize: '13.5px', color: '#374151', margin: '0 0 18px', lineHeight: 1.6 }}>
              Cette séance est en <strong>{profilDialog.matiere || '—'} / {profilDialog.niveau || '—'}</strong>, différente de votre profil courant (<strong>{sessionMatiere || '—'} / {sessionNiveau || '—'}</strong>). Pour la reprendre, passez d'abord sur le profil correspondant.
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

      {/* Aperçu « HTML » — MODALE fermable (clic dehors, croix, Échap). */}
      {apercuHtml !== null && (
        <div
          onClick={() => setApercuHtml(null)}
          style={{ position: 'fixed', inset: 0, zIndex: 2000, background: 'rgba(15,23,42,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 10, maxWidth: 820, width: '100%', maxHeight: '88vh', display: 'flex', flexDirection: 'column', boxShadow: '0 20px 60px rgba(0,0,0,0.3)', overflow: 'hidden' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
              <span style={{ fontWeight: 700, color: '#0f172a', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                <IconGlobe /> Aperçu mis en forme
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                <button type="button" onClick={() => imprimerApercu(apercuHtml)} className="btn-secondary" title="Imprimer cette séance mise en forme">
                  <IconPrint /> Imprimer
                </button>
                <button type="button" onClick={() => setApercuHtml(null)} title="Fermer l'aperçu" style={{ width: 28, height: 28, borderRadius: '50%', border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
            </div>
            <div className="apercu-corps" style={{ overflowY: 'auto', padding: '22px 28px', color: '#1e293b', lineHeight: 1.7, fontSize: 15 }} dangerouslySetInnerHTML={{ __html: apercuHtml }} />
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
