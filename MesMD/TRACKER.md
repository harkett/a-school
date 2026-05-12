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

- [ ] **FB2 — Email admin → prof** | Facile | 2h
  *Bouton "Contacter" dans AdminFeedbacks. 3 templates : Traité / Demande de précision / Remerciement. Admin peut modifier le corps avant envoi. Endpoint `POST /api/admin/feedbacks/{id}/email`. Trace en BDD : `email_sent_at` + `email_type`.*

---

### Mes Outils — Leviers pédagogiques
*Specs détaillées dans `SPECS_LEVIERS/`. Ordre d'implémentation : L2 → L5 → L6 → L4.*

- [ ] **L2 — Détecteur d'ambiguïtés cognitives** | Facile | 1 session
  *Analyse un exercice ou énoncé → zones de risque d'incompréhension + reformulations corrigées. Ajouté dans "Bientôt disponible" 12/05.*

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

- [ ] **Historique de connexions** | Facile | 3h
  *Savoir quand les profs se connectent (heure de pointe, fréquence) oriente les décisions produit.*


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
  *Prof choisit matière + niveau + thème. aSchool génère scénario + énigmes + épreuve finale. HTML imprimable.*

- [ ] **Google OAuth** | Difficile | 2-3 semaines
  *Réduit la friction d'inscription. Inutile avant validation des pilotes — ne pas réduire la friction si le produit n'est pas encore validé.*

- [ ] **L4 — Cohérence curriculaire inter-disciplines** | Difficile | 2-3 sessions
  *Aligne automatiquement notions et progressions entre toutes les matières. Le plus complexe — nécessite les programmes officiels. En dernier. Ajouté dans "Bientôt disponible" 12/05.*

- [ ] **Pipeline qualité automatique** | Moyen | progressif
  *Assemblage des 6 leviers en un rapport qualité synthétique sur chaque sortie. Se construit au fil des leviers livrés.*

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
