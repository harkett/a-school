import { Fragment, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

const LEVEL_STYLE = {
  critical: { bg: '#fee2e2', color: '#dc2626', label: 'Critique' },
  warning:  { bg: '#ffedd5', color: '#d97706', label: 'Attention' },
  info:     { bg: '#dbeafe', color: '#1d4ed8', label: 'Info' },
}

const CLE_ALERTES = ['admin', 'alerts']

export default function AdminAlertes() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [reglages, setReglages] = useState(false)

  const { data: alerts = [], isPending: loading } = useQuery({
    queryKey: CLE_ALERTES,
    queryFn: async () => {
      const r = await fetch('/api/admin/alerts', { credentials: 'include' })
      if (r.status === 401) { navigate('/admin/login'); return [] }
      return await r.json()
    },
  })

  async function markRead(id) {
    await fetchWithTimeout(`/api/admin/alerts/${id}/read`, { method: 'POST', credentials: 'include' }, TIMEOUT_STD)
    queryClient.setQueryData(CLE_ALERTES, prev => (prev || []).map(a => a.id === id ? { ...a, is_read: true } : a))
  }

  const nonLues = alerts.filter(a => !a.is_read).length

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">
          Alertes système
          {nonLues > 0 && (
            <span style={{ marginLeft: 8, padding: '2px 8px', borderRadius: 99, fontSize: 11, background: '#fee2e2', color: '#dc2626', fontWeight: 700 }}>
              {nonLues} non lue{nonLues > 1 ? 's' : ''}
            </span>
          )}
        </h2>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">Vérification automatique toutes les 5 min</span>
          <button
            onClick={() => setReglages(v => !v)}
            title="Régler les seuils qui déclenchent les alertes"
            style={{ padding: '4px 12px', fontSize: 11, borderRadius: 6,
                     border: '1px solid #e2e8f0', cursor: 'pointer',
                     background: reglages ? '#eff6ff' : 'white', color: '#1F6EEB' }}
          >
            Seuils
          </button>
        </div>
      </div>

      {/* LES SEUILS SE RÈGLENT ICI, comme l'aide du menu l'annonçait déjà. Ils vivaient en base
          — donc « sans développeur » — mais aucun écran ne les modifiait : une valeur qu'on croit
          modifiable et qui ne l'est pas est pire qu'une valeur écrite dans le code. */}
      {reglages && <Seuils onFerme={() => setReglages(false)} />}

      {alerts.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>✓</div>
          <p className="text-sm">Aucune alerte — tout va bien.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {alerts.map(a => {
            const s = LEVEL_STYLE[a.level] || LEVEL_STYLE.info
            return (
              <div
                key={a.id}
                style={{
                  background: 'white',
                  border: `1px solid ${a.is_read ? '#e2e8f0' : s.bg}`,
                  borderLeft: `4px solid ${a.is_read ? '#e2e8f0' : s.color}`,
                  borderRadius: 8,
                  padding: '14px 18px',
                  opacity: a.is_read ? 0.6 : 1,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 14,
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700, background: s.bg, color: s.color }}>
                      {s.label}
                    </span>
                    <span className="text-xs text-gray-400">{a.date}</span>
                  </div>
                  <p style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', margin: 0 }}>{a.title}</p>
                  <p style={{ fontSize: 12, color: '#64748b', margin: '3px 0 0' }}>{a.message}</p>

                  {/* DE QUI, ET AVEC QUOI VÉRIFIER. Une alerte qui dit « vérifier dans le panel
                      admin » oblige à refaire le travail qu'elle vient de faire : le professeur
                      concerné, les faits mesurés et le chemin sont maintenant dans la carte. */}
                  {(a.prof || a.donnees || a.lien) && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center',
                                  gap: 8, marginTop: 8 }}>
                      {a.prof && (
                        <span style={{ fontSize: 11, fontWeight: 600, color: '#1e293b',
                                       background: '#f1f5f9', borderRadius: 4, padding: '2px 8px' }}>
                          {a.prof}
                        </span>
                      )}
                      {a.donnees && Object.entries(a.donnees)
                        .filter(([, v]) => v !== null && typeof v !== 'object')
                        .map(([cle, v]) => (
                          <span key={cle} style={{ fontSize: 11, color: '#64748b',
                                                   background: '#f8fafc', border: '1px solid #e2e8f0',
                                                   borderRadius: 4, padding: '2px 8px' }}>
                            {cle.replace(/_/g, ' ')} : <strong>{String(v)}</strong>
                          </span>
                        ))}
                      {a.lien && (
                        <button
                          onClick={() => navigate(a.lien)}
                          title="Ouvrir l’écran où vérifier"
                          style={{ fontSize: 11, color: '#1F6EEB', background: 'none',
                                   border: 'none', cursor: 'pointer', padding: '2px 4px',
                                   textDecoration: 'underline' }}
                        >
                          Aller voir
                        </button>
                      )}
                    </div>
                  )}
                </div>
                {!a.is_read && (
                  <button
                    onClick={() => markRead(a.id)}
                    title="Marquer comme lu"
                    style={{
                      padding: '4px 12px', fontSize: 11, borderRadius: 4,
                      border: '1px solid #e2e8f0', cursor: 'pointer',
                      background: 'white', color: '#64748b', flexShrink: 0,
                    }}
                  >
                    Lu
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// LE RÉGLAGE DES SEUILS — ce qui décide qu'une situation devient une alerte.
//
// UN SEUL BOUTON POUR TOUT, et c'est voulu : ces sept valeurs se lisent ensemble. Baisser le
// nombre d'appareils tolérés sans regarder la fenêtre de temps donne un résultat qu'on ne
// comprend pas. Le serveur refuse le lot entier si une seule valeur est hors bornes — on
// n'enregistre pas à moitié un réglage de surveillance.
function Seuils({ onFerme }) {
  const [lignes, setLignes] = useState(null)
  const [erreur, setErreur] = useState('')
  const [occupe, setOccupe] = useState(false)
  const [fait, setFait]     = useState(false)

  useEffect(() => {
    fetchWithTimeout('/api/admin/alerts/seuils', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => r.json())
      .then(d => setLignes(d.seuils))
      .catch(() => setErreur('Lecture des seuils impossible.'))
  }, [])

  async function enregistrer() {
    setOccupe(true)
    setErreur('')
    setFait(false)
    try {
      const seuils = Object.fromEntries(lignes.map(l => [l.cle, Number(l.valeur)]))
      const r = await fetchWithTimeout('/api/admin/alerts/seuils', {
        method: 'PUT', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seuils }),
      }, TIMEOUT_STD)
      if (!r.ok) {
        let detail = 'Enregistrement impossible.'
        try { detail = (await r.json()).detail || detail } catch { /* corps illisible */ }
        throw new Error(detail)
      }
      setFait(true)
    } catch (e) {
      setErreur(e.message)
    } finally {
      setOccupe(false)
    }
  }

  if (erreur && !lignes) return <p style={{ fontSize: 13, color: '#dc2626' }}>{erreur}</p>
  if (!lignes) return <p style={{ fontSize: 13, color: '#9ca3af' }}>Chargement des seuils…</p>

  return (
    <div style={{ border: '1px solid #bfdbfe', background: '#eff6ff', borderRadius: 10,
                  padding: 16, marginBottom: 16 }}>
      <p style={{ fontSize: 12, color: '#1e40af', marginBottom: 12 }}>
        Au-delà de ces valeurs, l’administrateur est prévenu. <strong>Rien n’est jamais fermé ni
        bloqué</strong> — une alerte informe, elle ne sanctionne pas.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 110px', gap: '8px 12px',
                    alignItems: 'center' }}>
        {lignes.map((l, i) => (
          // La clé va sur le FRAGMENT : les deux cellules d'une ligne appartiennent à la même
          // grille, et une clé posée sur chacune séparément ne dit rien à React de leur couple.
          <Fragment key={l.cle}>
            <label htmlFor={l.cle} style={{ fontSize: 12.5, color: '#334155' }}>
              {l.libelle}
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                id={l.cle}
                type="number"
                min={l.min}
                max={l.max}
                value={l.valeur ?? ''}
                onChange={e => setLignes(v => v.map((x, j) => j === i ? { ...x, valeur: e.target.value } : x))}
                style={{ width: 66, border: '1px solid #d1d5db', borderRadius: 6,
                         padding: '4px 7px', fontSize: 12.5, outline: 'none' }}
              />
              <span style={{ fontSize: 11, color: '#94a3b8' }}>{l.unite}</span>
            </div>
          </Fragment>
        ))}
      </div>

      {erreur && <p style={{ fontSize: 12, color: '#dc2626', marginTop: 10 }}>{erreur}</p>}
      {fait && <p style={{ fontSize: 12, color: '#15803d', marginTop: 10 }}>
        Seuils enregistrés — ils s’appliquent au prochain contrôle.
      </p>}

      <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
        <button
          onClick={enregistrer}
          disabled={occupe}
          title="Enregistrer les seuils"
          style={{ padding: '5px 14px', fontSize: 12, borderRadius: 7, border: 'none',
                   background: '#1F6EEB', color: '#fff', fontWeight: 500,
                   cursor: occupe ? 'not-allowed' : 'pointer', opacity: occupe ? 0.45 : 1 }}
        >
          Valider
        </button>
        <button
          onClick={onFerme}
          title="Fermer sans enregistrer"
          style={{ padding: '5px 14px', fontSize: 12, borderRadius: 7, border: 'none',
                   background: '#dc2626', color: '#fff', fontWeight: 500, cursor: 'pointer' }}
        >
          Fermer
        </button>
      </div>
    </div>
  )
}
