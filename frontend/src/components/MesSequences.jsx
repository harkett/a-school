import { useState, useEffect } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

const IconShare = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
  </svg>
)

function IconTrash() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="3 6 5 6 21 6"/>
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
      <path d="M10 11v6"/><path d="M14 11v6"/>
      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
    </svg>
  )
}


function formatDate(iso) {
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

export default function MesSequences({ onCharger, sessionMatiere, sessionNiveau, onNavigate, userName }) {
  const isMobile = window.innerWidth < 768
  const [sequences, setSequences]       = useState([])
  const [loading, setLoading]           = useState(true)
  const [detailModal, setDetailModal]   = useState(null)
  const [deleteDialog, setDeleteDialog] = useState(null)
  const [deleting, setDeleting]         = useState(null)
  const [toggling, setToggling]           = useState(null)
  const [anonymeDialog, setAnonymeDialog] = useState(null)
  const [hovered, setHovered]             = useState(null)

  useEffect(() => {
    fetch('/api/mes-sequences', { credentials: 'include' })
      .then(r => r.json())
      .then(data => { setSequences(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const filtered = sequences.filter(s => {
    if (sessionMatiere && s.matiere !== sessionMatiere) return false
    if (sessionNiveau  && s.niveau  !== sessionNiveau)  return false
    return true
  })

  const labelProfil = [sessionMatiere, sessionNiveau].filter(Boolean).join(', ')

  async function togglePartage(id, newValue, anonyme = false) {
    setToggling(id)
    try {
      const res = await fetchWithTimeout(`/api/mes-sequences/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ partagee: newValue, anonyme }),
      })
      if (res.ok) {
        setSequences(prev => prev.map(s => s.id === id ? { ...s, partagee: newValue } : s))
      }
    } finally {
      setToggling(null)
    }
  }

  async function supprimerSequence(id) {
    setDeleting(id)
    try {
      const res = await fetchWithTimeout(`/api/mes-sequences/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      }, TIMEOUT_STD)
      if (res.ok) {
        setSequences(prev => prev.filter(s => s.id !== id))
        if (detailModal?.id === id) setDetailModal(null)
      }
    } finally {
      setDeleting(null)
      setDeleteDialog(null)
    }
  }

  return (
    <div className="flex flex-col gap-3 w-full">

      {/* En-tête */}
      <div className="flex flex-col gap-1">
        <div className="flex items-baseline gap-3">
          <h2 className="text-base font-semibold text-gray-800">Mes séquences</h2>
          {!loading && filtered.length > 0 && (
            <span style={{ fontSize: 12, color: 'var(--bordeaux)', background: '#fdf2f5', border: '1px solid #f4c4ce', borderRadius: 99, padding: '1px 10px', fontWeight: 600 }}>
              {filtered.length} séquence{filtered.length > 1 ? 's' : ''}
            </span>
          )}
        </div>
        {!loading && labelProfil && (
          <span className="text-xs text-gray-400">{labelProfil}</span>
        )}
      </div>

      {loading && <p className="text-sm text-gray-400 py-4">Chargement…</p>}

      {!loading && sequences.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune séquence sauvegardée.</p>
          <p className="text-xs text-gray-400 mt-1">Générez une séquence depuis Mes outils → Séquence pour la retrouver ici.</p>
        </div>
      )}

      {!loading && sequences.length > 0 && filtered.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune séquence pour {labelProfil}.</p>
          <p className="text-xs text-gray-400 mt-1">Générez votre première séquence depuis Mes outils → Séquence.</p>
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          {filtered.map((s, i) => (
            <div
              key={s.id}
              onMouseEnter={() => setHovered(s.id)}
              onMouseLeave={() => setHovered(null)}
              style={{
                borderBottom: i < filtered.length - 1 ? '1px solid #e5e7eb' : 'none',
                background: hovered === s.id ? '#f8fafc' : 'white',
                transition: 'background 0.15s',
              }}
            >
              {/* Ligne principale */}
              <div className="flex items-start gap-3 px-5 py-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-gray-800">{s.theme}</span>
                    {s.partagee && (
                      <span style={{ fontSize: 11, color: 'var(--bleu)', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 99, padding: '1px 8px', flexShrink: 0 }}>
                        Partagé
                      </span>
                    )}
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
                    <span className="text-xs text-gray-400">· {formatDate(s.created_at)}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0"
                  style={{ opacity: (isMobile || hovered === s.id) ? 1 : 0, transition: 'opacity 0.15s' }}>
                  <button
                    onClick={() => setDetailModal(s)}
                    title="Voir le contenu complet de la séquence générée"
                    style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: '#475569', background: 'none', border: '1px solid #e2e8f0', borderRadius: 6, padding: '4px 10px', cursor: 'pointer' }}
                  >
                    Plus de détails
                  </button>

                  <button
                    onClick={() => !s.partagee ? setAnonymeDialog(s.id) : togglePartage(s.id, false)}
                    disabled={toggling === s.id}
                    title={s.partagee ? 'Retirer de la bibliothèque partagée' : 'Partager cette séquence avec vos collègues'}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 4,
                      background: 'none', border: '1px solid',
                      borderColor: s.partagee ? 'var(--bleu)' : '#e5e7eb',
                      borderRadius: 6, padding: '4px 8px',
                      cursor: toggling === s.id ? 'wait' : 'pointer',
                      color: s.partagee ? 'var(--bleu)' : '#9ca3af',
                      fontSize: 11, fontWeight: s.partagee ? 500 : 400,
                      transition: 'color 0.15s, border-color 0.15s',
                    }}
                  >
                    <IconShare />
                    {s.partagee ? 'Partagé' : 'Partager'}
                  </button>

                  <button
                    onClick={() => onCharger(s)}
                    title="Recharger cette séquence dans le formulaire"
                    className="btn-primary"
                  >
                    Recharger
                  </button>
                  <button
                    onClick={() => setDeleteDialog({ id: s.id, theme: s.theme })}
                    title="Supprimer définitivement cette séquence"
                    style={{ display: 'flex', alignItems: 'center', padding: '5px 8px', background: 'none', border: '1px solid #fca5a5', borderRadius: 6, color: 'var(--bordeaux)', cursor: 'pointer' }}
                  >
                    <IconTrash />
                  </button>
                </div>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* Dialog anonymat */}
      {anonymeDialog && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={() => setAnonymeDialog(null)}
        >
          <div
            style={{ background: '#fff', borderRadius: '10px', padding: '24px 28px', maxWidth: '420px', width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ fontWeight: 700, fontSize: '15px', marginBottom: '8px', color: '#1e293b' }}>
              Comment souhaitez-vous apparaître ?
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '0 0 20px', lineHeight: 1.6 }}>
              Votre séquence sera visible dans <strong>Mon réseau</strong> par vos collègues.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button
                onClick={() => { togglePartage(anonymeDialog, true, false); setAnonymeDialog(null) }}
                title="Votre nom complet sera affiché dans Mon réseau"
                style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '12px 16px', cursor: 'pointer', textAlign: 'left' }}
              >
                <div style={{ fontWeight: 600, fontSize: 13, color: '#1e293b' }}>Afficher mon nom</div>
                <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>{userName}</div>
              </button>
              <button
                onClick={() => { togglePartage(anonymeDialog, true, true); setAnonymeDialog(null) }}
                title="Votre nom ne sera pas affiché — vous apparaîtrez comme Anonyme"
                style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '12px 16px', cursor: 'pointer', textAlign: 'left' }}
              >
                <div style={{ fontWeight: 600, fontSize: 13, color: '#1e293b' }}>Rester anonyme</div>
                <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>Votre séquence sera visible mais votre nom n'apparaîtra pas</div>
              </button>
            </div>
            <div style={{ marginTop: 16, textAlign: 'right' }}>
              <button
                onClick={() => setAnonymeDialog(null)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: 13, cursor: 'pointer' }}
              >
                Annuler
              </button>
            </div>
          </div>
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
            {/* En-tête modale */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '20px 24px 16px', borderBottom: '1px solid #e2e8f0', gap: 12 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 4 }}>
                  {detailModal.theme}
                </div>
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
                    {detailModal.matiere} · {detailModal.niveau} · {formatDate(detailModal.created_at)}
                  </span>
                </div>
              </div>
              <button onClick={() => setDetailModal(null)} title="Fermer"
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 20, lineHeight: 1, padding: '2px 4px', flexShrink: 0 }}>
                ×
              </button>
            </div>

            {/* Corps scrollable */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }}>Séquence générée</div>
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 13, color: '#374151', lineHeight: 1.7, margin: 0, fontFamily: 'inherit' }}>
                {detailModal.resultat}
              </pre>
            </div>

            {/* Pied modale */}
            <div style={{ padding: '14px 24px', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button onClick={() => setDetailModal(null)}
                style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: 6, padding: '8px 18px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
                Fermer
              </button>
              <button onClick={() => { onCharger(detailModal); setDetailModal(null) }}
                title="Recharger cette séquence dans le formulaire"
                className="btn-primary">
                Recharger
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dialog suppression */}
      {deleteDialog && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={() => setDeleteDialog(null)}
        >
          <div
            style={{ background: '#fff', borderRadius: '10px', padding: '24px 28px', maxWidth: '420px', width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ fontWeight: 700, fontSize: '15px', marginBottom: '10px', color: '#1e293b' }}>
              Supprimer cette séquence ?
            </div>
            <p style={{ fontSize: '13.5px', color: '#374151', margin: '0 0 6px', lineHeight: 1.6 }}>
              <strong>"{deleteDialog.theme}"</strong>
            </p>
            <p style={{ fontSize: '13px', color: '#ef4444', margin: '0 0 20px', lineHeight: 1.5 }}>
              Cette action est irréversible — la séquence sera définitivement supprimée.
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setDeleteDialog(null)}
                style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
              >
                Annuler
              </button>
              <button
                onClick={() => supprimerSequence(deleteDialog.id)}
                disabled={deleting === deleteDialog.id}
                title="Confirmer la suppression définitive de cette séquence"
                style={{ background: 'var(--bordeaux)', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: deleting ? 'wait' : 'pointer' }}
              >
                {deleting === deleteDialog.id ? 'Suppression…' : 'Supprimer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {!loading && (
        <p className="text-xs text-gray-400 text-center mt-1">
          Vous enseignez plusieurs matières ?{' '}
          <button
            onClick={() => onNavigate?.('mon-profil')}
            style={{ color: 'var(--bordeaux)', textDecoration: 'underline', background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontSize: 'inherit' }}
          >
            Changez votre matière dans le profil
          </button>{' '}
          pour voir les séquences correspondantes.
        </p>
      )}
    </div>
  )
}
