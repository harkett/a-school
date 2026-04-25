import { useEffect, useState } from 'react'
import { useNavigate, useLocation, Link, Outlet } from 'react-router-dom'

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

  const navItems = [
    { to: '/admin/logs', label: 'Connexions' },
  ]

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#f0f4f8' }}>
      {/* Barre admin */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-sm font-semibold text-gray-800">
            <span style={{ color: 'var(--bordeaux)', fontWeight: 700 }}>A</span>-SCHOOL
            <span className="ml-2 text-xs font-normal text-gray-400">Administration</span>
          </span>
          <nav className="flex gap-1">
            {navItems.map(item => (
              <Link
                key={item.to}
                to={item.to}
                className="px-3 py-1.5 rounded text-xs font-medium transition-colors"
                style={
                  location.pathname === item.to
                    ? { background: 'var(--bleu)', color: 'white' }
                    : { color: '#6b7280' }
                }
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={async () => {
              await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
              navigate('/login')
            }}
            title="Retour à A-SCHOOL"
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
            style={{ background: 'none', border: 'none', cursor: 'pointer' }}
          >
            ← A-SCHOOL
          </button>
          <button
            onClick={logout}
            title="Se déconnecter de l'administration"
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
            style={{ background: 'none', border: 'none', cursor: 'pointer' }}
          >
            Déconnexion
          </button>
        </div>
      </header>

      {/* Contenu */}
      <main className="flex-1 p-6 max-w-5xl w-full mx-auto">
        <Outlet />
      </main>
    </div>
  )
}
