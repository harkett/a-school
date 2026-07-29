const TYPE_COLOR = {
  'Consigne vague':                  { bg: '#fef3c7', text: '#92400e', border: '#fde68a' },
  'Vocabulaire technique non défini': { bg: '#f3e8ff', text: '#6b21a8', border: '#d8b4fe' },
  'Double sens':                     { bg: '#fce7f3', text: '#9d174d', border: '#f9a8d4' },
  'Critères de réussite absents':    { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' },
  'Référence implicite':             { bg: '#e0f2fe', text: '#075985', border: '#7dd3fc' },
  'Consigne trop longue':            { bg: '#f0fdf4', text: '#166534', border: '#86efac' },
}

const DEFAULT_COLOR = { bg: '#f1f5f9', text: '#334155', border: '#cbd5e1' }

// Affichage du rapport d'ambiguïtés (verdict + cartes) — SEULE source de l'affichage, partagée
// entre le module autonome (Analyse → Ambiguité) et la cartouche « Résultat Ambiguïté » de Créer
// une activité. onDemanderSequence est OPTIONNEL : fourni → bouton « Créer une séance » sur chaque
// carte (module autonome) ; absent → cartouche en lecture seule (Créer une activité).
export default function AmbiguitesResultat({ resultat, onDemanderSequence }) {
  if (!resultat) return null
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

      {/* Verdict */}
      {resultat.ambiguites.length === 0 ? (
        <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#166534', lineHeight: 1.6 }}>
          <strong>Énoncé clair</strong> — {resultat.verdict}
        </div>
      ) : (
        <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#92400e', lineHeight: 1.6 }}>
          <strong>{resultat.ambiguites.length} ambiguïté{resultat.ambiguites.length > 1 ? 's' : ''} détectée{resultat.ambiguites.length > 1 ? 's' : ''}</strong> — {resultat.verdict}
        </div>
      )}

      {/* Liste des ambiguïtés */}
      {resultat.ambiguites.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {resultat.ambiguites.map((a, i) => {
            const c = TYPE_COLOR[a.type] || DEFAULT_COLOR
            return (
              <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
                {/* En-tête carte */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: c.text, background: c.bg, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '2px 10px', whiteSpace: 'nowrap' }}>
                    {a.type}
                  </span>
                </div>
                {/* Corps carte */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '12px 14px' }}>
                  {/* Extrait */}
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                      Extrait problématique
                    </div>
                    <div style={{ fontSize: '13px', color: '#374151', fontStyle: 'italic', background: '#fafafa', borderLeft: '3px solid #e2e8f0', padding: '6px 10px', borderRadius: '3px' }}>
                      "{a.extrait}"
                    </div>
                  </div>
                  {/* Risque */}
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                      Risque pour l'élève
                    </div>
                    <div style={{ fontSize: '13px', color: '#374151', lineHeight: 1.5 }}>{a.risque}</div>
                  </div>
                  {/* Reformulation */}
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: '#166534', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                      Reformulation corrigée
                    </div>
                    <div style={{ fontSize: '13px', color: '#166534', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '5px', padding: '8px 10px', lineHeight: 1.5 }}>
                      {a.reformulation}
                    </div>
                  </div>

                  {/* Bouton Créer une séance — uniquement si le parent le fournit */}
                  {onDemanderSequence && (
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                        onClick={() => onDemanderSequence(a.reformulation)}
                        title="Utiliser cette reformulation comme thème pour créer une séance pédagogique"
                        style={{ fontSize: '12px', color: '#6366f1', background: 'none', border: '1px solid #c7d2fe', borderRadius: '5px', padding: '5px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}
                      >
                        Créer une séance →
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
