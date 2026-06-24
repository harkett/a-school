# CLAUDE.md — Référence permanente aSchool

> Chargé automatiquement à chaque session. Règles + contexte technique — source unique de vérité.

---

## 🔍 Règle n°1 — Vérifier la cohérence AVANT de toucher (absolue)

Avant toute modification, ou tout appui, sur un élément du projet — document, fichier de code, n'importe quoi — **vérifier d'abord qu'il est cohérent** :
- le **lire en entier** (pas le diff, pas en survol) ;
- contrôler que ses **liens / chemins / références existent** réellement ;
- contrôler que son **contenu n'est pas périmé** ni contredit par la réalité (code, git, autres docs).

Cette vérification est **systématique et ne dépend d'aucune demande** : elle précède toute action. Si une incohérence est trouvée, **la signaler avant d'agir** — ne jamais construire par-dessus. (Règle née le 09/06/2026 : sans elle, je bâtis sur du périmé jusqu'à ce qu'on m'arrête.)

---

## Vision

Plateforme web de génération d'activités pédagogiques pour les enseignants (collège → supérieur), sans compétences techniques requises. Construit étape par étape, validé avec des profs pilotes réels.

**Tagline few-shot :** "À partir de quelques utilisations, aSchool s'adapte à votre façon de formuler les exercices."

**Vision multi-niveaux (cap, non engagé) :** aSchool décliné par niveau — Crèche · Maternelle · Primaire · Collège · Lycée · Supérieur. Détail + statut : `MesMD/TABLEAU-DE-BORD.md` → § « Direction produit ».

---

## Périmètre produit — aSchool est POUR l'enseignant (règle absolue)

Le **public unique d'aSchool, à tous les niveaux** (Crèche → Supérieur), est **l'enseignant**. Une fonctionnalité qui ne sert pas le prof à enseigner est **hors périmètre**, même si elle est « pédagogique ». Sont **exclus** : tout ce qui s'adresse directement à l'étudiant (emploi, CV, portfolio personnel) ou à un autre public (conseillers d'orientation, recruteurs). Tout ce que l'IA produit pour les étudiants est généré **par le prof**, qui reste l'unique utilisateur de l'outil.

---

## Stack technique

| Composant | Détail |
|---|---|
| Backend | FastAPI — `backend/main.py` — port 8001 (local, cohabitation) / 8001 (VPS) |
| Frontend | React + Vite — `frontend/` — port 5173 |
| BDD | SQLite (local + VPS) |
| IA | Groq API — `llama-3.3-70b-versatile` |
| Dictée | Groq Whisper API — batch `whisper-large-v3` (streaming Deepgram gelé sur `wip/deepgram-streaming`) |
| Auth profs | email + bcrypt + JWT (python-jose) + httpOnly cookies |
| Auth admin | Cookie `aschool_admin` — JWT séparé `{"role": "admin"}` |
| SMTP | mail.infomaniak.com:587 — `SMTP_USERNAME=harketti@afia.fr` |

---

## VPS production

| Info | Valeur |
|---|---|
| URL | https://aschool.fr |
| IP | 83.228.245.163 |
| SSH | ubuntu@83.228.245.163 |
| Chemin | /var/www/aSchool/ |
| Service | `aschool.service` (systemd) |
| Port | 8001 (8000 occupé par Django AFIA-FR) |
| OS | Ubuntu 24.04 LTS |
| SSL expiry | 2026-07-15 |

**Statut : opérationnel en production — des profs réels l'utilisent. Ne jamais remettre en doute.**

---

## Scripts clés

```powershell
.\Scripts\run.ps1              # Lance backend (:8001) + frontend (:5173) — régénère activities auto · param -BackendPort (défaut 8001)
.\Scripts\push.ps1             # Sauvegarde GitHub UNIQUEMENT (git push seul) — ne déploie PAS la prod, ne bump PAS la version
.\Scripts\deploy.ps1 "message" # Bump PATCH auto → commit → push GitHub → déploiement VPS (geste sous validation explicite)
```

**Deux gestes, deux scripts, jamais confondus :** `git push` / `push.ps1` = sauvegarde GitHub, n'affecte **pas** la prod. `deploy.ps1` = déploiement VPS, **sous validation explicite**.

Version courante : **3.2.9** — PATCH incrémenté automatiquement par `deploy.ps1` (`npm version patch`). MINOR et MAJOR = manuels.

**Cohabitation locale :** le port 8000 local est souvent pris par un autre projet (A-VIEWCAM). `run.ps1` lance donc aSchool sur **8001** (paramètre `-BackendPort`, défaut 8001), ne tue jamais le 8000 voisin, et passe `VITE_API_PORT` au frontend (proxy Vite configurable via `process.env.VITE_API_PORT`). Cohérent avec le VPS (aSchool en 8001 derrière Django AFIA-FR).

---

## Catalogue d'activités

- **Source de vérité :** `MesMD/MATRICE_ACTIVITES_ASCHOOL.md`
- **Générateur :** `parse_markdown.py` → `src/generated_activities.py` — **NE PAS ÉDITER MANUELLEMENT**
- **Runtime :** `src/activities.py` construit l'index au démarrage
- 12 matières × 43 activités uniques = 140 entrées

**Matières :** Français, Histoire-Géo, Philosophie, Mathématiques, NSI, Physique-Chimie, SVT, Technologie, SES, Langues Vivantes, Arts, EPS

---

## Taxonomie des outils — note de conception (classement, pas mode d'emploi prof)

> Grille pour RANGER tout outil prof. À usage interne (nous / futur dev), jamais
> dans l'aide prof. Actée le 12/06/2026. Le réagencement du menu selon cette
> grille est un chantier SÉPARÉ, non encore fait. Une version prof simplifiée de
> cette logique est rédigée et **réservée pour le chantier menu** (à publier dans
> l'Aide AVEC le réagencement, pour que l'aide colle au menu réel — pas avant).

**4 verbes, pas un fourre-tout :**

| Verbe | Définition | Exemples |
|---|---|---|
| **CRÉER** | Produire un contenu **de zéro** (point de départ vierge) | Activité, Séquence — et les *types de sortie* : Mémo flash, Fiche, Escape game, Supports de créativité, Quiz… |
| **ANALYSER** | Examiner un contenu **existant** et constater (sans le modifier) | Ambiguïtés, Consigne, Équité |
| **AMÉLIORER** | Agir sur l'**existant** pour l'optimiser (même finalité, en mieux) | Optimiseur de séquences |
| **ADAPTER** | Transformer un contenu **existant** pour un besoin élève (re-ciblage) | Différenciation (proactif, AVANT : DYS/FLE/approfondissement) + Remédiation (réactif, APRÈS : combler un écart constaté) |

**Critère de tri d'un nouvel outil (la question qui tranche) :**
« Point de départ vierge (**Créer**) OU action sur un contenu déjà là ? »
Si action sur l'existant → constater (**Analyser**) / optimiser à finalité égale
(**Améliorer**) / re-cibler pour un autre besoin (**Adapter**).

**Reclassements actés :**
- **Remédiation n'est PAS un type créé de zéro** → elle transforme l'existant →
  **ADAPTER** (avec Différenciation). Générée de zéro, elle serait indiscernable
  d'une Activité « plus facile » → sans valeur propre. C'est sa transformation de
  l'existant qui la justifie.
- **Différenciation n'est pas une simple « option »** → c'est une opération
  **ADAPTER** à part entière.

**Ne pas confondre les niveaux :**
- Les **verbes** (Créer/Analyser/Améliorer/Adapter) = familles d'outils (frères).
- Sous Créer/Activité, les **types de sortie** (QCM, fiche, mémo flash…) = enfants, pas frères.
- Les **options** de génération (avec/sans correction, nb de questions, visuels…) = réglages, pas des outils.

**Hors menu (à ne pas remonter au rang d'outil) :**
- Les fonctions « méta séquence » (versioning, affinage interactif, sortie JSON)
  ne sont PAS des entrées de menu → fonctions internes à l'écran Séquence.

---

## Routes API principales

### Auth (`backend/routers/auth.py`)
| Méthode | Route | Description |
|---|---|---|
| POST | `/api/auth/signup` | Inscription |
| POST | `/api/auth/login` | Connexion → cookies JWT |
| GET | `/api/auth/verify-email?token=` | Activation compte |
| POST | `/api/auth/resend-verification` | Renvoyer l'email de vérification |
| POST | `/api/auth/request-reset` | Demande reset mot de passe |
| POST | `/api/auth/reset-password` | Reset mot de passe (token + nouveau mdp) |
| POST | `/api/auth/refresh` | Renouvellement access token |
| GET | `/api/auth/me` | Profil courant |
| POST | `/api/auth/logout` | Révocation + suppression cookies |

### Prof (routes principales)
| Méthode | Route | Description |
|---|---|---|
| GET / PATCH | `/api/user/profile` | Profil prof |
| POST | `/api/generate` | Générer une activité (auth JWT + few-shot) |
| POST | `/api/generate-sequence` | L1 — Générateur d'orchestrations |
| POST | `/api/optimize-sequence` | L3 — Optimiseur de séquences |
| POST | `/api/detect-ambiguites` | L2 — Détecteur d'ambiguïtés cognitives |
| POST | `/api/ocr` | OCR image JPG/PNG |
| GET | `/api/mes-activites` | Historique activités |
| GET | `/api/mes-activites/{id}` | Détail activité |
| DELETE | `/api/mes-activites/{id}` | Supprimer activité |
| POST | `/api/feedback` | Envoyer feedback ou notation |
| GET | `/api/mes-feedbacks` | Feedbacks du prof connecté |
| GET | `/api/dashboard` | Données page Accueil (dernière activité, séquence) |
| GET | `/api/mon-reseau` | Activités partagées par les collègues |
| GET | `/api/mon-reseau/sequences` | Séquences partagées |

### Admin — voir `PLAN_BACKOFFICE_FASTAPI.md` pour le détail complet.

---

## Cycle vs Niveau — distinction absolue (ne jamais confondre)

**Un cycle et un niveau sont deux choses différentes.** Un **niveau** = une seule année scolaire (ex. la 4e). Un **cycle** = un **groupe de niveaux** (ex. le cycle 4 de l'EN = 5e + 4e + 3e). Le cycle **contient** des niveaux : c'est le **contenant**, le niveau est le **contenu**. Jamais l'un pour l'autre — surtout en codant (`cycle_id` ≠ `niveau_id`, requête « par cycle » ≠ « par niveau »).

Dans aSchool : table `cycles` = Crèche · Maternelle · Primaire · Collège · Lycée · Supérieur ; table `niveaux` = 6e, 5e, 4e, 3e, 2nde… (chaque niveau rattaché à un cycle). **Piège connu** : l'Éducation nationale appelle aussi « cycle » ses **cycles 1 à 4**, qui regroupent les niveaux **autrement** et **ne s'alignent pas** sur nos cycles (ex. la 6e est en cycle 3 EN mais dans notre cycle Collège). En cas de doute, relire `seed_programmes.py` (CYCLES vs NIVEAUX) avant d'agir.

---

## Tables BDD (`data/aschool.db`)

### Tables auth + profil
- `users` — email, password_hash, is_verified, created_at, last_login, failed_attempts, locked_until, subject, prenom, nom, niveau
- `email_tokens` — token, email, purpose (verify_email / reset_password), expires_at, used
- `refresh_tokens` — user_email, token_hash, expires_at, revoked
- `connexion_logs` — email, action, ip, created_at

### Tables app
- `feedbacks` — user_email, type (feedback|notation), message, rating, category, statut, created_at
- `activites_sauvegardees` — user_email, activite_key, activite_label, niveau, sous_type, nb, avec_correction, texte_source, resultat

### Tables backoffice (voir section Auth ci-dessus)
`UserSession`, `FailedLoginAttempt`, `AdminAuditLog`, `AdminAlert`

---

## Variables d'environnement

```env
GROQ_API_KEY=...
JWT_SECRET=...
SMTP_HOST=mail.infomaniak.com
SMTP_PORT=587
SMTP_USERNAME=contact@aschool.fr
SMTP_PASSWORD=...
SMTP_FROM=aSchool <contact@aschool.fr>
FEEDBACK_FROM=aSchool Feedback <feedback@aschool.fr>
FEEDBACK_NOTIFY_EMAIL=contact@aschool.fr
APP_URL=https://aschool.fr
ADMIN_USERNAME=...
ADMIN_PASSWORD=...
ADMIN_EMAIL=...
ENV=production
```

---

## Streamlit est MORT — depuis le 24/04/2026

Streamlit a été abandonné définitivement le 24/04/2026. Le projet tourne sur **FastAPI + React**.

**Fichiers morts supprimés :**
- `app.py` — ancienne UI Streamlit (supprimé)
- `src/auth.py` — ancienne auth Streamlit avec magic links (supprimé)
- `.streamlit/secrets.toml` — config Streamlit (supprimé)

**Ce qui n'existe plus :**
- Magic links (remplacé par email token 60 min + JWT httpOnly cookies)
- `st.secrets` (remplacé par `os.getenv()`)
- `send_magic_link()` / `notify_admin_connexion()` (supprimées)
- `streamlit_cookies_controller`, `streamlit_mic_recorder` (supprimés)

**Règle absolue :** toute référence à Streamlit, magic link, `st.secrets`, `send_magic_link`, `notify_admin_connexion` trouvée dans le code ou la doc est du **code mort à supprimer immédiatement**, sans demander.

---

## SMTP — Règles absolues

- Ne jamais changer de fournisseur SMTP sans demande explicite
- `SMTP_FROM` = `aSchool <contact@aschool.fr>` (emails vers les profs)
- `FEEDBACK_FROM` = `aSchool Feedback <feedback@aschool.fr>` (notifications admin)
- Tout le code SMTP passe par `_smtp_send()` dans `backend/auth.py` — ne jamais créer de connexion SMTP ailleurs
- `feedback_client.py` est deprecated — ne jamais réutiliser
- Voir `MesMD/EMAILS.md` avant toute modification email

**Action en attente :** Infomaniak force l'adresse d'expédition à correspondre au compte authentifié — les emails partent avec `harketti@afia.fr` au lieu de `contact@aschool.fr`. Solution : acheter les boîtes `contact@aschool.fr` + `feedback@aschool.fr` (~3€/mois chacune) et mettre à jour `SMTP_USERNAME`/`SMTP_PASSWORD` dans `.env`. Le code n'a pas besoin de changer.

---

## Auth — Ne pas toucher

L'auth JWT (bcrypt + python-jose, httpOnly cookies) fonctionne parfaitement depuis le 25/04/2026. Ne jamais modifier `backend/auth.py` ni `backend/routers/auth.py` sans demande explicite.

**Routes sensibles** (request-reset, resend-verification) : toujours retourner `{"status": "ok"}` qu'il y ait un utilisateur ou non — anti-énumération d'adresses email.

**Architecture profs :**
- Cookie `aschool_refresh` — JWT avec `type: "refresh"`, `sub: email`, `jti: session_key`
- Middleware `UserSessionMiddleware` crée une entrée `UserSession` à chaque requête prof

**Architecture admin :**
- Cookie `aschool_admin` — JWT avec `{"sub": "admin", "role": "admin"}` — sans `type: "refresh"`
- Le middleware NE crée PAS de `UserSession` pour l'admin
- Garde-fou `force-logout` : refus 403 si `user_email == ADMIN_EMAIL` (env var)

**Tables BDD backoffice :**

| Table | Usage |
|---|---|
| `UserSession` | Sessions actives des profs (middleware) |
| `FailedLoginAttempt` | Tentatives échouées sur `/admin/login` |
| `AdminAuditLog` | Toutes les actions admin (FORCE_LOGOUT, DELETE_USER…) |
| `AdminAlert` | Alertes auto (CPU, disque, brute force) — APScheduler 5 min |

---

## Déploiement VPS — Convention obligatoire

Toutes les applications web sont dans `/var/www/<nom-app>/` — standard Linux FHS.

| Application | Chemin | .env |
|---|---|---|
| aSchool | `/var/www/aSchool/` | `/var/www/aSchool/.env` |
| AFIA-FR | `/home/ubuntu/AFIA-FR/` ⚠️ | `/home/ubuntu/AFIA-FR/backend/.env` ⚠️ à migrer |

Ne jamais suggérer `/home/ubuntu/` pour un nouveau déploiement — toujours `/var/www/`.

---

## Renommage — Règle de cascade obligatoire

Dès qu'un nom UI change (page, section, composant, route), produire dans la même réponse la liste complète des impacts : fichiers frontend, page IDs dans App.jsx, composants, routes backend, noms de fichiers. Demander si on traite maintenant ou si on note dans le TABLEAU DE BORD sous "En attente de cascade". Ne jamais clore la session sans que chaque impact soit traité ou noté.

---

## Workflow obligatoire

Proposer → valider → coder → tester. Ne jamais coder sans validation explicite de l'utilisateur.

---

## Vocabulaire — le mot « blocage / bloqué par » est banni (règle absolue)

Le mot **« blocage »** et la formule **« bloqué par »** ne doivent apparaître **nulle part** dans le projet (TRACKER, docs, code, commits, UI). Logique : un obstacle qu'on peut lever, on le lève tout de suite (règle du caillou) → ce n'est plus un blocage ; un obstacle qu'on ne peut pas lever maintenant est une **tâche en attente** qui part au backlog → pas un blocage non plus. Le mot n'a donc jamais lieu d'être.

Vocabulaire de remplacement, selon le sens :
- **« dépend de »** — dépendance technique entre deux tâches réelles du tracker (B a besoin que A soit fait d'abord).
- **« en attente de »** — la tâche attend un élément extérieur ou non encore planifiable (info admin, arbitrage non tranché).
- **« prérequis / impératif »** — condition dure avant une action (ex. avant `deploy.ps1`).
- **« désactiver » / « refuser » / « neutraliser »** — pour une action de code qui empêche quelque chose (un bouton, un insert). Jamais « bloquer ».

---

## Règles de conduite Claude — absolues

1. Pas de réponse hâtive — prendre le temps de lire avant de répondre.
2. Ne jamais présenter une supposition comme une certitude. Si l'info n'est pas connue : dire « je ne sais pas ».
3. Vérifier la doc officielle avant d'affirmer un fait technique. La doc fait foi, pas la mémoire.
4. Rester strictement dans le périmètre du bloc en cours. Une tâche = un bloc, pas de « tant qu'on y est ».
5. 🔒 Ne rien exécuter sans demande explicite — analyser, proposer, attendre validation.
6. Ne pas lire de fichiers locaux non fournis explicitement dans la tâche.
7. Une chose à la fois — traiter un point, le finir, passer au suivant.
8. 🔒 Tout point critique codé s'accompagne de son test automatisé, écrit dans la même session, sinon la fonction est inachevée.
9. 🔒 **Joignabilité AVANT la chaîne.** Pour toute affirmation « live / vert / fonctionnel », le **premier** contrôle est : *l'entrée est-elle exposée à l'utilisateur ?* (point d'entrée non gaté dans l'UI — pas `disabled`, pas « bientôt »). Seulement **après**, vérifier la chaîne de code. Un chemin de code qui marche mais que le prof ne peut pas atteindre n'est **PAS** fonctionnel — le dire « live » est faux. (Règle née le 14/06/2026 : « Consigne fonctionnel » affirmé sur la foi du backend, alors que la sidebar la masquait « bientôt ».)

---

## Synchronisation afia.fr — Règle absolue

À chaque push **MINOR ou MAJOR**, appliquer cette procédure :

**Claude (session aSchool) :**
1. Générer automatiquement le contenu complet et mis à jour de `School.jsx` reflétant l'état réel de l'app en production
2. Le produire prêt à coller — bloc JSX complet, rien à reformater

**Utilisateur (session AFIA-FR, à chaud après le push) :**
1. Ouvrir `D:\AFIA-FR\frontend-web\src\pages\School.jsx`
2. Remplacer le contenu par le bloc généré par Claude
3. Déployer AFIA-FR

**Ne pas modifier AFIA-FR depuis ce projet.** Claude produit, l'utilisateur applique.

PATCH = aucune action requise.

---

## Nom du produit — aSchool

Le nom affiché dans toute l'interface, les textes, les boutons et les messages est **aSchool** (a minuscule, S majuscule). Jamais "ASchool", jamais "IA".

**Ressources graphiques (hors projet — ne pas modifier depuis ici) :**
- Charte graphique : `D:\A-PUB\PUB_ASCHOOL\PLAN_CAMPAGNE-ASCHOOL\Charte_Graphique.md`
- Brief logo principal : `D:\A-PUB\PUB_ASCHOOL\PLAN_CAMPAGNE-ASCHOOL\Logo_aSchool.md`
- Brief logo vertical : `D:\A-PUB\PUB_ASCHOOL\PLAN_CAMPAGNE-ASCHOOL\Logo_Vertical.md`
- Brief icône carrée : `D:\A-PUB\PUB_ASCHOOL\PLAN_CAMPAGNE-ASCHOOL\Icone8carre.md`

---

## Bulles d'aide — Règle absolue

Tout bouton, lien d'action ou icône cliquable doit avoir un attribut `title="..."` décrivant ce qu'il fait. Sans exception. Vérifier également que le texte est lisible : `color: white !important` sur tout fond foncé.

---

## Incohérences & erreurs de saisie — modale bloquante (règle absolue, toute l'app)

**Toute incohérence ou erreur de saisie = boîte de dialogue bloquante qui explique le problème en langage humain et force la correction. JAMAIS un avertissement passif inline.**

Un marqueur passif (étiquette grise à côté d'un champ, texte « à mettre à jour », badge discret) **n'est pas un garde-fou** : c'est un raisonnement de machine (« je signale »). L'humain ne le lit pas, ne comprend pas qu'il doit agir, ferme la page — et reste dans un état faux que le système l'a **laissé** créer. Un logiciel sérieux **arrête** l'utilisateur et **l'oblige** à corriger.

Donc, à chaque fois qu'un état devient incohérent ou invalide :
1. **Modale** (overlay plein écran, impossible à ignorer) — réutiliser `showError()` de `frontend/src/errorDialog.js`, rendu par `App.jsx`.
2. **Message en langage de l'utilisateur** (prof) : dire le **problème** ET l'**action attendue**. Pas de jargon, pas de « mettre à jour ».
3. **Forcer la correction** : neutraliser la valeur fautive et **bloquer l'action principale** (bouton désactivé) tant que l'état n'est pas redevenu cohérent. Pas d'échappatoire.
4. Pour un cas important, ne pas hésiter à être **très explicite**, quitte à enchaîner deux confirmations.

**Cas fondateur (12/06/2026) :** `MonProfil.jsx` — matière du profil incohérente avec le niveau choisi (ex. « Français » + « Master »). Déclenchée **à l'ouverture** (profil hérité) ET **à chaque changement de niveau**, modale + matière vidée + `Valider` bloqué (`profilPretAValider`, `utils/profil.js`). C'est le patron à répliquer partout.

---

## Pilotage — deux docs, deux rôles, un seul pilote par couche (règle absolue)

**Deux documents vivants, jamais deux pilotes qui se contredisent :**

| Document | Fait foi sur | Pour qui |
|---|---|---|
| `MesMD/TRACKER.md` | **Pilotage** — ordre + statut (☐ 🔄 ⏸️ ✅) + dépendance en clair | l'utilisateur (vue lisible d'un coup d'œil) |
| `MesMD/TABLEAU-DE-BORD.md` | **Détail** — score, description, synergies, audits, RAG + **journal FAIT** | Claude (référence de fond) |

> **Règle de tenue (absolue) :** Le TRACKER fait foi sur le pilotage (ordre + statut + dépendance). Le TABLEAU fait foi sur le détail (score, description, journal FAIT). Le statut est mis à jour dans le TRACKER, dans la même réponse où l'on démarre ou finit une tâche. Le tableau est synchronisé en fin de session, pour le journal FAIT seulement.

> Les fiches `MesMD/BOUSSOLE/Dxx.md` restent la **couche détail** d'un chantier.

- **Le statut vit à UN SEUL endroit : le TRACKER.** Le tableau de bord ne porte plus de colonne « État ». Garder un statut des deux côtés recrée le double pilote — interdit.
- **L'ordre appartient à l'utilisateur** (priorité P1/P2/P3 dans le TRACKER) ; **les dépendances techniques à Claude**, écrites noir sur blanc dans le TRACKER et **prouvées en citant la fiche** — jamais gardées de tête.
- **Aucun autre document ne ré-ordonne les priorités.** Tout plan, diagnostic ou audit ponctuel est **absorbé** en chantier `Dxx` (détail dans le TABLEAU) — jamais un pilote concurrent.
- **Toute idée mentionnée en session → notée immédiatement dans le réservoir du `TABLEAU-DE-BORD.md`**, dans la même réponse. Quand l'utilisateur décide de l'attaquer, elle remonte en une ligne dans le TRACKER.
- **Les checklists de chantier ☐/☑** vivent dans les fiches `Dxx`.
- **Pas de doc-archive dans l'arbre de travail.** Les anciens états (vieux CR, plans clôturés) vivent dans l'**historique git**, pas dans un fichier vivant. Ne jamais recréer de document d'archive dans l'arbre. Claude ne consulte l'historique git **que sur demande explicite** — un état daté lu spontanément induit en erreur (c'est ce piège qui a motivé la règle).
- **Périmètre de lecture = `main` uniquement.** Le contenu des autres branches (ex. `wip/deepgram-streaming` = chantier Deepgram gelé) n'est jamais lu spontanément — c'est du git, donc lecture **sur demande explicite** seulement. Mes outils par défaut ne voient que le checkout courant ; je ne lance pas de commande git large (`git grep --all`, `git log --all`, checkout d'une autre branche) de moi-même.
- **Durable → `CLAUDE.md` ; les trackers ne portent que l'éphémère.** Toute information qui doit rester **pérenne** (décision d'architecture, règle, choix techno durable) vit dans **`CLAUDE.md`** (et/ou la mémoire Claude) — **jamais seulement dans un tracker**. Les trackers de **chantier** (`TRACKER_REFORME.md`, `TRACKER_FOURNISSEURS_IA.md`…) sont **jetables** : une fois le chantier fini, archivés/supprimés. **Nuance : `TRACKER.md` et `TABLEAU-DE-BORD.md` sont des docs de pilotage *vivants/continus*** — ils ne sont pas jetés, **mais n'hébergent pas non plus une décision pérenne** : leur rôle est le pilotage/détail **courant**, pas la mémoire durable. Un tracker peut **pointer** vers la décision dans `CLAUDE.md`, jamais en être l'unique dépositaire.

---

## Cadence de travail — une ligne du TRACKER par session (règle par défaut)

**Par défaut : une session = une ligne du `TRACKER.md`.** On finit et on
committe une ligne avant d'attaquer la suivante — jamais plusieurs en
parallèle. C'est ce qui garde le statut du TRACKER honnête (rien à moitié fait).

Deux exceptions, **jugées par Claude au moment d'« attaquer XX »,
signalées AVANT de coder, tranchées par l'utilisateur** :
- **Ligne minuscule** (cosmétique, ~30 min) → Claude propose de la regrouper
  avec la ligne voisine.
- **Gros chantier** (plusieurs semaines) → Claude propose de le découper en
  plusieurs sessions.

**Découpage d'un gros chantier — « stable » n'est pas « fini » :** chaque
sous-session se clôt sur un état **stable et committable** (le code tourne,
rien de cassé, c'est committé), pas forcément sur la feature entière livrée.
On ne laisse jamais de code cassé entre deux sessions, mais on ne s'impose
pas de tout boucler en une fois — intenable sur un chantier de semaines.

---

## Règles UI permanentes

- **Profil = source unique** pour matière et niveau. Jamais de `<select>` matière/niveau dans les features — toujours lire depuis le profil.
- **Aucune liste de référence en dur dans le frontend.** Les matières — et toute liste de référence (niveaux, cycles…) — se lisent depuis la base via l'API, jamais une liste codée en dur dans un composant. Pour les matières : hook `useMatieres` → `GET /api/matieres?categorie=secondaire`. Une liste en dur se périme en silence le jour où la donnée bouge. (Règle née 15/06/2026, P5.10 : 8 écrans dupliquaient la même liste de 12 matières.)
- **Bouton d'action principale** = classe `btn-primary` + icône SVG + `title=` tooltip + positionné en bas à droite. Référence : bouton "Générer l'activité" dans `Parametres.jsx`.
- **Header** : `height: 65px`, `overflow: hidden`. **Logo** : `height: 140px`. INTOUCHABLES.
- **Tagline** "Générateur d'activités pédagogiques" = `<span>` HTML blanc dans le header, toujours présent, jamais dans le PNG seul.
- Pas d'emojis dans l'interface.
- Navigateur de référence : **Edge** (jamais Chrome dans les instructions).
- **Menu / navigation = du général au détaillé.** Tout menu se range en **familles (catégories) → options**, jamais une liste à plat où l'on ajoute une entrée de plus à chaque page. Toute nouvelle page se loge **sous une famille existante**. Standard pro appliqué au back-office le 23/06 (5 catégories + accordéon repliable, chevron visible, hiérarchie de tailles titre>option, liseré **bleu = section active** / **bordeaux #A63045 = page active**, shell figé sidebar+header+footer, header = fil d'Ariane « catégorie › page »). Même esprit que la taxonomie outils prof (« ne pas confondre les niveaux »).

### Layout général

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER  [Logo | Générateur d'activités pédagogiques        │
│           | matière | nom prénom | Se déconnecter]          │
├────────────┬────────────────────────────────────────────────┤
│            │                                                │
│  SIDEBAR   │  CONTENU (selon la page active)               │
│            │                                                │
│  Accueil   │                                                │
│  Mes       │                                                │
│  outils ▾  │                                                │
│   Activité │                                                │
│    · Créer │                                                │
│    · Histo.│                                                │
│   Séquence │                                                │
│    · Créer │                                                │
│    · Optim.│                                                │
│    · Histo.│                                                │
│   Analyse  │                                                │
│    · Ambig.│                                                │
│    · Consig│                                                │
│    · Équité│                                                │
│  Mon       │                                                │
│  réseau ▾  │                                                │
│   Activités│                                                │
│   Séquences│                                                │
│  Mon profil│                                                │
│  Mes feedbk│                                                │
│  Mes stats │                                                │
│  ────────  │                                                │
│  Bientôt   │                                                │
│  Aide      │                                                │
│  Avis      │                                                │
│  À propos  │                                                │
├────────────┴────────────────────────────────────────────────┤
│  FOOTER                                                     │
└─────────────────────────────────────────────────────────────┘
```

### Couleurs

| Rôle | Valeur |
|---|---|
| Bordeaux accent | `#A63045` |
| Bordeaux hover | `#832538` |
| Bleu primaire | `#1F6EEB` |
| Bleu hover | `#1558C0` |

### Classes boutons

| Classe | Usage | Style |
|---|---|---|
| `btn-primary` | Action principale (Générer…) | Bleu, blanc, icône SVG + texte |
| `btn-action` | Actions secondaires (Fichier, Dicter…) | Gris `#E5E7EB`, bordure, icône SVG + texte |
| `btn-secondary` | Télécharger, Fermer… | Blanc, bordure, icône SVG + texte |

---

## Responsive mobile — Règle PWA

Toute adaptation mobile utilise `const isMobile = window.innerWidth < 768` défini localement dans chaque composant. Ne jamais casser le layout desktop (> 768px). Patterns établis :
- Sidebar : `useState(() => window.innerWidth < 768)` → repliée par défaut sur mobile
- Header : tagline masquée, matière sous le nom, bouton "Déconnecter" raccourci
- Grilles `1fr Xpx` → `1fr` sur mobile
- Boutons hover-only → toujours visibles sur mobile (`isMobile || hovered`)
- Longs blocs tutoriel/aide → masqués sur mobile (`!isMobile`)

---

## Fournisseur IA — Règle absolue

Deux fournisseurs, pour pouvoir basculer de l'un à l'autre : **Groq** (`llama-3.3-70b-versatile`) par défaut + **Anthropic** (Claude) comme cible de bascule. Gemini n'est **pas** banni — l'adaptateur `_gemini` existe et reste fonctionnel, mais **dormant** : ni défaut, ni cible.

---

## Aide — Règle absolue

Dès qu'une fonctionnalité est livrée, sa section Aide est rédigée dans la **même session** — à chaud, pendant que c'est frais. Jamais en retard. Jamais reporté à "plus tard".

---

## Base vectorielle (ChromaDB) — Règle absolue

La base ChromaDB (`backend/rag/chroma_db/`) est une **donnée GÉNÉRÉE**, pas du code : « données ≠ code ». Source de vérité = le **PDF du référentiel** (`REFERENTIELS/`) + le **script d'ingestion**. Elle **ne se commite JAMAIS dans git** : `.gitignore` sur `backend/rag/chroma_db/`, **reconstruite au déploiement** via `python -m backend.rag.ingest_referentiel` (étape `[2.5/7]` de `deploy/deploy.sh`).

(Acté + exécuté le 23/06 — corrige un raccourci de POC : la base avait été commitée par commodité le 18/05, jamais re-questionné. Conséquence : au 1er déploiement, le `git pull` retire la base commitée et l'étape d'ingestion la reconstruit.)

---

## Secrets — Règle absolue

Ne jamais afficher mots de passe, clés API ou tokens en clair dans la discussion, même si l'utilisateur le demande.

**Où vivent les secrets.** Les secrets (clés API, mots de passe, `JWT_SECRET`, tokens) vivent dans le `.env` — hors git, hors base — un par environnement (local + VPS prod). **Jamais en base, jamais administrables depuis l'UI admin.** À l'échelle actuelle (prod avec profs pilotes), le `.env` bien tenu est le bon niveau : **être en prod ne change rien**. **Seul déclencheur d'une marche suivante = une explosion d'aSchool** (croissance massive, gros volume d'utilisateurs réels) → gestionnaire de secrets cloud (Secret Manager Infomaniak ou autre), **pas un HSM**. YAGNI jusque-là.

---

## Sync docs — Règle de fin de session

En fin de chaque session de dev importante : mettre à jour ce fichier (version, règles nouvelles) + synchroniser TABLEAU-DE-BORD.md.
