// Numéro d'étape des cartouches de l'écran Créer (patron pro « stepper » : des numéros
// statiques, l'état réel coche ce qui est fait — plus aucun halo qui se promène).
export default function EtapeBadge({ n, fait }) {
  return (
    <span
      title={fait ? 'Étape faite' : `Étape ${n}`}
      style={{
        width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 10.5, fontWeight: 700,
        background: fait ? '#16a34a' : 'var(--bleu)', color: '#fff',
      }}
    >
      {fait ? '✓' : n}
    </span>
  )
}
