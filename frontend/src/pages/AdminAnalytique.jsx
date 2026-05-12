import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const MATIERES = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']
const NIVEAUX  = ['6e', '5e', '4e', '3e', '2nde', '1ère', 'Terminale', 'Supérieur']

function KpiCard({ label, value, sub, color }) {
  return (
    <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 20px', flex: 1, minWidth: 140 }}>
      <div style={{ fontSize: 24, fontWeight: 700, color: color || '#1e293b' }}>{value}</div>
      <div style={{ fontSize: 13, color: '#475569', marginTop: 2 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

function TypePill({ label, nb }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99,
      padding: '2px 8px', fontSize: 11, color: '#475569', whiteSpace: 'nowrap',
    }}>
      {label} <strong style={{ color: '#1e293b' }}>×{nb}</strong>
    </span>
  )
}

function NiveauPill({ niv, total }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 3,
      background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 99,
      padding: '2px 7px', fontSize: 11, color: '#1d4ed8', whiteSpace: 'nowrap',
    }}>
      {niv} <strong>×{total}</strong>
    </span>
  )
}

function DetailRow({ matiere, matData }) {
  const niveaux = Object.entries(matData.par_niveau).sort((a, b) => b[1].total - a[1].total)
  return (
    <div style={{ padding: '12px 20px 16px', background: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 10 }}>
        {matiere} — {matData.total} activité{matData.total > 1 ? 's' : ''}
      </div>
      {niveaux.map(([niv, nivData]) => (
        <div key={niv} style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#475569', marginBottom: 4 }}>
            {niv} ({nivData.total})
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {Object.entries(nivData.par_type)
              .sort((a, b) => b[1] - a[1])
              .map(([typ, nb]) => (
                <TypePill key={typ} label={typ} nb={nb} />
              ))
            }
          </div>
        </div>
      ))}
    </div>
  )
}

export default function AdminAnalytique() {
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(true)
  const [expanded, setExpanded] = useState({})
  const [filterMat, setFilterMat] = useState('')
  const [filterNiv, setFilterNiv] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/stats/analytique', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        return r.json()
      })
      .then(d => { if (d) setData(d) })
      .finally(() => setLoading(false))
  }, [navigate])

  function toggleExpand(email, matiere) {
    const key = `${email}::${matiere}`
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }))
  }

  if (loading) return <p style={{ color: '#94a3b8', padding: 32 }}>Chargement…</p>
  if (!data)   return <p style={{ color: '#ef4444', padding: 32 }}>Erreur de chargement.</p>

  const { profs, totaux } = data

  // Filtrer les profs
  const profsFiltres = profs
    .map(p => {
      if (!filterMat && !filterNiv) return p
      const parMatFiltre = Object.entries(p.par_matiere).reduce((acc, [mat, matData]) => {
        if (filterMat && mat !== filterMat) return acc
        if (filterNiv) {
          const parNivFiltre = Object.entries(matData.par_niveau)
            .filter(([niv]) => niv === filterNiv)
            .reduce((a, [n, d]) => ({ ...a, [n]: d }), {})
          if (Object.keys(parNivFiltre).length === 0) return acc
          const total = Object.values(parNivFiltre).reduce((s, d) => s + d.total, 0)
          acc[mat] = { total, par_niveau: parNivFiltre }
        } else {
          acc[mat] = matData
        }
        return acc
      }, {})
      if (Object.keys(parMatFiltre).length === 0) return null
      const total = Object.values(parMatFiltre).reduce((s, d) => s + d.total, 0)
      return { ...p, par_matiere: parMatFiltre, total }
    })
    .filter(Boolean)
    .sort((a, b) => b.total - a.total)

  const topType = Object.entries(totaux.par_type)[0]
  const topMat  = Object.entries(totaux.par_matiere)[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* Titre */}
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: '#1e293b', margin: 0 }}>Activités — détail par prof</h1>
        <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
          Activités générées par prof — détail par matière, niveau et type d'activité.
        </p>
      </div>

      {/* KPI cards */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <KpiCard label="Activités totales"   value={totaux.grand_total} color="#A63045" />
        <KpiCard label="Profs actifs"        value={profs.length} />
        <KpiCard label="Matière la + active" value={topMat?.[0] || '—'} sub={topMat ? `${topMat[1]} activités` : ''} />
        <KpiCard label="Type le + utilisé"   value={topType?.[0] || '—'} sub={topType ? `×${topType[1]}` : ''} />
      </div>

      {/* Filtres */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>Filtrer :</span>
        <select
          value={filterMat}
          onChange={e => setFilterMat(e.target.value)}
          style={{ border: '1px solid #e2e8f0', borderRadius: 6, padding: '5px 10px', fontSize: 12, background: 'white', color: '#1e293b' }}
        >
          <option value="">Toutes les matières</option>
          {MATIERES.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
        <select
          value={filterNiv}
          onChange={e => setFilterNiv(e.target.value)}
          style={{ border: '1px solid #e2e8f0', borderRadius: 6, padding: '5px 10px', fontSize: 12, background: 'white', color: '#1e293b' }}
        >
          <option value="">Tous les niveaux</option>
          {NIVEAUX.map(n => <option key={n} value={n}>{n}</option>)}
        </select>
        {(filterMat || filterNiv) && (
          <button
            onClick={() => { setFilterMat(''); setFilterNiv('') }}
            style={{ fontSize: 11, color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
          >
            Réinitialiser
          </button>
        )}
        <span style={{ fontSize: 12, color: '#94a3b8', marginLeft: 'auto' }}>
          {profsFiltres.length} prof{profsFiltres.length > 1 ? 's' : ''}
          {' · '}
          {profsFiltres.reduce((s, p) => s + p.total, 0)} activité{profsFiltres.reduce((s, p) => s + p.total, 0) > 1 ? 's' : ''}
        </span>
      </div>

      {/* Tableau par prof */}
      {profsFiltres.length === 0 ? (
        <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, padding: '40px 20px', textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
          Aucun résultat pour ce filtre.
        </div>
      ) : (
        <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden' }}>
          {/* En-tête tableau */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 120px 110px 70px auto',
            padding: '10px 20px', background: '#f8fafc',
            borderBottom: '1px solid #e2e8f0',
            fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px',
          }}>
            <span>Prof</span>
            <span>Matière profil</span>
            <span>Niveau profil</span>
            <span style={{ textAlign: 'right' }}>Total</span>
            <span></span>
          </div>

          {profsFiltres.map((prof, pi) => {
            const matieres = Object.entries(prof.par_matiere).sort((a, b) => b[1].total - a[1].total)
            const nom = [prof.prenom, prof.nom].filter(Boolean).join(' ') || prof.email

            return (
              <div key={prof.email} style={{ borderBottom: pi < profsFiltres.length - 1 ? '1px solid #e2e8f0' : 'none' }}>
                {matieres.map(([mat, matData], mi) => {
                  const expandKey = `${prof.email}::${mat}`
                  const isExpanded = expanded[expandKey]
                  const niveauxPills = Object.entries(matData.par_niveau)
                    .sort((a, b) => b[1].total - a[1].total)

                  return (
                    <div key={mat}>
                      {/* Ligne principale */}
                      <div style={{
                        display: 'grid', gridTemplateColumns: '1fr 120px 110px 70px auto',
                        padding: '12px 20px', alignItems: 'center',
                        background: isExpanded ? '#f0f9ff' : 'white',
                        borderTop: mi > 0 ? '1px dashed #f1f5f9' : 'none',
                        transition: 'background 0.15s',
                      }}>
                        {/* Prof info */}
                        <div>
                          {mi === 0 && (
                            <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{nom}</div>
                          )}
                          {mi === 0 && (
                            <div style={{ fontSize: 11, color: '#94a3b8' }}>{prof.email}</div>
                          )}
                          {mi > 0 && <div style={{ fontSize: 11, color: '#94a3b8', paddingLeft: 12 }}>↳ {mat}</div>}
                          {mi === 0 && (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
                              {niveauxPills.map(([niv, d]) => (
                                <NiveauPill key={niv} niv={niv} total={d.total} />
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Matière profil */}
                        <span style={{ fontSize: 12, color: '#475569' }}>
                          {mi === 0 ? (prof.subject || '—') : mat}
                        </span>

                        {/* Niveau profil */}
                        <span style={{ fontSize: 12, color: '#475569' }}>
                          {mi === 0 ? (prof.niveau_profil || '—') : ''}
                        </span>

                        {/* Total */}
                        <span style={{ fontSize: 14, fontWeight: 700, color: '#A63045', textAlign: 'right' }}>
                          {matData.total}
                        </span>

                        {/* Bouton détail */}
                        <button
                          onClick={() => toggleExpand(prof.email, mat)}
                          title={isExpanded ? 'Masquer le détail' : 'Voir le détail par type d\'activité'}
                          style={{
                            background: 'none', border: '1px solid #e2e8f0', borderRadius: 6,
                            padding: '4px 10px', fontSize: 11, cursor: 'pointer',
                            color: isExpanded ? '#1d4ed8' : '#64748b',
                            borderColor: isExpanded ? '#bfdbfe' : '#e2e8f0',
                            background: isExpanded ? '#eff6ff' : 'white',
                            marginLeft: 8, whiteSpace: 'nowrap',
                          }}
                        >
                          {isExpanded ? '▲ Masquer' : '▼ Détail'}
                        </button>
                      </div>

                      {/* Ligne détail expandée */}
                      {isExpanded && (
                        <DetailRow matiere={mat} matData={matData} />
                      )}
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>
      )}

      {/* Totaux globaux */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        {/* Par matière */}
        <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #e2e8f0', fontSize: 12, fontWeight: 600, color: '#64748b' }}>
            Total par matière
          </div>
          {Object.entries(totaux.par_matiere).map(([mat, nb]) => {
            const pct = totaux.grand_total ? Math.round(nb / totaux.grand_total * 100) : 0
            return (
              <div key={mat} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ fontSize: 12, color: '#1e293b', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{mat}</span>
                <div style={{ width: 80, background: '#f1f5f9', borderRadius: 99, height: 6, flexShrink: 0 }}>
                  <div style={{ width: `${pct}%`, background: '#A63045', height: 6, borderRadius: 99 }} />
                </div>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#A63045', minWidth: 28, textAlign: 'right' }}>{nb}</span>
              </div>
            )
          })}
        </div>

        {/* Par niveau */}
        <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #e2e8f0', fontSize: 12, fontWeight: 600, color: '#64748b' }}>
            Total par niveau
          </div>
          {Object.entries(totaux.par_niveau).map(([niv, nb]) => {
            const pct = totaux.grand_total ? Math.round(nb / totaux.grand_total * 100) : 0
            return (
              <div key={niv} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ fontSize: 12, color: '#1e293b', width: 60, flexShrink: 0 }}>{niv}</span>
                <div style={{ flex: 1, background: '#f1f5f9', borderRadius: 99, height: 6 }}>
                  <div style={{ width: `${pct}%`, background: '#1F6EEB', height: 6, borderRadius: 99 }} />
                </div>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#1F6EEB', minWidth: 28, textAlign: 'right' }}>{nb}</span>
              </div>
            )
          })}
        </div>

      </div>

      {/* Top 20 types */}
      <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden' }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #e2e8f0', fontSize: 12, fontWeight: 600, color: '#64748b' }}>
          Top 20 types d'activités (toutes matières)
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, padding: 16 }}>
          {Object.entries(totaux.par_type).map(([typ, nb]) => (
            <span key={typ} style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
              padding: '5px 10px', fontSize: 12, color: '#475569',
            }}>
              {typ}
              <span style={{ fontWeight: 700, color: '#A63045', background: '#fdf2f5', borderRadius: 99, padding: '1px 6px', fontSize: 11 }}>
                {nb}
              </span>
            </span>
          ))}
        </div>
      </div>

    </div>
  )
}
