# L4 — Cohérence curriculaire inter-disciplines

> Spec en cours de construction — à améliorer au fil des expérimentations.
> Approche : 1 matière pilote → tester → décider si ça vaut le coup → élargir.

---

## Objectif

Permettre à un prof de voir automatiquement quelles notions de sa matière se recoupent avec d'autres disciplines au même niveau. Exemples :

- "Révolution française" Histoire 4e ↔ "Droits de l'homme" EMC 4e
- "Statistiques" Maths 2nde ↔ "Analyse de données" SVT 2nde
- "Le roman au XIXe siècle" Français 3e ↔ "La révolution industrielle" Histoire 3e

**Valeur pour le prof :** identifier des opportunités de projets inter-matières, vérifier la cohérence de sa progression avec les autres disciplines du même niveau, éviter les redondances ou les prérequis manquants.

---

## Pourquoi c'est potentiellement très intéressant

- Aucun outil existant ne fait ça simplement pour les profs du secondaire
- Les programmes officiels sont publics — la donnée existe déjà
- L'IA (Groq) peut faire le travail de rapprochement sémantique
- Différenciateur fort vis-à-vis des outils concurrents
- Utile même sans inter-disciplinarité : un prof voit si sa prog est en phase avec le programme officiel

---

## Ce que l'outil retourne (à affiner)

Pistes de sortie — à valider avec un prof pilote avant de coder :

1. **Liste de rapprochements** — "Voici 3 notions d'autres matières qui recoupent votre thème"
2. **Score de cohérence** — "Votre séquence couvre 80% des attendus officiels de ce niveau"
3. **Suggestions de projets inter-matières** — "Votre thème X peut faire l'objet d'un projet avec le prof de Y"

> La sortie n°1 est la plus simple à implémenter et la plus directement utile. Commencer par elle.

---

## Architecture technique envisagée

### Étape 1 — Données (1 journée)
- Source : eduscol.education.fr — programmes officiels par matière et par niveau
- Format : PDFs + HTML (mise en page complexe, tableaux imbriqués)
- Travail : extraire et structurer en JSON : `matière → niveau → chapitre → notions[]`
- Volume : ~96 documents (12 matières × 8 niveaux) — commencer par 1

### Étape 2 — Alignement sémantique
- Approche A (simple) : prompt Groq — "Voici les notions de matière A et les notions de matière B au même niveau. Trouve les rapprochements pertinents."
- Approche B (robuste) : embeddings vectoriels (sentence-transformers) + similarité cosinus — plus précis, fonctionne sans LLM à chaque requête
- **Commencer par l'approche A** — plus rapide à tester, suffisant pour valider l'utilité

### Étape 3 — Intégration aSchool
- Nouveau levier dans Mes outils → Analyse
- Input : matière + niveau (depuis le profil) + thème/notion saisi par le prof
- Output : liste de rapprochements avec matière, niveau, notion, explication courte

---

## Plan d'expérimentation — étape par étape

### Phase 0 — Choisir la matière pilote
Critères : riche en connexions inter-disciplines, programme bien documenté, profs actifs sur la plateforme.

**Candidats :**
- **Histoire-Géographie** — connexions naturelles avec EMC, Français, SVT, SES. Programme très structuré sur eduscol.
- **Français** — connexions avec HG (même siècle), Philo, LV. Mais programme plus littéraire, moins "notionnel".
- **SVT** — connexions fortes avec Maths (stats), Physique-Chimie, HG (géologie/climatologie).

> À décider avec un prof pilote — celui qui sera le premier utilisateur.

### Phase 1 — Preuve de concept (1 session)
1. Choisir 1 matière + 1 niveau (ex : HG 4e)
2. Extraire manuellement les notions clés du programme officiel (pas de parsing automatique pour l'instant — copier-coller suffit)
3. Faire la même chose pour 2 autres matières du même niveau (ex : Français 4e + EMC 4e)
4. Tester le prompt Groq : "Trouve les rapprochements entre ces notions"
5. Évaluer le résultat avec un vrai prof : est-ce pertinent ? utile ? surprenant ?

### Phase 2 — Si Phase 1 convaincante
- Automatiser l'extraction des programmes (script Python)
- Couvrir toutes les matières × tous les niveaux
- Intégrer dans aSchool comme outil à part entière

### Phase 3 — Amélioration continue
- Passer aux embeddings vectoriels si le prompt Groq montre ses limites
- Ajouter le score de cohérence (sortie n°2)
- Permettre au prof de signaler un rapprochement pertinent ou non (feedback loop)

---

## Critères de décision après Phase 1

On continue si :
- Au moins 1 prof dit "je n'avais pas pensé à ça, c'est vraiment utile"
- Les rapprochements détectés sont pédagogiquement cohérents (pas juste des faux amis lexicaux)
- Le temps de réponse est acceptable (< 5 secondes)

On arrête ou on pivote si :
- Les rapprochements sont trop évidents (déjà connus de tous les profs)
- Les rapprochements sont trop absurdes (hallucinations sémantiques)
- Aucun prof ne voit l'intérêt concret dans sa pratique

---

## Statut

- [ ] Phase 0 — Choisir matière pilote (avec prof pilote)
- [ ] Phase 1 — Preuve de concept
- [ ] Phase 2 — Automatisation + intégration
- [ ] Phase 3 — Amélioration continue
