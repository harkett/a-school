// Cascade matière ← niveau pour « Mon profil ». Fonctions PURES (testées, node --test).
//
// Règle : la matière dépend du NIVEAU choisi — le programme du diplôme/niveau, via les
// paires matière×niveau du référentiel (source = /api/programmes → matieres_par_niveau).
// Côté PROF, on ne montre QUE les niveaux traités (ayant reçu leur vrai référentiel) ;
// les niveaux « non traités » sont filtrés/cachés (l'admin, lui, continue de tout voir).

// Filtre la liste des niveaux affichée au PROF : seulement les niveaux traités
// (traite !== false), et on retire un cycle qui n'a plus aucun niveau visible.
export function niveauxTraites(niveauxParCycle) {
  return (niveauxParCycle || [])
    .map(g => ({ ...g, niveaux: g.niveaux.filter(n => n.traite !== false) }))
    .filter(g => g.niveaux.length > 0)
}

// Le niveau (courant) fait-il partie des niveaux DISPONIBLES (traités) ?
// Introuvable ou traite=false → false (indisponible) → déclenche la modale « niveau caché ».
// Pas de niveau → true (cas vide géré par le blocage de « Valider »).
export function niveauDisponible(niveauxParCycle, niveau) {
  if (!niveau) return true
  for (const g of (niveauxParCycle || [])) {
    const n = g.niveaux.find(x => x.nom === niveau)
    if (n) return n.traite !== false
  }
  return false
}

// Matières du niveau choisi (scope par niveau, dans l'ordre du référentiel).
// null = pas de niveau, ou niveau absent des données → l'appelant montre tout, groupé.
export function matieresDuNiveau(matieresParNiveau, niveau) {
  if (!niveau) return null
  const grp = (matieresParNiveau || []).find(g => g.niveau === niveau)
  return grp ? grp.matieres : null
}

// Une matière (par son nom) est-elle présente dans la liste affichée ?
export function matiereConnue(matieresAffichees, subject) {
  return (matieresAffichees || []).some(m => m.nom === subject)
}

// Incohérence DURE : un niveau ET une matière sont choisis, mais la matière n'est pas
// enseignée à ce niveau. Déclenche la modale bloquante (jamais d'avertissement passif).
// false tant que le niveau n'a pas de liste connue → on ne juge pas ce qu'on ne peut trancher.
export function matiereIncoherente(matieresParNiveau, niveau, subject) {
  if (!niveau || !subject) return false
  const liste = matieresDuNiveau(matieresParNiveau, niveau)
  if (liste == null) return false
  return !matiereConnue(liste, subject)
}

// Le profil est-il enregistrable ? NIVEAU et MATIÈRE valides sont OBLIGATOIRES — un profil
// de prof sans niveau n'a pas de sens (on génère pour quel niveau ?). On force le choix.
export function profilPretAValider(matieresParNiveau, niveau, subject) {
  if (!niveau) return false                                            // niveau obligatoire
  if (!subject) return false                                          // matière obligatoire
  return !matiereIncoherente(matieresParNiveau, niveau, subject)
}
