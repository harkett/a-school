import { useEffect, useState } from 'react'
import { showError } from '../errorDialog'

// Écran « Paramètres » — LECTURE SEULE. La table `settings` (clé / valeur) lue
// depuis la base et affichée. On montre le LIBELLÉ lisible (jamais le code technique) quand la
// clé pointe vers un catalogue ; une valeur longue est tronquée + « Voir » (modale) ; un
// paramètre qui pointe vers une table a un « Détails » qui montre la ligne pointée réelle.
// Cet écran ne modifie rien : changer une valeur passe par un autre moyen (un secret se change
// dans le .env, jamais dans l'UI).

const SEUIL = 80  // au-delà, la valeur est tronquée dans la cellule (le tout va dans la modale)

// Libellés français des colonnes des lignes pointées (ai_fournisseurs / ai_modeles).
const CHAMP_FR = {
  code: 'Code', label: 'Libellé', cle_env: 'Variable de clé', actif: 'Actif',
  fournisseur: 'Fournisseur', modele: 'Modèle', recommande: 'Recommandé', ordre: 'Ordre',
}

export default function AdminParametres() {
  const [params, setParams] = useState([])   // [{ key, value, label, ecran_dedie, pointe_vers }]
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null)    // { titre, texte } | { titre, details } | null

  async function charger() {
    setLoading(true)
    try {
      const res = await fetch('/api/admin/parametres', { credentials: 'include' })
      const data = await res.json()
      setParams(Array.isArray(data) ? data : [])
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { charger() }, [])

  const cellStyle = { padding: '8px', color: '#374151', wordBreak: 'break-word' }
  const btnVoir = {
    marginLeft: 8, border: '1px solid #D1D5DB', background: '#F9FAFB', borderRadius: 6,
    padding: '2px 10px', fontSize: 12, cursor: 'pointer', color: '#374151', whiteSpace: 'nowrap',
  }

  function fmt(v) {
    if (typeof v === 'boolean') return v ? 'oui' : 'non'
    return String(v)
  }

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <h2 className="text-sm font-semibold text-gray-700 mb-1">Paramètres</h2>
        <p className="text-xs text-gray-400">
          Table des paramètres du projet (clé / valeur), en lecture seule.
          Cet écran affiche ce qui est en base ; il ne modifie rien. Un secret se change dans le
          fichier <code>.env</code> du serveur, jamais ici.
        </p>
      </div>

      {loading && <p className="text-xs text-gray-400">Chargement…</p>}

      {!loading && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: '#6B7280', fontSize: 12 }}>
                <th style={{ padding: '6px 8px', width: '30%' }}>Clé</th>
                <th style={{ padding: '6px 8px', width: '70%' }}>Valeur</th>
              </tr>
            </thead>
            <tbody>
              {params.length === 0 && (
                <tr><td colSpan={2} style={{ padding: '10px 8px', color: '#9CA3AF' }}>Aucun paramètre en base.</td></tr>
              )}
              {params.map(p => {
                // On affiche le LIBELLÉ si la clé pointe vers un catalogue, sinon la valeur brute.
                const affiche = p.label || p.value || ''
                const tropLong = affiche.length > SEUIL
                return (
                  <tr key={p.key} style={{ borderTop: '1px solid #F1F5F9', verticalAlign: 'top' }}>
                    <td style={cellStyle}>
                      <div style={{ fontWeight: 600 }}>{p.key}</div>
                      {p.ecran_dedie && (
                        <div style={{ color: '#6B7280', fontSize: 11, marginTop: 4, fontStyle: 'italic' }}>
                          Réglé sur son écran dédié.
                        </div>
                      )}
                    </td>
                    <td style={cellStyle}>
                      <span>{tropLong ? affiche.slice(0, SEUIL) + '…' : affiche}</span>
                      {tropLong && (
                        <button style={btnVoir} title="Voir la valeur entière"
                                onClick={() => setModal({ titre: p.key, texte: p.value || '' })}>
                          Voir
                        </button>
                      )}
                      {p.pointe_vers && (
                        <button style={btnVoir} title="Voir la ligne pointée en base"
                                onClick={() => setModal({ titre: p.key, details: p.pointe_vers })}>
                          Détails
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modale — valeur longue en entier, OU ligne pointée réelle */}
      {modal && (
        <div
          onClick={() => setModal(null)}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 1000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: 'white', borderRadius: 10, maxWidth: 720, width: '100%',
              maxHeight: '80vh', display: 'flex', flexDirection: 'column', overflow: 'hidden',
              boxShadow: '0 10px 40px rgba(0,0,0,0.25)',
            }}
          >
            <div style={{ padding: '14px 18px', borderBottom: '1px solid #F1F5F9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong style={{ fontSize: 14, color: '#374151' }}>{modal.titre}</strong>
              <button onClick={() => setModal(null)} title="Fermer"
                      style={{ border: 'none', background: 'transparent', fontSize: 20, cursor: 'pointer', color: '#6B7280', lineHeight: 1 }}>
                ×
              </button>
            </div>
            <div style={{ padding: 18, overflow: 'auto' }}>
              {modal.texte !== undefined && (
                <pre style={{
                  whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0,
                  fontSize: 13, color: '#374151', fontFamily: 'inherit',
                }}>
                  {modal.texte}
                </pre>
              )}
              {modal.details && (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <tbody>
                    {Object.entries(modal.details)
                      .filter(([k]) => k !== 'table')
                      .map(([k, v]) => (
                        <tr key={k} style={{ borderTop: '1px solid #F1F5F9' }}>
                          <td style={{ padding: '8px', color: '#6B7280', width: '40%' }}>{CHAMP_FR[k] || k}</td>
                          <td style={{ padding: '8px', color: '#374151', fontWeight: 500 }}>{fmt(v)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
