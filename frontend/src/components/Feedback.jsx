// La FENÊTRE d'envoi d'un retour — celle qu'ouvrent le menu du haut et la modale d'erreur.
//
// ELLE NE PORTE PLUS SON PROPRE FORMULAIRE. Elle en avait un, plus pauvre que celui de l'écran
// « Nouveau » : ni pièce jointe, ni limites lues du serveur, ni compteur de caractères. Deux
// formulaires pour un seul geste, dont un qui ne recevait aucun des correctifs de l'autre — le
// prof qui signalait un problème depuis une erreur ne pouvait pas y joindre sa capture d'écran,
// alors que c'est exactement là qu'il en a une.
//
// FenetrePro est gardée telle quelle : déplaçable, étirable, sans voile — le prof continue de
// voir l'écran dont il parle pendant qu'il écrit.
import FenetrePro from './FenetrePro.jsx'
import MesFeedbacks from '../pages/MesFeedbacks.jsx'

export default function Feedback({ onClose, contexte, incidentRef }) {
  return (
    <FenetrePro titre="Envoyer un retour" onFermer={onClose} largeur={620} hauteur={640}
                minWidth={420} minHeight={400} zIndex={460}>
      <MesFeedbacks vue="envoyer" dansFenetre onClose={onClose}
                    contexte={contexte} incidentRef={incidentRef} />
    </FenetrePro>
  )
}
