import { useState, useEffect } from 'react'

const FEATURES = [
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
        <line x1="12" y1="18" x2="12.01" y2="18"/>
      </svg>
    ),
    titre: 'Application mobile',
    description: 'A-SCHOOL directement sur votre téléphone. Générez des activités depuis n\'importe où, même sans ordinateur.',
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12 6 12 12 16 14"/>
      </svg>
    ),
    titre: 'Quiz interactif',
    description: 'Créez un quiz, partagez un lien à vos élèves, et suivez leurs réponses en direct depuis votre écran. Outil de diagnostic rapide, sans inscription pour les élèves.',
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2-.2-2.8-.9-.9-2.1-.9-2.8-.2z"/>
        <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
        <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
        <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
      </svg>
    ),
    titre: 'Escape Game pédagogique',
    description: 'Générez un scénario complet avec énigmes adaptées au niveau et épreuve finale de validation. Évaluez vos élèves de manière ludique et collaborative.',
  },
]

export default function BientotDisponible() {
  const [idee, setIdee] = useState('')
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [erreur, setErreur] = useState(false)

  useEffect(() => {
    if (!sent) return
    const t = setTimeout(() => setSent(false), 4000)
    return () => clearTimeout(t)
  }, [sent])

  async function submitIdee() {
    if (!idee.trim()) { setErreur(true); return }
    setSending(true)
    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message: idee.trim(), type: 'idee', rating: 0 }),
      })
      setSent(true)
      setIdee('')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col gap-6 w-full">

      <div className="flex flex-col gap-1">
        <h2 className="text-base font-semibold text-gray-800">Bientôt disponible</h2>
        <p className="text-xs text-gray-400">
          Les fonctionnalités en cours de développement — elles arrivent prochainement sur A-SCHOOL.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        {FEATURES.map(f => (
          <div
            key={f.titre}
            className="bg-white rounded-lg border border-gray-200 shadow-sm px-5 py-4 flex items-start gap-4"
          >
            <div style={{
              flexShrink: 0,
              width: 40, height: 40,
              borderRadius: 10,
              background: '#eff6ff',
              border: '1px solid #bfdbfe',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#2563eb',
            }}>
              {f.icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-gray-800">{f.titre}</span>
                <span style={{
                  fontSize: 10, fontWeight: 600,
                  color: '#2563eb', background: '#eff6ff',
                  border: '1px solid #bfdbfe',
                  borderRadius: 99, padding: '1px 8px',
                  textTransform: 'uppercase', letterSpacing: '0.04em',
                }}>
                  Prochainement
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1" style={{ lineHeight: 1.55 }}>
                {f.description}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-5 py-4 flex flex-col gap-3">
        <div>
          <div className="text-sm font-semibold text-gray-800">Vous avez une idée ?</div>
          <p className="text-xs text-gray-400 mt-0.5">
            Proposez une fonctionnalité — chaque suggestion est lue et prise en compte.
          </p>
        </div>

        {sent ? (
          <div className="text-sm text-green-600 bg-green-50 border border-green-200 rounded px-3 py-2">
            Merci pour votre suggestion ! Elle a bien été transmise.
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <textarea
              value={idee}
              onChange={e => { setIdee(e.target.value); setErreur(false) }}
              placeholder="Décrivez votre idée en quelques mots…"
              maxLength={500}
              rows={3}
              className="border rounded px-3 py-2 text-sm text-gray-700 resize-none"
              style={{ outline: 'none', borderColor: erreur ? '#f87171' : '#e5e7eb' }}
            />
            {erreur && (
              <p className="text-xs" style={{ color: '#ef4444', marginTop: 2 }}>
                Veuillez saisir votre idée avant d'envoyer.
              </p>
            )}
            <button
              onClick={submitIdee}
              disabled={sending}
              className="btn-primary self-start"
              title="Envoyer votre idée à l'équipe A-SCHOOL"
            >
              {sending ? 'Envoi…' : 'Proposer'}
            </button>
          </div>
        )}
      </div>

    </div>
  )
}
