# aSchool — TRACKER

> **Source de vérité unique.** Toute idée, tâche ou livraison est ici — nulle part ailleurs.
> Specs techniques détaillées → `SPECS_LEVIERS/`

> Note dev : Bannière "Bientôt disponible" sidebar prof → `Sidebar.jsx`, bloc `{!collapsed && ...}` en bas.

> **Règle Aide :** Dès qu'une fonctionnalité est livrée, sa section Aide est rédigée dans la même session — à chaud, pendant que c'est frais. Jamais en retard.

---

## PRIORITAIRE

- [x] **PWA — Installabilité** | Livré 12/05
  *IOSInstallBanner, bfcache fix, cross-tab logout, SW update banner — testé iOS Safari.*

- [x] **PWA — Service Worker** | Livré 12/05
  *SW opérationnel, offline banner, cache propre au logout, update détectée automatiquement.*

- [x] **PWA — Responsive mobile (pages restantes)** | Livré 12/05
  *ZoneResultat, Bibliothèque, Aide — complété. Toutes les pages adaptées mobile.*

---

## IMPORTANT

### Feedback — Améliorations (ordre d'implémentation)

- [x] **FB1+FB3+FB4 — Page Mes feedbacks** | Livré 12/05
  *Page sidebar "Mes feedbacks". 2 onglets : Envoyer / Mes retours. Upload multi-fichiers (PNG/JPEG/PDF, max 5Mo, max 5 fichiers), drag&drop + Parcourir. Bouton Modifier si statut nouveau/en_cours. Capture écran via Win+Maj+S (message d'aide intégré). Aide rédigée à chaud (section "Mes feedbacks" dans Aide.jsx).*

- [ ] **Pages légales CNIL — placeholders [À COMPLÉTER]** | En attente infos admin
  *4 pages légales (Mentions légales, PC, CGU, Cookies) rédigées et corrigées dans `CNIL/`. Placeholders restants : forme juridique, SIRET, capital social, adresse siège, nom dirigeant, ville siège. Bloqué par délais administration française. À compléter dès réception des infos — puis intégrer dans le React (4 routes + liens footer).*

- [x] **Aide — Rubrique "Premiers pas"** | Livré 14/05
  *3 sections ajoutées dans Aide.jsx : Créer votre compte (inscription + vérif + mdp oublié), Compléter votre profil (importance profil complet), Première activité (5 étapes + exports). GUIDE_PREMIERE_CONNEXION.md supprimé — contenu intégré dans l'Aide.*

- [x] **Aide — Sections Historique Activités / Séquences / Mon réseau** | Livré 13/05
  *4 nouvelles sections dans Aide.jsx : Historique des activités (Plus de détails, Reprendre, Partager, Supprimer), Historique des séquences (idem + choix anonymat + badge Partagé), Mon réseau (Activités et Séquences partagées, Utiliser). Section Partager mise à jour avec nouveau flow anonymat. Catégorie "Gérer" ajoutée dans la nav.*

- [ ] **FB2 — Email admin → prof** | Facile | 2h
  *Bouton "Contacter" dans AdminFeedbacks. 3 templates : Traité / Demande de précision / Remerciement. Admin peut modifier le corps avant envoi. Endpoint `POST /api/admin/feedbacks/{id}/email`. Trace en BDD : `email_sent_at` + `email_type`.*

---

### Mes Outils — Leviers pédagogiques
*Specs détaillées dans `SPECS_LEVIERS/`. Ordre d'implémentation : L2 → L5 → L6 → L4.*

> **Standard obligatoire — chaque outil doit respecter ces 8 points :**
> 1. Page dédiée (route propre)
> 2. Onglets figés : outil principal + "Comment ça marche"
> 3. Layout : seul le contenu scroll (`flex:1 minHeight:0 overflowY:auto`)
> 4. Bouton d'action dans la barre d'onglets (btn-primary + icône + title)
> 5. Dialog pour formulaire incomplet (jamais bouton désactivé)
> 6. Auto-scroll vers le résultat après génération
> 7. Validation du texte source avant appel API
> 8. **Bouton "Tester un exemple" pré-rempli par matière/niveau** (style secondaire, aligné à droite du label)

- [x] **L2 — Détecteur d'ambiguïtés cognitives** | Livré
  *Analyse un exercice ou énoncé → zones de risque d'incompréhension + reformulations corrigées. Ajouté dans "Bientôt disponible" 12/05. Composant Ambiguites.jsx fonctionnel, intégré dans Mes outils → Analyse.*

- [ ] **L5 — Analyseur de consignes** | Facile | 1 session
  *Analyse chirurgicale d'une consigne isolée → clarté, charge cognitive, erreurs typiques + version optimisée.*

- [ ] **L6 — Détecteur d'équité pédagogique** | Facile | 1 session
  *Audit d'une évaluation → 3 biais : contenu, difficulté, émotionnel.*

---

- [x] **Aide — Refonte visuelle pro** | Livré 12/05
  *Layout 2 colonnes — nav sticky gauche (Installation / Créer / Comprendre / Problèmes), contenu à droite. Mobile : accordéon inchangé.*

- [ ] **Page /contact** | Facile | 2h
  *Remplace l'adresse email brute dans le footer — réduit le spam.*

- [ ] **Civilité M./Mme dans le profil** | Facile | 2h
  *Personnalisation de l'en-tête. Détail qui compte pour les profs.*

- [ ] **Onboarding email J+2 / J+7 / J+14** | Moyen | 3 jours
  *APScheduler déjà installé, J+0 welcome existe. Un prof relancé au bon moment revient — impact rétention direct.*

- [ ] **Analyse des notations Groq** | Facile | 1 jour
  *Groq intégré, notations en BDD. Un prompt + un bloc dans AdminFeedbacks. Utile dès 15 retours pour orienter le produit.*

- [ ] **Migration React Query (TanStack Query)** | Difficile | 1 session dédiée
  *Standard industrie 2024-2026 pour la gestion des données en React. Remplace les 20+ fetch manuels : timeout AbortController, retry automatique différencié (auth vs Groq), loading/error centralisés, cache staleTime par type de requête. À traiter en session dédiée — ne pas mélanger avec d'autres chantiers.*

- [ ] **Timeouts sessions** | Facile | 2h
  *Sessions trop longues signalées. À traiter séparément — ne pas toucher à l'auth sans analyse préalable.*

- [ ] **Fiche de révision Français + Fiche pédagogique HG** | Facile | 30min
  *Ajouter ces deux types d'activités manquants dans la matrice activités (sur le modèle des fiches existantes dans les autres matières).*

- [x] **Accueil — Réorganisation** | Livré 13/05
  *Stats déplacées vers page "Mes stats" (menu sidebar après Mes feedbacks). Page Accueil épurée : bandeau bienvenue + "Mes dernières créations" (3 sections : Activité / Séquence / Analyse raccourcis) + colonne droite CTA + lien stats + astuce. Astuce clampée à 4 lignes max (WebkitLineClamp). Backend : `/api/dashboard` renvoie désormais `derniere_sequence` (theme, matiere, niveau, duree, mode, description_classe, resultat).*

- [x] **Stats & Fréquentation — 3 blocs** | Livré 13/05
  *3 blocs distincts validés le 13/05. Ordre d'implémentation : B3 → B2 → B1.*

  **B1 — Stats personnelles prof** *(widget KPI page Accueil)*
  Calculées à la volée depuis données existantes : total activités générées, séquences créées, activités partagées, type favori ("votre spécialité"), estimation heures gagnées (15 min × nb activités), streak créateur (X jours consécutifs), score d'adaptation few-shot ("aSchool vous connaît à X%"), "vos partages repris X fois" (nécessite `utilise_count` en BDD).

  **B2 — Jauge communauté** *(page Accueil profs + admin)*
  Le site "bat" — effet réseau, fidélisation : "X profs actifs aujourd'hui · X activités générées cette semaine · X partages en circulation". Données anonymes, mises à jour à chaque chargement. Visible aussi dans le backoffice admin.

  **B3 — Graphe de fréquentation** *(backoffice admin + vue admin de B2)*
  Courbe connexions uniques par jour sur 30/90 jours. Histogramme heure de pointe (0h→24h). Nécessite table `connexions(user_email, created_at)` alimentée à chaque login. Couvre aussi "Historique de connexions" — une seule tâche pour deux besoins. Librairie : Recharts.

  > **Note : réfléchir à d'autres stats** pertinentes pour les profs et l'admin (ex : taux de partage, matières les plus actives, progression mensuelle…)


---

## TRANSVERSE AFIA — Multi-projets

- [ ] **Synchronisation pages afia.fr ↔ projets** | Facile | À faire au prochain push MINOR/MAJOR
  *Besoin : la page afia.fr/school doit refléter en temps réel l'état de l'app en production.*
  *Solution retenue : Claude s'en charge. À chaque push MINOR ou MAJOR, Claude génère automatiquement le contenu mis à jour de `School.jsx` (AFIA-FR) — prêt à coller depuis la session AFIA-FR. Règle ajoutée dans CLAUDE.md. S'applique à tous les projets AFIA (AFIASAVE, AFIALOC…) avec la même règle dans leurs CLAUDE.md respectifs.*

---

## OPTIONNEL

- [ ] **Bouton "Partagez avec vos collègues"** | Moyen | 1 session
  *Prof connecté envoie une invitation par email à ses collègues depuis l'interface. Nom pré-rempli via JWT. Backend : `POST /api/partager/` (max 5 adresses / 5 appels par jour). Frontend : modale légère `PartagerCollègues.jsx` dans la sidebar.*

- [ ] **Gestion emails sortants — backoffice admin** | Moyen | 1-2 sessions
  *Journal des emails envoyés (destinataire, type, date, statut). Stats envois par période. Gestion bounces → liste noire automatique. Lien désinscription dans chaque mail. Prérequis : SMTP transactionnel avec webhooks (Brevo/Resend) avant campagnes de masse.*



- [ ] **Ambiguité → Créer une séquence** | Facile | 1h
  *Bouton "Créer une séquence →" sur chaque carte de reformulation corrigée. Navigue vers creer-sequence en pré-remplissant le champ Thème avec la reformulation. À implémenter après L5/L6.*

- [ ] **Quiz interactif élèves** | Difficile | 2 semaines
  *Prof génère QCM → lien public → élèves répondent sur téléphone → résultats live. Différenciateur fort. Spec v1 validée 07/05.*


- [ ] **Aide spécifique par matière** | Moyen | 3-5 jours
  *Infrastructure prête (subject en BDD). Textes d'aide adaptés = meilleure prise en main pour chaque prof.*

- [ ] **Admin — Menu Activités en groupe** | Facile | 2h
  *Prépare la modération des activités partagées. Pattern `group: true` déjà disponible dans AdminLayout.*

- [ ] **Projet demo-perf — FastAPI + PostgreSQL à l'échelle** | Difficile | À faire en fin de projet
  *Projet technique séparé (hors aSchool) pour tester la stack sous charge réelle. Stack : FastAPI + SQLAlchemy async (asyncpg) + PostgreSQL + Docker. Seed via Faker + COPY PostgreSQL (objectif : 5–10M lignes en ~30s). Scénarios : requête naïve vs index BTree/GIN, pagination OFFSET vs cursor-based, filtre combiné avec/sans index composite, N+1 query, connection pool sous charge (locust). Démos profs : pas besoin de données pré-chargées — toujours faire la démo sur l'exemple du prof lui-même (bien plus parlant).*

- [ ] **Support niveau Supérieur (BTS/prépa/licence)** | Difficile | 2 semaines
  *Ouvre un segment nouveau — formateurs BTS/prépa. Surtout du travail de prompts et d'activités.*

- [ ] **Théâtre — 13e matière** | Moyen | 1-2 semaines
  *Définir activités dans MATRICE_ACTIVITES + parse_markdown.py. Prérequis : trouver un prof pilote théâtre.*

- [ ] **Escape Game pédagogique** | Difficile | 2-3 semaines
  *Prof choisit matière + niveau + thème. aSchool génère scénario + énigmes + épreuve finale. HTML imprimable.*

- [ ] **Google OAuth** | Difficile | 2-3 semaines
  *Réduit la friction d'inscription. Inutile avant validation des pilotes — ne pas réduire la friction si le produit n'est pas encore validé.*

- [ ] **L4 — Cohérence curriculaire inter-disciplines** | Difficile | 2-3 sessions
  *Aligne automatiquement notions et progressions entre matières. Ex : "Révolution française" Histoire 4e ↔ "Droits de l'homme" EMC 4e · "Statistiques" Maths 2nde ↔ "Analyse de données" SVT 2nde. Ajouté dans "Bientôt disponible" 12/05.*

  **3 étapes identifiées :**
  1. **Structuration des données** — Extraire les programmes officiels MEN (PDFs/HTML eduscol.fr) et les structurer en `matière → niveau → chapitre → notions → compétences`. ~96 documents (12 matières × 8 niveaux). ~1 journée de travail mécanique. Les données sont publiques, l'extraction est le seul effort.
  2. **Alignement inter-disciplines** — Similarité sémantique entre notions : deux notions liées peuvent ne partager aucun mot-clé. Solution envisagée : LLM Groq avec contexte structuré (prompt lourd) ou embeddings vectoriels. C'est le vrai défi technique.
  3. **Définir la sortie** — Ce qu'on retourne au prof : liste de rapprochements ? score de cohérence ? suggestions de projets inter-matières ? À définir avant de coder.

  > **Approche :** commencer par 1 matière × 1 niveau — si c'est utile, on élargit. Pas d'anticipation.






- [ ] **Pipeline qualité automatique** | Moyen | progressif
  *Assemblage des 6 leviers en un rapport qualité synthétique sur chaque sortie. Se construit au fil des leviers livrés.*

- [ ] **Validation texte source par LLM (Option B)** | Facile | 2h
  *Avant la génération, appel Groq rapide : "ce texte est-il un contenu pédagogique exploitable ?" → réponse JSON `{valide, raison}`. Si invalide → dialog avec explication précise. Plus intelligent que la détection heuristique (Option A livrée 13/05) — gère la langue étrangère, les formules maths, etc. À implémenter quand Option A montrera ses limites.*

---

## SESSION DÉDIÉE — Dette technique (à planifier dès que possible)

- [x] **1. Alignement noms UI ↔ code** | Livré 13/05
  *`bibliotheque` → `mon-reseau` partout : composants (`MonReseau.jsx`, `MonReseauSequences.jsx`), page IDs, routes API (`/api/mon-reseau`, `/api/mon-reseau/sequences`), Sidebar. Bug `seqFormVisible` supprimé. CORS `school.afia.fr` → `aschool.fr` dans main.py et deploy.sh. Règle de cascade ajoutée dans CLAUDE.md.*

- [x] **2. Nettoyage code mort** | Livré 13/05
  *`Bibliotheque.jsx` et `BibliothequeSequences.jsx` supprimés. Références `BIBLIOTHEQUE_PAGES`, `IconBibliotheque` renommées. Ancienne page ID `'bibliotheque'` (vestige) retirée de App.jsx.*

- [ ] **3. Dette technique complète** | À planifier après L5 + L6 + FB2
  *Périmètre : dépendances obsolètes, cohérence gestion d'erreurs API, migration React Query, documentation règles métier, revue sécurité routes. Estimation : 2 sessions dédiées.*

---

## NON RETENU — À reconsidérer plus tard

- **Capture d'écran intégrée dans le feedback** — Le bouton "Capturer l'écran" (API navigateur `getDisplayMedia`) a été supprimé le 12/05/2026. Problème : ne permet pas de sélectionner une zone précise — capture l'écran entier, une fenêtre ou un onglet, ce qui est inutile et trompeur pour un prof. Utilisateur non satisfait. Solution envisagée : script Python local (mss + tkinter) permettant de dessiner un rectangle comme le Snipping Tool Windows, le prof uploade ensuite le PNG via le formulaire. À reprendre en session dédiée quand le script Python sera prêt.

- **`logoutManager.ts` — Service de déconnexion centralisé** — Extraire la logique logout d'AuthContext vers `src/services/logoutManager.ts`. Pertinent si : (1) logout dispersé dans 5+ composants sans passer par le contexte, (2) plusieurs variantes de logout (normal / forcé admin / inactivité / SSO), (3) besoin de tests unitaires purs TS sans React. Aujourd'hui la logique est déjà centralisée dans AuthContext — ne pas créer de couche inutile. À reconsidérer si Google OAuth ou SSO est ajouté.

- **Recrutement profs pilotes via Facebook / Twitter-X** — Testé, décevant : algorithme, bruit, profil trop international pour un produit ancré dans l'Éducation nationale française. À reconsidérer si quelqu'un d'autre reprend la stratégie d'acquisition.

- **Générateur de trajectoires multi-séances** — Extension naturelle de L1 (Mode 3). Quand L1 sera solide, ajouter "trajectoire sur plusieurs semaines" est l'évolution logique. Spec dans `SPECS_LEVIERS/Leviers_non_retenus.md`.

- **Laboratoire de Simulation de Classe** — Le prof teste sa séance sur une classe virtuelle IA avant de la donner en vrai. Vision long terme : nécessite un moteur de simulation interactif, pas juste un générateur de documents. Spec dans `SPECS_LEVIERS/Leviers_non_retenus.md`.

---

## HORS SCOPE

- **Intégration ENT / Pronote** — API propriétaires, accords institutionnels, des mois de travail
- **Tableau de bord multi-profs établissement** — Nécessite concept "établissement" en BDD + rôles
- **Migration SQLite → PostgreSQL** — Uniquement si charge réelle. SQLite tient jusqu'à 500 users actifs/jour
- **Cartographie cognitive des classes** — Nécessite que les élèves interagissent avec aSchool. Contraire à la philosophie du produit (outil prof uniquement).
- **Profilage Pédagogique Dynamique (PPD)** — Même problème + contrainte RGPD lourde sur les mineurs.

---

## FAIT ✅

- [x] **Mon réseau (ex-Ma bibliothèque)** — Accordéon sidebar avec 2 sous-menus : Activités / Séquences. Partage des séquences + choix anonymat (Afficher mon nom / Rester anonyme) au moment du partage. Label "Partages de vos collègues" + bulle d'aide dans les deux pages. "Plus de détails" modal dans les deux pages. (13/05)
- [x] **Historique Activités — normalisé** — Modale "Plus de détails" fond sombre, bouton "Reprendre" (ex-Charger), suppression avec confirmation. (13/05)
- [x] **Historique Séquences — normalisé** — Modale "Plus de détails" fond sombre, bouton "Partager" + choix anonymat, suppression avec confirmation. (13/05)
- [x] **Blocage profil incomplet** — Modal bloquant dans App.jsx si prenom ou nom manquant — redirige vers Mon profil. (13/05)
- [x] **Mon journal supprimé** — Placeholder inutile (doublon Historique Activités/Séquences) retiré de sidebar et App.jsx. (13/05)
- [x] **Analyse → Historique supprimé** — Sous-menu inutile (Consignes/Équité pas encore codés, analyses one-shot). (13/05)

- [x] **Auto-versioning PATCH** — push.ps1 bumpe automatiquement le PATCH à chaque déploiement. Version initiale : 3.2.0 (12/05)
- [x] **SW mise à jour — bannière bordeaux + countdown 30s** — registerType: prompt, auto-reload 30s, bouton "Actualiser maintenant" (12/05)
- [x] **Aide — Sections complètes** — PWA offline, PWA update, Dictée vocale, OCR, Partage activités, Séquences corrigé (L1 live) (12/05)
- [x] **Bientôt disponible — mis à jour** — L2 + L4 ajoutés, Application mobile retirée (PWA livrée), sidebar "En développement" à jour (12/05)
- [x] **Aide — Refonte visuelle pro** — Layout 2 colonnes desktop, accordéon mobile inchangé (12/05)
- [x] **PWA — Complète** — Installabilité iOS, SW, responsive toutes pages, polish mobile, tests post-prod validés (12/05)
- [x] **PWA — Checklist QA complète** — 20/35 points validés en dev, 15 prod vérifiés (12/05)
- [x] **L3 — Optimiseur de séquences** — `POST /api/optimize-sequence`, 6 critères, séquence optimisée + score (11/05)
- [x] **L1 — Générateur d'orchestrations** — `POST /api/generate-sequence`, Mode standard + Mode remédiation (11/05)
- [x] **Analytique admin — 4 sous-pages** — Vue générale / Activités / Outils / Communauté (11/05)
- [x] **Menu Mes Outils amélioré** (11/05)
- [x] **Filtre automatique Mes activités par profil** — Suppression dropdowns, badge compteur bordeaux (09/05)
- [x] **Tableau analytique admin** — KPI cards, tableau prof×matière×niveau×type, top 20 types (09/05)
- [x] **Widget stats communauté** — Total plateforme + nb profs + top 3 types (09/05)
- [x] **Fiches Matières** — Backend + Frontend (09/05)
- [x] **Rebranding aSchool + migration domaine** — aschool.fr en production, school.afia.fr obsolète (11/05)
- [x] **Logo et icône finalisés** (09/05)
- [x] **Bibliothèque complète** — 73 exemples, 100% des couples matière×niveau (08/05)
- [x] **Comptes non vérifiés en admin** — Badge jaune, filtre, boutons Valider/Email/Supprimer (08/05)
- [x] **Page Maintenance BDD** — /admin/maintenance, 7 catégories orphelines, boutons Purger (08/05)
- [x] **Mail groupé admin** — /admin/communication, cases à cocher, filtre, SMTP, audit (07/05)
- [x] **Documents légaux CNIL** — ML, PC, CGU, cookies, PL finalisés dans CNIL/ (07/05)
- [x] **Partage d'activités entre collègues** — Bibliothèque + toggle partage par activité (07/05)
- [x] **Backoffice admin complet** — Sessions live, brute force, audit trail, alertes auto (02/05)
- [x] **Few-shot adaptation au style prof** — Adapte le style après 3 saves du même type (30/04)
- [x] **Export PDF** — window.print() dans ZoneResultat.jsx
- [x] **Pied de page .docx + impression CSS + signature mailto**
- [x] **Compteur "X activités créées"** — Badge bordeaux sur le total filtré par profil
