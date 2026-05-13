import { useState, useEffect } from 'react'

function KpiCard({ label, value, sub, color }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '14px 16px', textAlign: 'center', flex: 1 }}>
      <div style={{ fontSize: 28, fontWeight: 800, color: color || '#1e293b', lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 11, color: '#64748b', marginTop: 5, fontWeight: 600 }}>{label}</div>
      {sub && <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

export default function MesStats() {
  const [perso,     setPerso]     = useState(null)
  const [commu,     setCommu]     = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const isMobile = window.innerWidth < 768

  useEffect(() => {
    const opts = { credentials: 'include' }
    fetch('/api/stats/perso', opts)
      .then(r => r.ok ? r.json() : null).then(d => { if (d) setPerso(d) }).catch(() => {})
    fetch('/api/stats/communaute', opts)
      .then(r => r.ok ? r.json() : null).then(d => { if (d) setCommu(d) }).catch(() => {})
    fetch('/api/dashboard', opts)
      .then(r => r.ok ? r.json() : null).then(d => { if (d) setDashboard(d) }).catch(() => {})
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

      <div style={{ fontSize: 15, fontWeight: 700, color: '#1e293b' }}>Mes statistiques</div>

      {/* ── Votre activité ── */}
      <div>
        <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>
          Votre activité
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
          <KpiCard
            label="Activités depuis votre début"
            value={perso?.activites_total ?? '—'}
            color="var(--bordeaux)"
            sub={perso?.heures_gagnees > 0 ? `~${perso.heures_gagnees}h gagnées` : null}
          />
          <KpiCard
            label="Mes séquences"
            value={perso?.sequences ?? '—'}
            color="#7c3aed"
            sub="orchestrations"
          />
          <KpiCard
            label="Partagées"
            value={dashboard?.mes_partages ?? '—'}
            color="#059669"
            sub="avec vos collègues"
          />
        </div>
      </div>

      {/* ── Insights perso ── */}
      {perso && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(3, 1fr)', gap: 10 }}>

          {/* Votre type favori */}
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '14px 16px' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
              Votre type favori
            </div>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b', lineHeight: 1.3, wordBreak: 'break-word' }}>
              {perso.type_favori || <span style={{ color: '#cbd5e1', fontStyle: 'italic', fontWeight: 400 }}>Aucun encore</span>}
            </div>
          </div>

          {/* Activités ce mois-ci */}
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '14px 16px' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
              Activités ce mois-ci
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
              <span style={{ fontSize: 28, fontWeight: 800, color: '#1e40af', lineHeight: 1 }}>{perso.activites_ce_mois}</span>
              <span style={{ fontSize: 11, color: '#3b82f6', fontWeight: 600 }}>ce mois</span>
            </div>
          </div>

          {/* Score adaptation */}
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '14px 16px', gridColumn: isMobile ? '1 / -1' : 'auto' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
              aSchool vous connaît à {perso.score_adaptation}%
            </div>
            <div style={{ background: '#f1f5f9', borderRadius: 99, height: 8, overflow: 'hidden' }}>
              <div style={{
                width: `${perso.score_adaptation}%`,
                height: '100%', borderRadius: 99,
                background: perso.score_adaptation >= 100
                  ? 'linear-gradient(90deg, #059669, #34d399)'
                  : perso.score_adaptation >= 50
                    ? 'linear-gradient(90deg, #1d4ed8, #60a5fa)'
                    : 'linear-gradient(90deg, #64748b, #94a3b8)',
                transition: 'width 0.6s ease',
              }} />
            </div>
            <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 5 }}>
              {perso.score_adaptation === 0
                ? 'Sauvegardez 3 activités du même type pour l\'activer'
                : perso.score_adaptation < 100
                  ? 'En cours d\'adaptation à votre style'
                  : 'Style reconnu — les activités vous ressemblent'}
            </div>
          </div>

        </div>
      )}

      {/* ── Vitalité de la communauté ── */}
      {commu && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>
            La communauté aSchool
          </div>
          <div style={{
            background: 'linear-gradient(90deg, #f0f9ff 0%, #f5f3ff 100%)',
            border: '1px solid #ddd6fe',
            borderRadius: 10,
            padding: '14px 6px',
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
          }}>
            {[
              { value: commu.profs_actifs_aujourd_hui, label: "profs actifs\naujourd'hui", color: '#1e40af' },
              { value: commu.profs_actifs_semaine,     label: 'actifs\ncette semaine',     color: '#7c3aed' },
              { value: commu.activites_total,           label: 'activités\nsur aSchool',    color: 'var(--bordeaux)' },
              { value: commu.partages_total,            label: 'partages\nentre collègues', color: '#059669' },
            ].map((s, i, arr) => (
              <div key={s.label} style={{
                textAlign: 'center',
                padding: '4px 8px',
                borderRight: i < arr.length - 1 ? '1px solid #ddd6fe' : 'none',
              }}>
                <div style={{ fontSize: isMobile ? 18 : 22, fontWeight: 800, color: s.color, lineHeight: 1 }}>{s.value}</div>
                <div style={{ fontSize: 9, fontWeight: 600, color: '#6366f1', textTransform: 'uppercase', marginTop: 3, lineHeight: 1.3, whiteSpace: 'pre-line' }}>
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  )
}
