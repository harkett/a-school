import { useEffect, useState } from 'react'
import { useNavigate, useLocation, Link, Outlet } from 'react-router-dom'

const NAV_ITEMS = [
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
    to:    '/admin/feedbacks',
    label: 'Feedbacks',
    aide:  'Retours et suggestions des utilisateurs — stockés dans A-SCHOOL, note moyenne et répartition.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
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
]

export default function AdminLayout() {
  const [checked, setChecked] = useState(false)
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

  async function logout() {
    await fetch('/api/admin/logout', { method: 'POST', credentials: 'include' })
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
          {NAV_ITEMS.map(item => {
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

            const content = (
              <>
                <span style={{ opacity: isActive ? 1 : 0.7 }}>{item.icon}</span>
                <span>{item.label}</span>
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
            onClick={async () => {
              await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
              navigate('/')
            }}
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
