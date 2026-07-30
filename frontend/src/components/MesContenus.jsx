// « Mes contenus » — 3 sous-options du menu (Séquences / Séances / Activités), chacune
// ouvrant SA page. L'utilisateur remplit chaque page pas à pas, à sa demande :
//  - Activités : COPIE de l'écran « Mes activités » (Historique), branchée sur le MONDE NEUF
//    (contenus/ActivitesContenus.jsx) — demandée le 30/07 ;
//  - Séances : même motif que Activités (contenus/SeancesContenus.jsx) — demandée le 30/07 ;
//  - Séquences : même motif (contenus/SequencesContenus.jsx) — branchée sur le réel le 30/07.
import ActivitesContenus from './contenus/ActivitesContenus.jsx'
import SeancesContenus from './contenus/SeancesContenus.jsx'
import SequencesContenus from './contenus/SequencesContenus.jsx'

export default function MesContenus({ type = 'activite', onOuvrirActivite, onOuvrirSeance, onOuvrirSequence, sessionMatiere, sessionNiveau, userName }) {
  if (type === 'activite') {
    return (
      <ActivitesContenus
        onOuvrirActivite={onOuvrirActivite}
        sessionMatiere={sessionMatiere}
        sessionNiveau={sessionNiveau}
        userName={userName}
      />
    )
  }
  if (type === 'seance') {
    return (
      <SeancesContenus
        onOuvrirSeance={onOuvrirSeance}
        onOuvrirActivite={onOuvrirActivite}
        sessionMatiere={sessionMatiere}
        sessionNiveau={sessionNiveau}
      />
    )
  }
  // Page Séquences — même motif que les pages voisines, branchée sur le réel (30/07).
  return (
    <SequencesContenus
      onOuvrirSequence={onOuvrirSequence}
      sessionMatiere={sessionMatiere}
      sessionNiveau={sessionNiveau}
    />
  )
}
