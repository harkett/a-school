// Ce que les DEUX rangées d'apport de texte partagent — celle de l'activité (TexteSource.jsx) et
// celle de la séance (ApportTexte.jsx). Elles font le même geste (importer un TXT, lire une image,
// lire un PDF, dicter) et le disaient jusqu'ici avec des phrases recopiées mot pour mot dans les
// deux fichiers. Une phrase écrite deux fois finit toujours par n'être corrigée qu'une seule.

// Libellés des JaugeAttente communs aux deux rangées. « Propose-moi… » n'est pas ici : sa phrase
// dépend de la zone (thème, compétences, matériel…) et voyage donc avec l'appel.
export const JAUGE_IMAGE  = 'aSchool lit votre image et en extrait le texte…'
export const JAUGE_PDF    = 'aSchool lit votre PDF et en extrait le texte…'
export const JAUGE_DICTEE = 'aSchool transcrit votre dictée — le texte s\'insérera à la fin…'

// Le message d'échec du MICRO, en français, pour le prof.
//
// Le code affichait `err.message` du navigateur quand la panne n'était pas un refus d'autorisation
// — donc « Requested device not found » ou « Could not start audio source », en anglais et en
// vocabulaire technique, dans une boîte de dialogue destinée à un enseignant. On traduit les cas
// réels et on ne recopie JAMAIS le message brut : ce qu'on ne sait pas nommer se dit simplement.
export function messageMicro(err) {
  const nom = err && err.name
  if (nom === 'NotAllowedError' || nom === 'SecurityError') {
    return "Accès au microphone refusé.\n\nPour utiliser la dictée vocale, autorisez l'accès au microphone dans les paramètres de votre navigateur."
  }
  if (nom === 'NotFoundError' || nom === 'OverconstrainedError') {
    return "Aucun microphone détecté.\n\nBranchez un micro (ou un casque avec micro), puis réessayez."
  }
  if (nom === 'NotReadableError' || nom === 'AbortError') {
    return "Le microphone est déjà utilisé par une autre application.\n\nFermez-la (visioconférence, enregistreur…) puis réessayez."
  }
  return "Impossible d'accéder au microphone.\n\nVérifiez qu'un micro est branché et qu'aucune autre application ne l'utilise, puis réessayez."
}
