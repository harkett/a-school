// Le SABLIER de la règle maison : « tout appel IA montre le sablier ET la jauge ». Le bouton qui
// tourne pendant qu'aSchool travaille.
//
// Il était défini À L'IDENTIQUE dans TexteSource.jsx et ApportTexte.jsx (conséquence de la copie
// assumée entre les deux composants) : deux définitions du même geste finissent toujours par
// diverger — l'une prend une nouvelle taille, l'autre garde l'ancienne, et le prof voit deux
// sabliers différents selon l'écran. Une seule définition, ici.
export default function IconSablier() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}>
      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
    </svg>
  )
}
