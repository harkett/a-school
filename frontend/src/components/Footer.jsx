import { useState } from 'react'
import { Link } from 'react-router-dom'
import { APP_VERSION } from '../version'

function ModalMentions({ onClose }) {
  return (
    <div
      onClick={onClose}
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{ background: 'white', borderRadius: 12, border: '1px solid #e2e8f0', padding: 32, width: '100%', maxWidth: 600, maxHeight: '85vh', overflowY: 'auto', position: 'relative' }}
      >
        <button
          onClick={onClose}
          title="Fermer"
          style={{ position: 'absolute', top: 16, right: 16, background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 18, lineHeight: 1 }}
        >✕</button>

        <h1 style={{ fontSize: 16, fontWeight: 600, color: '#1e293b', marginBottom: 24 }}>Mentions légales</h1>

        <Section titre="Éditeur du site">
          <p>Ce site est édité par <strong>AFIA</strong>.</p>
          <p>Contact : <a href="mailto:contact@aschool.fr" style={{ color: '#475569', textDecoration: 'underline' }}>contact@aschool.fr</a></p>
        </Section>

        <Section titre="Hébergement">
          <p>Ce site est hébergé sur un serveur privé virtuel (VPS) exploité par <strong>AFIA</strong>.</p>
          <p>Adresse : <strong>school.afia.fr</strong></p>
        </Section>

        <Section titre="Propriété intellectuelle">
          <p>L'ensemble du contenu de ce site (textes, interfaces, logique applicative) est la propriété exclusive d'AFIA. Toute reproduction, représentation ou diffusion, totale ou partielle, sans autorisation écrite préalable est interdite.</p>
          <p>© 2026 AFIA — Tous droits réservés.</p>
        </Section>

        <Section titre="Données personnelles (RGPD)">
          <p>Dans le cadre de l'utilisation de A-SCHOOL, les données suivantes sont collectées :</p>
          <ul style={{ listStyleType: 'disc', paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <li>Adresse e-mail</li>
            <li>Matière enseignée</li>
            <li>Activités pédagogiques générées</li>
          </ul>
          <p>Ces données sont utilisées exclusivement pour le fonctionnement de l'application et ne sont transmises à aucun tiers.</p>
          <p>Conformément au RGPD, vous disposez d'un droit d'accès, de rectification et de suppression. Pour exercer ce droit : <a href="mailto:contact@aschool.fr" style={{ color: '#475569', textDecoration: 'underline' }}>contact@aschool.fr</a></p>
          <p>Les données sont conservées pendant la durée d'activité du compte et supprimées sur demande.</p>
        </Section>

        <Section titre="Cookies">
          <p>Ce site utilise uniquement des cookies techniques nécessaires à l'authentification (tokens de session). Aucun cookie publicitaire ou de traçage n'est utilisé.</p>
        </Section>
      </div>
    </div>
  )
}

function Section({ titre, children }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <h2 style={{ fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 6 }}>{titre}</h2>
      <div style={{ fontSize: 13, color: '#6b7280', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {children}
      </div>
    </div>
  )
}

export default function Footer() {
  const [showMentions, setShowMentions] = useState(false)

  return (
    <>
      <footer className="bg-white border-t border-gray-200 px-6 py-3">
        <p className="text-center text-xs italic text-gray-400 mb-1">
          "Plus le monde s'ouvre, plus nous avons besoin de proximité..."
        </p>
        <div className="flex justify-between text-xs text-gray-400">
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <img src="/logo.png" alt="aSchool" style={{ height: 18, width: 'auto' }} />
            {' · '}
            <button
              onClick={() => setShowMentions(true)}
              title="Consulter les mentions légales"
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 'inherit', padding: 0, textDecoration: 'underline' }}
            >
              Mentions légales
            </button>
          </span>
          <span>
            v{APP_VERSION} · <a href="mailto:contact@aschool.fr" style={{ color: '#94a3b8' }}>contact@aschool.fr</a>
            {' · '}
            <Link to="/admin" style={{ color: '#e2e8f0' }} title="Administration">admin</Link>
          </span>
        </div>
      </footer>

      {showMentions && <ModalMentions onClose={() => setShowMentions(false)} />}
    </>
  )
}
