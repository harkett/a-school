# Fonctionnalités A-SCHOOL — Suivi

> **Bannière "Bientôt disponible" dans la sidebar prof** : mise à jour manuelle dans `frontend/src/components/Sidebar.jsx`, bloc `{!collapsed && ...}` en bas du fichier.

---

## Niveau 0 — Quick Wins (cette semaine)

- [x] **Pied de page .docx** — ✅ Déjà livré (ZoneResultat.jsx ligne 48).
- [x] **Pied de page impression (CSS @media print)** — ✅ Déjà livré (ZoneResultat.jsx `imprimer()`).
- [x] **Signature dans le mailto:** — ✅ Déjà livré (ZoneResultat.jsx `envoyerMail()`).
- [x] **Compteur "X activités créées"** — ✅ Livré 09/05/2026 (MesActivites.jsx — badge bordeaux sur le total filtré par profil).
- [ ] **Page `/contact`** — Remplace l'adresse en texte brut dans le footer, réduit le spam. Effort : 2h.
- [ ] **Civilité (M. / Mme) dans le profil et l'en-tête** — Champ `civilite` en BDD, formulaire inscription, Mon profil, en-tête. Effort : 2h.

---

## Niveau 1 — Application mobile PWA (priorité suivante)

Spec complète dans `MesMD/PLAN_PWA_MOBILE.md`. Pas d'app native, pas de store, même code React existant.

- [ ] **Étape 1 — Installabilité** — `manifest.json` + icônes (192×192, 512×512, apple-touch-icon) + `vite-plugin-pwa` + méta tags `index.html`. L'app peut être ajoutée à l'écran d'accueil depuis Safari iOS et Chrome Android. Effort : 1 jour.
- [ ] **Étape 2 — Service Worker et cache** — Stratégies Workbox par ressource (CacheFirst pour assets, NetworkFirst pour API, NetworkOnly pour génération). Page offline. L'interface charge instantanément, "Mes activités" accessible hors connexion. Effort : 1-2 jours.
- [ ] **Étape 3 — Interface responsive mobile** — Drawer sidebar, Header hamburger, layout flex-col/flex-row, composants adaptés 390px (TexteSource, ZoneResultat, MesActivites, modales, pages auth). Effort : 2-3 semaines. Prioriser après retours pilotes si usage mobile confirmé.
- [ ] **Étape 4 — Polish mobile** — Splash screen, touch 44px, clavier virtuel, prompt installation, notification mise à jour SW. Effort : 2-3 jours.

**Étapes 1+2 : démarrer maintenant (3 jours, aucun risque de régression desktop).**
**Étapes 3+4 : après retours pilotes ou dès que le besoin mobile est confirmé.**

---

## Niveau 2 — Court Terme

- [x] **Tableau analytique admin** — ✅ Livré 09/05/2026. Nouvel onglet "Analytique" dans le backoffice : KPI cards, tableau par prof × matière × niveau × type (expandable), barres par matière et niveau, top 20 types. Endpoints : `/api/admin/stats/analytique` + `/api/stats/matiere`. Widget stats communauté dans "Mes activités" (total plateforme + nb profs + top types).
- [x] **Filtre automatique "Mes activités" par profil** — ✅ Livré 09/05/2026. Suppression des dropdowns manuels. Filtre automatique sur matière+niveau du profil. Message discret en bas avec lien vers "Mon profil" pour les profs multi-matières.
- [ ] **Séquence onboarding email J+2 / J+7 / J+14** — APScheduler déjà installé. Impact direct sur la rétention. Effort : 2-3 jours.
- [x] **Partage d'activités entre collègues** — Bibliothèque + toggle partage par activité (matière + niveau). ✅ Livré 07/05/2026.
- [ ] **Analyse A-SCHOOL des notations (Groq)** — Groq intégré, notations en BDD. Un prompt + bloc dans AdminFeedbacks. Utile dès 15-20 retours. Effort : 1 jour.
- [ ] **Historique de connexions (Option B — SESSION_RESUME)** — Événement `SESSION_RESUME` dans l'audit avec déduplication (1 entrée max / 30 min par user). Backend : `middleware.py`. Effort : 3h.

---

## Niveau 3 — Moyen Terme

- [x] **Export PDF** — Impression via `window.print()` dans ZoneResultat.jsx. ✅ Livré.
- [ ] **Logo aSchool + rebranding interface** — Brief validé 08/05/2026 (charte graphique dans `D:\A-PUB\PUB_ASCHOOL\PLAN_CAMPAGNE-ASCHOOL\Charte_Graphique.md`). Créer le logo (a ouvert géométrique bordeaux, trame azur, livre minimaliste). Puis remplacer "A-SCHOOL" par "aSchool" dans toute l'interface (`a` minuscule bordeaux + `School` neutre). À faire **en même temps** que la migration de domaine. Effort : 1-2 jours après création du logo.
- [ ] **Migration domaine aschool.fr** — Migrer `school.afia.fr` → `aschool.fr` quand le domaine est configuré. Mises à jour : `.env APP_URL`, config Nginx, SMTP_FROM. Faire **en même temps** que le rebranding "aSchool". Effort : 1 jour.
- [ ] **Quiz interactif élèves** — Spec v1 complète validée 07/05/2026 (voir MEMOIRE_PROJET.md). Prof génère QCM → lien public → élèves répondent sur téléphone → résultats en direct. Affiché "Bientôt disponible" dans la Sidebar. Effort : 1-2 semaines.
- [ ] **Aide spécifique par matière** — Infrastructure prête (subject en BDD). Textes d'aide adaptés à la matière du prof. Effort : 3-5 jours.

---

## Niveau 4 — Long Terme

- [ ] **Support niveau Supérieur (BTS/prépa/licence)** — Travail de prompts et d'activités. Nouveau segment formateurs. Effort : 1-2 semaines.
- [ ] **Théâtre — 13e matière** — Définir les activités dans MATRICE_ACTIVITES_ASCHOOL.md + relancer parse_markdown.py. Prérequis : trouver un prof pilote théâtre. Effort : 1-2 semaines.
- [ ] **Escape Game pédagogique** — Prof choisit matière + niveau + thème narratif. A-SCHOOL génère : scénario d'introduction, 3 à 5 énigmes, épreuve finale. Sortie : document HTML imprimable. Complémentaire au Quiz interactif. **Intégration Canva/Genially : non retenue.** Effort : 2-3 semaines.
- [ ] **Google OAuth** — Réduit la friction d'inscription. Dépendance Google. À faire après validation pilotes. Effort : 2-3 semaines.

---

## Niveau 5 — Hors Scope Actuel

- [ ] **Intégration ENT (Pronote)** — API propriétaires, accords institutionnels. Des mois de travail, blocages hors de ton contrôle.
- [ ] **Tableau de bord multi-profs établissement** — Nécessite concept "établissement" en BDD + rôles. Phase 5 minimum.
- [ ] **Migration SQLite → PostgreSQL** — Uniquement si charge réelle. SQLite tient jusqu'à 500 utilisateurs actifs quotidiens. Ne pas migrer par anticipation.
