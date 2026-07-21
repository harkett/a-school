import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

// Fenêtre sur la table `types_activite` (get direct à chaque ouverture). Une action : SUPPRIMER un type
// (bouton poubelle en bout de ligne). Contrôle DELETE côté base (règle 4) : le back refuse si le type est
// encore utilisé (activité sauvegardée / jalon few-shot) ; le front reflète ça en GRISANT le bouton.
// Le PROMPT n'est PAS ici : il est spécifique au couple × type (sur le lien referentiel_types_activite),
// pas sur le catalogue global — donc aucun prompt ne s'affiche ni ne s'édite à ce niveau.
export default function AdminTypesActivite() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  // get : (re)lit la table en base. Rappelé après une suppression — zéro copie, on relit toujours.
  function charger() {
    return fetch('/api/admin/activite-types', { credentials: 'include' })
      .then(r => { if (r.status === 401) { navigate('/admin/login'); return null } return r.json() })
      .then(data => { if (data) setRows(data.types || []) })
  }

  useEffect(() => { charger().finally(() => setLoading(false)) }, [navigate])  // eslint-disable-line react-hooks/exhaustive-deps

  // DELETE encadré : seulement si supprimable (bouton actif), après confirmation. Puis on relit la table.
  async function supprimer(t) {
    if (!t.supprimable) return
    if (!window.confirm(`Supprimer définitivement le type « ${t.label} » ?\nCette action est irréversible.`)) return
    const r = await fetch(`/api/admin/activite-types/${t.id}`, { method: 'DELETE', credentials: 'include' })
    if (r.status === 401) { navigate('/admin/login'); return }
    if (!r.ok) {
      const d = await r.json().catch(() => ({}))
      window.alert(d.detail || 'Suppression impossible.')
      await charger()   // on resynchronise l'état réel (ex. quelqu'un l'a utilisé entre-temps)
      return
    }
    await charger()
  }

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  const th = { padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }
  const td = { padding: '10px 16px', color: '#1e293b' }

  return (
    <div>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">Type d'activité d'un couple</h2>
        <span className="text-xs text-gray-400">{rows.length} type{rows.length > 1 ? 's' : ''}</span>
      </div>

      <p className="text-xs text-gray-500 mb-3" style={{ maxWidth: 720, lineHeight: 1.5 }}>
        Contenu de la table <code>types_activite</code>, lu directement en base. La poubelle supprime un type
        <b> jamais utilisé</b> ; elle est grisée dès qu'une activité ou un jalon s'en sert.
      </p>

      {rows.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}><p className="text-sm">La table est vide.</p></div>
      ) : (
        <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                <th style={th}>id</th>
                <th style={th}>Libellé</th>
                <th style={th}>Clé</th>
                <th style={th}>Défaut</th>
                <th style={th}>Actif</th>
                <th style={th}>Ordre</th>
                <th style={{ ...th, textAlign: 'center' }}>Suppr.</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((t, i) => (
                <tr key={t.id} style={{ borderBottom: i < rows.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                  <td style={{ ...td, color: '#94a3b8', fontFamily: 'monospace' }}>{t.id}</td>
                  <td style={{ ...td, fontWeight: 600 }}>{t.label}</td>
                  <td style={{ ...td, fontFamily: 'monospace', color: '#64748b' }}>{t.key}</td>
                  <td style={td}>{t.is_default ? 'oui' : ''}</td>
                  <td style={td}>{t.actif ? 'oui' : 'non'}</td>
                  <td style={td}>{t.ordre}</td>
                  <td style={{ ...td, textAlign: 'center' }}>
                    <button
                      onClick={() => supprimer(t)}
                      disabled={!t.supprimable}
                      title={t.supprimable
                        ? `Supprimer le type « ${t.label} »`
                        : `Utilisé par ${t.usage} activité(s)/jalon(s) — suppression impossible`}
                      style={{
                        height: 30, width: 30, borderRadius: 8, border: '1px solid ' + (t.supprimable ? '#fecaca' : '#e2e8f0'),
                        background: t.supprimable ? '#fef2f2' : '#f8fafc',
                        color: t.supprimable ? '#dc2626' : '#cbd5e1',
                        cursor: t.supprimable ? 'pointer' : 'not-allowed',
                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 15, lineHeight: 1,
                      }}
                    >🗑</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
