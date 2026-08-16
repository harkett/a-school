// L'ATTENTE, TOUJOURS DESSINÉE PAREIL — un sablier au-dessus, une jauge en dessous.
//
// POURQUOI UN COMPOSANT. Deux écrans font patienter le futur professeur : celui qui suit
// l'inscription (« vérifiez votre boîte mail ») et celui qui active le compte. Écrits chacun de
// leur côté, ils divergeaient — l'un avait une phrase immobile, l'autre rien du tout — et une page
// figée ne se distingue pas d'une page en travail.
//
// LA JAUGE NE MONTRE AUCUN POURCENTAGE, et c'est voulu : on ne sait pas combien de temps prend une
// activation, encore moins quand un courriel sera lu. Une barre qui va et vient dit « ça vit »,
// une barre chiffrée mentirait.
// `compact` : la même attente, à côté d'un bouton plutôt qu'au milieu d'une page. Le dessin ne
// change pas — sablier, texte, jauge — seules les tailles suivent. Une seconde mécanique pour
// « la même chose en plus petit » finirait par diverger de celle-ci, comme les deux écrans
// d'attente d'origine avaient divergé.
export default function Attente({ texte, sablier = true, compact = false }) {
  const tailleSablier = compact ? 18 : 34
  const largeurJauge = compact ? '100%' : 260

  return (
    <>
      <style>{`
        @keyframes aschool-sablier { 0%,45% { transform: rotate(0deg) } 55%,100% { transform: rotate(180deg) } }
        @keyframes aschool-jauge   { 0% { left: -35% } 100% { left: 100% } }
      `}</style>

      {sablier && (
        <div style={{ fontSize: tailleSablier, lineHeight: 1, marginBottom: compact ? 6 : 14,
                      animation: 'aschool-sablier 1.8s ease-in-out infinite' }}>⏳</div>
      )}

      {texte && (compact
        ? <p style={{ fontSize: 12, color: '#64748b', margin: '0 0 6px' }}>{texte}</p>
        : <p className="text-sm text-gray-500 mb-4">{texte}</p>)}

      <div style={{ position: 'relative', height: 5, borderRadius: 99, overflow: 'hidden',
                    background: '#e2e8f0', maxWidth: largeurJauge, margin: '0 auto' }}>
        <div style={{ position: 'absolute', top: 0, bottom: 0, width: '35%', borderRadius: 99,
                      background: '#1F6EEB', animation: 'aschool-jauge 1.2s ease-in-out infinite' }} />
      </div>
    </>
  )
}
