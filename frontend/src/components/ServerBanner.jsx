import { useEffect, useState } from 'react'
import { registerServerHealthHandler } from '../serverHealth'

// Bandeau « serveur ralenti » affiché AUTOMATIQUEMENT quand le navigateur du prof
// constate que les appels échouent de façon répétée (cf. serverHealth.js). Ton sobre
// (pas le rouge alarmant d'UpdateBanner) : on informe, on rassure, on ne fait pas peur.
// Se masque tout seul dès qu'un appel repasse.
export default function ServerBanner() {
  const [degraded, setDegraded] = useState(false)

  useEffect(() => {
    registerServerHealthHandler(setDegraded)
  }, [])

  if (!degraded) return null

  return (
    <div
      role="status"
      style={{
        background: '#334155',
        color: '#fff',
        textAlign: 'center',
        padding: '10px 16px',
        fontSize: '13px',
        fontWeight: 500,
        lineHeight: 1.5,
        position: 'sticky',
        top: 0,
        zIndex: 10000,
      }}
    >
      aSchool est temporairement ralenti et certaines actions peuvent mettre du temps à
      répondre. Nous travaillons déjà à rétablir le service. Réessayez dans quelques
      minutes — <strong>vos activités enregistrées sont en sécurité.</strong>
    </div>
  )
}
