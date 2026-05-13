import { useState, useEffect } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

const IconTrash = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
    <path d="M10 11v6"/><path d="M14 11v6"/>
    <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
  </svg>
)

const IconShare = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
  </svg>
)


function StatsCommunaute({ matiere, niveau }) {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    if (!matiere && !niveau) return
    const params = new URLSearchParams()
    if (matiere) params.append('matiere', matiere)
    if (niveau)  params.append('niveau', niveau)
    fetch(`/api/stats/matiere?${params}`, { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setStats(d) })
      .catch(() => {})
  }, [matiere, niveau])

  if (!stats || stats.total_plateforme === 0) return null

  return (
    <div style={{
      background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
      padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
    }}>
      <div style={{ display: 'flex', flex: 1, gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <div>
          <span style={{ fontSize: 11, color: '#94a3b8', display: 'block' }}>Sur la plateforme</span>
          <span style={{ fontSize: 15, fontWeight: 700, color: '#1e293b' }}>{stats.total_plateforme}</span>
          <span style={{ fontSize: 11, color: '#64748b' }}> activités · {stats.nb_profs} prof{stats.nb_profs > 1 ? 's' : ''}</span>
        </div>
        {stats.top_types.length > 0 && (
          <div>
            <span style={{ fontSize: 11, color: '#94a3b8', display: 'block' }}>Types populaires</span>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 2 }}>
              {stats.top_types.map(t => (
                <span key={t.label} style={{
                  fontSize: 11, background: 'white', border: '1px solid #e2e8f0',
                  borderRadius: 99, padding: '1px 8px', color: '#475569',
                }}>
                  {t.label} <strong style={{ color: '#A63045' }}>×{t.nb}</strong>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function MesActivites({ onCharger, sessionMatiere, sessionNiveau, onNavigate, userName }) {
  const isMobile = window.innerWidth < 768
  const [activites, setActivites] = useState([])
  const [loading, setLoading]     = useState(true)
  const [hovered, setHovered]     = useState(null)
  const [toggling, setToggling]         = useState(null)
  const [detailModal, setDetailModal]   = useState(null)
  const [anonymeDialog, setAnonymeDialog] = useState(null)
  const [deleteDialog, setDeleteDialog] = useState(null)
  const [deleting, setDeleting]     = useState(null)

  useEffect(() => {
    fetch('/api/mes-activites', { credentials: 'include' })
      .then(r => r.json())
      .then(data => { setActivites(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  async function supprimerActivite(id) {
    setDeleting(id)
    try {
      const res = await fetchWithTimeout(`/api/mes-activites/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      }, TIMEOUT_STD)
      if (res.ok) {
        setActivites(prev => prev.filter(a => a.id !== id))
        if (detailModal?.id === id) setDetailModal(null)
      }
    } finally {
      setDeleting(null)
      setDeleteDialog(null)
    }
  }

  async function togglePartage(id, newValue, anonyme = false) {
    setToggling(id)
    try {
      const res = await fetchWithTimeout(`/api/mes-activites/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ partagee: newValue, anonyme }),
      })
      if (res.ok) {
        setActivites(prev => prev.map(a => a.id === id ? { ...a, partagee: newValue } : a))
      }
    } finally {
      setToggling(null)
    }
  }

  const filtered = activites.filter(a => {
    if (sessionMatiere && a.matiere !== sessionMatiere) return false
    if (sessionNiveau  && a.niveau  !== sessionNiveau)  return false
    return true
  })

  const labelProfil = [sessionMatiere, sessionNiveau].filter(Boolean).join(', ')

  return (
    <div className="flex flex-col gap-3 w-full">

      {/* En-tête */}
      <div className="flex flex-col gap-1">
        <div className="flex items-baseline gap-3">
          <h2 className="text-base font-semibold text-gray-800">Mes activités</h2>
          {!loading && filtered.length > 0 && (
            <span style={{ fontSize: 12, color: 'var(--bordeaux)', background: '#fdf2f5', border: '1px solid #f4c4ce', borderRadius: 99, padding: '1px 10px', fontWeight: 600 }}>
              {filtered.length} activité{filtered.length > 1 ? 's' : ''} créée{filtered.length > 1 ? 's' : ''}
            </span>
          )}
        </div>
        {!loading && labelProfil && (
          <span className="text-xs text-gray-400">
            {labelProfil}
          </span>
        )}
      </div>

      {/* Widget stats communauté */}
      {!loading && <StatsCommunaute matiere={sessionMatiere} niveau={sessionNiveau} />}

      {loading && (
        <p className="text-sm text-gray-400 py-4">Chargement…</p>
      )}

      {!loading && activites.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune activité sauvegardée.</p>
          <p className="text-xs text-gray-400 mt-1">Générez une activité depuis l'Accueil pour la retrouver ici.</p>
        </div>
      )}

      {!loading && activites.length > 0 && filtered.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune activité pour {labelProfil}.</p>
          <p className="text-xs text-gray-400 mt-1">Générez votre première activité depuis l'Accueil.</p>
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          {filtered.map((a, i) => (
            <div
              key={a.id}
              onMouseEnter={() => setHovered(a.id)}
              onMouseLeave={() => setHovered(null)}
              style={{
                borderBottom: i < filtered.length - 1 ? '1px solid #e5e7eb' : 'none',
                background: hovered === a.id ? '#f3f4f6' : 'white',
                transition: 'background 0.15s',
              }}
            >
              <div className="flex items-center gap-3 px-5 py-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-gray-800 truncate">
                      {a.objet || a.activite_label}
                    </span>
                    {a.partagee && (
                      <span style={{ fontSize: 11, color: 'var(--bleu)', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 99, padding: '1px 8px', flexShrink: 0 }}>
                        Partagé
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 flex-wrap mt-0.5">
                    <span className="text-xs text-gray-400">{a.activite_label}</span>
                    <span className="text-xs text-gray-400">· {a.niveau}</span>
                    {a.sous_type && <span className="text-xs text-gray-400">· {a.sous_type}</span>}
                    {a.nb && <span className="text-xs text-gray-400">· {a.nb} questions</span>}
                    <span className="text-xs text-gray-400">
                      · {a.avec_correction ? 'Avec correction' : 'Sans correction'}
                    </span>
                  </div>
                  {!a.objet && (
                    <p className="text-xs text-gray-400 mt-0.5 truncate italic">{a.apercu}</p>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0"
                  style={{ opacity: (isMobile || hovered === a.id) ? 1 : 0, transition: 'opacity 0.15s' }}>
                  <button
                    onClick={() => setDetailModal(a)}
                    title="Voir le texte source et le résultat complet de l'activité"
                    style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: '#475569', background: 'none', border: '1px solid #e2e8f0', borderRadius: 6, padding: '4px 10px', cursor: 'pointer' }}
                  >
                    Plus de détails
                  </button>

                  <button
                    onClick={() => !a.partagee ? setAnonymeDialog(a.id) : togglePartage(a.id, false)}
                    disabled={toggling === a.id}
                    title={a.partagee ? 'Retirer de la bibliothèque partagée' : 'Partager cette activité avec vos collègues'}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 4,
                      background: 'none', border: '1px solid',
                      borderColor: a.partagee ? 'var(--bleu)' : '#e5e7eb',
                      borderRadius: 6, padding: '4px 8px',
                      cursor: toggling === a.id ? 'wait' : 'pointer',
                      color: a.partagee ? 'var(--bleu)' : '#9ca3af',
                      fontSize: 11, fontWeight: a.partagee ? 500 : 400,
                      transition: 'color 0.15s, border-color 0.15s',
                    }}
                  >
                    <IconShare />
                    {a.partagee ? 'Partagé' : 'Partager'}
                  </button>

                  <button
                    onClick={() => onCharger(a)}
                    title="Reprendre cette activité dans le formulaire"
                    className="btn-primary shrink-0"
                  >
                    Reprendre
                  </button>

                  <button
                    onClick={() => setDeleteDialog({ id: a.id, label: a.objet || a.activite_label })}
                    title="Supprimer définitivement cette activité"
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
              Votre activité sera visible dans <strong>Mon réseau</strong> par vos collègues.
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
                <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>Votre activité sera visible mais votre nom n'apparaîtra pas</div>
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
              Supprimer cette activité ?
            </div>
            <p style={{ fontSize: '13.5px', color: '#374151', margin: '0 0 6px', lineHeight: 1.6 }}>
              <strong>"{deleteDialog.label}"</strong>
            </p>
            <p style={{ fontSize: '13px', color: '#ef4444', margin: '0 0 20px', lineHeight: 1.5 }}>
              Cette action est irréversible — l'activité sera définitivement supprimée.
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setDeleteDialog(null)}
                style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
              >
                Annuler
              </button>
              <button
                onClick={() => supprimerActivite(deleteDialog.id)}
                disabled={deleting === deleteDialog.id}
                title="Confirmer la suppression définitive de cette activité"
                style={{ background: 'var(--bordeaux)', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: deleting ? 'wait' : 'pointer' }}
              >
                {deleting === deleteDialog.id ? 'Suppression…' : 'Supprimer'}
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
                  {detailModal.objet || detailModal.activite_label}
                </div>
                <div style={{ fontSize: 12, color: '#94a3b8' }}>
                  {detailModal.activite_label} · {detailModal.niveau}
                  {detailModal.sous_type ? ` · ${detailModal.sous_type}` : ''}
                  {detailModal.nb ? ` · ${detailModal.nb} questions` : ''}
                  {` · ${detailModal.avec_correction ? 'Avec correction' : 'Sans correction'}`}
                </div>
              </div>
              <button onClick={() => setDetailModal(null)} title="Fermer"
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 20, lineHeight: 1, padding: '2px 4px', flexShrink: 0 }}>
                ×
              </button>
            </div>

            {/* Corps scrollable */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
              {detailModal.texte_source && detailModal.texte_source.trim().length > 0 && (
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }}>Texte source</div>
                  <p style={{ fontSize: 13, color: '#64748b', fontStyle: 'italic', lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, padding: '10px 14px' }}>
                    {detailModal.texte_source}
                  </p>
                </div>
              )}
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }}>Résultat généré</div>
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 13, color: '#374151', lineHeight: 1.7, margin: 0, fontFamily: 'inherit' }}>
                  {detailModal.resultat}
                </pre>
              </div>
            </div>

            {/* Pied modale */}
            <div style={{ padding: '14px 24px', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button onClick={() => setDetailModal(null)}
                style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: 6, padding: '8px 18px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
                Fermer
              </button>
              <button onClick={() => { onCharger(detailModal); setDetailModal(null) }}
                title="Reprendre cette activité dans le formulaire"
                className="btn-primary">
                Reprendre
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
          pour voir les activités correspondantes.
        </p>
      )}
    </div>
  )
}
