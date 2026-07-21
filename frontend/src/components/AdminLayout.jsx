import { useEffect, useState } from 'react'
import { useNavigate, useLocation, Link, Outlet } from 'react-router-dom'
import { fetchWithTimeout, TIMEOUT_AUTH } from '../utils/api.js'
import { registerErrorHandler } from '../errorDialog'

const SEP = { separator: true }

// Menu rangé du général au détaillé : 6 catégories (groupes) + 2 entrées simples.
// Règle (CLAUDE.md) : toute nouvelle page se range sous une famille existante,
// jamais une entrée à plat de plus. « Pédagogie » = le métier construit ; « Contenu »
// = les données brutes de référence (référentiels sources + tables).
const NAV_ITEMS = [
  // — Référentiel (écran unique CRUD) —
  {
    to:    '/admin/referentiels',
    label: 'Référentiel',
    aide:  'L’écran unique du référentiel : choisir un couple, puis créer / consulter / modifier / supprimer — tout en base (get pour afficher, put pour enregistrer).',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <path d="M14 2v6h6"/>
        <path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>
      </svg>
    ),
  },
  // — Pédagogie (le métier construit sur le contenu) —
  {
    group:  true,
    label:  'Pédagogie',
    aide:   'Le métier construit sur le contenu : programme officiel, activités et fiches matières.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
      </svg>
    ),
    items: [
      { to: '/admin/programmes',   label: 'Programmes',     aide: 'Programme officiel : cocher les paires matière × niveau, ajouter des niveaux (Supérieur, Crèche). Désactivation, jamais de suppression.' },
    ],
  },
  // — Contenu (les données brutes de référence) —
  {
    group:  true,
    label:  'Contenu',
    aide:   'Les données brutes de référence : référentiels sources et tables (cycles, matières, familles, famille-couples).',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3"/>
        <path d="M3 5v14a9 3 0 0 0 18 0V5"/>
        <path d="M3 12a9 3 0 0 0 18 0"/>
      </svg>
    ),
    items: [
      { to: '/admin/familles', label: 'Familles', aide: 'Contenu de la table familles (id, nom, description, rejet), lu directement en base. Fenêtre de contrôle en lecture seule.' },
      { to: '/admin/fc-autorisees', label: 'Famille-Couples', aide: 'Contenu de la table famille_couples : les couples (famille + niveau, cycle dérivé du niveau), lu directement en base. Fenêtre de contrôle en lecture seule.' },
      { to: '/admin/cycles',   label: 'Cycles',   aide: 'Contenu de la table cycles (id, nom, ordre), lu directement en base. Fenêtre de contrôle en lecture seule.' },
      { to: '/admin/matieres', label: 'Matières', aide: 'Contenu de la table matieres (id, nom, ordre, actif), lu directement en base. Fenêtre de contrôle en lecture seule.' },
      { to: '/admin/types-activite', label: 'Type d\'activité', aide: 'Contenu de la table types_activite, lu directement en base. Fenêtre de contrôle en lecture seule.' },
    ],
  },
  // — Profs & communication —
  {
    group:  true,
    label:  'Profs & communication',
    aide:   'Les enseignants et les échanges avec eux : profils, mail groupé, retours.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
    items: [
      { to: '/admin/profils',       label: 'Profs',       aide: 'Profils des enseignants — consulter et modifier matière, niveau, prénom et nom.' },
      { to: '/admin/communication', label: 'Mail groupé', aide: 'Envoyer un message à plusieurs profs en une fois — sélection par matière, filtre, cases à cocher.' },
      { to: '/admin/feedbacks',     label: 'Feedbacks',   aide: 'Retours et suggestions des utilisateurs — note moyenne, répartition, statuts.', badgeKey: 'feedbacks_nouveaux' },
    ],
  },
  // — Supervision & sécurité —
  {
    group:  true,
    label:  'Supervision & sécurité',
    aide:   'L\'état du système et la sécurité : sessions, serveur, alertes, journaux d\'accès, audit.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    ),
    items: [
      { to: '/admin/sessions',   label: 'Sessions',   aide: 'Profs connectés en ce moment — navigateur, dernière activité, durée. Déconnexion forcée possible.' },
      { to: '/admin/serveur',    label: 'Serveur',    aide: 'Métriques VPS (CPU, RAM, disque), statistiques d\'activité et graphe des connexions.' },
      { to: '/admin/alertes',    label: 'Alertes',    aide: 'Alertes automatiques : CPU critique, disque plein, tentatives d\'intrusion. Vérification toutes les 5 min.', badgeKey: 'alertes_nonlues' },
      { to: '/admin/logs',       label: 'Connexions', aide: 'Journal des connexions utilisateurs — qui s\'est connecté, quand et depuis quelle adresse IP.' },
      { to: '/admin/tentatives', label: 'Tentatives', aide: 'Tentatives de connexion échouées — IP, identifiant tenté, statut bloqué ou non.' },
      { to: '/admin/audit',      label: 'Audit',      aide: 'Historique des actions sensibles effectuées par l\'administrateur (déconnexions forcées, suppressions…).' },
    ],
  },
  // — Analytique —
  {
    group:  true,
    label:  'Analytique',
    prefix: '/admin/analytique',
    aide:   'Statistiques et analyses de la plateforme.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"/>
        <line x1="12" y1="20" x2="12" y2="4"/>
        <line x1="6"  y1="20" x2="6"  y2="14"/>
        <line x1="2"  y1="20" x2="22" y2="20"/>
      </svg>
    ),
    items: [
      { to: '/admin/analytique/general',    label: 'Vue générale',  aide: 'KPIs globaux : activités, outils, communauté.' },
      { to: '/admin/analytique/activites',  label: 'Activités',     aide: 'Détail par prof, matière, niveau et type.' },
      { to: '/admin/analytique/outils',     label: 'Outils',        aide: 'Utilisation de Séquence et Optimiseur.' },
      { to: '/admin/analytique/communaute', label: 'Communauté',    aide: 'Activités partagées — contributeurs et top types.' },
    ],
  },
  // — Base de données — entrée de premier niveau (au même niveau que « Système »), au-dessus.
  {
    to:    '/admin/base',
    label: 'Base de données',
    aide:  'Sur quelle base l\'application est réellement connectée (réelle « aschool » vs miroir de test) — garde-fou.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3"/>
        <path d="M3 5v14a9 3 0 0 0 18 0V5"/>
        <path d="M3 12a9 3 0 0 0 18 0"/>
      </svg>
    ),
  },
  // — Système —
  {
    group:  true,
    label:  'Système',
    aide:   'Réglages de la plateforme et maintenance.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </svg>
    ),
    items: [
      { to: '/admin/parametres/generation', label: 'Génération LLM', aide: 'Modèle d\'IA et réglages du moteur de génération des textes.' },
      { to: '/admin/parametres/email',      label: 'Email',          aide: 'Email de bienvenue envoyé automatiquement à chaque nouvel inscrit.' },
      { to: '/admin/parametres/general',    label: 'Paramètres',     aide: 'Table des paramètres du projet (clé / valeur / description), en consultation.' },
      { to: '/admin/maintenance',           label: 'Maintenance',    aide: 'Nettoyage de la base de données — tokens expirés, sessions fermées, comptes fantômes, logs anciens.' },
    ],
  },
  // — Labo (écrans brouillons, temporaires) — derrière Système.
  {
    to:    '/admin/labo',
    label: 'Labo',
    aide:  'Écrans brouillons : on met une fonctionnalité au point isolément, avec les vrais get/put, avant de l\'intégrer dans la vraie page.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 3h6"/>
        <path d="M10 3v6.5L4.5 18a2 2 0 0 0 1.7 3h11.6a2 2 0 0 0 1.7-3L14 9.5V3"/>
        <path d="M7 15h10"/>
      </svg>
    ),
  },
  SEP,
  // — Entrées simples (hors catégorie) —
  {
    to:    '/admin/compte',
    label: 'Mon compte',
    aide:  'Changer le mot de passe du compte administrateur.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
    ),
  },
  {
    to:    '/admin/aide',
    label: 'Aide',
    aide:  'Documentation complète du backoffice — fonctionnalités, astuces, comportements.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    ),
  },
]

export default function AdminLayout() {
  const [checked, setChecked] = useState(false)
  const [notifs, setNotifs]   = useState({ feedbacks_nouveaux: 0, alertes_nonlues: 0 })
  const [adminAlert, setAdminAlert] = useState(null)  // modale bloquante côté admin
  const navigate  = useNavigate()
  const location  = useLocation()

  // Accordéon : la catégorie dépliée. Initialisée sur celle qui contient la page courante.
  const _activeGroup = NAV_ITEMS.find(
    it => it.group && (it.prefix ? location.pathname.startsWith(it.prefix) : it.items.some(s => location.pathname === s.to))
  )
  const [openGroup, setOpenGroup] = useState(_activeGroup ? _activeGroup.label : null)

  // showError() est un singleton (errorDialog.js) : son handler est enregistré dans le
  // shell prof, NON monté en admin. Sans ce réenregistrement, showError serait inactif
  // sur /admin/* — l'erreur de saisie échouerait en silence. On rebranche la modale ici.
  useEffect(() => { registerErrorHandler(setAdminAlert) }, [])

  useEffect(() => {
    fetch('/api/admin/check', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) navigate('/admin/login')
        else setChecked(true)
      })
      .catch(() => navigate('/admin/login'))
  }, [navigate])

  useEffect(() => {
    if (!checked) return
    function fetchNotifs() {
      fetch('/api/admin/stats/overview', { credentials: 'include' })
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d) setNotifs({ feedbacks_nouveaux: d.feedbacks_nouveaux || 0, alertes_nonlues: d.alertes_nonlues || 0 }) })
        .catch(() => {})
    }
    fetchNotifs()
    const id = setInterval(fetchNotifs, 60000)
    return () => clearInterval(id)
  }, [checked])

  async function logout() {
    await fetchWithTimeout('/api/admin/logout', { method: 'POST', credentials: 'include' }, TIMEOUT_AUTH)
    navigate('/admin/login')
  }

  // Badge rouge réutilisé : en-tête de catégorie (repliée) + sous-entrée.
  const badgeStyle = {
    padding: '1px 6px', borderRadius: 99, fontSize: 10,
    fontWeight: 700, background: '#fee2e2', color: '#dc2626',
    lineHeight: '16px', flexShrink: 0,
  }

  if (!checked) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#f0f4f8' }}>
      <span className="text-gray-400 text-sm">Chargement…</span>
    </div>
  )

  // Fil d'Ariane de la page courante (en-tête fixe) — déduit du menu.
  let crumbCat = null, crumbPage = ''
  for (const it of NAV_ITEMS) {
    if (it.group) {
      const sub = it.items.find(s => location.pathname === s.to)
      if (sub) { crumbCat = it.label; crumbPage = sub.label; break }
    } else if (it.to && location.pathname === it.to) {
      crumbPage = it.label; break
    }
  }

  return (
    <div style={{ height: '100vh', display: 'flex', overflow: 'hidden' }}>

      {/* Sidebar — figée, pleine hauteur */}
      <aside style={{ width: 220, height: '100vh', background: '#1e293b', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>

        {/* Logo */}
        <div style={{ padding: '24px 20px 20px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'white', letterSpacing: '-0.3px' }}>
            <span style={{ color: '#e05a6e' }}>A</span>-SCHOOL
          </div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginTop: 2 }}>
            Administration
          </div>
        </div>

        {/* Nav items — défile à l'intérieur de la sidebar si le menu est long */}
        <nav style={{ flex: 1, padding: '12px 10px', overflowY: 'auto' }}>
          {NAV_ITEMS.map((item, i) => {
            if (item.separator) return (
              <div key={`sep-${i}`} style={{ height: 1, background: 'rgba(255,255,255,0.08)', margin: '6px 4px' }} />
            )

            if (item.group) {
              // « Active » = la catégorie contient la page courante (surbrillance).
              const isGroupActive = item.prefix
                ? location.pathname.startsWith(item.prefix)
                : item.items.some(s => location.pathname === s.to)
              // « Ouverte » = dépliée (accordéon), indépendant de l'active → on peut replier.
              const isOpen = openGroup === item.label
              // Badges des enfants remontés sur l'en-tête : visibles quand la catégorie est repliée.
              const groupBadge = item.items.reduce(
                (n, s) => n + (s.badgeKey && notifs[s.badgeKey] > 0 ? notifs[s.badgeKey] : 0), 0
              )
              return (
                <div key={`group-${i}`} style={{ marginBottom: 2 }}>
                  {/* En-tête de catégorie — plus grand/gras ; clic = bascule ouvrir / replier */}
                  <div
                    onClick={() => {
                      if (isOpen) { setOpenGroup(null); return }   // ouverte → on la replie
                      setOpenGroup(item.label)                      // fermée → on l'ouvre…
                      if (!isGroupActive) navigate(item.items[0].to) // …et on y va (le bleu suit) si on n'y est pas déjà
                    }}
                    title={item.aide}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '11px 12px', borderRadius: 8, marginTop: 4,
                      fontSize: 14, fontWeight: 600,
                      color: isGroupActive ? '#fff' : 'rgba(255,255,255,0.62)',
                      background: isGroupActive ? 'rgba(255,255,255,0.06)' : 'transparent',
                      borderLeft: isGroupActive ? '3px solid #3b82f6' : '3px solid transparent',
                      cursor: 'pointer', userSelect: 'none', transition: 'color 0.15s',
                    }}
                    onMouseEnter={e => { if (!isGroupActive) e.currentTarget.style.color = 'rgba(255,255,255,0.9)' }}
                    onMouseLeave={e => { if (!isGroupActive) e.currentTarget.style.color = 'rgba(255,255,255,0.62)' }}
                  >
                    <span style={{ opacity: isGroupActive ? 1 : 0.75, display: 'flex' }}>{item.icon}</span>
                    <span>{item.label}</span>
                    <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
                      {!isOpen && groupBadge > 0 && <span style={badgeStyle}>{groupBadge}</span>}
                      <svg
                        width="15" height="15" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                        style={{ opacity: 0.6, transform: isOpen ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.18s' }}
                      >
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                    </span>
                  </div>

                  {/* Sous-entrées — plus petites, décalées sous un rail, liseré bordeaux quand actives */}
                  {isOpen && (
                    <div style={{ marginLeft: 18, borderLeft: '1px solid rgba(255,255,255,0.10)', marginTop: 2, marginBottom: 4 }}>
                      {item.items.map(sub => {
                        const isSubActive = location.pathname === sub.to
                        const subBadge = sub.badgeKey && notifs[sub.badgeKey] > 0 ? notifs[sub.badgeKey] : null
                        return (
                          <Link
                            key={sub.to}
                            to={sub.to}
                            title={sub.aide}
                            style={{
                              display: 'flex', alignItems: 'center', gap: 8,
                              padding: '7px 12px', marginLeft: -1,
                              borderLeft: isSubActive ? '3px solid #A63045' : '3px solid transparent',
                              borderRadius: '0 6px 6px 0',
                              fontSize: 12, fontWeight: isSubActive ? 600 : 400,
                              color: isSubActive ? '#fff' : 'rgba(255,255,255,0.5)',
                              background: isSubActive ? 'rgba(166,48,69,0.16)' : 'transparent',
                              textDecoration: 'none', transition: 'all 0.15s',
                            }}
                            onMouseEnter={e => { if (!isSubActive) e.currentTarget.style.color = 'rgba(255,255,255,0.85)' }}
                            onMouseLeave={e => { if (!isSubActive) e.currentTarget.style.color = 'rgba(255,255,255,0.5)' }}
                          >
                            <span>{sub.label}</span>
                            {subBadge && <span style={{ ...badgeStyle, marginLeft: 'auto' }}>{subBadge}</span>}
                          </Link>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            }

            const isActive = !item.external && location.pathname === item.to
            const style = {
              display:        'flex',
              alignItems:     'center',
              gap:            10,
              padding:        '9px 12px',
              borderRadius:   8,
              marginBottom:   2,
              fontSize:       14,
              fontWeight:     isActive ? 600 : 500,
              color:          isActive ? 'white' : 'rgba(255,255,255,0.55)',
              background:     isActive ? 'rgba(255,255,255,0.1)' : 'transparent',
              textDecoration: 'none',
              cursor:         'pointer',
              transition:     'all 0.15s',
              borderLeft:     isActive ? '3px solid #3b82f6' : '3px solid transparent',
            }

            const badge = item.badgeKey && notifs[item.badgeKey] > 0 ? notifs[item.badgeKey] : null

            const content = (
              <>
                <span style={{ opacity: isActive ? 1 : 0.7 }}>{item.icon}</span>
                <span>{item.label}</span>
                {badge && (
                  <span style={{
                    padding: '1px 6px', borderRadius: 99, fontSize: 10,
                    fontWeight: 700, background: '#fee2e2', color: '#dc2626',
                    lineHeight: '16px', flexShrink: 0,
                  }}>
                    {badge}
                  </span>
                )}
                <span
                  title={item.aide}
                  style={{
                    marginLeft:   'auto',
                    width:        16,
                    height:       16,
                    borderRadius: '50%',
                    background:   'rgba(255,255,255,0.12)',
                    color:        'rgba(255,255,255,0.5)',
                    fontSize:     10,
                    fontWeight:   700,
                    display:      'flex',
                    alignItems:   'center',
                    justifyContent: 'center',
                    cursor:       'help',
                    flexShrink:   0,
                  }}
                >
                  ?
                </span>
              </>
            )

            return item.external ? (
              <a
                key={item.to}
                href={item.to}
                target="afeedback"
                rel="noopener noreferrer"
                title={item.aide}
                style={style}
                onMouseEnter={e => { if (!isActive) e.currentTarget.style.color = 'rgba(255,255,255,0.85)' }}
                onMouseLeave={e => { if (!isActive) e.currentTarget.style.color = 'rgba(255,255,255,0.55)' }}
              >
                {content}
              </a>
            ) : (
              <Link
                key={item.to}
                to={item.to}
                title={item.aide}
                style={style}
                onMouseEnter={e => { if (!isActive) e.currentTarget.style.color = 'rgba(255,255,255,0.85)' }}
                onMouseLeave={e => { if (!isActive) e.currentTarget.style.color = 'rgba(255,255,255,0.55)' }}
              >
                {content}
              </Link>
            )
          })}
        </nav>

        {/* Bas de sidebar */}
        <div style={{ padding: '12px 10px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', flexDirection: 'column', gap: 2 }}>
          <button
            onClick={() => navigate('/')}
            title="Retourner à l'application aSchool"
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '9px 12px', borderRadius: 8,
              fontSize: 13, color: 'rgba(255,255,255,0.45)',
              background: 'none', border: 'none', cursor: 'pointer',
              textAlign: 'left', width: '100%', transition: 'color 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.color = 'rgba(255,255,255,0.8)'}
            onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,255,255,0.45)'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            aSchool
          </button>

          <button
            onClick={logout}
            title="Se déconnecter de l'administration"
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '9px 12px', borderRadius: 8,
              fontSize: 13, color: 'rgba(255,255,255,0.45)',
              background: 'none', border: 'none', cursor: 'pointer',
              textAlign: 'left', width: '100%', transition: 'color 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.color = 'rgba(255,255,255,0.8)'}
            onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,255,255,0.45)'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Déconnexion
          </button>

          <div style={{ padding: '8px 12px 2px', fontSize: 10, color: 'rgba(255,255,255,0.2)', letterSpacing: '0.3px' }}>
            v1.3 · 02/05/2026
          </div>
        </div>
      </aside>

      {/* Contenu principal — en-tête fixe + zone centrale qui défile + footer figé */}
      <main style={{ flex: 1, height: '100vh', background: '#f0f4f8', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* En-tête fixe — fil d'Ariane « catégorie › page » : où on est */}
        <header style={{
          flexShrink: 0, height: 56, borderBottom: '1px solid #e2e8f0', background: '#fff',
          display: 'flex', alignItems: 'center', gap: 8, padding: '0 32px',
        }}>
          {crumbCat && (
            <>
              <span style={{ fontSize: 13, color: '#94a3b8' }}>{crumbCat}</span>
              <span style={{ fontSize: 13, color: '#cbd5e1' }}>›</span>
            </>
          )}
          <span style={{ fontSize: 15, fontWeight: 600, color: '#1e293b' }}>{crumbPage || 'Administration'}</span>
        </header>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {/* Plafond de largeur 900 px pour la plupart des écrans admin. EXCEPTIONS : Référentiel et
              Type d'activité exploitent toute la largeur (beaucoup de colonnes) → pas de plafond sur ces routes. */}
          <div style={{ padding: 32, maxWidth: (location.pathname.includes('/referentiels') || location.pathname.includes('/types-activite')) ? 'none' : 900, width: '100%', margin: '0 auto' }}>
            <Outlet />
          </div>
        </div>

        {/* Footer */}
        <footer style={{
          borderTop: '1px solid #e2e8f0',
          padding: '12px 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#f0f4f8',
          flexShrink: 0,
        }}>
          <span style={{ fontSize: 11, color: '#94a3b8' }}>
            <span style={{ color: '#A63045', fontWeight: 700 }}>A</span>-SCHOOL — Administration
          </span>

          {/* Légende des pastilles d'étape — seulement sur l'écran Référentiel, où elles servent.
              Placée dans le footer global pour qu'un lecteur extérieur comprenne les couleurs. */}
          {location.pathname === '/admin/referentiels' && (
            <span style={{ display: 'flex', flexWrap: 'wrap', gap: 14, fontSize: 11, color: '#94a3b8', alignItems: 'center' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 9, height: 9, borderRadius: '50%', background: '#16a34a' }} />fait / validé
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 9, height: 9, borderRadius: '50%', background: '#dc2626' }} />à faire
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 9, height: 9, borderRadius: '50%', background: '#facc15', border: '1px solid rgba(0,0,0,0.12)' }} />non vérifié
              </span>
            </span>
          )}

          <span style={{ fontSize: 11, color: '#94a3b8' }}>
            © {new Date().getFullYear()} AFIA — aschool.fr
          </span>
        </footer>
      </main>

      {/* Modale bloquante admin (showError) — overlay plein écran, impossible à ignorer */}
      {adminAlert && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#fff', borderRadius: '12px', padding: '28px 24px', maxWidth: '420px', width: '90%', textAlign: 'center', boxShadow: '0 8px 32px rgba(0,0,0,0.2)' }}>
            <div style={{ fontSize: '14px', color: '#1e293b', marginBottom: '20px', lineHeight: 1.6, whiteSpace: 'pre-line' }}>{adminAlert}</div>
            <button
              onClick={() => setAdminAlert(null)}
              title="Fermer ce message"
              style={{ background: '#1F6EEB', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px 28px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}
            >
              OK
            </button>
          </div>
        </div>
      )}

    </div>
  )
}
