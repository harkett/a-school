// L'arrivée dans la démonstration — /demo?jeton=…
//
// Le prof vient de cliquer « Démonstration » dans son espace réel. Il atterrit ici, sur l'AUTRE
// instance, avec un jeton signé valable cinq minutes. Cette page l'échange contre une session et
// l'envoie dans l'application. Il n'y a pas d'écran d'identification à passer : il a déjà été
// authentifié là d'où il vient.
//
// L'adresse est nettoyée juste après (replace) : un jeton qui traîne dans la barre d'adresse
// finit par être recopié, mis en favori, ou collé dans un message.
import { useEffect, useRef, useState } from 'react'

// Le jeton se LIT dans l'adresse, il ne se met pas en mémoire d'écran : c'est une donnée d'entrée,
// connue avant le premier affichage. La ranger dans un état obligeait à afficher l'écran une
// première fois pour rien, puis à le réafficher aussitôt — c'est ce que la règle React
// `set-state-in-effect` reprochait ici (nettoyé le 07/08/2026).
const LIEN_INCOMPLET = 'Ce lien est incomplet. Repartez de votre espace et cliquez sur « Démonstration ».'

export default function DemoEntree() {
  const jeton = new URLSearchParams(window.location.search).get('jeton')
  // `erreur` ne porte QUE ce qui vient du serveur — donc plus tard, et de façon asynchrone.
  // Le lien incomplet, lui, se sait dès le rendu : il ne passe plus par là.
  const [erreurServeur, setErreurServeur] = useState('')
  const erreur = jeton ? erreurServeur : LIEN_INCOMPLET
  const lance = useRef(false)   // React monte deux fois en développement — le jeton s'use une seule

  useEffect(() => {
    if (!jeton || lance.current) return
    lance.current = true
    fetch('/api/demo/entrer', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jeton }),
    })
      .then(async r => {
        if (!r.ok) {
          const d = await r.json().catch(() => ({}))
          throw new Error(typeof d.detail === 'string' ? d.detail : "L’entrée n’a pas pu se faire.")
        }
        // Rechargement complet plutôt que navigation interne : le contexte d'authentification
        // relit ses cookies au démarrage, il ne les redemande pas en cours de route.
        window.location.replace('/')
      })
      .catch(e => setErreurServeur(e.message || "L’entrée n’a pas pu se faire."))
  }, [jeton])

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', background: '#f8fafc', padding: 24 }}>
      <div style={{ maxWidth: 460, textAlign: 'center' }}>
        {erreur ? (
          <>
            <h1 style={{ fontSize: 18, fontWeight: 700, color: '#0f172a', margin: '0 0 10px' }}>
              Entrée impossible
            </h1>
            <p style={{ fontSize: 14, color: '#475569', margin: 0 }}>{erreur}</p>
          </>
        ) : (
          <p style={{ fontSize: 14, color: '#475569', margin: 0 }}>
            Ouverture de la démonstration…
          </p>
        )}
      </div>
    </div>
  )
}
