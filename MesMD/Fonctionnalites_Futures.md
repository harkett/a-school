# Fonctionnalités A-SCHOOL — Suivi

> **Bannière "Bientôt disponible" dans la sidebar prof** : mise à jour manuelle dans `frontend/src/components/Sidebar.jsx`, bloc `{!collapsed && ...}` en bas du fichier.

---

## Niveau 0 — Quick Wins

- [ ] **Pied de page .docx** — "Activité générée avec A-SCHOOL — school.afia.fr" dans chaque export. Effort : 2h.
- [ ] **Pied de page impression (CSS @media print)** — Même effet sur les feuilles distribuées en classe. Effort : 1h.
- [ ] **Signature dans le mailto:** — Le collègue qui reçoit voit d'où ça vient. Effort : 30min.
- [ ] **Compteur "X activités créées"** — SQL COUNT + affichage React. Favorise la rétention. Effort : 3h.
- [ ] **Page `/contact`** — Remplace l'adresse en texte brut dans le footer, réduit le spam. Effort : 2h.
- [ ] **Civilité (M. / Mme) dans le profil et l'en-tête** — Champ `civilite` en BDD, formulaire inscription, Mon profil, en-tête. Effort : 2h.

---

## Niveau 1 — Court Terme

- [ ] **Séquence onboarding email J+2 / J+7 / J+14** — APScheduler déjà installé. Impact direct sur la rétention. Effort : 2-3 jours.
- [x] **Partage d'activités entre collègues** — Bibliothèque + toggle partage par activité (matière + niveau). ✅ Livré 07/05/2026.
- [ ] **Analyse A-SCHOOL des notations (Groq)** — Groq intégré, notations en BDD. Un prompt + bloc dans AdminFeedbacks. Utile dès 15-20 retours. Effort : 1 jour.
- [ ] **Historique de connexions (Option B — SESSION_RESUME)** — Événement `SESSION_RESUME` dans l'audit avec déduplication (1 entrée max / 30 min par user). Backend : `middleware.py`. Effort : 3h.

---

## Niveau 2 — Moyen Terme

- [x] **Export PDF** — Impression via `window.print()` dans ZoneResultat.jsx. ✅ Livré.
- [ ] **Aide spécifique par matière** — Infrastructure prête (subject en BDD). Textes d'aide adaptés à la matière du prof. Effort : 3-5 jours.
- [ ] **Support niveau Supérieur (BTS/prépa/licence)** — Travail de prompts et d'activités. Nouveau segment formateurs. Effort : 1-2 semaines.
- [ ] **Théâtre — 13e matière** — Définir les activités dans MATRICE_ACTIVITES_ASCHOOL.md + relancer parse_markdown.py. Prérequis : trouver un prof pilote théâtre. Effort : 1-2 semaines.
- [ ] **Quiz interactif élèves** — Spec v1 complète validée 07/05/2026 (voir MEMOIRE_PROJET.md). Prof génère QCM → lien public → élèves répondent sur téléphone → résultats en direct. Affiché "Bientôt disponible" dans la Sidebar. Effort : 1-2 semaines.
- [ ] **Escape Game pédagogique** — Prof choisit matière + niveau + thème narratif (ex : "mystère scientifique", "voyage dans le temps"). A-SCHOOL génère : scénario d'introduction, 3 à 5 énigmes adaptées au niveau (chacune liée à une compétence), et une épreuve finale de validation des apprentissages. Sortie : document HTML imprimable complet, prêt à distribuer en classe. L'épreuve finale interactive pourra s'appuyer sur le Quiz interactif (fonctionnalité complémentaire). **Intégration Canva/Genially : non retenue** — leurs API sont réservées aux offres Enterprise payantes et créent une dépendance externe non justifiée. La valeur d'A-SCHOOL est dans la génération du contenu pédagogique, pas dans la mise en forme visuelle. Effort estimé : 2-3 semaines.

---

## Niveau 3 — Long Terme

- [ ] **Application mobile (PWA)** — manifest.json + service worker + UI responsive mobile-first. Attendre retours pilotes avant de commencer. Effort : 2-4 semaines.
- [ ] **Google OAuth** — Réduit la friction d'inscription. Dépendance Google. À faire après validation pilotes. Effort : 2-3 semaines.

---

## Niveau 4 — Hors Scope Actuel

- [ ] **Intégration ENT (Pronote)** — API propriétaires, accords institutionnels. Des mois de travail, blocages hors de ton contrôle.
- [ ] **Tableau de bord multi-profs établissement** — Nécessite concept "établissement" en BDD + rôles. Phase 4 minimum.
- [ ] **Migration SQLite → PostgreSQL** — Uniquement si charge réelle. SQLite tient jusqu'à 500 utilisateurs actifs quotidiens. Ne pas migrer par anticipation.

---

## Sur la question du mobile

La PWA est la bonne approche : pas d'app native, pas de Play Store/App Store, pas de revue Apple/Google.

Ce que ça demande :
- `manifest.json + icônes` → 2-3h
- `Service worker basique` → 1 jour
- `Interface responsive mobile` → gros morceau (2-3 semaines si l'UI actuelle n'est pas mobile-first)
- `Tests iOS + Android` → 2-3 jours

**Conseil :** attendre les retours pilotes. Les profs préparent leurs cours sur ordinateur. Commencer par les Niveaux 0 et 1, collecter des retours, puis PWA si les pilotes le demandent.
