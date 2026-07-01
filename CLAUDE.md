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

## 🔒 Règle de périmètre — le dossier aSchool, rien d'autre (absolue, permanente)

**Le seul périmètre de travail est le dossier `D:\A-SCHOOL` et son environnement direct** (comme un dossier ouvert dans VS Code — ce dossier et son environnement, c'est tout le monde de Claude). En dehors de ce dossier : **interdiction absolue** d'aller chercher, lire, scanner ou fouiller quoi que ce soit — **surtout pas le disque `C:\`, ni Windows, ni les autres installations / bases / applications** de la machine. Elles appartiennent à d'autres projets de Harketti et **ne regardent pas aSchool**.

Si quelque chose **hors** du dossier aSchool est nécessaire (un binaire, un chemin, une info système), **le demander explicitement à Harketti et attendre son GO** — ou le laisser fournir la réponse lui-même. **On ne sort jamais du dossier de son propre chef.**

(Règle née le 30/06/2026 : un scan de tout Windows est tombé sur le PostgreSQL d'une **autre** application, pris à tort pour celui d'aSchool ; tout un faux diagnostic bâti dessus, et la suppression des données d'un projet tiers **qui fonctionne** évitée de justesse. Une journée perdue. Ne se reproduit plus.)

> **Seule exception, explicitement désignée par Harketti :** le cluster PostgreSQL d'aSchool vit hors du dossier projet, dans `C:\Users\harketti\PostgreSQL\16` (port 5433). On n'y touche **que** parce que Harketti l'a nommément rattaché à aSchool. **Tout autre PostgreSQL de la machine est hors périmètre** (notamment l'install v17 `Program Files` / port 5432 = autres applications).

---

## Vision

### 🏆 Le cap — en lettres d'or (ambition fondatrice, absolue)

> **aSchool vise à être un logiciel PROFESSIONNEL — pas un bricolage, pas un prototype, pas « un truc qui marche à peu près ». L'ambition n'est pas d'être *un* bon outil pour profs : c'est d'être *LE* logiciel de référence de sa catégorie, au standard professionnel le plus exigeant, celui qui place la barre si haut qu'il ne laisse pas de place à un autre.**
>
> **Socle non négociable : aSchool doit tourner autour d'une BASE DE DONNÉES RELATIONNELLE professionnelle. TOUTES les données doivent vivre en base — matières, niveaux, types d'activité, prompts, référentiels, réglages, contenus. Rien de métier ne doit être codé en dur. Une donnée en dur est un défaut à corriger, jamais un état acceptable.**
>
> **Source de la donnée : aSchool ne doit rien s'inventer. Son contenu pédagogique doit être EXTRAIT des référentiels officiels, puis affiné et ciblé par un RAG (recherche augmentée) qui filtre et ne retient que ce qui est réellement pertinent pour le couple matière + niveau. Pas de référentiel pour un couple → aSchool ne génère pas plutôt que d'inventer.**
>
> **Chaque ligne de code, chaque écran, chaque décision se juge à cette aune : « est-ce digne d'un logiciel professionnel de référence, adossé à la base, ancré sur le référentiel ? » Si la réponse est non, ce n'est pas fini.**

---

## 📜 Script éphémère — le SEUL moyen de remplir la base (règle absolue)

**Le mot « seed » est banni. On dit « script éphémère ».**

Toutes les données métier **doivent vivre** dans la **BASE** — **aucune donnée métier ne doit être codée en dur** (cap fondateur ci-dessus). Quand il faut **remplir la base**, on n'écrit **jamais** un fichier permanent qui porte des données en dur (comme l'était `seed_programmes.py`, supprimé). On écrit un **script éphémère**.

**Définition.** Un script éphémère est un script **jetable**, créé dans un **seul but** : lire une **source officielle**, **alimenter la base une fois**, puis **être supprimé**. Il ne fait **jamais** partie de l'application, il ne **reste jamais** dans le projet.

**Cycle de vie, non négociable :** **créer → alimenter la base → supprimer.** Une fois la base remplie, le script **disparaît** (historique git si besoin). Un script qui *reste* dans le projet en portant de la donnée métier est un **défaut** — c'est exactement ce qu'on ne veut plus.

**Distinction clé :** ce n'est pas l'usage d'un script qui est interdit, c'est qu'un script **persiste** en portant la donnée. Remplir puis disparaître = sain. Rester avec des données en dur = à virer.

---

Plateforme web de génération d'activités pédagogiques pour les enseignants, sans compétences techniques requises. Construit étape par étape, validé avec des profs pilotes réels.

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
| BDD | **PostgreSQL** (psycopg, port 5433) — moteur **unique** ; SQLite **banni** (garde-fou `backend/database.py` qui refuse de démarrer sans `DATABASE_URL` PostgreSQL ; tests sur base dédiée `aschool_test` via `conftest.py`, 3 verrous). pgvector pour le RAG. |
| IA | Groq API — `llama-3.3-70b-versatile` |
| Dictée | Groq Whisper API — batch `whisper-large-v3` (streaming Deepgram gelé sur `wip/deepgram-streaming`) |
| Auth profs | email + bcrypt + JWT (python-jose) + httpOnly cookies |
| Auth admin | Cookie `aschool_admin` — JWT séparé `{"role": "admin"}` |
| Emails | Infomaniak (SMTP) — voir § Gestion des emails |

---

## VPS production

| Info | Valeur |
|---|---|
| URL | https://aschool.fr |
| IP | 83.228.245.163 |
| SSH | ubuntu@83.228.245.163 |
| Chemin | /var/www/a-school/ |
| Service | `aschool.service` (systemd) |
| Port | 8001 (8000 occupé par Django AFIA-FR) |
| OS | Ubuntu 24.04.4 LTS |
| SSL expiry | 2026-08-05 |

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

Source de vérité = `backend/routers/` (le code fait foi).

---

## Cycle vs Niveau — distinction absolue (ne jamais confondre)

**Un cycle et un niveau sont deux choses différentes.** Un **niveau** = une seule année scolaire (ex. la 4e). Un **cycle** = un **groupe de niveaux** (ex. le cycle 4 de l'EN = 5e + 4e + 3e). Le cycle **contient** des niveaux : c'est le **contenant**, le niveau est le **contenu**. Jamais l'un pour l'autre — surtout en codant (`cycle_id` ≠ `niveau_id`, requête « par cycle » ≠ « par niveau »).

Dans aSchool : table `cycles` = Crèche · Maternelle · Primaire · Collège · Lycée · Supérieur ; table `niveaux` = 6e, 5e, 4e, 3e, 2nde… (chaque niveau rattaché à un cycle). **Piège connu** : l'Éducation nationale appelle aussi « cycle » ses **cycles 1 à 4**, qui regroupent les niveaux **autrement** et **ne s'alignent pas** sur nos cycles (ex. la 6e est en cycle 3 EN mais dans notre cycle Collège).

---

## Tables BDD (PostgreSQL — base `aschool`)

Source de vérité = `backend/models_db.py` (le code fait foi).

---

## Variables d'environnement

Source de vérité = `.env.example` (le code fait foi). Secrets jamais affichés, jamais en base (cf. règle Secrets).

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

## Gestion des emails

Tout ce qui concerne les emails est regroupé ici. Le détail complet (chaque
adresse, chaque fonction d'envoi) vit dans `MesMD/EMAILS.md`, à lire avant toute
modification email.

### Fournisseur
aSchool envoie ses emails via Infomaniak (`mail.infomaniak.com`, port `587`).
Ne jamais changer de fournisseur sans demande explicite.

### Connexion — le point qui nous a coûté cher
Pour se connecter au serveur d'envoi, Infomaniak refuse le mot de passe du
webmail. Il faut un mot de passe dédié, généré dans Infomaniak (Service Mail,
puis l'adresse, puis Appareils, puis Ajouter un appareil). C'est ce mot de passe
que l'on met dans le `.env`. Sans lui, la connexion est refusée avec l'erreur
« 535 Invalid login or password ».

### Où vivent les réglages
Toutes les adresses et le mot de passe vivent dans le `.env`. On ne les recopie
jamais dans ce fichier, jamais dans le code, et on ne les affiche jamais en clair.
Le compte de connexion et l'adresse d'expéditeur doivent être la même adresse,
car Infomaniak l'exige. Les emails d'aSchool sont **envoyés depuis** le domaine
aschool.fr (identité expéditrice). Seule exception : les alertes techniques
d'administration sont **reçues** sur `ADMIN_EMAIL`, qui reste une adresse afia.fr
par choix.

### Une seule porte de sortie
Tout le code d'envoi passe par la fonction `_smtp_send()` dans `backend/auth.py`.
Ne jamais ouvrir une connexion SMTP ailleurs.

### Qui reçoit quoi
Les emails aux profs (activation, bienvenue, mot de passe oublié) partent vers
l'adresse de chaque prof. Les notifications que l'administrateur lit (feedbacks,
nouvelles inscriptions) arrivent dans l'adresse `FEEDBACK_NOTIFY_EMAIL` du `.env`.
Les alertes techniques du serveur arrivent dans `ADMIN_EMAIL` du `.env`.

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

---

## Déploiement VPS — Convention obligatoire

Toutes les applications web sont dans `/var/www/<nom-app>/` — standard Linux FHS.

| Application | Chemin | .env |
|---|---|---|
| aSchool | `/var/www/a-school/` | `/var/www/a-school/.env` |
| AFIA-FR | `/home/ubuntu/AFIA-FR/` ⚠️ | `/home/ubuntu/AFIA-FR/backend/.env` ⚠️ à migrer |

Ne jamais suggérer `/home/ubuntu/` pour un nouveau déploiement — toujours `/var/www/`.

---

## Renommage — Règle de cascade obligatoire

Dès qu'un nom UI change (page, section, composant, route), produire dans la même réponse la liste complète des impacts : fichiers frontend, page IDs dans App.jsx, composants, routes backend, noms de fichiers. Demander si on traite maintenant ou si on note dans le TABLEAU DE BORD sous "En attente de cascade". Ne jamais clore la session sans que chaque impact soit traité ou noté.

---

## Workflow obligatoire

Proposer → valider → coder → **tester en deux étages, dans cet ordre, jamais sautés** :

1. **Proposer** — analyser, proposer, attendre validation. Jamais coder sans validation explicite.
2. **Coder** — une tâche à la fois.
3. **Étage 1 — Claude teste, pour de vrai.** Avant toute affirmation, j'**exécute réellement** ce que j'ai produit, avec mes propres moyens (lancer le script, le test, le build, l'appel…). **Deviner est interdit** : « ça devrait marcher » n'est pas un test. Je ne dis « c'est bon, j'en suis sûr » **que si je l'ai exécuté et que j'en suis réellement sûr**. Si je ne peux pas l'exécuter, je le dis explicitement (« non testé ») — jamais de fausse certitude.
4. **Étage 2 — l'utilisateur teste derrière.** Une fois mon étage validé, l'utilisateur teste à son tour, en conditions réelles d'**admin ou de prof**, **chaque fois que c'est possible** (parfois aucun geste réel n'atteint le cas → on s'appuie alors sur l'étage 1 + les tests auto, et je le dis).

Deviner au lieu de tester = faute. (Règle durcie le 24/06/2026 : script de diagnostic committé sans avoir jamais été lancé, bug révélé seulement à la 1re vraie exécution.)

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

Le nom du produit s'écrit **aSchool** : un « a » minuscule et un « S » majuscule. On ne l'écrit jamais « ASchool ».

**Choix de marque.** aSchool est présenté aux utilisateurs comme un logiciel pédagogique, jamais comme « une IA ». Dans tout ce que voit l'utilisateur (les écrans, les textes, les boutons, les messages), on n'affiche jamais les mots « IA » ni « intelligence artificielle ». Cette règle concerne seulement ce que voit l'utilisateur. Elle ne concerne pas les documents internes comme ce fichier, le code, ou les messages de commit.

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

### Le cycle de vie d'une idée (du berceau au rangement)

Une idée **naît dans la discussion** et se travaille dans un **tracker éphémère**
(son berceau) : on l'ancre, on la pèse, on la mûrit tranquillement. **Tant qu'elle
est une idée, elle reste dans l'éphémère — elle ne touche rien d'autre** (ni TRACKER,
ni tableau de bord, ni fiche).

Quand elle est **mûre et validée par l'utilisateur**, elle n'est plus une idée :
c'est un **travail**. Là seulement elle s'éclate dans les documents permanents :
- **TRACKER** → une ligne simple et humaine, le jour où on décide de la faire
  (ce que l'utilisateur suit).
- **Fiche Dxx (BOUSSOLE)** → tout son détail technique.
- **Tableau de bord** → elle apparaît dans l'inventaire des travaux, avec un lien
  vers sa fiche.

Si ce qu'on a tranché est une **règle durable** (pas une tâche) → elle va dans
**`CLAUDE.md`**, jamais dans un tracker.

Le tracker éphémère, une fois vidé de cette idée, **finit à la poubelle**
(historique git).

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
- **Aucune liste de référence en dur dans le frontend.** Les matières — et toute liste de référence (niveaux, cycles…) — se lisent depuis la base via l'API, jamais une liste codée en dur dans un composant. Pour les matières : hook `useMatieres` → `GET /api/matieres`. Une liste en dur se périme en silence le jour où la donnée bouge. (Règle née 15/06/2026, P5.10 : 8 écrans dupliquaient la même liste de 12 matières.)
- **Bouton d'action principale** = classe `btn-primary` + icône SVG + `title=` tooltip + positionné en bas à droite. Référence : bouton "Générer l'activité" dans `App.jsx` (écran « Créer une activité »).
- **Header** : `height: 65px`, `overflow: hidden`. **Logo** : `height: 140px`. INTOUCHABLES.
- **Tagline** "Générateur d'activités pédagogiques" = `<span>` HTML blanc dans le header, toujours présent, jamais dans le PNG seul.
- Pas d'emojis dans l'interface.
- Navigateur de référence : **Edge** (jamais Chrome dans les instructions).
- **Menu / navigation = du général au détaillé.** Tout menu se range en **familles (catégories) → options**, jamais une liste à plat où l'on ajoute une entrée de plus à chaque page. Toute nouvelle page se loge **sous une famille existante**. Standard pro appliqué au back-office le 23/06 (5 catégories + accordéon repliable, chevron visible, hiérarchie de tailles titre>option, liseré **bleu = section active** / **bordeaux #A63045 = page active**, shell figé sidebar+header+footer, header = fil d'Ariane « catégorie › page »). Même esprit que la taxonomie outils prof (« ne pas confondre les niveaux »).

### Layout général

Shell figé : **header + sidebar + contenu + footer**. Le menu réel (source de vérité) = `frontend/src/components/Sidebar.jsx` — ne pas le recopier ici (il dérive).

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

## Base vectorielle (PostgreSQL / pgvector) — Règle absolue

Les vecteurs du RAG vivent dans **PostgreSQL** (table `referentiel_chunks`, colonne `embedding` de type `vector` via **pgvector**) — **plus aucun dossier `chroma_db/`**, ChromaDB a été **retiré définitivement le 29/06/2026**. Comme toute base, c'est une **donnée GÉNÉRÉE**, pas du code : « données ≠ code ». Source de vérité = le **PDF du référentiel** (`REFERENTIELS/`) + le **script d'ingestion** (`backend/rag/pgvector_store.py`). Les vecteurs ne vivent **jamais dans git** (ils sont en base), **reconstruits au déploiement** via `python -m backend.rag.pgvector_store` (étape `[2.5/7]` de `deploy/deploy.sh`).

Prérequis d'ingestion : la table `referentiel_chunks` doit être **migrée** (Alembic) et la ligne `referentiels` du couple présente — sinon l'ingestion lève une **erreur claire** (jamais une base trouée en silence).

(Bascule pgvector actée le 29/06/2026 — éradication de ChromaDB : code, dépendance et dossier `chroma_db/` supprimés ; le moteur RAG est désormais PostgreSQL unique, cohérent avec « SQLite banni ».)

---

## Référentiel = source de vérité unique (règle absolue)

Le **référentiel officiel** du couple matière+niveau est **LA source de vérité**. **Un couple sans référentiel ne génère pas** : il reste « en construction ». La génération (`/api/generate`) **doit s'ancrer sur le référentiel du couple** — décision tranchée le **26/06/2026**, **pas encore branchée** : aujourd'hui seul le bouton « Tester un exemple » (`/api/exemple-referentiel`) lit le référentiel ; `/api/generate` n'en lit **aucun** (le niveau n'est qu'une étiquette dans le prompt).

Intégrer un nouveau couple suit la procédure de [`REFERENTIELS/README.md`](REFERENTIELS/README.md) : l'admin choisit cycle+niveau dans des **combos** (liste fermée) → aSchool génère le **dossier-clé** = nom du niveau normalisé en `MAJUSCULES_UNDERSCORE` (ex. `BTS_CIEL_OPTION_A/`, unique et non renommable) → l'IA **propose** le PDF officiel → l'admin **valide** → découper / **relier** / tester. Deux preuves distinctes : « le bon référentiel remonte » (indexation) ≠ « la génération s'appuie dessus » (cœur).

**Reste à faire (chantier à part) :** « automatiser le Temps 3 » — routage couple→référentiel **data-driven** (aujourd'hui en dur dans `exemple_referentiel.py`) **+ branchement du cœur** `/api/generate`.

---

## Secrets — Règle absolue

Ne jamais afficher mots de passe, clés API ou tokens en clair dans la discussion, même si l'utilisateur le demande.

**Où vivent les secrets.** Les secrets (clés API, mots de passe, `JWT_SECRET`, tokens) vivent dans le `.env` — hors git, hors base — un par environnement (local + VPS prod). **Jamais en base, jamais administrables depuis l'UI admin.** À l'échelle actuelle (prod avec profs pilotes), le `.env` bien tenu est le bon niveau : **être en prod ne change rien**. **Seul déclencheur d'une marche suivante = une explosion d'aSchool** (croissance massive, gros volume d'utilisateurs réels) → gestionnaire de secrets cloud (Secret Manager Infomaniak ou autre), **pas un HSM**. YAGNI jusque-là.

---

## Sync docs — Règle de fin de session

En fin de chaque session de dev importante : mettre à jour ce fichier (version, règles nouvelles) + synchroniser TABLEAU-DE-BORD.md.
