// Catalogue UNIQUE des aides « i » de la page « Mes contenus → Séquences ». Même principe que
// utils/aideSeances.js : le petit « i » derrière un titre lit ces textes, jamais réécrits dans le JSX.
//  - court : bulle affichée au SURVOL du « i » (une phrase) ;
//  - long  : carte affichée au CLIC (l'aide complète, épinglée).
// Textes honnêtes (règle des deux publics) : on ne décrit que ce que l'écran fait vraiment.
const GUIDE_SEQUENCES = [
  {
    cle: 'ecran',
    titre: 'Mes séquences',
    court: "Toutes vos séquences — chacune avec ses séances, dans l'ordre du plan.",
    long: "Cette page réunit toutes les séquences que vous avez créées. Une séquence = un objectif + la suite ordonnée des séances qui y mènent. La liste est à gauche, le détail de la séquence choisie à droite : son contexte, ses précisions et ses séances avec leur état. « Reprendre » rouvre la séquence dans son écran pour travailler ses séances une à une.\n\nCORRIGER : une séquence n'est plus figée une fois créée. En la reprenant, vous retouchez librement son objectif, son contexte, son ampleur et ses compétences ; vos modifications s'enregistrent toutes seules, sans bouton à cliquer. Le plan, lui, n'est pas retouché : les séances existent déjà avec leur déroulé, vous les travaillez une à une.\n\nSUPPRIMER : la corbeille, à droite de chaque ligne, retire définitivement la séquence — mais JAMAIS ses séances. Celles-ci restent dans vos contenus : elles repassent simplement en « non rangées ». La fenêtre de confirmation vous dit combien de séances sont concernées avant que vous validiez.",
  },
  {
    cle: 'onglets',
    titre: 'Les deux onglets',
    court: "Niveau en cours = votre couple du moment ; Toutes = tout, regroupé par couple.",
    long: "« Niveau en cours » n'affiche que les séquences de votre matière et de votre niveau actuels. « Toutes mes séquences » affiche l'ensemble, regroupé par matière-niveau, votre couple courant épinglé en haut.",
  },
  {
    cle: 'contexte',
    titre: 'Contexte',
    court: "Le contexte que vous aviez fourni pour bâtir le plan.",
    long: "C'est le contexte rapide que vous aviez donné au moment de générer le plan (effectif, ambiance de la classe…). Il est conservé pour que vous sachiez toujours dans quelles conditions cette séquence a été pensée.",
  },
  {
    cle: 'seances',
    titre: 'Les séances de cette séquence',
    court: "Le plan : chaque séance avec son état — « à générer » ou « générée ».",
    long: "Le plan de la séquence, dans l'ordre : chaque ligne est une vraie séance enregistrée. « À générer » = son déroulé n'existe pas encore ; « générée » = son déroulé est écrit. Pour travailler les séances (générer un déroulé, y accrocher des activités), cliquez « Reprendre » : tout se fait dans l'écran Séquence.",
  },
]

// Renvoie les props { titre, court, long } à étaler dans <InfoGuide />. Clé inconnue → objet vide.
export function aideSequences(cle) {
  const e = GUIDE_SEQUENCES.find(x => x.cle === cle) || {}
  return { titre: e.titre, court: e.court, long: e.long }
}
