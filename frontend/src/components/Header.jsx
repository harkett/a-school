export default function Header({ matiere, email, prenom, nom, onLogout }) {
  const nomAffiche = [prenom, nom].filter(Boolean).join(' ') || email
  return (
    <header className="flex items-center justify-between px-6 py-4" style={{ backgroundColor: 'var(--bleu)' }}>
      <div className="flex items-center gap-3">
        <img src="/icon.png" alt="A-SCHOOL" style={{ width: 34, height: 34, borderRadius: 8, flexShrink: 0 }} />
        <span className="text-white font-bold text-xl tracking-tight">
          <span style={{ color: 'var(--bordeaux)' }}>A</span>-SCHOOL
        </span>
        <span className="text-white text-base" style={{ opacity: 0.75 }}>
          | Générateur d'activités pédagogiques
        </span>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <span style={{ color: 'rgba(255,255,255,0.35)' }}>|</span>
        <span style={{ color: 'white', fontWeight: 600 }}>{matiere}</span>
        <span style={{ color: 'rgba(255,255,255,0.35)' }}>|</span>
        <span
          title={`Connecté avec : ${email}`}
          style={{ color: 'rgba(255,255,255,0.6)', cursor: 'default', borderBottom: '1px dotted rgba(255,255,255,0.3)' }}
        >
          {nomAffiche}
        </span>
        <button
          onClick={onLogout}
          title="Fermer votre session et revenir à la page de connexion"
          style={{
            color: 'white', border: '1px solid rgba(255,255,255,0.4)',
            borderRadius: '6px', padding: '0.3rem 0.85rem',
            fontSize: '0.8rem', background: 'none', cursor: 'pointer',
            display: 'inline-flex', alignItems: 'center', gap: '5px',
          }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          Se déconnecter
        </button>
      </div>
    </header>
  )
}
