// Frise de progression de l'écran Créer : le parcours en 5 étapes LIBELLÉES, en pleine largeur
// sous la barre du haut. Les états (fait ✓ vert / en cours bordeaux / à venir gris) sont LUS de
// la progression réelle (type choisi, texte saisi, généré, vérifié), jamais copiés.
// « Améliorer » est la dernière étape du parcours (pas encore construite → reste « à venir »).
export default function FriseProgression({ typeOk, texteOk, loading, resultat, verifOk }) {
  // « Généré » = résultat présent ET génération finie (sinon un résultat partiel basculerait trop tôt).
  const termine = !!resultat && !loading
  const etapes = [
    { n: 1, label: 'Paramètres',   fait: !!typeOk },
    { n: 2, label: 'Texte source', fait: !!texteOk },
    { n: 3, label: 'Générer',      fait: termine },
    { n: 4, label: 'Vérifier',     fait: !!verifOk },
    { n: 5, label: 'Améliorer',    fait: false },
  ]
  // Étape « en cours » = la 1re pas encore faite ; pendant la génération c'est « Générer » (index 2).
  const courant = loading ? 2 : etapes.findIndex(e => !e.fait)

  return (
    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', rowGap: 8 }}>
      {etapes.map((e, i) => {
        const estCourant = i === courant
        const bg   = e.fait ? '#16a34a' : estCourant ? 'var(--bordeaux)' : '#fff'
        const fg   = (e.fait || estCourant) ? '#fff' : '#94a3b8'
        const bord = e.fait ? '#16a34a' : estCourant ? 'var(--bordeaux)' : '#cbd5e1'
        return (
          <span key={e.n} style={{ display: 'flex', alignItems: 'center' }}>
            {i > 0 && (
              <span style={{ width: 30, height: 2, borderRadius: 2, margin: '0 9px',
                             background: etapes[i - 1].fait ? '#16a34a' : '#e2e8f0' }} />
            )}
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                             display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                             fontSize: 12, fontWeight: 800, fontVariantNumeric: 'tabular-nums',
                             background: bg, color: fg, border: `1.5px solid ${bord}`,
                             boxShadow: estCourant ? '0 0 0 4px rgba(140,29,64,0.14)' : 'none' }}>
                {e.fait ? '✓' : e.n}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap',
                             color: estCourant ? '#1e293b' : e.fait ? '#64748b' : '#94a3b8' }}>
                {e.label}
              </span>
            </span>
          </span>
        )
      })}
    </div>
  )
}
