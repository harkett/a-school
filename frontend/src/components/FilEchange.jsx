/**
 * Fil d'échange sur un retour — les réponses qui suivent le message d'ouverture.
 *
 * UN SEUL composant pour les deux écrans (« Mes retours » côté prof, « Retours utilisateurs »
 * côté admin) : la mise en forme du fil ne se décide qu'ici, jamais recopiée d'un côté ou de
 * l'autre. Qui parle est calculé par le serveur (champs `auteur` et `de_moi`) pour que les deux
 * écrans disent la même chose et que l'administration s'appelle toujours « aSchool ».
 */
const MAX = 2000

export default function FilEchange({
  messages = [],
  valeur = '',
  onChange,
  onEnvoyer,
  envoiEnCours = false,
  placeholder = 'Écrivez votre réponse…',
  libelleBouton = 'Répondre',
}) {
  const peutEnvoyer = valeur.trim().length > 0 && !envoiEnCours

  return (
    <div style={{ marginTop: 14, borderTop: '1px solid #f1f5f9', paddingTop: 14 }}>

      {messages.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 14 }}>
          {messages.map(m => {
            const admin = m.de_l_administration
            return (
              <div
                key={m.id}
                style={{
                  borderLeft: `3px solid ${admin ? 'var(--bleu, #1F6EEB)' : '#cbd5e1'}`,
                  background: admin ? '#f5f9ff' : '#fafafa',
                  borderRadius: '0 6px 6px 0',
                  padding: '9px 12px',
                }}
              >
                <div style={{
                  display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
                  gap: 10, marginBottom: 3,
                }}>
                  <span style={{
                    fontSize: '0.75rem', fontWeight: 600,
                    color: admin ? 'var(--bleu, #1F6EEB)' : '#475569',
                  }}>
                    {m.auteur}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#9ca3af', flexShrink: 0 }}>{m.date}</span>
                </div>
                <p style={{
                  margin: 0, fontSize: '0.85rem', color: '#374151',
                  lineHeight: 1.6, whiteSpace: 'pre-wrap',
                }}>
                  {m.corps}
                </p>
              </div>
            )
          })}
        </div>
      )}

      <textarea
        value={valeur}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        rows={3}
        maxLength={MAX}
        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 resize-none focus:outline-none focus:border-blue-400"
      />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginTop: 6 }}>
        <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>
          {valeur.length}/{MAX}
        </span>
        <button
          type="button"
          onClick={onEnvoyer}
          disabled={!peutEnvoyer}
          title={libelleBouton}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '6px 16px', borderRadius: 6, border: 'none',
            background: 'var(--bleu, #1F6EEB)', color: 'white',
            fontSize: '0.82rem', fontWeight: 500,
            cursor: peutEnvoyer ? 'pointer' : 'default',
            opacity: peutEnvoyer ? 1 : 0.45,
          }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
          {envoiEnCours ? 'Envoi…' : libelleBouton}
        </button>
      </div>
    </div>
  )
}
