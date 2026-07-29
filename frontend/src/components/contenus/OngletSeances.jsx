// Cartouche de l'onglet SÉANCES — autonome. Une colonne : la liste des séances ; le clic
// (ou le crayon) ouvre la séance dans SON écran (reprise complète), l'œil montre l'aperçu.
import { useState } from 'react'
import { ApercuModal, LigneContenu, ListeBlanche } from './commun.jsx'

export default function OngletSeances({ seances, onOuvrirSeance }) {
  const [apercu, setApercu] = useState(null)

  return (
    <>
      <ListeBlanche vide={seances.length === 0} messageVide="Aucune séance ici pour l'instant.">
        {seances.map((c, i) => (
          <LigneContenu
            key={c.id}
            c={c}
            dernier={i === seances.length - 1}
            onClick={() => onOuvrirSeance(c)}
            title="Ouvrir cette séance"
            onApercu={setApercu}
            onModifier={() => onOuvrirSeance(c)}
            titleModifier="Reprendre cette séance dans son écran"
          />
        ))}
      </ListeBlanche>
      <ApercuModal apercu={apercu} onFermer={() => setApercu(null)} />
    </>
  )
}
