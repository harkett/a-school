// Affichage du rapport de « Vérifier le résultat » : une CHECKLIST — une carte par axe,
// TOUJOURS les 5, même celles au statut OK (le prof voit que tous les contrôles ont tourné).
// Diagnostic seul (aucune réécriture). Données lues sur `resultat`, jamais stockées (zéro copie).
const STATUT = {
  ok:             { label: 'OK',             text: '#166534', bg: '#f0fdf4', border: '#86efac' },
  info:           { label: 'À surveiller',   text: '#1e40af', bg: '#eff6ff', border: '#bfdbfe' },
  probleme:       { label: 'À corriger',     text: '#92400e', bg: '#fffbeb', border: '#fcd34d' },
  non_applicable: { label: 'Non applicable', text: '#475569', bg: '#f8fafc', border: '#e2e8f0' },
}
const DEFAUT = { label: '—', text: '#475569', bg: '#f8fafc', border: '#e2e8f0' }

export default function VerificationResultat({ resultat }) {
  if (!resultat) return null
  const axes = resultat.axes || []
  const nbProbl = axes.filter(a => a.statut === 'probleme').length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

      {/* Verdict */}
      {nbProbl === 0 ? (
        <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#166534', lineHeight: 1.6 }}>
          <strong>Rien à corriger</strong>{resultat.verdict ? ` — ${resultat.verdict}` : ''}
        </div>
      ) : (
        <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#92400e', lineHeight: 1.6 }}>
          <strong>{nbProbl} point{nbProbl > 1 ? 's' : ''} à corriger</strong>{resultat.verdict ? ` — ${resultat.verdict}` : ''}
        </div>
      )}

      {/* Une carte par axe — la checklist complète */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {axes.map((a, i) => {
          const s = STATUT[a.statut] || DEFAUT
          const aDuCorps = !!(a.constat || a.extrait)
          return (
            <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
              {/* En-tête carte : nom de l'axe (texte simple) + pastille de statut */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', borderBottom: aDuCorps ? '1px solid #f1f5f9' : 'none' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#1e293b' }}>{a.axe}</span>
                <span style={{ marginLeft: 'auto', fontSize: '11px', fontWeight: 700, color: s.text, background: s.bg, border: `1px solid ${s.border}`, borderRadius: '12px', padding: '2px 10px', whiteSpace: 'nowrap' }}>
                  {s.label}
                </span>
              </div>
              {/* Corps : le constat + l'extrait cité (v1 : pas de saut « voir dans le texte ») */}
              {aDuCorps && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '12px 14px' }}>
                  {a.constat && <div style={{ fontSize: '13px', color: '#374151', lineHeight: 1.5 }}>{a.constat}</div>}
                  {a.extrait && (
                    <div style={{ fontSize: '13px', color: '#374151', fontStyle: 'italic', background: '#fafafa', borderLeft: '3px solid #e2e8f0', padding: '6px 10px', borderRadius: '3px' }}>
                      "{a.extrait}"
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
