import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

// Consulter les référentiels — LECTURE SEULE. Deux panneaux :
//  - à gauche, le menu des couples DÉJÀ déposés (Cycle · Niveau, groupés par famille), bulle d'aide au survol ;
//  - à droite, le détail du couple choisi : le même écran que la page de travail, mais en consultation
//    (PDF, source, forçage, matières, prompt de découpe). Tout est lu en base (get, zéro copie) via les
//    endpoints existants : /referentiels/liste, /etat, /prompt-decoupe, /referentiels/pdf.
export default function AdminReferentielsConsulter() {
  const [refs, setRefs] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)     // la ligne du référentiel choisi (liste)
  const [etat, setEtat] = useState(null)             // { referentiel:{fichier,source,date_doc,forcage_motif}, matieres:[] }
  const [prompt, setPrompt] = useState(null)         // { existe, prompt, valide }
  const [detailLoading, setDetailLoading] = useState(false)
  const [showPdf, setShowPdf] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/referentiels/liste', { credentials: 'include' })
      .then(r => { if (r.status === 401) { navigate('/admin/login'); return null } return r.json() })
      .then(data => { if (data) setRefs(data.referentiels || []) })
      .finally(() => setLoading(false))
  }, [navigate])

  // Charge le détail du couple choisi (etat + prompt de découpe), en lecture seule.
  function ouvrir(ref) {
    setSelected(ref); setEtat(null); setPrompt(null); setShowPdf(false); setDetailLoading(true)
    const q = `cycle_id=${ref.cycle_id}&niveau=${encodeURIComponent(ref.niveau)}`
    Promise.all([
      fetch(`/api/admin/referentiels/etat?${q}`, { credentials: 'include' }).then(r => (r.ok ? r.json() : null)).catch(() => null),
      fetch(`/api/admin/referentiels/prompt-decoupe?${q}`, { credentials: 'include' }).then(r => (r.ok ? r.json() : null)).catch(() => null),
    ]).then(([e, p]) => { setEtat(e); setPrompt(p) }).finally(() => setDetailLoading(false))
  }

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  const carte = { background: 'white', borderRadius: 12, border: '1px solid #e2e8f0', padding: 16 }
  const titreCarte = { fontSize: 14, fontWeight: 700, color: '#1e293b', marginBottom: 10 }
  const infoLabel = { color: '#94a3b8' }
  const infoVal = { color: '#1e293b', fontWeight: 600 }

  return (
    <div>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">Consulter les référentiels</h2>
        <span className="text-xs text-gray-400">{refs.length} référentiel{refs.length > 1 ? 's' : ''}</span>
      </div>

      <p className="text-xs text-gray-500 mb-3" style={{ maxWidth: 720, lineHeight: 1.5 }}>
        Les référentiels déjà déposés, en lecture seule. Choisissez un couple à gauche pour voir son détail à droite.
      </p>

      {refs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
          <p className="text-sm">Aucun référentiel déposé pour le moment.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>

          {/* Menu de gauche : la liste directe des couples déposés (Cycle · Niveau), bulle d'aide au survol. */}
          <div style={{ width: 280, flexShrink: 0, background: 'white', borderRadius: 12,
            border: '1px solid #e2e8f0', overflow: 'hidden' }}>
            {refs.map(r => {
              const actif = selected && selected.id === r.id
              return (
                <button key={r.id} type="button" onClick={() => ouvrir(r)}
                  title={`Famille : ${r.famille || '—'} · Cycle : ${r.cycle} · Niveau : ${r.niveau}. Cliquez pour consulter le détail (lecture seule).`}
                  style={{ display: 'block', width: '100%', textAlign: 'left', padding: '9px 12px',
                    border: 'none', borderBottom: '1px solid #f1f5f9', cursor: 'pointer', fontSize: 13,
                    background: actif ? '#eff6ff' : '#fff', color: actif ? '#1d4ed8' : '#1e293b',
                    fontWeight: actif ? 600 : 400 }}>
                  {r.cycle} · {r.niveau}
                  {r.forcage_motif && <span title="Validé en forçage" style={{ marginLeft: 6, color: '#b45309' }}>⚠</span>}
                </button>
              )
            })}
          </div>

          {/* Détail à droite : lecture seule. */}
          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>
            {!selected ? (
              <div style={{ ...carte, color: '#94a3b8', textAlign: 'center', padding: '3rem' }}>
                Choisissez un couple dans le menu de gauche.
              </div>
            ) : detailLoading ? (
              <div style={{ ...carte, color: '#94a3b8' }}>Chargement du détail…</div>
            ) : (
              <>
                {/* Couple */}
                <div style={carte}>
                  <div style={titreCarte}>Famille-Couple</div>
                  <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', fontSize: 13 }}>
                    <span><span style={infoLabel}>Famille : </span><strong style={infoVal}>{selected.famille || '—'}</strong></span>
                    <span><span style={infoLabel}>Cycle : </span><strong style={infoVal}>{selected.cycle}</strong></span>
                    <span><span style={infoLabel}>Niveau : </span><strong style={infoVal}>{selected.niveau}</strong></span>
                  </div>
                </div>

                {/* Référentiel PDF + source + forçage */}
                <div style={carte}>
                  <div style={titreCarte}>Référentiel au format PDF</div>
                  <div style={{ fontSize: 13, color: '#1e293b' }}>
                    <span style={infoLabel}>Fichier d’origine : </span>
                    <strong>{etat?.referentiel?.fichier || selected.fichier}</strong>{' '}
                    <button type="button" onClick={() => setShowPdf(true)}
                      title="Ouvrir le PDF du référentiel pour le relire"
                      style={{ marginLeft: 8, background: 'none', border: 'none', padding: 0, color: '#1d4ed8',
                        fontSize: 13, fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}>
                      Voir le référentiel
                    </button>
                  </div>
                  <div style={{ fontSize: 13, color: '#475569', marginTop: 6 }}>
                    <span style={infoLabel}>Source : </span>{etat?.referentiel?.source || '—'}
                    {etat?.referentiel?.date_doc ? <> · <span style={infoLabel}>Date : </span>{etat.referentiel.date_doc}</> : null}
                  </div>
                  {etat?.referentiel?.forcage_motif && (
                    <div style={{ marginTop: 8, padding: '10px 12px', borderRadius: 8,
                      background: '#fffbeb', border: '1px solid #fde68a', fontSize: 12, color: '#92400e' }}>
                      <strong>⚠ Validé en forçage</strong> — motif : {etat.referentiel.forcage_motif}
                    </div>
                  )}
                  {/* Verdict IA du couple figé à la validation (referentiels.verif_couple via /etat).
                      Lecture seule, JSON parsé à l'affichage — zéro copie. */}
                  {etat?.referentiel?.verif_couple && (() => {
                    let v = null
                    try { v = JSON.parse(etat.referentiel.verif_couple) } catch { v = null }
                    if (!v) return null
                    // Libellé du couple + famille : lus dans la ligne du référentiel choisi (liste),
                    // jamais recopiés. Affichage identique à l'écran de création (zéro copie).
                    return (
                      <div style={{ marginTop: 8, padding: '10px 12px', borderRadius: 8, fontSize: 12,
                        background: v.correspond ? '#f0fdf4' : '#fef2f2',
                        border: `1px solid ${v.correspond ? '#bbf7d0' : '#fecaca'}`,
                        color: v.correspond ? '#166534' : '#991b1b' }}>
                        <strong>{v.correspond
                          ? `✓ Couple : ${selected.cycle} / ${selected.niveau} — confirmé par le document`
                          : `✗ Couple : ${selected.cycle} / ${selected.niveau} — non confirmé par le document`}</strong>
                        {v.niveau_lu ? <div style={{ color: '#475569', marginTop: 2 }}>niveau lu : {v.niveau_lu}</div> : null}
                        {v.raison && <div style={{ color: '#475569', marginTop: 2 }}>{v.raison}</div>}
                        {selected.famille && <div style={{ color: '#166534', marginTop: 4 }}>✓ Cette famille ({selected.famille}) a sa place à ce niveau</div>}
                      </div>
                    )
                  })()}
                </div>

                {/* Matières */}
                <div style={carte}>
                  <div style={titreCarte}>
                    Matières de ce référentiel
                    <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 6 }}>
                      ({(etat?.matieres || []).length})
                    </span>
                  </div>
                  {(etat?.matieres || []).length === 0 ? (
                    <div style={{ fontSize: 13, color: '#94a3b8' }}>Aucune matière enregistrée pour ce niveau.</div>
                  ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {etat.matieres.map(m => (
                        <span key={m.id} style={{ fontSize: 12, fontWeight: 600, padding: '3px 10px',
                          borderRadius: 6, background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0' }}>
                          {m.nom}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Prompt de découpe (lecture seule) */}
                <div style={carte}>
                  <div style={titreCarte}>
                    Prompt de découpe
                    {prompt?.existe && (
                      <span style={{ marginLeft: 8, fontSize: 12, fontWeight: 600,
                        color: prompt.valide ? '#166534' : '#b45309' }}>
                        {prompt.valide ? '· validé' : '· à valider'}
                      </span>
                    )}
                  </div>
                  {prompt?.existe && prompt.prompt ? (
                    <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: 12, padding: 10, color: '#334155',
                      background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, whiteSpace: 'pre-wrap',
                      maxHeight: 260, overflow: 'auto' }}>{prompt.prompt}</pre>
                  ) : (
                    <div style={{ fontSize: 13, color: '#94a3b8' }}>Aucun prompt de découpe généré pour ce couple.</div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Fenêtre de relecture du PDF (réutilise l'endpoint /referentiels/pdf). */}
      {showPdf && selected && (
        <div onClick={() => setShowPdf(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                {etat?.referentiel?.fichier || selected.fichier}
              </span>
              <button type="button" onClick={() => setShowPdf(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <iframe title="Référentiel PDF"
              src={`/api/admin/referentiels/pdf?cycle_id=${selected.cycle_id}&niveau=${encodeURIComponent(selected.niveau)}`}
              style={{ flex: 1, width: '100%', border: 'none' }} />
          </div>
        </div>
      )}
    </div>
  )
}
