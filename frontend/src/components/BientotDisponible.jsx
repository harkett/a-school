import { useState, useEffect } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

const FEATURES = [
  {
    feature_key: 'ambiguites-cognitives',
    categorie: 'Outils pédagogiques',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    ),
    titre: 'Détecter les ambiguïtés',
    description: 'Collez un exercice ou un énoncé — aSchool identifie les zones à risque d\'incompréhension, les termes à double sens et les étapes implicites non formulées. Des reformulations corrigées sont proposées immédiatement.',
  },
  {
    feature_key: 'analyser-consigne',
    categorie: 'Outils pédagogiques',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        <line x1="11" y1="8" x2="11" y2="14"/>
        <line x1="8" y1="11" x2="14" y2="11"/>
      </svg>
    ),
    titre: 'Analyser une consigne',
    description: 'Collez n\'importe quelle consigne — aSchool détecte les ambiguïtés, les étapes implicites, les mots à double sens et les risques d\'erreur typiques. Résultat : une version clarifiée, précise et didactiquement solide.',
  },
  {
    feature_key: 'verifier-evaluation',
    categorie: 'Outils pédagogiques',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M9 11l3 3L22 4"/>
        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
      </svg>
    ),
    titre: 'Vérifier une évaluation',
    description: 'Soumettez une évaluation existante — aSchool détecte les questions qui mesurent autre chose que ce qu\'elles prétendent évaluer, les biais de difficulté et les formulations anxiogènes. Une version corrigée est générée automatiquement.',
  },
  {
    feature_key: 'coherence-curriculaire',
    categorie: 'Outils pédagogiques',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="18" cy="5" r="3"/>
        <circle cx="6" cy="12" r="3"/>
        <circle cx="18" cy="19" r="3"/>
        <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
        <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
      </svg>
    ),
    titre: 'Cohérence inter-disciplines',
    description: 'Vérifiez si vos progressions s\'articulent avec celles des autres matières. aSchool aligne automatiquement notions et calendriers pédagogiques pour éviter les doublons et les contradictions entre disciplines.',
  },
  {
    feature_key: 'quiz-interactif',
    categorie: 'Autre',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12 6 12 12 16 14"/>
      </svg>
    ),
    titre: 'Quiz interactif élèves',
    description: 'Générez un quiz depuis une activité, partagez un lien à vos élèves, et suivez leurs réponses en direct sur votre écran. Sans inscription pour les élèves — un simple lien suffit.',
  },
  {
    feature_key: 'escape-game',
    categorie: 'Autre',
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
  const [votes, setVotes] = useState({})
  const [mesVotes, setMesVotes] = useState([])

  useEffect(() => {
    fetch('/api/feature-votes', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) { setVotes(d.votes); setMesVotes(d.mes_votes) } })
      .catch(() => {})
  }, [])

  async function handleVote(feature_key) {
    const voted = mesVotes.includes(feature_key)
    setMesVotes(prev => voted ? prev.filter(k => k !== feature_key) : [...prev, feature_key])
    setVotes(prev => ({ ...prev, [feature_key]: (prev[feature_key] || 0) + (voted ? -1 : 1) }))
    try {
      const r = await fetchWithTimeout('/api/feature-vote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ feature_key }),
      })
      if (r.ok) {
        const d = await r.json()
        setVotes(prev => ({ ...prev, [feature_key]: d.count }))
        setMesVotes(prev => d.voted ? [...new Set([...prev, feature_key])] : prev.filter(k => k !== feature_key))
      }
    } catch {}
  }

  useEffect(() => {
    if (!sent) return
    const t = setTimeout(() => setSent(false), 4000)
    return () => clearTimeout(t)
  }, [sent])

  async function submitIdee() {
    if (!idee.trim()) { setErreur(true); return }
    setSending(true)
    try {
      await fetchWithTimeout('/api/feedback', {
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
          Les fonctionnalités en cours de développement — elles arrivent prochainement sur aSchool.
        </p>
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
              title="Envoyer votre idée à l'équipe aSchool"
            >
              {sending ? 'Envoi…' : 'Proposer'}
            </button>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-5 py-4 flex flex-col gap-5">
        <div>
          <div className="text-sm font-semibold text-gray-800">Nos idées à nous</div>
          <p className="text-xs text-gray-400 mt-0.5">
            Les fonctionnalités en cours de développement — elles arrivent prochainement sur aSchool.
          </p>
        </div>

        {['Outils pédagogiques', 'Autre'].map(cat => (
          <div key={cat} className="flex flex-col gap-3">
            <div style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {cat}
            </div>
            {FEATURES.filter(f => f.categorie === cat).map(f => (
              <div
                key={f.titre}
                className="rounded-lg border border-gray-100 px-4 py-3 flex items-start gap-4"
                style={{ background: '#fafafa' }}
              >
                <div style={{
                  flexShrink: 0,
                  width: 38, height: 38,
                  borderRadius: 9,
                  background: cat === 'Outils pédagogiques' ? '#f5f3ff' : '#eff6ff',
                  border: `1px solid ${cat === 'Outils pédagogiques' ? '#c4b5fd' : '#bfdbfe'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: cat === 'Outils pédagogiques' ? '#7c3aed' : '#2563eb',
                }}>
                  {f.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-gray-800">{f.titre}</span>
                    <span style={{
                      fontSize: 10, fontWeight: 600,
                      color: cat === 'Outils pédagogiques' ? '#7c3aed' : '#2563eb',
                      background: cat === 'Outils pédagogiques' ? '#f5f3ff' : '#eff6ff',
                      border: `1px solid ${cat === 'Outils pédagogiques' ? '#c4b5fd' : '#bfdbfe'}`,
                      borderRadius: 99, padding: '1px 8px',
                      textTransform: 'uppercase', letterSpacing: '0.04em',
                    }}>
                      Prochainement
                    </span>
                  </div>
                  <div className="flex items-end justify-between gap-3 mt-1">
                    <p className="text-xs text-gray-500 flex-1" style={{ lineHeight: 1.55 }}>
                      {f.description}
                    </p>
                    <button
                      onClick={() => handleVote(f.feature_key)}
                      title={mesVotes.includes(f.feature_key) ? 'Retirer mon vote' : 'Je veux cette fonctionnalité'}
                      style={{
                        flexShrink: 0,
                        display: 'flex', alignItems: 'center', gap: 5,
                        padding: '4px 11px', fontSize: 12, fontWeight: 700,
                        border: `1.5px solid ${mesVotes.includes(f.feature_key) ? 'var(--bordeaux)' : '#e2e8f0'}`,
                        borderRadius: 99,
                        background: mesVotes.includes(f.feature_key) ? '#fff0f0' : '#f8fafc',
                        color: mesVotes.includes(f.feature_key) ? 'var(--bordeaux)' : '#94a3b8',
                        cursor: 'pointer',
                        transition: 'all .15s',
                      }}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill={mesVotes.includes(f.feature_key) ? 'var(--bordeaux)' : 'none'} stroke="currentColor" strokeWidth="2.5">
                        <polyline points="18 15 12 9 6 15"/>
                      </svg>
                      {votes[f.feature_key] || 0}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

    </div>
  )
}
