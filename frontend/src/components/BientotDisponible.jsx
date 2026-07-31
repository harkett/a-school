import { useState, useEffect } from 'react'
import { fetchWithTimeout, lireReponse, messagePourEcran, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'

// Les CARTES viennent du serveur (table features_votables — source unique, plus aucune
// liste en dur ici). Seul le DESSIN reste côté écran : mapping nom d'icône → SVG,
// pictogramme neutre si le nom est inconnu.
const ICONES = {
  loupe: (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      <line x1="11" y1="8" x2="11" y2="14"/>
      <line x1="8" y1="11" x2="14" y2="11"/>
    </svg>
  ),
  coche: (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 11l3 3L22 4"/>
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
    </svg>
  ),
  reseau: (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="18" cy="5" r="3"/>
      <circle cx="6" cy="12" r="3"/>
      <circle cx="18" cy="19" r="3"/>
      <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
      <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
    </svg>
  ),
  horloge: (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 16 14"/>
    </svg>
  ),
  mobile: (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
      <line x1="12" y1="18" x2="12.01" y2="18"/>
    </svg>
  ),
  fusee: (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2-.2-2.8-.9-.9-2.1-.9-2.8-.2z"/>
      <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
      <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
      <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
    </svg>
  ),
}
const ICONE_DEFAUT = (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 3l1.9 5.8L20 10.7l-5.9 1.9L12 18.4l-2.1-5.8L4 10.7l6.1-1.9z"/>
  </svg>
)

export default function BientotDisponible() {
  const [idee, setIdee] = useState('')
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [erreur, setErreur] = useState(false)
  const [features, setFeatures] = useState(null)      // null = chargement en cours
  const [chargementRate, setChargementRate] = useState(false)
  const [mesVotes, setMesVotes] = useState([])
  const [voteEnCours, setVoteEnCours] = useState(null) // key du vote qui attend le serveur

  async function charger() {
    setFeatures(null)
    setChargementRate(false)
    try {
      const r = await fetchWithTimeout('/api/feature-votes', { credentials: 'include' }, TIMEOUT_STD)
      const d = await lireReponse(r)
      setFeatures(d.features)
      setMesVotes(d.mes_votes)
    } catch (e) {
      setChargementRate(true)
      showError(messagePourEcran(e))
    }
  }

  useEffect(() => { charger() }, [])

  // Pas de compteur monté en avance : le clic envoie, la RÉPONSE du serveur fait foi.
  // Vote refusé = boîte de dialogue, l'écran ne bouge pas.
  async function handleVote(feature_key) {
    if (voteEnCours) return
    setVoteEnCours(feature_key)
    try {
      const r = await fetchWithTimeout('/api/feature-vote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ feature_key }),
      })
      const d = await lireReponse(r)
      setFeatures(prev => prev.map(f => f.key === feature_key ? { ...f, count: d.count } : f))
      setMesVotes(prev => d.voted ? [...new Set([...prev, feature_key])] : prev.filter(k => k !== feature_key))
    } catch (e) {
      showError(messagePourEcran(e))
    } finally {
      setVoteEnCours(null)
    }
  }

  useEffect(() => {
    if (!sent) return
    const t = setTimeout(() => setSent(false), 4000)
    return () => clearTimeout(t)
  }, [sent])

  // « Merci » seulement si le serveur a VRAIMENT enregistré : la réponse est lue (lireReponse
  // lève sur !ok) et l'échec part en boîte de dialogue. L'idée reste dans le champ pour que
  // le prof la renvoie — on ne la perd pas derrière un faux succès.
  async function submitIdee() {
    if (!idee.trim()) { setErreur(true); return }
    setSending(true)
    try {
      const r = await fetchWithTimeout('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message: idee.trim(), type: 'idee', rating: 0 }),
      })
      await lireReponse(r)
      setSent(true)
      setIdee('')
    } catch (e) {
      showError(messagePourEcran(e))
    } finally {
      setSending(false)
    }
  }

  const categories = features ? [...new Set(features.map(f => f.categorie))] : []

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
            Les fonctionnalités en cours de développement — votez pour celles que vous attendez le plus.
          </p>
        </div>

        {chargementRate ? (
          <button
            onClick={charger}
            className="btn-primary self-start"
            title="Recharger les fonctionnalités votables"
          >
            Réessayer
          </button>
        ) : !features ? (
          <p className="text-sm text-gray-400">Chargement…</p>
        ) : categories.map(cat => (
          <div key={cat} className="flex flex-col gap-3">
            <div style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {cat}
            </div>
            {features.filter(f => f.categorie === cat).map(f => (
              <div
                key={f.key}
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
                  {ICONES[f.icone] || ICONE_DEFAUT}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-gray-800">{f.label}</span>
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
                      onClick={() => handleVote(f.key)}
                      disabled={voteEnCours !== null}
                      title={mesVotes.includes(f.key) ? 'Retirer mon vote' : 'Je veux cette fonctionnalité'}
                      style={{
                        flexShrink: 0,
                        display: 'flex', alignItems: 'center', gap: 5,
                        padding: '4px 11px', fontSize: 12, fontWeight: 700,
                        border: `1.5px solid ${mesVotes.includes(f.key) ? 'var(--bordeaux)' : '#e2e8f0'}`,
                        borderRadius: 99,
                        background: mesVotes.includes(f.key) ? '#fff0f0' : '#f8fafc',
                        color: mesVotes.includes(f.key) ? 'var(--bordeaux)' : '#94a3b8',
                        cursor: voteEnCours ? 'wait' : 'pointer',
                        opacity: voteEnCours === f.key ? 0.6 : 1,
                        transition: 'all .15s',
                      }}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill={mesVotes.includes(f.key) ? 'var(--bordeaux)' : 'none'} stroke="currentColor" strokeWidth="2.5">
                        <polyline points="18 15 12 9 6 15"/>
                      </svg>
                      {f.count}
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
