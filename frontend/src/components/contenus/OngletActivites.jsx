// Cartouche de l'onglet ACTIVITÉS — autonome (décision utilisateur du 30/07 : une cartouche
// par onglet, toucher l'une ne peut pas abîmer les autres). Deux colonnes : la liste des
// activités à gauche, le résultat de l'activité sélectionnée à droite (rendu comme à la
// création). La première activité est sélectionnée d'office ; le crayon rouvre l'écran
// Activité en reprise.
import { useState } from 'react'
import SplitPane from '../SplitPane.jsx'
import { ApercuModal, DetailActivite, LigneContenu, ListeBlanche, PlaceholderDetail } from './commun.jsx'

export default function OngletActivites({ activites, email, selectionInitiale, onOuvrirActivite }) {
  const [detailId, setDetailId] = useState(() => selectionInitiale ?? activites[0]?.id ?? null)
  const [apercu, setApercu] = useState(null)

  const detail = activites.find(a => a.id === detailId) || null

  const liste = (
    <ListeBlanche vide={activites.length === 0} messageVide="Aucune activité ici pour l'instant.">
      {activites.map((c, i) => (
        <LigneContenu
          key={c.id}
          c={c}
          dernier={i === activites.length - 1}
          estSel={c.id === detailId}
          onClick={() => setDetailId(c.id)}
          title="Afficher le résultat de cette activité à droite"
          onApercu={setApercu}
          onModifier={() => onOuvrirActivite(c)}
          titleModifier="Reprendre cette activité dans l'écran Activité (modifier, régénérer)"
        />
      ))}
    </ListeBlanche>
  )

  const droite = detail
    ? <DetailActivite detail={detail} email={email} />
    : <PlaceholderDetail texte="Cliquez une activité à gauche pour afficher son résultat ici." />

  return (
    <>
      <div style={{ flex: 1, minHeight: 0 }}>
        <SplitPane storageKey="contenus-split-v1" defautGauche={54} gauche={liste} droite={droite} />
      </div>
      <ApercuModal apercu={apercu} onFermer={() => setApercu(null)} />
    </>
  )
}
