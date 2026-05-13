import { useState, useEffect } from 'react'

const MATIERES = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']
const NIVEAUX  = ['6e', '5e', '4e', '3e', '2nde', '1ère', 'Terminale', 'Supérieur']

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

export default function MonReseauSequences({ onCharger, sessionMatiere, sessionNiveau }) {
  const isMobile = window.innerWidth < 768
  const [matiere, setMatiere]     = useState(sessionMatiere || '')
  const [niveau,  setNiveau]      = useState('')
  const [sequences, setSequences] = useState([])
  const [loading, setLoading]     = useState(true)
  const [hovered, setHovered]     = useState(null)
  const [detailModal, setDetailModal] = useState(null)

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams()
    if (matiere) params.set('matiere', matiere)
    if (niveau)  params.set('niveau',  niveau)
    fetch(`/api/mon-reseau/sequences?${params}`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => { setSequences(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [matiere, niveau])

  const labelFiltre = [matiere, niveau].filter(Boolean).join(', ') || 'Toutes les séquences'

  return (
    <div className="flex flex-col gap-3 w-full">

      {/* En-tête + filtres */}
      <div className="flex flex-col gap-2">
        <div className="flex items-baseline gap-3">
          <h2 className="text-base font-semibold text-gray-800">Mon réseau — Séquences</h2>
          {!loading && (
            <span style={{ fontSize: 12, color: '#6b7280', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '1px 10px' }}>
              {sequences.length} séquence{sequences.length > 1 ? 's' : ''}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span className="text-xs text-gray-500" style={{ fontWeight: 500 }}>
            Séquences — <span style={{ color: '#1e293b' }}>{labelFiltre}</span>
          </span>
          <div style={{ display: 'flex', gap: 6, marginLeft: 'auto' }}>
            <select
              value={matiere}
              onChange={e => setMatiere(e.target.value)}
              title="Filtrer par matière"
              className="border border-gray-200 rounded px-2 py-1 text-xs bg-white text-gray-600"
            >
              <option value="">Toutes les matières</option>
              {MATIERES.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
            <select
              value={niveau}
              onChange={e => setNiveau(e.target.value)}
              title="Filtrer par niveau de classe"
              className="border border-gray-200 rounded px-2 py-1 text-xs bg-white text-gray-600"
            >
              <option value="">Tous les niveaux</option>
              {NIVEAUX.map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: '#475569' }}>Partages de vos collègues</span>
          <span
            title="Ces séquences ont été partagées par vos collègues sur aSchool. Vos propres partages sont visibles dans Séquence → Historique avec le badge bleu Partagé."
            style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 15, height: 15, borderRadius: '50%', background: '#e2e8f0', color: '#64748b', fontSize: 10, fontWeight: 700, cursor: 'help', flexShrink: 0 }}
          >i</span>
        </div>
      </div>

      {loading && <p className="text-sm text-gray-400 py-4">Chargement…</p>}

      {!loading && sequences.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">
            Aucune séquence partagée{matiere || niveau ? ` pour ${labelFiltre}` : ''}.
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Depuis "Séquences → Historique", cliquez sur "Partager" pour rendre une séquence visible ici.
          </p>
        </div>
      )}

      {!loading && sequences.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          {sequences.map((s, i) => (
            <div
              key={s.id}
              onMouseEnter={() => setHovered(s.id)}
              onMouseLeave={() => setHovered(null)}
              style={{
                borderBottom: i < sequences.length - 1 ? '1px solid #e5e7eb' : 'none',
                background: hovered === s.id ? '#f3f4f6' : 'white',
                transition: 'background 0.15s',
              }}
            >
              <div className="flex items-center gap-4 px-5 py-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-gray-800 truncate">{s.theme}</span>
                    <span style={{
                      fontSize: 11, fontWeight: 600, borderRadius: 99, padding: '1px 8px',
                      background: s.mode === 'remediation' ? '#fef3c7' : '#eff6ff',
                      color:      s.mode === 'remediation' ? '#92400e'  : '#1d4ed8',
                      border:     `1px solid ${s.mode === 'remediation' ? '#fde68a' : '#bfdbfe'}`,
                    }}>
                      {s.mode === 'remediation' ? 'Remédiation' : 'Standard'}
                    </span>
                    <span style={{ fontSize: 11, color: '#475569', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '1px 8px' }}>
                      {s.duree} min
                    </span>
                  </div>
                  <div className="flex items-center gap-1 flex-wrap mt-0.5">
                    <span className="text-xs text-gray-400">{s.matiere}</span>
                    <span className="text-xs text-gray-400">· {s.niveau}</span>
                  </div>
                  <p className="text-xs mt-0.5" style={{ color: '#94a3b8' }}>
                    Partagé par <span style={{ color: '#64748b', fontWeight: 500 }}>{s.partagee_par}</span>
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0"
                  style={{ opacity: (isMobile || hovered === s.id) ? 1 : 0, transition: 'opacity 0.15s' }}>
                  <button
                    onClick={() => setDetailModal(s)}
                    title="Voir le contenu complet de la séquence"
                    style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: '#475569', background: 'none', border: '1px solid #e2e8f0', borderRadius: 6, padding: '4px 10px', cursor: 'pointer' }}
                  >
                    Plus de détails
                  </button>
                  <button
                    onClick={() => onCharger(s)}
                    title="Charger cette séquence comme point de départ"
                    className="btn-primary shrink-0"
                  >
                    Utiliser
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modale détail */}
      {detailModal && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}
          onClick={() => setDetailModal(null)}
        >
          <div
            style={{ background: '#fff', borderRadius: 12, width: '100%', maxWidth: 680, maxHeight: '85vh', display: 'flex', flexDirection: 'column', boxShadow: '0 16px 48px rgba(0,0,0,0.22)' }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '20px 24px 16px', borderBottom: '1px solid #e2e8f0', gap: 12 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 4 }}>{detailModal.theme}</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', marginTop: 4 }}>
                  <span style={{
                    fontSize: 11, fontWeight: 600, borderRadius: 99, padding: '1px 8px',
                    background: detailModal.mode === 'remediation' ? '#fef3c7' : '#eff6ff',
                    color:      detailModal.mode === 'remediation' ? '#92400e'  : '#1d4ed8',
                    border:     `1px solid ${detailModal.mode === 'remediation' ? '#fde68a' : '#bfdbfe'}`,
                  }}>
                    {detailModal.mode === 'remediation' ? 'Remédiation' : 'Standard'}
                  </span>
                  <span style={{ fontSize: 11, color: '#475569', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '1px 8px' }}>
                    {detailModal.duree} min
                  </span>
                  <span style={{ fontSize: 12, color: '#94a3b8' }}>
                    {detailModal.matiere} · {detailModal.niveau} · par {detailModal.partagee_par}
                  </span>
                </div>
              </div>
              <button onClick={() => setDetailModal(null)} title="Fermer"
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 20, lineHeight: 1, padding: '2px 4px', flexShrink: 0 }}>
                ×
              </button>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }}>Séquence générée</div>
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 13, color: '#374151', lineHeight: 1.7, margin: 0, fontFamily: 'inherit' }}>
                {detailModal.resultat}
              </pre>
            </div>
            <div style={{ padding: '14px 24px', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button onClick={() => setDetailModal(null)}
                style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: 6, padding: '8px 18px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
                Fermer
              </button>
              <button onClick={() => { onCharger(detailModal); setDetailModal(null) }}
                title="Charger cette séquence comme point de départ"
                className="btn-primary">
                Utiliser
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
