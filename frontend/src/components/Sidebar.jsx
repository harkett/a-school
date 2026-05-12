import { useState } from 'react'

const IconHome = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
)
const IconHistory = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
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
const IconFeedback = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
)
const IconActivites = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/>
    <line x1="16" y1="17" x2="8" y2="17"/>
    <polyline points="10 9 9 9 8 9"/>
  </svg>
)
const IconBibliotheque = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
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
const IconUser = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)
const IconMesOutils = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="7" height="7"/>
    <rect x="14" y="3" width="7" height="7"/>
    <rect x="14" y="14" width="7" height="7"/>
    <rect x="3" y="14" width="7" height="7"/>
  </svg>
)
const IconMenu = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="3" y1="6" x2="21" y2="6"/>
    <line x1="3" y1="12" x2="21" y2="12"/>
    <line x1="3" y1="18" x2="21" y2="18"/>
  </svg>
)

export default function Sidebar({ page, onNavigate, onFeedback, onNotation }) {
  const [collapsed, setCollapsed] = useState(() => window.innerWidth < 768)

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

  return (
    <aside
      className="bg-white border-r border-gray-200 flex flex-col shrink-0 transition-all"
      style={{ width: collapsed ? 48 : 176, overflow: 'hidden' }}
    >
      <button
        onClick={() => setCollapsed(c => !c)}
        title="Réduire ou agrandir le menu"
        className="flex items-center gap-2 p-4 text-gray-500 hover:bg-gray-50 border-none bg-none cursor-pointer text-sm font-medium"
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

      {!collapsed && (
        <div style={{ padding: '4px 16px 12px', borderBottom: '1px solid #f1f5f9' }}>
          <img src="/Logo_aSchool.png" alt="aSchool" style={{ width: '100%', height: 'auto', display: 'block' }} />
        </div>
      )}

      <nav className={`flex flex-col gap-1 flex-1 ${collapsed ? '' : 'px-4'}`}>
        {navItem('accueil', 'Accueil', IconHome, 'Tableau de bord — vue d\'ensemble')}
        {navItem('mes-outils', 'Mes outils', IconMesOutils, 'Mes outils pédagogiques — créer une activité, une séquence, améliorer')}
        {navItem('mes-activites', 'Mes activités', IconActivites, 'Retrouver et recharger une activité précédemment générée')}
        {navItem('bibliotheque', 'Ma bibliothèque', IconBibliotheque, 'Activités partagées par vos collègues')}
        {navItem('mon-profil', 'Mon profil', IconUser, 'Modifier vos informations : prénom, nom, matière, niveau par défaut')}
        {navItem('historique', 'Mon journal', IconHistory, 'Voir vos générations précédentes')}
      </nav>

      <nav className={`flex flex-col gap-1 pb-3 border-t border-gray-100 pt-3 ${collapsed ? '' : 'px-4'}`}>
        {navItem('bientot-disponible', 'Bientôt disponible', IconRocket, 'Fonctionnalités à venir — proposez vos idées')}
        {navItem('aide', 'Aide', IconHelp, 'Consulter la documentation et l\'aide')}
        <a
          href="#"
          title="Envoyer un feedback ou signaler un problème"
          onClick={e => { e.preventDefault(); onFeedback() }}
          className={`py-1.5 flex items-center gap-2 text-sm transition-colors ${collapsed ? 'justify-center' : ''} text-gray-500 hover:text-gray-800`}
        >
          <IconFeedback />
          {!collapsed && <span>Feedback</span>}
        </a>
        <a
          href="#"
          title="Notez A-SCHOOL — donnez votre avis sur la plateforme en 30 secondes"
          onClick={e => { e.preventDefault(); onNotation() }}
          className={`py-1.5 flex items-center gap-2 text-sm transition-colors ${collapsed ? 'justify-center' : ''} text-gray-500 hover:text-gray-800`}
        >
          <IconStar />
          {!collapsed && <span>Avis</span>}
        </a>
        {navItem('apropos', 'À propos', IconInfo, 'Informations sur A-SCHOOL — version, contact')}
      </nav>

      {!collapsed && (
        <div style={{
          margin: '0 8px 10px',
          padding: '8px 10px',
          borderRadius: '8px',
          background: '#f0f7ff',
          border: '1px solid #bfdbfe',
          fontSize: '11px',
        }}>
          <div style={{ fontWeight: 600, color: '#1d4ed8', marginBottom: 4 }}>En développement</div>
          <div style={{ color: '#3b82f6', lineHeight: 1.6 }}>
            · Application mobile
          </div>
        </div>
      )}
    </aside>
  )
}
