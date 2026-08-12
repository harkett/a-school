import { useEffect, useState } from 'react'
import { TYPES_CONTENUS } from '../utils/typesContenus.js'

const IconHome = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
)
const IconHelp = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/>
    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
    <line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>
)
const IconInfo = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
)
const IconStar = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
  </svg>
)
const IconRocket = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2-.2-2.8-.9-.9-2.1-.9-2.8-.2z"/>
    <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
    <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
    <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
  </svg>
)
const IconDemo = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 2v6L4.5 17a2 2 0 0 0 1.8 3h11.4a2 2 0 0 0 1.8-3L15 8V2"/>
    <line x1="8" y1="2" x2="16" y2="2"/>
    <line x1="6.5" y1="14" x2="17.5" y2="14"/>
  </svg>
)
const IconUser = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)
const IconMesContenus = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polygon points="12 2 2 7 12 12 22 7 12 2"/>
    <polyline points="2 17 12 22 22 17"/>
    <polyline points="2 12 12 17 22 12"/>
  </svg>
)
const IconMesAnalyses = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="7" height="7"/>
    <rect x="14" y="3" width="7" height="7"/>
    <rect x="14" y="14" width="7" height="7"/>
    <rect x="3" y="14" width="7" height="7"/>
  </svg>
)
const IconMesEvaluations = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
    <path d="M9 14l2 2 4-4"/>
  </svg>
)
const IconMenu = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="3" y1="6" x2="21" y2="6"/>
    <line x1="3" y1="12" x2="21" y2="12"/>
    <line x1="3" y1="18" x2="21" y2="18"/>
  </svg>
)
const IconFeedback = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
)
const IconStats = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="20" x2="18" y2="10"/>
    <line x1="12" y1="20" x2="12" y2="4"/>
    <line x1="6" y1="20" x2="6" y2="14"/>
  </svg>
)

// « Mes analyses » — ex-section « Analyse » de Mes outils, sortie au premier niveau le 30/07
// (décision utilisateur). L'ancien monde se DÉMOLIT (décision 30/07) : mes-activites /
// mes-sequences / creer-sequence / mon-reseau sont supprimés ; mes-outils / creer-activite /
// optimiseur (inaccessibles depuis le menu) tombent au palier suivant.
const MES_ANALYSES_PAGES = ['ambiguites', 'consigne', 'equite']
// Le monde NEUF « Mes contenus » : une sous-option PAR TYPE (décision utilisateur du 30/07 —
// fini le mélange des trois dans un seul écran). Les écrans seance/activite en font partie.
const MES_CONTENUS_PAGES = ['mes-contenus', 'contenus-sequences', 'contenus-seances', 'contenus-activites', 'seance', 'activite']

export default function Sidebar({ page, onNavigate, onNotation }) {
  const [collapsed, setCollapsed] = useState(() => window.innerWidth < 768)
  const [contenusOpen, setContenusOpen] = useState(true)   // les 3 sous-options visibles d'office
  const [evalOpen, setEvalOpen] = useState(false)
  // « Mes feedbacks » s'ouvre de lui-même quand on est sur l'écran des retours, et se plie
  // sinon : le prof y va rarement, le groupe n'a pas à occuper deux lignes en permanence.
  const [retoursOuvert, setRetoursOuvert] = useState(false)
  const retoursOpen = retoursOuvert || page === 'mes-feedbacks' || page === 'nouveau-retour'

  // Le groupe « Mes analyses » est ouvert dès qu'on est SUR une de ses pages — c'est un calcul,
  // pas une ouverture à déclencher après la navigation. Le prof peut le plier ou le déplier à la
  // main : son geste vaut pour la page où il l'a fait, et la navigation reprend la main ensuite.
  const [analysesChoisi, setAnalysesChoisi] = useState(null)   // { pour: page, valeur } | null
  const analysesOpen = analysesChoisi?.pour === page ? analysesChoisi.valeur : MES_ANALYSES_PAGES.includes(page)
  const setAnalysesOpen = (maj) => setAnalysesChoisi({
    pour: page,
    valeur: typeof maj === 'function' ? maj(analysesOpen) : maj,
  })

  const navItem = (id, label, Icon, title) => (
    <a
      href="#"
      title={title}
      onClick={e => { e.preventDefault(); onNavigate(id) }}
      className={`py-1.5 flex items-center gap-2 text-sm transition-colors ${
        collapsed ? 'justify-center' : ''
      } ${
        page === id
          ? (collapsed ? '' : 'nav-link-active')
          : 'text-gray-500 hover:text-gray-800'
      }`}
      style={page === id && collapsed ? { color: 'var(--bordeaux)', fontWeight: 600 } : {}}
    >
      <Icon />
      {!collapsed && <span>{label}</span>}
    </a>
  )

  const subNavItem = (pageId, label, title, opts = {}) => {
    // couleur = identité de TYPE (utils/typesContenus.js) : le point devant le libellé la
    // porte en permanence, et l'entrée active s'allume dans cette couleur au lieu du bordeaux.
    // `action` : une sous-entrée qui ne navigue pas mais DÉCLENCHE quelque chose — « Envoyer mon
    // retour » ouvre la fenêtre du formulaire, elle n'a pas de page à elle. Sans cette option, il
    // aurait fallu une seconde fabrique presque identique à celle-ci.
    const { disabled = false, couleur = null, action = null } = opts
    if (disabled) {
      // Outil pas encore prêt : visible, grisé, NON cliquable (span sans handler — clic réellement bloqué).
      return (
        <span
          key={pageId + label}
          title={title}
          style={{
            padding: '3px 4px 3px 6px',
            display: 'flex', alignItems: 'center', gap: '8px',
            fontSize: '12px', lineHeight: 1.4,
            color: '#b4bac3', cursor: 'not-allowed', borderRadius: '4px',
          }}
        >
          <span style={{ width: 4, height: 4, borderRadius: '50%', background: '#d1d5db', flexShrink: 0 }} />
          <span>{label}</span>
          <span style={{ marginLeft: 'auto', fontSize: 9, fontWeight: 600, color: '#94a3b8', background: '#f1f5f9', borderRadius: 99, padding: '1px 6px', flexShrink: 0 }}>bientôt</span>
        </span>
      )
    }
    const isActive = page === pageId
    return (
      <a
        key={pageId + label}
        href="#"
        title={title}
        onClick={e => { e.preventDefault(); action ? action() : onNavigate(pageId) }}
        style={{
          padding: '3px 4px 3px 6px',
          display: 'flex', alignItems: 'center', gap: '8px',
          fontSize: '12px', lineHeight: 1.4,
          color: isActive ? (couleur || 'var(--bordeaux)') : '#6b7280',
          fontWeight: isActive ? 600 : 400,
          textDecoration: 'none', borderRadius: '4px',
          transition: 'color 0.15s',
        }}
      >
        <span style={{ width: couleur ? 5 : 4, height: couleur ? 5 : 4, borderRadius: '50%', background: couleur || (isActive ? 'var(--bordeaux)' : '#d1d5db'), flexShrink: 0 }} />
        <span>{label}</span>
      </a>
    )
  }

  const analysesActive = MES_ANALYSES_PAGES.includes(page)

  return (
    <aside
      className="bg-white border-r border-gray-200 flex flex-col shrink-0 transition-all"
      style={{ width: collapsed ? 48 : 176, overflow: 'hidden' }}
    >
      <button
        onClick={() => setCollapsed(c => !c)}
        title="Réduire ou agrandir le menu"
        className="shrink-0 flex items-center gap-2 p-4 text-gray-500 hover:bg-gray-50 border-none bg-none cursor-pointer text-sm font-medium"
        style={{ background: 'none', border: 'none' }}
      >
        {collapsed
          ? <img src="/icon.png" alt="aSchool" style={{ width: 28, height: 28, borderRadius: 6 }} />
          : <IconMenu />
        }
        {!collapsed && (
          <>
            <span>Menu</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="ml-auto">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
          </>
        )}
      </button>

      <nav className={`sidebar-scroll flex flex-col gap-1 flex-1 min-h-0 ${collapsed ? '' : 'px-4'}`}>
        {navItem('accueil', 'Accueil', IconHome, 'Tableau de bord — vue d\'ensemble')}

        {/* Mes contenus — section à 3 sous-options, UNE PAR TYPE (décision 30/07 : fini le
            mélange des trois mondes dans un seul écran à onglets). */}
        {collapsed ? (
          navItem('contenus-activites', 'Mes contenus', IconMesContenus, 'Mes contenus — vos séquences, séances et activités')
        ) : (
          <div>
            <button
              onClick={() => setContenusOpen(o => !o)}
              title="Mes contenus — développer ou réduire le menu"
              className="py-1.5 flex items-center gap-2 text-sm transition-colors w-full"
              style={{
                background: 'none', border: 'none', cursor: 'pointer', padding: '6px 0',
                color: MES_CONTENUS_PAGES.includes(page) ? 'var(--bordeaux)' : '#6b7280',
                fontWeight: MES_CONTENUS_PAGES.includes(page) ? 600 : 400,
              }}
            >
              <IconMesContenus />
              <span>Mes contenus</span>
              <svg
                xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2.5"
                style={{ marginLeft: 'auto', flexShrink: 0, transform: contenusOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.15s' }}
              >
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>

            {contenusOpen && (
              <div style={{ marginLeft: 18, marginBottom: 4, display: 'flex', flexDirection: 'column' }}>
                {subNavItem('contenus-sequences', 'Séquences', 'Vos séquences — les conteneurs de séances', { couleur: TYPES_CONTENUS.sequence.accent })}
                {subNavItem('contenus-seances', 'Séances', 'Vos séances — créées et enregistrées automatiquement', { couleur: TYPES_CONTENUS.seance.accent })}
                {subNavItem('contenus-activites', 'Activités', 'Vos activités — créées et enregistrées automatiquement', { couleur: TYPES_CONTENUS.activite.accent })}
              </div>
            )}
          </div>
        )}

        {/* Mes analyses — ex-section « Analyse » de Mes outils, sortie au premier niveau
            le 30/07 (« Mes outils » supprimé du menu, routes et code en place). */}
        {collapsed ? (
          // Replié, ce bouton EST la section : il vise sa première analyse.
          navItem('ambiguites', 'Mes analyses', IconMesAnalyses, 'Mes analyses — analyser un texte pour détecter les ambiguïtés')
        ) : (
          <div>
            <button
              onClick={() => setAnalysesOpen(o => !o)}
              title="Mes analyses — développer ou réduire le menu"
              className="py-1.5 flex items-center gap-2 text-sm transition-colors w-full"
              style={{
                background: 'none', border: 'none', cursor: 'pointer', padding: '6px 0',
                color: analysesActive ? 'var(--bordeaux)' : '#6b7280',
                fontWeight: analysesActive ? 600 : 400,
              }}
            >
              <IconMesAnalyses />
              <span>Mes analyses</span>
              <svg
                xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2.5"
                style={{ marginLeft: 'auto', flexShrink: 0, transform: analysesOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.15s' }}
              >
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>

            {analysesOpen && (
              <div style={{ marginLeft: 18, marginBottom: 4, display: 'flex', flexDirection: 'column' }}>
                {subNavItem('ambiguites', 'Ambiguïté', "Analyser un texte pour détecter les ambiguïtés cognitives d'un énoncé ou exercice")}
                {/* Consignes EXISTE (composant Consigne + backend analyse/consigne.py) : le menu
                    la donnait pour « bientôt » et la grisait, alors que l'Accueil l'ouvrait
                    normalement. Deux écrans, deux vérités — c'est le menu qui se trompait. */}
                {subNavItem('consigne', 'Consignes', "Analyser la qualité didactique d'une consigne")}
                {subNavItem('equite', 'Équité', "Bientôt disponible — auditer l'équité d'une évaluation", { disabled: true })}
              </div>
            )}
          </div>
        )}

        {/* Mes évaluations — toit posé, contenu à venir (formation = Mes outils ; évaluation = ici) */}
        {collapsed ? (
          <span
            title="Mes évaluations — bientôt"
            className="py-1.5 flex items-center justify-center text-sm text-gray-400"
            style={{ cursor: 'default' }}
          >
            <IconMesEvaluations />
          </span>
        ) : (
          <div>
            <button
              onClick={() => setEvalOpen(o => !o)}
              title="Mes évaluations — développer ou réduire le menu"
              className="py-1.5 flex items-center gap-2 text-sm transition-colors w-full"
              style={{
                background: 'none', border: 'none', cursor: 'pointer', padding: '6px 0',
                color: '#6b7280', fontWeight: 400,
              }}
            >
              <IconMesEvaluations />
              <span>Mes évals</span>
              <svg
                xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2.5"
                style={{ marginLeft: 'auto', flexShrink: 0, transform: evalOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.15s' }}
              >
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
            {evalOpen && (
              <div style={{ marginLeft: 18, marginBottom: 4, display: 'flex', flexDirection: 'column' }}>
                {/* Les QUATRE possibilités d'évaluation, une par ligne — le fourre-tout
                    « Sujets · grilles · quiz » débordait sur trois lignes et donnait un seul
                    état à trois chantiers distincts (migration a5c9e3b7d1f4). */}
                {subNavItem('eval-sujets', 'Sujets', 'Bientôt disponible — créer et gérer vos sujets', { disabled: true })}
                {subNavItem('eval-grilles', 'Grilles', "Bientôt disponible — créer et gérer vos grilles d'évaluation", { disabled: true })}
                {subNavItem('eval-quiz', 'Quiz', 'Bientôt disponible — créer et gérer vos quiz', { disabled: true })}
                {subNavItem('eval-ccf', 'CCF', 'Bientôt disponible — le contrôle en cours de formation, sa situation et sa grille', { disabled: true })}
              </div>
            )}
          </div>
        )}

        {/* « Mon réseau » (partages de l'ancien monde) a été démoli le 30/07 — il renaîtra
            sur le partage du monde neuf, conçu sur les tables neuves. */}
        {navItem('mon-profil', 'Mon profil', IconUser, 'Modifier vos informations : prénom, nom, matière, niveau par défaut')}
        {/* MES FEEDBACKS — un groupe, deux gestes. Écrire un retour et relire ceux qu'on a
            envoyés sont deux choses différentes, et l'entrée unique n'en offrait qu'une : pour
            écrire, il fallait passer par le menu du haut. Les deux sont maintenant côte à côte,
            au même endroit. */}
        <div>
          <button
            onClick={() => setRetoursOuvert(o => !o)}
            title="Mes feedbacks — développer ou réduire le menu"
            className="py-1.5 flex items-center gap-2 text-sm transition-colors w-full"
            style={{
              background: 'none', border: 'none', cursor: 'pointer', padding: '6px 0',
              color: '#6b7280', fontWeight: 400,
            }}
          >
            <IconFeedback />
            {!collapsed && <span>Mes feedbacks</span>}
            {!collapsed && (
              <svg
                xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2.5"
                style={{ marginLeft: 'auto', flexShrink: 0, transform: retoursOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.15s' }}
              >
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            )}
          </button>
          {retoursOpen && !collapsed && (
            <div style={{ marginLeft: 18, marginBottom: 4, display: 'flex', flexDirection: 'column' }}>
              {subNavItem('nouveau-retour', 'Nouveau', 'Envoyer un nouveau retour (feedback)')}
              {subNavItem('mes-feedbacks', 'Historique', 'Consulter vos retours envoyés et leur statut')}
            </div>
          )}
        </div>
        {navItem('mes-stats', 'Mes stats', IconStats, 'Mes statistiques personnelles et la vitalité de la plateforme')}
      </nav>

      <nav className={`shrink-0 flex flex-col gap-1 pb-3 border-t border-gray-100 pt-3 ${collapsed ? '' : 'px-4'}`}>
        <LienDemonstration collapsed={collapsed} />
        {navItem('bientot-disponible', 'Bientôt disponible', IconRocket, 'Fonctionnalités à venir — proposez vos idées')}
        {navItem('aide', 'Centre d\'aide', IconHelp, 'Consulter la documentation et l\'aide')}
        <a
          href="#"
          title="Notez aSchool — donnez votre avis sur la plateforme en 30 secondes"
          onClick={e => { e.preventDefault(); onNotation() }}
          className={`py-1.5 flex items-center gap-2 text-sm transition-colors ${collapsed ? 'justify-center' : ''} text-gray-500 hover:text-gray-800`}
        >
          <IconStar />
          {!collapsed && <span>Avis</span>}
        </a>
        {navItem('apropos', 'À propos', IconInfo, 'Informations sur aSchool — version, contact')}
      </nav>

      {!collapsed && (
        <div className="shrink-0" style={{
          margin: '0 8px 10px',
          padding: '8px 10px',
          borderRadius: '8px',
          background: '#f0f7ff',
          border: '1px solid #bfdbfe',
          fontSize: '11px',
        }}>
          <div style={{ fontWeight: 600, color: '#1d4ed8', marginBottom: 4 }}>En développement</div>
          <div style={{ color: '#3b82f6', lineHeight: 1.6 }}>
            · Détecter les biais d'équité
          </div>
        </div>
      )}
    </aside>
  )
}

// L'entrée « Démonstration » — la seule du menu qui sorte de l'application.
//
// Elle n'est pas une navigation interne : le bac à sable est une AUTRE instance, sur une autre
// adresse, branchée sur une autre base. D'où le lien ordinaire vers /api/demo/aller, qui fabrique
// le jeton au moment du clic et redirige. Ni window.open ni fetch : une fenêtre ouverte après un
// appel réseau se fait bloquer par le navigateur, et un jeton fabriqué à l'affichage du menu
// serait déjà périmé au clic.
//
// Grisée tant que le prof n'a pas de démonstration : sa bulle d'aide porte alors la raison
// rendue par le serveur — pas de niveau au profil, démonstration en préparation, pas en ligne.
function LienDemonstration({ collapsed }) {
  const [etat, setEtat] = useState(null)

  useEffect(() => {
    let vivant = true
    fetch('/api/demo/pour-moi', { credentials: 'include' })
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (vivant) setEtat(d) })
      .catch(() => { /* le menu ne doit pas tomber parce que cette entrée-là n'a pas répondu */ })
    return () => { vivant = false }
  }, [])

  if (!etat || etat.ici) return null   // `ici` : on EST déjà dans la démonstration

  const classes = `py-1.5 flex items-center gap-2 text-sm transition-colors ${
    collapsed ? 'justify-center' : ''}`

  if (!etat.disponible) {
    return (
      <span className={`${classes} text-gray-300`} title={etat.raison}
            style={{ cursor: 'not-allowed' }}>
        <IconDemo />
        {!collapsed && <span>Démonstration</span>}
      </span>
    )
  }

  return (
    <a
      href="/api/demo/aller"
      target="_blank"
      rel="noreferrer"
      title={`Ouvrir la démonstration de ${etat.niveau} dans un nouvel onglet — un bac à sable où rien de ce que vous faites n’atteint vos vrais contenus`}
      className={`${classes} text-gray-500 hover:text-gray-800`}
    >
      <IconDemo />
      {!collapsed && <span>Démonstration</span>}
    </a>
  )
}
