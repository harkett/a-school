import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

function MetricCard({ label, value, sub, color }) {
  return (
    <div style={{
      background: 'white', borderRadius: 10, padding: '20px 24px',
      border: '1px solid #e2e8f0', flex: 1, minWidth: 140,
    }}>
      <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 700, color: color || '#1e293b', lineHeight: 1 }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

function BarChart({ data, labelKey = 'day', color = '#3b82f6' }) {
  if (!data.length) return <p className="text-sm text-gray-400">Pas encore de données.</p>
  const max = Math.max(...data.map(d => d.count), 1)
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 80 }}>
      {data.map(d => (
        <div key={d[labelKey]} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          <div
            title={`${d[labelKey]} : ${d.count} connexion${d.count !== 1 ? 's' : ''}`}
            style={{
              width: '100%', borderRadius: '3px 3px 0 0',
              background: color,
              height: `${Math.max(d.count > 0 ? 4 : 1, Math.round((d.count / max) * 72))}px`,
              opacity: d.count > 0 ? 0.8 : 0.15,
              cursor: 'default',
            }}
          />
        </div>
      ))}
    </div>
  )
}

export default function AdminServeur() {
  const [metrics, setMetrics] = useState(null)
  const [overview, setOverview] = useState(null)
  const [logins, setLogins]   = useState([])
  const [hours, setHours]     = useState([])
  const [dbSize, setDbSize]   = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const opts = { credentials: 'include' }
    Promise.all([
      fetch('/api/admin/server-metrics', opts).then(r => r.status === 401 ? null : r.json()),
      fetch('/api/admin/stats/overview',  opts).then(r => r.status === 401 ? null : r.json()),
      fetch('/api/admin/stats/logins',    opts).then(r => r.status === 401 ? null : r.json()),
      fetch('/api/admin/db-size',         opts).then(r => r.status === 401 ? null : r.json()),
      fetch('/api/admin/stats/hours',     opts).then(r => r.status === 401 ? null : r.json()),
    ]).then(([m, o, l, d, h]) => {
      if (!m) { navigate('/admin/login'); return }
      setMetrics(m)
      setOverview(o)
      setLogins(l || [])
      setDbSize(d)
      setHours(h || [])
    }).catch(() => navigate('/admin/login')).finally(() => setLoading(false))
  }, [navigate])

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  const ramColor  = metrics.ram_percent  > 80 ? '#dc2626' : metrics.ram_percent  > 60 ? '#d97706' : '#15803d'
  const cpuColor  = metrics.cpu_percent  > 80 ? '#dc2626' : metrics.cpu_percent  > 50 ? '#d97706' : '#15803d'
  const diskColor = metrics.disk_percent > 80 ? '#dc2626' : metrics.disk_percent > 60 ? '#d97706' : '#15803d'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* Cards activité */}
      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Activité</h2>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <MetricCard label="Profs inscrits"      value={overview?.total_profs ?? '—'} />
          <MetricCard label="Connexions aujourd'hui" value={overview?.connexions_today ?? '—'} />
          <MetricCard label="Profs en ligne"      value={overview?.sessions_online ?? '—'} color="#15803d" />
          <MetricCard label="Feedbacks nouveaux"  value={overview?.feedbacks_nouveaux ?? '—'} color={overview?.feedbacks_nouveaux > 0 ? '#d97706' : undefined} />
        </div>
      </div>

      {/* Cards serveur */}
      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Serveur VPS</h2>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <MetricCard label="CPU" value={`${metrics.cpu_percent}%`} color={cpuColor} />
          <MetricCard label="RAM" value={`${metrics.ram_percent}%`}
            sub={`${metrics.ram_used_gb} / ${metrics.ram_total_gb} Go`} color={ramColor} />
          <MetricCard label="Disque" value={`${metrics.disk_percent}%`}
            sub={`${metrics.disk_used_gb} / ${metrics.disk_total_gb} Go`} color={diskColor} />
          <MetricCard label="Uptime" value={`${metrics.uptime_hours}h`} />
          <MetricCard label="Base de données" value={dbSize ? `${dbSize.size_mb} Mo` : '—'} />
        </div>
      </div>

      {/* Graphe connexions 30j */}
      <div style={{ background: 'white', borderRadius: 10, padding: '20px 24px', border: '1px solid #e2e8f0' }}>
        <h2 className="text-sm font-semibold text-gray-700 mb-1">
          Connexions — 30 derniers jours
        </h2>
        <p className="text-xs text-gray-400 mb-4">
          {logins.reduce((s, d) => s + d.count, 0)} connexions au total
        </p>
        <BarChart data={logins} labelKey="day" />
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: 10, color: '#cbd5e1' }}>
          {logins.length > 0 && (
            <>
              <span>{logins[0]?.day}</span>
              <span>{logins[logins.length - 1]?.day}</span>
            </>
          )}
        </div>
      </div>

      {/* Heures de pointe */}
      <div style={{ background: 'white', borderRadius: 10, padding: '20px 24px', border: '1px solid #e2e8f0' }}>
        <h2 className="text-sm font-semibold text-gray-700 mb-1">
          Heures de pointe
        </h2>
        <p className="text-xs text-gray-400 mb-4">
          Répartition des connexions par heure de la journée (toutes périodes confondues)
        </p>
        <BarChart data={hours} labelKey="hour" color="#8b5cf6" />
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 10, color: '#cbd5e1' }}>
          <span>00h</span>
          <span>06h</span>
          <span>12h</span>
          <span>18h</span>
          <span>23h</span>
        </div>
      </div>

    </div>
  )
}
