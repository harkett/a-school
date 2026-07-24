import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

// LA page « Contenu » : tout le contenu pédagogique dans UN SEUL tableau qui se déroule —
// cycle → niveau (le couple) → référentiel, matières, types d'activité (et leurs précisions).
// Remplace les trois anciennes fenêtres à plat (Cycles / Matières / Types d'activité) : ici on
// voit QUI est rattaché À QUOI, pas des listes déconnectées. Lecture seule stricte : un seul
// get (/api/admin/contenu) qui lit les vraies tables ; pour AGIR on va dans Référentiel ou
// Programmes — cette page regarde, elle ne touche à rien.

// Badge d'origine d'un type — même vérité que sur l'écran Référentiel : le lien dit qui l'a
// posé (source), le catalogue dit d'où vient le type (origine).
function BadgeType({ source, origine }) {
  const b = source === 'ia'
    ? (origine === 'ia'
        ? { texte: 'IA', bg: '#f3e8ff', fg: '#7e22ce' }
        : { texte: 'SYSTÈME · IA', bg: '#e0f2fe', fg: '#0369a1' })
    : source === 'admin'
      ? { texte: 'ADMIN', bg: '#e0e7ff', fg: '#4338ca' }
      : { texte: 'SYSTÈME', bg: '#f1f5f9', fg: '#64748b' }
  return (
    <span style={{ marginLeft: 8, padding: '1px 7px', borderRadius: 4, fontSize: 10, fontWeight: 600, background: b.bg, color: b.fg, whiteSpace: 'nowrap' }}>
      {b.texte}
    </span>
  )
}

// Pastille d'état compacte (référentiel : PDF, épuré, découpe…).
function Etat({ ok, texte }) {
  return (
    <span style={{
      padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap',
      background: ok ? '#dcfce7' : '#f1f5f9', color: ok ? '#16a34a' : '#94a3b8',
    }}>{texte}</span>
  )
}

const CHEVRON = (ouvert) => (
  <span aria-hidden="true" style={{
    display: 'inline-block', width: 14, fontSize: 10, color: '#94a3b8',
    transform: ouvert ? 'rotate(90deg)' : 'none', transition: 'transform 0.12s',
  }}>▶</span>
)

export default function AdminContenu() {
  const [cycles, setCycles] = useState([])
  const [loading, setLoading] = useState(true)
  const [nivOuverts, setNivOuverts] = useState(() => new Set())      // niveaux dépliés
  const [typesOuverts, setTypesOuverts] = useState(() => new Set())  // `${niveauId}|${typeId}` → précisions dépliées
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/admin/contenu', { credentials: 'include' })
      .then(r => { if (r.status === 401) { navigate('/admin/login'); return null } return r.json() })
      .then(data => { if (data) setCycles(data.cycles || []) })
      .finally(() => setLoading(false))
  }, [navigate])

  function basculerNiveau(id) {
    setNivOuverts(prev => {
      const s = new Set(prev)
      if (s.has(id)) s.delete(id); else s.add(id)
      return s
    })
  }
  function basculerType(cle) {
    setTypesOuverts(prev => {
      const s = new Set(prev)
      if (s.has(cle)) s.delete(cle); else s.add(cle)
      return s
    })
  }

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  const nbNiveaux = cycles.reduce((n, c) => n + c.niveaux.length, 0)

  return (
    <div>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">Contenu</h2>
        <span className="text-xs text-gray-400">
          {cycles.length} cycle{cycles.length > 1 ? 's' : ''} · {nbNiveaux} niveau{nbNiveaux > 1 ? 'x' : ''}
        </span>
      </div>

      <p className="text-xs text-gray-500 mb-3" style={{ maxWidth: 760, lineHeight: 1.5 }}>
        Tout le contenu pédagogique, lu en direct dans la base : chaque cycle déroule ses niveaux, et
        chaque niveau montre son référentiel, ses matières et ses types d'activité (cliquez un niveau
        pour le déplier, un type pour ses précisions). Lecture seule — pour agir, passez par
        les écrans <b>Référentiel</b> et <b>Programmes</b>.
      </p>

      {cycles.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}><p className="text-sm">Aucun cycle en base.</p></div>
      ) : (
        <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <tbody>
              {cycles.map(cycle => (
                <CycleBloc
                  key={cycle.id}
                  cycle={cycle}
                  nivOuverts={nivOuverts}
                  typesOuverts={typesOuverts}
                  basculerNiveau={basculerNiveau}
                  basculerType={basculerType}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function CycleBloc({ cycle, nivOuverts, typesOuverts, basculerNiveau, basculerType }) {
  return (
    <>
      {/* ─ Ligne CYCLE ─ */}
      <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
        <td colSpan={2} style={{ padding: '10px 16px' }}>
          <span style={{ fontWeight: 700, color: '#1e293b', fontSize: 13.5 }}>{cycle.nom}</span>
          <span style={{ marginLeft: 10, fontSize: 11, color: '#94a3b8' }}>
            {cycle.niveaux.length} niveau{cycle.niveaux.length > 1 ? 'x' : ''}
          </span>
        </td>
      </tr>

      {cycle.niveaux.length === 0 && (
        <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
          <td colSpan={2} style={{ padding: '8px 16px 8px 40px', color: '#94a3b8', fontSize: 12.5 }}>
            Aucun niveau dans ce cycle.
          </td>
        </tr>
      )}

      {cycle.niveaux.map(niveau => {
        const ouvert = nivOuverts.has(niveau.id)
        const ref = niveau.referentiel
        return (
          <NiveauBloc
            key={niveau.id}
            niveau={niveau}
            ref_={ref}
            ouvert={ouvert}
            typesOuverts={typesOuverts}
            basculerNiveau={basculerNiveau}
            basculerType={basculerType}
          />
        )
      })}
    </>
  )
}

function NiveauBloc({ niveau, ref_, ouvert, typesOuverts, basculerNiveau, basculerType }) {
  return (
    <>
      {/* ─ Ligne NIVEAU (cliquable) ─ */}
      <tr
        onClick={() => basculerNiveau(niveau.id)}
        style={{ borderBottom: '1px solid #f1f5f9', cursor: 'pointer', background: ouvert ? '#fcfdff' : 'white' }}
      >
        <td style={{ padding: '9px 16px 9px 28px', whiteSpace: 'nowrap' }}>
          {CHEVRON(ouvert)}
          <span style={{ fontWeight: 600, color: '#1e293b', marginLeft: 4 }}>{niveau.nom}</span>
        </td>
        <td style={{ padding: '9px 16px', textAlign: 'right' }}>
          {ref_ === null ? (
            <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, background: '#fef3c7', color: '#b45309', whiteSpace: 'nowrap' }}>
              vide — à remplir
            </span>
          ) : (
            <span style={{ display: 'inline-flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <Etat ok texte="PDF déposé" />
              <Etat ok={ref_.epure} texte={ref_.epure ? 'texte épuré' : 'épuré manquant'} />
              <Etat ok={ref_.decoupe_valide} texte={ref_.decoupe_valide ? 'découpe validée' : 'découpe en cours'} />
              <span style={{ fontSize: 11, color: '#64748b', alignSelf: 'center', whiteSpace: 'nowrap' }}>
                {ref_.nb_unites} unité{ref_.nb_unites > 1 ? 's' : ''} · {niveau.matieres.length} matière{niveau.matieres.length > 1 ? 's' : ''} · {niveau.types.length} type{niveau.types.length > 1 ? 's' : ''}
              </span>
            </span>
          )}
        </td>
      </tr>

      {/* ─ Détail du niveau (déplié) ─ */}
      {ouvert && (
        <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
          <td colSpan={2} style={{ padding: '4px 16px 14px 52px', background: '#fcfdff' }}>

            {/* Provenance du référentiel */}
            {ref_ !== null && (ref_.source || ref_.date_doc) && (
              <p style={{ margin: '8px 0 0', fontSize: 11.5, color: '#94a3b8' }}>
                {ref_.source ? <>Source : {ref_.source}</> : null}
                {ref_.source && ref_.date_doc ? ' · ' : null}
                {ref_.date_doc ? <>Document daté : {ref_.date_doc}</> : null}
              </p>
            )}

            {/* Matières du couple */}
            <p style={{ margin: '12px 0 6px', fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Matières ({niveau.matieres.length})
            </p>
            {niveau.matieres.length === 0 ? (
              <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>Aucune matière au programme de ce niveau.</p>
            ) : (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {niveau.matieres.map(m => (
                  <span key={`${m.id}-${m.variante}`} style={{ padding: '3px 10px', borderRadius: 6, fontSize: 12, background: '#f1f5f9', color: '#334155', border: '1px solid #e2e8f0' }}>
                    {m.nom}{m.variante ? ` (${m.variante})` : ''}
                  </span>
                ))}
              </div>
            )}

            {/* Types d'activité du couple */}
            <p style={{ margin: '14px 0 6px', fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Types d'activité ({niveau.types.length})
            </p>
            {ref_ === null ? (
              <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>Pas encore de référentiel : aucun type rattaché.</p>
            ) : niveau.types.length === 0 ? (
              <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>Aucun type rattaché à ce couple pour le moment.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {niveau.types.map(t => {
                  const cle = `${niveau.id}|${t.id}`
                  const tOuvert = typesOuverts.has(cle)
                  return (
                    <div key={t.id}>
                      <button
                        onClick={() => basculerType(cle)}
                        style={{
                          display: 'inline-flex', alignItems: 'center', cursor: 'pointer',
                          border: 'none', background: 'none', padding: '3px 0', fontSize: 12.5,
                          color: '#1e293b', textAlign: 'left',
                        }}
                      >
                        {CHEVRON(tOuvert)}
                        <span style={{ fontWeight: 500, marginLeft: 4 }}>{t.label}</span>
                        <BadgeType source={t.source} origine={t.origine} />
                        <span style={{ marginLeft: 8, fontSize: 11, color: '#94a3b8' }}>
                          {t.precisions.length} précision{t.precisions.length > 1 ? 's' : ''}
                        </span>
                      </button>
                      {tOuvert && (
                        t.precisions.length === 0 ? (
                          <p style={{ margin: '2px 0 4px 34px', fontSize: 12, color: '#94a3b8' }}>Aucune précision pour ce type sur ce couple.</p>
                        ) : (
                          <ul style={{ margin: '2px 0 4px 34px', padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {t.precisions.map((p, i) => (
                              <li key={i} style={{ fontSize: 12, color: '#475569' }}>· {p}</li>
                            ))}
                          </ul>
                        )
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  )
}
