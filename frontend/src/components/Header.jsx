export default function Header({ matiere, email, prenom, nom, onLogout, onNavigate }) {
  const nomAffiche = [prenom, nom].filter(Boolean).join(' ') || email
  const isMobile = window.innerWidth < 768
  return (
    <header
      className="flex items-center justify-between px-6"
      style={{ backgroundColor: 'var(--bleu)', height: 65, overflow: 'hidden', position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100 }}
    >
      <div className="flex items-center gap-3">
        <img src="/Logo_aSchool_blanc.png" alt="aSchool" title="Générateur d'activités pédagogiques" style={{ height: 140, width: 'auto' }} />
        <span style={{ color: 'rgba(255,255,255,0.9)', fontSize: '1.4rem', fontWeight: 500, display: isMobile ? 'none' : undefined }}>
          Générateur d'activités pédagogiques
        </span>
      </div>
      <div className="flex items-center gap-4 text-sm">
        {!isMobile && <>
          <span style={{ color: 'rgba(255,255,255,0.35)' }}>|</span>
          <span style={{ color: 'white', fontWeight: 600 }}>{matiere}</span>
          <span style={{ color: 'rgba(255,255,255,0.35)' }}>|</span>
        </>}
        <button
          onClick={() => onNavigate('mon-profil')}
          title="Voir et modifier mon profil"
          style={{ color: 'rgba(255,255,255,0.8)', cursor: 'pointer', background: 'none', border: 'none', padding: 0, fontSize: 'inherit', fontFamily: 'inherit' }}
        >
          {isMobile ? (
            <div style={{ textAlign: 'right', lineHeight: 1.3 }}>
              <div style={{ fontWeight: 600, fontSize: '0.78rem', borderBottom: '1px dotted rgba(255,255,255,0.4)' }}>{nomAffiche}</div>
              <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.6)' }}>{matiere}</div>
            </div>
          ) : (
            <span style={{ borderBottom: '1px dotted rgba(255,255,255,0.4)' }}>{nomAffiche}</span>
          )}
        </button>
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
          {isMobile ? 'Déconnecter' : 'Se déconnecter'}
        </button>
      </div>
    </header>
  )
}
