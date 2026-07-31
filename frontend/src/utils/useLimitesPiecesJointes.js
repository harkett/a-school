import { useCallback, useEffect, useState } from 'react'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_STD } from './api.js'
import { showError } from '../errorDialog'

// Ce que le prof a le droit de joindre à un retour : taille max, nombre max, formats acceptés.
//
// Ces valeurs étaient écrites dans le code du serveur ET recopiées dans l'écran — changer la
// limite en base n'aurait donc changé que la moitié de l'application : le serveur aurait
// refusé à 4 Mo pendant que l'écran continuait d'annoncer 5. Elles vivent maintenant en base
// (réglages `feedback_piece_jointe_max_mo` et `feedback_pieces_jointes_max`) et l'écran les LIT.
//
// Deux écrans en ont besoin — « Mes retours » pour contrôler, l'Aide pour l'annoncer : d'où ce
// crochet partagé plutôt que deux lectures écrites deux fois.
//
// `limites` vaut null tant que la réponse n'est pas là : l'appelant n'a alors RIEN à annoncer
// et n'accepte aucun fichier — il ne devine pas une limite, et le serveur reste l'arbitre.
export function useLimitesPiecesJointes() {
  const [limites, setLimites] = useState(null)
  const [rate, setRate] = useState(false)

  const charger = useCallback(async () => {
    setRate(false)
    try {
      setLimites(await lireReponse(
        await apiFetch('/api/feedback/limites', { credentials: 'include' }, TIMEOUT_STD)))
    } catch (e) {
      setRate(true)
      showError(messagePourEcran(e))
    }
  }, [])

  useEffect(() => { charger() }, [charger])

  return { limites, rate, recharger: charger }
}
