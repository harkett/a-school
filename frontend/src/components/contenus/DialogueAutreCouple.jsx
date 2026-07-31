// « Contenu d'un autre profil » — LE garde-fou, partagé par tous les chemins qui rouvrent un
// contenu de Mes contenus (les pages listes ET la carte « dernière création » de l'Accueil).
//
// Pourquoi il existe : on ne régénère que dans le couple de travail courant. Reprendre une
// activité de 3e alors qu'on travaille en 6e produirait un contenu incohérent — et depuis que
// le serveur contrôle le type à l'écriture (étape 8), il refuse carrément, avec un message qui
// parle du niveau COURANT pendant que la carte du prof affiche l'autre. L'écran doit donc
// arrêter le geste AVANT, et dire ce qui se passe.
//
// Un seul fichier pour tous les appelants : l'Accueil et les pages listes ne peuvent pas
// diverger, et le jour où ce dialogue proposera de basculer de couple, il le proposera partout.
const NOMS = {
  activite: { titre: "Activité d'un autre profil", sujet: 'Cette activité' },
  seance:   { titre: "Séance d'un autre profil",   sujet: 'Cette séance' },
  sequence: { titre: "Séquence d'un autre profil", sujet: 'Cette séquence' },
}

export default function DialogueAutreCouple({ contenu, type = 'activite', sessionMatiere, sessionNiveau, onFermer }) {
  const nom = NOMS[type] || NOMS.activite
  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      onClick={onFermer}
    >
      <div
        style={{ background: '#fff', borderRadius: '10px', padding: '24px 28px', maxWidth: '440px', width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ fontWeight: 700, fontSize: '15px', marginBottom: '10px', color: '#1e293b' }}>
          {nom.titre}
        </div>
        <p style={{ fontSize: '13.5px', color: '#374151', margin: '0 0 18px', lineHeight: 1.6 }}>
          {nom.sujet} est en <strong>{contenu?.matiere || '—'} / {contenu?.niveau || '—'}</strong>,
          différente de votre profil courant (<strong>{sessionMatiere || '—'} / {sessionNiveau || '—'}</strong>).
          Pour la reprendre, passez d'abord sur le profil correspondant.
        </p>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={onFermer}
            title="Fermer"
            style={{ background: 'var(--bleu)', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
          >
            OK
          </button>
        </div>
      </div>
    </div>
  )
}
