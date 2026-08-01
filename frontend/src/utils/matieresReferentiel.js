// Les lignes de la table « Matières de ce référentiel » (écran admin Référentiels).
//
// Sorti de l'écran pour être PROUVÉ, même découpage que utils/profil.js face à MonProfil :
// l'écran rend, cette fonction décide de ce qu'il rend.
//
// La liste vient telle quelle de la base (GET /admin/referentiels/etat), dans son ordre.
// Chaque matière du référentiel porte son état : `validee` vraie = retenue par l'admin (elle
// est au programme, les profs du niveau la voient), fausse = proposée par la lecture du
// document, en attente de décision.
//
// IL N'Y A PLUS RIEN À RECOLLER. L'écran assemblait avant deux sources — les matières « en
// base » et les « candidates » — en dédoublonnant par nom : une candidate portant le nom d'une
// matière existante disparaissait. Tant que les matières étaient un catalogue partagé, c'était
// à peu près sans conséquence ; depuis que chaque référentiel possède les siennes, deux lignes
// de même nom sont deux matières différentes, et masquer l'une est une faute.
//
// `cochee` est le SEUL état d'écran : la case que l'admin coche avant « Récupérer ». Une
// matière déjà retenue arrive cochée et verrouillée (pour l'en sortir, c'est « Retirer »).
export function lignesMatieres(etatObj) {
  return (etatObj?.matieres || []).map(m => ({
    id: m.id, nom: m.nom, validee: !!m.validee, cochee: !!m.validee,
  }))
}

// Combien de matières sont réellement AU PROGRAMME. C'est ce comptage — pas la longueur de la
// liste — qui allume la pastille verte de la cartouche et fait avancer la procédure : une
// proposition non cochée ne met aucune matière à la disposition des profs.
export function nbRetenues(lignes) {
  return (lignes || []).filter(m => m.validee).length
}

// Reste-t-il quelque chose à retenir ? = une case cochée sur une ligne qui n'est pas encore au
// programme (proposition acceptée, ou ligne ajoutée à la main). C'est ce qui dégrise « Récupérer ».
export function aRetenir(lignes) {
  return (lignes || []).some(m => m.cochee && !m.validee)
}
