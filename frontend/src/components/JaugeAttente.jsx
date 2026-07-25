import { useEffect, useState } from 'react'

// Jauge d'attente réutilisable pour UN appel IA (durée inconnue, pas d'étapes mesurables) :
// barre navette animée + secondes écoulées — jamais de faux pourcentage. Montée uniquement
// pendant l'attente (le montage/démontage remet le compteur à zéro). Née côté admin
// (référentiels), partagée ici pour servir aussi les écrans prof (décision du 24/07 :
// une jauge dès qu'on appelle l'IA).
export default function JaugeAttente({ libelle }) {
  const [sec, setSec] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setSec(s => s + 1), 1000)
    return () => clearInterval(t)
  }, [])
  return (
    <div style={{ marginTop: 10 }}>
      <style>{'@keyframes jaugeAttente { 0% { margin-left: -35%; } 100% { margin-left: 100%; } }'}</style>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12,
        color: '#475569', marginBottom: 4 }}>
        <span>{libelle}</span>
        <span style={{ fontWeight: 600 }}>{sec} s</span>
      </div>
      <div style={{ height: 8, borderRadius: 999, background: '#e2e8f0', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: '35%', background: '#7c3aed',
          borderRadius: 999, animation: 'jaugeAttente 1.6s linear infinite' }} />
      </div>
    </div>
  )
}
