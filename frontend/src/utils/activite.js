// Logique pure de l'écran Activité (Mes contenus) — extraite pour être testable
// sans harnais React (runner `node --test`). estPageCreer a été démolie le 30/07
// avec l'ancien écran Créer.

// Champs du type d'activité remis à VIERGE : plus AUCUNE présélection (règle appli — tout
// combo démarre sur son placeholder gris « Choisissez… », le prof fait le choix). Avant, on
// reposait ici le 1er type de la matière et sa 1re précision : les deux combos arrivaient
// remplies et l'étape ① passait au vert sans que le prof ait rien choisi.
// Renvoie l'objet à fusionner dans `params`.
export function typeVierge() {
  return {
    activite_type_id: null,   // identité du type = son id ; null = rien de choisi
    sous_type: null,
    nb: null,   // posé (à 5) par la carte Paramètres au choix du type, si son prompt le demande
    avec_correction: false,
  }
}
