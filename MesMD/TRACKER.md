# A-SCHOOL — TRACKER

> **Source de vérité unique.** Toute idée, tâche ou livraison est ici — nulle part ailleurs.
> Specs techniques détaillées → `SPECS_LEVIERS/`

> Note dev : Bannière "Bientôt disponible" sidebar prof → `Sidebar.jsx`, bloc `{!collapsed && ...}` en bas.

---

## PRIORITAIRE

- [x] **PWA — Installabilité** | Livré 12/05
  *IOSInstallBanner, bfcache fix, cross-tab logout, SW update banner — testé iOS Safari.*

- [x] **PWA — Service Worker** | Livré 12/05
  *SW opérationnel, offline banner, cache propre au logout, update détectée automatiquement.*

- [ ] **PWA — Responsive mobile (pages restantes)** | Moyen | 1 session
  *Pages à finir : ZoneResultat (résultat généré), Bibliothèque, Aide. Cœur fait : header, sidebar, Accueil, Mes Outils, Mes Activités.*

---

## IMPORTANT

### Mes Outils — Leviers pédagogiques
*Specs détaillées dans `SPECS_LEVIERS/`. Ordre d'implémentation : L2 → L5 → L6 → L4.*

- [ ] **L2 — Détecteur d'ambiguïtés cognitives** | Facile | 1 session
  *Analyse un exercice ou énoncé → zones de risque d'incompréhension + reformulations corrigées.*

- [ ] **L5 — Analyseur de consignes** | Facile | 1 session
  *Analyse chirurgicale d'une consigne isolée → clarté, charge cognitive, erreurs typiques + version optimisée.*

- [ ] **L6 — Détecteur d'équité pédagogique** | Facile | 1 session
  *Audit d'une évaluation → 3 biais : contenu, difficulté, émotionnel.*

---

- [ ] **Aide — Refonte visuelle pro** | Moyen | 1 session
  *L'accordéon actuel est fonctionnel mais pas pro. Solution validée : layout 2 colonnes style docs (Stripe/Tailwind) — nav latérale sticky à gauche (Installation / Créer / Comprendre / Problèmes), contenu à droite au clic. Mobile : accordéon inchangé. Pour démarrer la session : dire "on fait la refonte de l'Aide".*

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

- [ ] **Historique de connexions** | Facile | 3h
  *Savoir quand les profs se connectent (heure de pointe, fréquence) oriente les décisions produit.*

- [ ] **PWA — Responsive mobile** | Difficile | 2-3 semaines
  *Interface adaptée 390px. À prioriser si l'usage mobile est confirmé par les retours pilotes.*

- [ ] **PWA — Polish mobile** | Moyen | 2-3 jours
  *Splash screen, touch 44px — finitions qui font la différence entre "acceptable" et "natif".*

- [ ] **PWA — Tests post-prod (Safari iPhone / Chrome Android / Edge Windows)** | Facile | 1 jour
  *Après déploiement sur aschool.fr : vérifier invite installation, icône écran d'accueil, comportement offline et banner hors connexion sur les 3 plateformes cibles.*

---

## OPTIONNEL

- [ ] **Quiz interactif élèves** | Difficile | 2 semaines
  *Prof génère QCM → lien public → élèves répondent sur téléphone → résultats live. Différenciateur fort. Spec v1 validée 07/05.*


- [ ] **Aide spécifique par matière** | Moyen | 3-5 jours
  *Infrastructure prête (subject en BDD). Textes d'aide adaptés = meilleure prise en main pour chaque prof.*

- [ ] **Admin — Menu Activités en groupe** | Facile | 2h
  *Prépare la modération des activités partagées. Pattern `group: true` déjà disponible dans AdminLayout.*

- [ ] **Support niveau Supérieur (BTS/prépa/licence)** | Difficile | 2 semaines
  *Ouvre un segment nouveau — formateurs BTS/prépa. Surtout du travail de prompts et d'activités.*

- [ ] **Théâtre — 13e matière** | Moyen | 1-2 semaines
  *Définir activités dans MATRICE_ACTIVITES + parse_markdown.py. Prérequis : trouver un prof pilote théâtre.*

- [ ] **Escape Game pédagogique** | Difficile | 2-3 semaines
  *Prof choisit matière + niveau + thème. A-SCHOOL génère scénario + énigmes + épreuve finale. HTML imprimable.*

- [ ] **Google OAuth** | Difficile | 2-3 semaines
  *Réduit la friction d'inscription. Inutile avant validation des pilotes — ne pas réduire la friction si le produit n'est pas encore validé.*

- [ ] **L4 — Cohérence curriculaire inter-disciplines** | Difficile | 2-3 sessions
  *Aligne automatiquement notions et progressions entre toutes les matières. Le plus complexe — nécessite les programmes officiels. En dernier.*

- [ ] **Pipeline qualité automatique** | Moyen | progressif
  *Assemblage des 6 leviers en un rapport qualité synthétique sur chaque sortie. Se construit au fil des leviers livrés.*

---

## NON RETENU — À reconsidérer plus tard

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

- [x] **PWA — Checklist QA complète** — 20/35 points validés en dev, 15 prod vérifiés (12/05)
- [x] **PWA — Responsive mobile v1** — Header, sidebar collapse, Accueil, Mes Outils liste verticale, Mes Activités bouton visible (12/05)
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
