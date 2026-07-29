// Écran « Mes contenus » — la bibliothèque unique du prof (séquences · séances · activités).
// Brique 0 : l'entrée de menu et la coquille de l'écran. La liste à plat arrive avec la brique 1.
export default function MesContenus() {
  return (
    <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center', textAlign: 'center' }}>
      <div style={{ fontSize: '15px', fontWeight: 700, color: '#1e293b' }}>Mes contenus</div>
      <p style={{ fontSize: '13px', color: '#64748b', margin: 0, maxWidth: '440px', lineHeight: 1.6 }}>
        Votre bibliothèque : toutes vos séquences, séances et activités réunies au même endroit.
        Écran en construction — la liste de vos contenus arrive ici.
      </p>
    </div>
  )
}
