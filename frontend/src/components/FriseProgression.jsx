// Frise « Vous êtes ici » de l'écran Créer : un résumé PERMANENT de la progression, sur la
// même ligne que le titre « Nouvelle activité ». Les pastilles ①②③④ disent l'état global d'un
// coup d'œil (les mêmes états que les pastilles des cartes — type choisi, texte saisi, généré —
// lus, jamais copiés) ; à la fin, un bandeau vert « Activité complétée » récompense.
export default function FriseProgression({ typeOk, texteOk, loading, resultat }) {
  // « Terminé » = le résultat est là ET la génération ne tourne plus (sinon, en plein flux, le
  // résultat partiel ferait basculer trop tôt en « complétée » alors que le sablier tourne encore).
  const termine = !!resultat && !loading
  const etapes = [
    { n: 1, fait: typeOk },
    { n: 2, fait: texteOk },
    { n: 3, fait: termine },
    { n: 4, fait: termine },
  ]

  if (termine) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 20,
                    fontSize: 12, fontWeight: 700, color: '#16a34a' }}>
        <span style={{ width: 18, height: 18, borderRadius: '50%', background: '#16a34a', color: '#fff',
                       display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 11 }}>✓</span>
        Activité complétée
      </div>
    )
  }

  const courant = etapes.findIndex(e => !e.fait)  // 1re étape pas encore faite
  const message = loading
    ? 'aSchool rédige votre activité…'
    : courant === 0 ? "Choisissez le type d'activité"
    : courant === 1 ? 'Décrivez votre demande'
    : 'Prêt à générer'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 20, minWidth: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        {etapes.map((e, i) => {
          const estCourant = loading ? e.n === 3 : i === courant
          const couleur = e.fait ? '#16a34a' : estCourant ? 'var(--bleu)' : '#cbd5e1'
          return (
            <span key={e.n} style={{ display: 'flex', alignItems: 'center' }}>
              {i > 0 && <span style={{ width: 14, height: 2, background: '#e2e8f0' }} />}
              <span style={{ width: 18, height: 18, borderRadius: '50%', background: couleur, color: '#fff',
                             fontSize: 10, fontWeight: 700, display: 'inline-flex', alignItems: 'center',
                             justifyContent: 'center', flexShrink: 0 }}>
                {e.fait ? '✓' : e.n}
              </span>
            </span>
          )
        })}
      </div>
      <span style={{ fontSize: 11.5, color: '#64748b', whiteSpace: 'nowrap',
                     overflow: 'hidden', textOverflow: 'ellipsis' }}>
        Vous êtes ici : {message}
      </span>
    </div>
  )
}
