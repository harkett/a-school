// Cartouche de l'onglet TOUT — autonome. La liste mélangée (séquences, séances, activités)
// à gauche ; à droite, le résultat de l'activité sélectionnée (comme l'onglet Activités —
// une séance, elle, s'ouvre dans SON écran au clic). Sa sélection vit ICI : changer d'onglet
// n'emmène rien ailleurs.
import { useState } from 'react'
import SplitPane from '../SplitPane.jsx'
import { ApercuModal, DetailActivite, LigneContenu, ListeBlanche, PlaceholderDetail } from './commun.jsx'

export default function OngletTout({ contenus, email, onOuvrirSeance, onOuvrirActivite }) {
  const [detailId, setDetailId] = useState(() => contenus.find(c => c.type === 'activite')?.id ?? null)
  const [apercu, setApercu] = useState(null)

  const detail = contenus.find(c => c.type === 'activite' && c.id === detailId) || null

  const liste = (
    <ListeBlanche vide={contenus.length === 0} messageVide="Rien ici pour l'instant.">
      {contenus.map((c, i) => {
        const proprietes = c.type === 'seance' ? {
          onClick: () => onOuvrirSeance(c),
          title: 'Ouvrir cette séance',
          onModifier: () => onOuvrirSeance(c),
          titleModifier: 'Reprendre cette séance dans son écran',
        } : c.type === 'activite' ? {
          onClick: () => setDetailId(c.id),
          title: 'Afficher le résultat de cette activité à droite',
          estSel: c.id === detailId,
          onModifier: () => onOuvrirActivite(c),
          titleModifier: "Reprendre cette activité dans l'écran Activité (modifier, régénérer)",
        } : {}
        return (
          <LigneContenu
            key={`${c.type}-${c.id}`}
            c={c}
            dernier={i === contenus.length - 1}
            onApercu={setApercu}
            {...proprietes}
          />
        )
      })}
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
