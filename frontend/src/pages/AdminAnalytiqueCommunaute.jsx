import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function AdminAnalytiqueCommunaute() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/communaute-stats', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        return r.json()
      })
      .then(d => { if (d) setData(d) })
      .finally(() => setLoading(false))
  }, [navigate])

  if (loading) return <p style={{ color: '#94a3b8', padding: 32 }}>Chargement…</p>
  if (!data)   return <p style={{ color: '#ef4444', padding: 32 }}>Erreur de chargement.</p>

  const { total_partages, nb_contributeurs, par_matiere, par_type, contributeurs } = data
  const maxMat = par_matiere[0]?.nb || 1
  const maxType = par_type[0]?.nb || 1

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      <div>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: '#1e293b', margin: 0 }}>Communauté</h1>
        <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
          Activités partagées par les enseignants dans la bibliothèque commune.
        </p>
      </div>

      {total_partages === 0 ? (
        <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, padding: '48px 32px', textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
          Aucune activité partagée pour le moment.
        </div>
      ) : (
        <>
          {/* KPIs */}
          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 24px', flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#059669' }}>{total_partages}</div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>Activités partagées</div>
            </div>
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 24px', flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#059669' }}>{nb_contributeurs}</div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>Profs contributeurs</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

            {/* Par matière */}
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden' }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #e2e8f0', fontSize: 12, fontWeight: 600, color: '#64748b' }}>
                Par matière
              </div>
              <div style={{ padding: '8px 0' }}>
                {par_matiere.map(({ matiere, nb }) => {
                  const pct = Math.round(nb / maxMat * 100)
                  return (
                    <div key={matiere} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 16px' }}>
                      <span style={{ fontSize: 12, color: '#1e293b', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {matiere}
                      </span>
                      <div style={{ width: 70, background: '#f1f5f9', borderRadius: 99, height: 6, flexShrink: 0 }}>
                        <div style={{ width: `${pct}%`, background: '#059669', height: 6, borderRadius: 99 }} />
                      </div>
                      <span style={{ fontSize: 12, fontWeight: 600, color: '#059669', minWidth: 24, textAlign: 'right' }}>{nb}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Par type */}
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden' }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #e2e8f0', fontSize: 12, fontWeight: 600, color: '#64748b' }}>
                Top types partagés
              </div>
              <div style={{ padding: '8px 0' }}>
                {par_type.map(({ label, nb }) => {
                  const pct = Math.round(nb / maxType * 100)
                  return (
                    <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 16px' }}>
                      <span style={{ fontSize: 12, color: '#1e293b', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {label}
                      </span>
                      <div style={{ width: 70, background: '#f1f5f9', borderRadius: 99, height: 6, flexShrink: 0 }}>
                        <div style={{ width: `${pct}%`, background: '#1F6EEB', height: 6, borderRadius: 99 }} />
                      </div>
                      <span style={{ fontSize: 12, fontWeight: 600, color: '#1F6EEB', minWidth: 24, textAlign: 'right' }}>{nb}</span>
                    </div>
                  )
                })}
              </div>
            </div>

          </div>

          {/* Contributeurs */}
          <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden' }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid #e2e8f0', fontSize: 12, fontWeight: 600, color: '#64748b' }}>
              Profs contributeurs
            </div>
            {contributeurs.map(({ email, nom, nb }, i) => (
              <div key={email} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 16px',
                borderBottom: i < contributeurs.length - 1 ? '1px solid #f1f5f9' : 'none',
              }}>
                <span style={{
                  width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, fontWeight: 700,
                  background: i === 0 ? '#dcfce7' : '#f1f5f9',
                  color: i === 0 ? '#15803d' : '#64748b',
                }}>
                  {i + 1}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{nom}</div>
                  <div style={{ fontSize: 11, color: '#94a3b8' }}>{email}</div>
                </div>
                <span style={{ fontSize: 13, fontWeight: 700, color: '#059669' }}>
                  {nb} partagée{nb > 1 ? 's' : ''}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
