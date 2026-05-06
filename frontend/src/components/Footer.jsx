import { Link } from 'react-router-dom'
import { APP_VERSION } from '../version'

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 px-6 py-3">
      <p className="text-center text-xs italic text-gray-400 mb-1">
        "Plus le monde s'ouvre, plus nous avons besoin de proximité..."
      </p>
      <div className="flex justify-between text-xs text-gray-400">
        <span>
          <span style={{ color: 'var(--bordeaux)', fontWeight: 600 }}>A</span>-SCHOOL
          {' · '}
          <Link to="/mentions-legales" className="hover:underline" style={{ color: '#94a3b8' }} title="Consulter les mentions légales">Mentions légales</Link>
        </span>
        <span>
          v{APP_VERSION} · <a href="mailto:contact@aschool.fr" style={{ color: '#94a3b8' }}>contact@aschool.fr</a>
          {' · '}
          <Link to="/admin" style={{ color: '#e2e8f0' }} title="Administration">admin</Link>
        </span>
      </div>
    </footer>
  )
}
