// Numéro d'étape des cartouches de l'écran Créer (patron pro « stepper »). Le CHIFFRE reste
// TOUJOURS affiché ; seule la couleur du rond change : BORDEAUX (couleur de l'appli) tant que
// l'étape n'est pas faite, VERT dès qu'elle l'est. Écriture blanche dans les deux cas (plus de
// ✓ qui remplace le numéro).
export default function EtapeBadge({ n, fait }) {
  return (
    <span
      title={fait ? `Étape ${n} — faite` : `Étape ${n}`}
      style={{
        width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 10.5, fontWeight: 700,
        background: fait ? '#16a34a' : 'var(--bordeaux)', color: '#fff',
      }}
    >
      {n}
    </span>
  )
}
