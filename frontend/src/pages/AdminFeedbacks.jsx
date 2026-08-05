import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchWithTimeout } from '../utils/api.js'
import { demanderConfirmation } from '../confirmDialog'
import FilEchange from '../components/FilEchange'

const ETOILES = r => '★'.repeat(r) + '☆'.repeat(5 - r)
const COULEUR = { 5: '#16a34a', 4: '#65a30d', 3: '#ca8a04', 2: '#ea580c', 1: '#dc2626' }

// Les statuts (codes, libellés, ordre) sont LUS EN BASE — plus aucune copie ici. Seules les
// COULEURS restent à l'écran : c'est de la présentation, pas une donnée. Elles se prennent
// dans cette palette PAR RANG, si bien qu'un statut ajouté en base est habillé lui aussi,
// sans retoucher ce fichier (l'ordre actuel redonne exactement les couleurs d'avant).
const PALETTE_STATUTS = [
  { bg: '#dbeafe', color: '#1d4ed8' },
  { bg: '#ffedd5', color: '#c2410c' },
  { bg: '#dcfce7', color: '#15803d' },
  { bg: '#f3f4f6', color: '#6b7280' },
  { bg: '#f5f3ff', color: '#6d28d9' },
]

// L'ancien tableau TRANSITIONS (« archivé ne revient qu'à traité ») a été RETIRÉ : cette règle
// n'existait qu'ici, le serveur accepte n'importe quel statut du catalogue. L'écran propose
// donc tous les statuts sauf celui en cours — ce qu'il montre est ce que le serveur fait.

export default function AdminFeedbacks() {
  const [onglet, setOnglet] = useState('notations')
  const [filtre, setFiltre] = useState('tous')
  const [brouillons, setBrouillons] = useState({})   // réponse en cours de frappe, par retour
  const [envoiId, setEnvoiId] = useState(null)       // retour dont la réponse part (sablier)
  const [avis, setAvis] = useState(null)             // { type: 'ok' | 'err', texte }

  // Les trois lectures de l'écran, tenues par react-query. Read-after-write : après chaque
  // écriture on relit le serveur (refetch), jamais de miroir local.
  const { data: items, isError: itemsRate, refetch: rechargerItems } = useQuery({
    queryKey: ['admin', 'feedbacks'],
    queryFn: async () => {
      const res = await fetch('/api/admin/feedbacks', { credentials: 'include' })
      if (!res.ok) throw new Error('feedbacks illisibles')
      return await res.json()
    },
  })
  // Catalogue des statuts : lu en base, il fabrique les filtres, les pastilles et les boutons.
  const { data: statuts, isError: statutsRate } = useQuery({
    queryKey: ['admin', 'feedback-statuts'],
    queryFn: async () => {
      const r = await fetch('/api/admin/feedback-statuts', { credentials: 'include' })
      if (!r.ok) throw new Error('statuts illisibles')
      return await r.json()
    },
  })
  // Les votes ne bloquent pas l'écran : illisibles, la section se montre simplement vide.
  const { data: featureVotes = null } = useQuery({
    queryKey: ['admin', 'feature-votes'],
    queryFn: async () => {
      const r = await fetch('/api/admin/feature-votes', { credentials: 'include' })
      return r.ok ? await r.json() : []
    },
  })

  async function recharger() { await rechargerItems() }

  const erreur = itemsRate ? 'Impossible de charger les données.'
    : statutsRate ? 'Impossible de charger les statuts de feedback.'
    : null

  if (erreur) return <p className="text-red-600 text-sm">{erreur}</p>
  if (!items || !statuts) return <p className="text-gray-400 text-sm">Chargement…</p>

  // Habillage d'un statut : libellé LU EN BASE, couleur prise par rang dans la palette.
  function statutInfo(code) {
    const i = statuts.findIndex(s => s.code === code)
    const s = i >= 0 ? statuts[i] : null
    const teinte = PALETTE_STATUTS[(i >= 0 ? i : statuts.length) % PALETTE_STATUTS.length]
    return { code, label: s ? s.label : code, ...teinte }
  }

  const statutParDefaut = statuts[0]?.code || 'nouveau'
  const FILTRES_FB = ['tous', ...statuts.map(s => s.code)]
  const libelleFiltre = f => (f === 'tous' ? 'Tous' : statutInfo(f).label)

  const notations = items.filter(f => f.type === 'notation' && f.rating > 0)
  const feedbacks = items.filter(f => f.type !== 'notation')

  const feedbacksFiltres = filtre === 'tous'
    ? feedbacks
    : feedbacks.filter(f => (f.statut || statutParDefaut) === filtre)

  async function changerStatut(id, statut) {
    await fetchWithTimeout(`/api/admin/feedbacks/${id}/statut`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ statut }),
    })
    await recharger()
  }

  async function supprimerFeedback(id) {
    if (!await demanderConfirmation({
      titre: 'Supprimer définitivement ce feedback ?',
      message: 'Le retour du prof et son échange seront perdus. Cette action est irréversible.',
      confirmLabel: 'Supprimer',
      danger: true,
    })) return
    await fetchWithTimeout(`/api/admin/feedbacks/${id}`, { method: 'DELETE', credentials: 'include' })
    await recharger()
  }

  async function repondre(id) {
    const corps = (brouillons[id] || '').trim()
    if (!corps) return
    setEnvoiId(id)
    setAvis(null)
    try {
      const res = await fetchWithTimeout(`/api/admin/feedbacks/${id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ corps }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'La réponse n\'a pas pu être enregistrée.')
      setBrouillons(b => ({ ...b, [id]: '' }))
      await recharger()
      setAvis(data.avis_envoye
        ? { type: 'ok', texte: 'Réponse envoyée. Le professeur a été prévenu par e-mail.' }
        : { type: 'err', texte: 'Réponse enregistrée : le professeur la verra dans aSchool. En revanche, l\'e-mail qui devait le prévenir n\'est pas parti — vérifiez l\'écran Système › Email.' })
    } catch (e) {
      setAvis({ type: 'err', texte: e.message })
    } finally {
      setEnvoiId(null)
    }
  }

  const moyenne = notations.length
    ? (notations.reduce((s, f) => s + f.rating, 0) / notations.length).toFixed(1)
    : '—'
  const csat = notations.length
    ? Math.round((notations.filter(f => f.rating >= 4).length / notations.length) * 100)
    : '—'

  const parNote = [5, 4, 3, 2, 1].map(n => ({
    note: n,
    count: notations.filter(f => f.rating === n).length,
  }))

  const tabStyle = active => ({
    padding: '7px 18px', borderRadius: 6, fontSize: 13, fontWeight: active ? 600 : 400,
    cursor: 'pointer', border: 'none',
    background: active ? 'var(--bleu)' : 'white',
    color: active ? 'white' : '#6b7280',
    boxShadow: active ? 'none' : 'inset 0 0 0 1px #e5e7eb',
  })

  const filtreStyle = active => ({
    padding: '4px 12px', fontSize: '12px', borderRadius: '4px', border: '1px solid',
    cursor: 'pointer', fontWeight: active ? 600 : 400,
    background: active ? '#1e40af' : '#fff',
    color: active ? '#fff' : '#6b7280',
    borderColor: active ? '#1e40af' : '#d1d5db',
  })

  return (
    <div className="flex flex-col gap-6">

      <h2 className="text-base font-semibold text-gray-800">Retours utilisateurs</h2>

      {/* Onglets */}
      <div className="flex gap-2">
        <button style={tabStyle(onglet === 'notations')} onClick={() => setOnglet('notations')}>
          Notations ({notations.length})
        </button>
        <button style={tabStyle(onglet === 'feedbacks')} onClick={() => setOnglet('feedbacks')}>
          Feedbacks ({feedbacks.length})
        </button>
        <button style={tabStyle(onglet === 'votes')} onClick={() => setOnglet('votes')}>
          Votes fonctionnalités
        </button>
      </div>

      {/* ── NOTATIONS ── */}
      {onglet === 'notations' && (
        <>
          {notations.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400 text-sm">
              Aucune notation reçue pour le moment.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
                  <div className="text-2xl font-bold" style={{ color: 'var(--bleu)' }}>{notations.length}</div>
                  <div className="text-xs text-gray-400 mt-1">Notations reçues</div>
                </div>
                <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
                  <div className="text-2xl font-bold" style={{ color: '#ca8a04' }}>{moyenne}<span className="text-sm font-normal text-gray-400">/5</span></div>
                  <div className="text-xs text-gray-400 mt-1">Note moyenne</div>
                </div>
                <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
                  <div className="text-2xl font-bold" style={{ color: '#16a34a' }}>{csat}<span className="text-sm font-normal text-gray-400">%</span></div>
                  <div className="text-xs text-gray-400 mt-1">CSAT (4-5 ★)</div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <p className="text-xs font-medium text-gray-500 mb-3">Répartition des notes</p>
                <div className="flex flex-col gap-2">
                  {parNote.map(({ note, count }) => {
                    const pct = notations.length ? Math.round((count / notations.length) * 100) : 0
                    return (
                      <div key={note} className="flex items-center gap-3">
                        <span className="text-xs w-6 text-right text-gray-500">{note}★</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-2">
                          <div className="h-2 rounded-full transition-all" style={{ width: `${pct}%`, background: COULEUR[note] }} />
                        </div>
                        <span className="text-xs text-gray-400 w-8">{count}</span>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="flex flex-col gap-3">
                {notations.map(f => (
                  <div key={f.id} className="bg-white rounded-xl border border-gray-200 p-5">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <span style={{ color: COULEUR[f.rating], fontSize: 18 }}>{ETOILES(f.rating)}</span>
                      <div className="text-right flex-shrink-0">
                        <div className="text-xs text-gray-400">{f.date}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{f.email}</div>
                      </div>
                    </div>
                    {f.message && f.message !== '—' && (
                      <p className="text-sm text-gray-700 leading-relaxed mb-3">{f.message}</p>
                    )}
                    <div className="flex justify-end">
                      <button
                        onClick={() => supprimerFeedback(f.id)}
                        title="Supprimer définitivement cette notation"
                        style={{
                          padding: '2px 10px', fontSize: '11px', borderRadius: '4px',
                          border: '1px solid #fca5a5', cursor: 'pointer',
                          background: '#fff', color: '#dc2626',
                        }}
                      >
                        Supprimer
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}

      {/* ── FEEDBACKS ── */}
      {onglet === 'feedbacks' && (
        <>
          {/* Filtres statut */}
          <div className="flex items-center gap-2 flex-wrap">
            {FILTRES_FB.map(f => (
              <button
                key={f}
                onClick={() => setFiltre(f)}
                title={`Filtrer : ${libelleFiltre(f)}`}
                style={filtreStyle(filtre === f)}
              >
                {libelleFiltre(f)}
                {f !== 'tous' && (
                  <span style={{ marginLeft: 6, opacity: 0.7 }}>
                    ({feedbacks.filter(fb => (fb.statut || statutParDefaut) === f).length})
                  </span>
                )}
              </button>
            ))}
            {filtre !== 'tous' && (
              <span className="text-xs text-gray-400 ml-1">
                {feedbacksFiltres.length} / {feedbacks.length}
              </span>
            )}
          </div>

          {avis && (
            <div style={{
              background: avis.type === 'ok' ? '#f0fdf4' : '#fef2f2',
              border: `1px solid ${avis.type === 'ok' ? '#bbf7d0' : '#fecaca'}`,
              color: avis.type === 'ok' ? '#15803d' : '#b91c1c',
              borderRadius: 8, padding: '10px 14px', fontSize: '0.85rem',
            }}>
              {avis.texte}
            </div>
          )}

          {feedbacksFiltres.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400 text-sm">
              Aucun feedback dans cette catégorie.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {feedbacksFiltres.map(f => {
                const st = statutInfo(f.statut || statutParDefaut)
                return (
                  <div key={f.id} className="bg-white rounded-xl border border-gray-200 p-5">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        {f.category && (
                          <span className="text-xs rounded px-2 py-0.5" style={{ background: '#eff6ff', color: '#1d4ed8' }}>
                            {f.category}
                          </span>
                        )}
                        <span className="text-xs rounded px-2 py-0.5 font-medium" style={{ background: st.bg, color: st.color }}>
                          {st.label}
                        </span>
                        {f.contexte && (
                          <span className="text-xs rounded px-2 py-0.5" title="D'où le prof a envoyé ce retour" style={{ background: '#f1f5f9', color: '#64748b' }}>
                            {f.contexte}
                          </span>
                        )}
                      </div>
                      <div className="text-right flex-shrink-0">
                        <div className="text-xs text-gray-400">{f.date}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{f.email}</div>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed mb-3">{f.message}</p>
                    {f.incident && (
                      <div style={{
                        marginBottom: 12, border: '1px solid #fecaca', background: '#fef2f2',
                        borderRadius: 6, padding: '10px 12px',
                      }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: '#b91c1c', letterSpacing: 0.3 }}>
                          INCIDENT TECHNIQUE · {f.incident.ref}
                        </div>
                        <div style={{
                          fontSize: 12, color: '#7f1d1d', marginTop: 4,
                          fontFamily: 'monospace', whiteSpace: 'pre-wrap',
                        }}>
                          {f.incident.error}
                        </div>
                        <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 6 }}>
                          {[
                            [f.incident.provider, f.incident.model].filter(Boolean).join(' · '),
                            f.incident.type_activite,
                            [f.incident.matiere, f.incident.niveau].filter(Boolean).join(' '),
                            f.incident.date,
                          ].filter(Boolean).join('  ·  ')}
                        </div>
                        {f.incident.consigne && (
                          <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
                            Consigne : {f.incident.consigne}
                          </div>
                        )}
                      </div>
                    )}
                    {/* Échange avec le prof : ses réponses, les vôtres, et de quoi répondre. */}
                    <FilEchange
                      messages={f.messages}
                      valeur={brouillons[f.id] || ''}
                      onChange={v => setBrouillons(b => ({ ...b, [f.id]: v }))}
                      onEnvoyer={() => repondre(f.id)}
                      envoiEnCours={envoiId === f.id}
                      placeholder="Répondre au professeur… Il recevra un e-mail l'invitant à lire votre réponse dans aSchool."
                    />

                    <div className="flex items-center justify-between gap-2 flex-wrap mt-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs text-gray-400">Changer le statut :</span>
                        {statuts
                          .filter(s => s.code !== (f.statut || statutParDefaut))
                          .map(s => {
                            const teinte = statutInfo(s.code)
                            return (
                              <button
                                key={s.code}
                                onClick={() => changerStatut(f.id, s.code)}
                                title={`Passer ce retour en « ${s.label} »`}
                                style={{
                                  padding: '2px 10px', fontSize: '11px', borderRadius: '4px',
                                  border: `1px solid ${teinte.color}`, cursor: 'pointer',
                                  background: '#fff', color: teinte.color,
                                }}
                              >
                                {s.label}
                              </button>
                            )
                          })}
                      </div>
                      <button
                        onClick={() => supprimerFeedback(f.id)}
                        title="Supprimer définitivement ce feedback"
                        style={{
                          padding: '2px 10px', fontSize: '11px', borderRadius: '4px',
                          border: '1px solid #fca5a5', cursor: 'pointer',
                          background: '#fff', color: '#dc2626',
                        }}
                      >
                        Supprimer
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}

      {/* ── VOTES ── */}
      {onglet === 'votes' && (
        <div className="flex flex-col gap-4">
          {!featureVotes || featureVotes.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400 text-sm">
              Aucun vote enregistré pour le moment.
            </div>
          ) : (
            <>
              <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
                <div className="text-2xl font-bold" style={{ color: 'var(--bleu)' }}>
                  {featureVotes.reduce((s, f) => s + f.count, 0)}
                </div>
                <div className="text-xs text-gray-400 mt-1">Votes total</div>
              </div>
              <div className="flex flex-col gap-3">
                {featureVotes.map((f, i) => {
                  const max = featureVotes[0]?.count || 1
                  const pct = max > 0 ? Math.round((f.count / max) * 100) : 0
                  return (
                    <div key={f.key} className="bg-white rounded-xl border border-gray-200 px-5 py-4">
                      <div className="flex items-center justify-between gap-3 mb-2">
                        <div className="flex items-center gap-2">
                          <span style={{
                            width: 22, height: 22, borderRadius: '50%', display: 'inline-flex',
                            alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700,
                            background: i === 0 ? '#fef3c7' : '#f1f5f9',
                            color: i === 0 ? '#92400e' : '#64748b',
                            flexShrink: 0,
                          }}>
                            {i + 1}
                          </span>
                          <span className="text-sm font-semibold text-gray-800">{f.label}</span>
                        </div>
                        <span className="text-sm font-bold" style={{ color: f.count > 0 ? 'var(--bordeaux)' : '#94a3b8' }}>
                          {f.count} vote{f.count !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-1.5">
                        <div
                          className="h-1.5 rounded-full transition-all"
                          style={{ width: `${pct}%`, background: f.count > 0 ? 'var(--bordeaux)' : '#e2e8f0' }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </div>
      )}

    </div>
  )
}
