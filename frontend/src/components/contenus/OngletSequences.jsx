// Cartouche de l'onglet SÉQUENCES — autonome. Une colonne : la liste des séquences
// (conteneurs de séances). L'ouverture du conteneur arrive avec les prochaines briques.
import { useState } from 'react'
import { ApercuModal, LigneContenu, ListeBlanche } from './commun.jsx'

export default function OngletSequences({ sequences }) {
  const [apercu, setApercu] = useState(null)

  return (
    <>
      <ListeBlanche vide={sequences.length === 0} messageVide="Aucune séquence ici pour l'instant.">
        {sequences.map((c, i) => (
          <LigneContenu
            key={c.id}
            c={c}
            dernier={i === sequences.length - 1}
            onApercu={setApercu}
          />
        ))}
      </ListeBlanche>
      <ApercuModal apercu={apercu} onFermer={() => setApercu(null)} />
    </>
  )
}
