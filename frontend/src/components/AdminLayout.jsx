import { useEffect, useState } from 'react'
import { useNavigate, useLocation, Link, Outlet } from 'react-router-dom'
import { fetchWithTimeout, TIMEOUT_AUTH } from '../utils/api.js'

const SEP = { separator: true }

const NAV_ITEMS = [
  // — Surveillance —
  {
    to:    '/admin/sessions',
    label: 'Sessions',
    aide:  'Profs connectés en ce moment — navigateur, dernière activité, durée. Déconnexion forcée possible.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
      </svg>
    ),
  },
  {
    to:    '/admin/serveur',
    label: 'Serveur',
    aide:  'Métriques VPS (CPU, RAM, disque), statistiques d\'activité et graphe des connexions.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="4" rx="1"/>
        <rect x="2" y="10" width="20" height="4" rx="1"/>
        <rect x="2" y="17" width="20" height="4" rx="1"/>
        <circle cx="6" cy="5" r="0.5" fill="currentColor"/>
        <circle cx="6" cy="12" r="0.5" fill="currentColor"/>
        <circle cx="6" cy="19" r="0.5" fill="currentColor"/>
      </svg>
    ),
  },
  SEP,
  // — Notifications —
  {
    to:       '/admin/alertes',
    label:    'Alertes',
    badgeKey: 'alertes_nonlues',
    aide:     'Alertes automatiques : CPU critique, disque plein, tentatives d\'intrusion. Vérification toutes les 5 min.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
    ),
  },
  {
    to:       '/admin/feedbacks',
    label:    'Feedbacks',
    badgeKey: 'feedbacks_nouveaux',
    aide:     'Retours et suggestions des utilisateurs — note moyenne, répartition, statuts.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
  },
  SEP,
  // — Utilisateurs —
  {
    to:    '/admin/communication',
    label: 'Mail groupé',
    aide:  'Envoyer un message à plusieurs profs en une fois — sélection par matière, filtre, cases à cocher.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 2L11 13"/>
        <path d="M22 2L15 22 11 13 2 9l20-7z"/>
      </svg>
    ),
  },
  {
    to:    '/admin/profils',
    label: 'Profs',
    aide:  'Profils des enseignants — consulter et modifier matière, niveau, prénom et nom.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <line x1="23" y1="11" x2="17" y2="11"/>
        <line x1="20" y1="8" x2="20" y2="14"/>
      </svg>
    ),
  },
  {
    to:    '/admin/activites',
    label: 'Activités',
    aide:  'Catalogue des activités pédagogiques disponibles, par matière et par sous-type.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
      </svg>
    ),
  },
  {
    to:    '/admin/fiches',
    label: 'Fiches matières',
    aide:  'Documents de présentation aSchool par matière — consulter, modifier et générer automatiquement via Groq.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
    ),
  },
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
  SEP,
  // — Accès & sécurité —
  {
    to:    '/admin/logs',
    label: 'Connexions',
    aide:  'Journal des connexions utilisateurs — qui s\'est connecté, quand et depuis quelle adresse IP.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
  },
  {
    to:    '/admin/tentatives',
    label: 'Tentatives',
    aide:  'Tentatives de connexion échouées — IP, identifiant tenté, statut bloqué ou non.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    ),
  },
  {
    to:    '/admin/audit',
    label: 'Audit',
    aide:  'Historique des actions sensibles effectuées par l\'administrateur (déconnexions forcées, suppressions…).',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
    ),
  },
  SEP,
  // — Aide —
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
  SEP,
  // — Configuration —
  {
    to:    '/admin/maintenance',
    label: 'Maintenance',
    aide:  'Nettoyage de la base de données — tokens expirés, sessions fermées, comptes fantômes, logs anciens.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
      </svg>
    ),
  },
  {
    to:    '/admin/parametres',
    label: 'Paramètres',
    aide:  'Configuration de l\'email de bienvenue et des messages automatiques.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </svg>
    ),
  },
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
]

export default function AdminLayout() {
  const [checked, setChecked] = useState(false)
  const [notifs, setNotifs]   = useState({ feedbacks_nouveaux: 0, alertes_nonlues: 0 })
  const navigate  = useNavigate()
  const location  = useLocation()

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

  if (!checked) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#f0f4f8' }}>
      <span className="text-gray-400 text-sm">Chargement…</span>
    </div>
  )

  return (
    <div className="min-h-screen flex">

      {/* Sidebar */}
      <aside style={{ width: 220, background: '#1e293b', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>

        {/* Logo */}
        <div style={{ padding: '24px 20px 20px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'white', letterSpacing: '-0.3px' }}>
            <span style={{ color: '#e05a6e' }}>A</span>-SCHOOL
          </div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginTop: 2 }}>
            Administration
          </div>
        </div>

        {/* Nav items */}
        <nav style={{ flex: 1, padding: '12px 10px' }}>
          {NAV_ITEMS.map((item, i) => {
            if (item.separator) return (
              <div key={`sep-${i}`} style={{ height: 1, background: 'rgba(255,255,255,0.08)', margin: '6px 4px' }} />
            )

            if (item.group) {
              const isGroupActive = location.pathname.startsWith(item.prefix)
              return (
                <div key={`group-${i}`}>
                  <div
                    onClick={!isGroupActive ? () => navigate(item.items[0].to) : undefined}
                    title={item.aide}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '9px 12px', borderRadius: 8, marginBottom: 2,
                      fontSize: 13, fontWeight: isGroupActive ? 600 : 400,
                      color: isGroupActive ? 'white' : 'rgba(255,255,255,0.55)',
                      background: isGroupActive ? 'rgba(255,255,255,0.07)' : 'transparent',
                      borderLeft: isGroupActive ? '3px solid #3b82f6' : '3px solid transparent',
                      cursor: isGroupActive ? 'default' : 'pointer',
                    }}
                    onMouseEnter={e => { if (!isGroupActive) e.currentTarget.style.color = 'rgba(255,255,255,0.85)' }}
                    onMouseLeave={e => { if (!isGroupActive) e.currentTarget.style.color = 'rgba(255,255,255,0.55)' }}
                  >
                    <span style={{ opacity: isGroupActive ? 1 : 0.7 }}>{item.icon}</span>
                    <span>{item.label}</span>
                    <span style={{ marginLeft: 'auto', fontSize: 10, color: 'rgba(255,255,255,0.35)' }}>
                      {isGroupActive ? '▾' : '▸'}
                    </span>
                  </div>
                  {isGroupActive && item.items.map(sub => {
                    const isSubActive = location.pathname === sub.to
                    return (
                      <Link
                        key={sub.to}
                        to={sub.to}
                        title={sub.aide}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 8,
                          padding: '7px 12px 7px 34px', borderRadius: 8, marginBottom: 2,
                          fontSize: 12, fontWeight: isSubActive ? 600 : 400,
                          color: isSubActive ? 'white' : 'rgba(255,255,255,0.5)',
                          background: isSubActive ? 'rgba(255,255,255,0.1)' : 'transparent',
                          textDecoration: 'none',
                          borderLeft: isSubActive ? '3px solid #60a5fa' : '3px solid transparent',
                          transition: 'all 0.15s',
                        }}
                        onMouseEnter={e => { if (!isSubActive) e.currentTarget.style.color = 'rgba(255,255,255,0.85)' }}
                        onMouseLeave={e => { if (!isSubActive) e.currentTarget.style.color = 'rgba(255,255,255,0.5)' }}
                      >
                        <span style={{ fontSize: 16, opacity: 0.4, lineHeight: 1 }}>·</span>
                        {sub.label}
                      </Link>
                    )
                  })}
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
              fontSize:       13,
              fontWeight:     isActive ? 600 : 400,
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
            title="Retourner à l'application A-SCHOOL"
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
            A-SCHOOL
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

      {/* Contenu principal */}
      <main style={{ flex: 1, background: '#f0f4f8', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, padding: 32, maxWidth: 900, width: '100%', margin: '0 auto' }}>
          <Outlet />
        </div>

        {/* Footer */}
        <footer style={{
          borderTop: '1px solid #e2e8f0',
          padding: '12px 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#f0f4f8',
        }}>
          <span style={{ fontSize: 11, color: '#94a3b8' }}>
            <span style={{ color: '#A63045', fontWeight: 700 }}>A</span>-SCHOOL — Administration
          </span>
          <span style={{ fontSize: 11, color: '#94a3b8' }}>
            © {new Date().getFullYear()} AFIA — school.afia.fr
          </span>
        </footer>
      </main>

    </div>
  )
}
