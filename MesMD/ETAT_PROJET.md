# A-SCHOOL — État du Projet

> **Rôle : référence principale du projet — à lire en premier avant toute session de développement.**
>
> Ce document contient :
> - L'état de toutes les fonctionnalités (✅ livré / 📋 prévu), avec le détail de chaque bloc
> - Les routes API complètes : auth, profil, admin — méthodes, chemins, descriptions
> - Le schéma complet des tables SQLite (`users`, `email_tokens`, `refresh_tokens`, `connexion_logs`, `feedbacks`, `activites_sauvegardees`) avec leurs colonnes
> - Les variables d'environnement attendues (local et VPS)
> - Les corrections techniques planifiées (activités manquantes dans certaines matières)
> - Les améliorations futures prévues (PWA mobile, export PDF, OAuth, partage...)
>
> **À consulter quand** : on veut savoir si une fonctionnalité existe, vérifier le nom exact d'une route API, retrouver un champ BDD, ou connaître les variables d'environnement.
>
> **Ne contient pas** : les décisions techniques passées (→ `DECISIONS_TECHNIQUES.md`), le plan de lancement et calendrier (→ `PLAN_LANCEMENT_ASCHOOL.md`), la configuration SMTP détaillée (→ `EMAILS.md`), le plan et état du backoffice admin (→ `PLAN_BACKOFFICE_FASTAPI.md`), le diagnostic auth (→ `AUTH_DIAGNOSTIC.md`).
>
> **Vérifié le : 30/04/2026 — À mettre à jour à chaque fonctionnalité livrée**

---

## 1. État général

| Domaine | Fonctionnalité | Statut |
|---|---|---|
| **Génération** | 12 matières (FR, HG, Maths, Phys-Chimie, SVT, SES, NSI, Philo, LV, Techno, Arts, EPS) | ✅ Livré |
| **Génération** | 43 types d'activités (matrice 12 matières × 26 types) | ✅ Livré |
| **Génération** | Correction incluse en option | ✅ Livré |
| **Génération** | Niveaux 6e → Terminale | ✅ Livré |
| **Génération** | Niveau Supérieur (bandeau "en développement") | ✅ Livré |
| **Saisie** | Saisie directe (copier-coller) | ✅ Livré |
| **Saisie** | Import fichier .txt | ✅ Livré |
| **Saisie** | Dictée vocale (Groq Whisper) | ✅ Livré |
| **Saisie** | OCR image JPG/PNG | ✅ Livré |
| **Export** | Word .docx | ✅ Livré |
| **Export** | Texte brut .txt | ✅ Livré |
| **Export** | Impression directe | ✅ Livré |
| **Export** | Envoi par email (mailto:) | ✅ Livré |
| **Compte** | Inscription email + vérification | ✅ Livré |
| **Compte** | Connexion JWT (httpOnly cookies) | ✅ Livré |
| **Compte** | Profil prof (prénom, nom, matière, niveau) | ✅ Livré |
| **Historique** | Mes activités (sauvegarde automatique) | ✅ Livré |
| **Admin** | Panel complet (Connexions, Activités, Feedbacks, Profs) | ✅ Livré |
| **Admin** | Logs avec matière | ✅ Livré |
| **Admin** | CSAT (moyenne, distribution, % satisfaits) | ✅ Livré |
| **Feedback** | Feedback catégorie + message | ✅ Livré |
| **Feedback** | Notation étoiles + commentaire | ✅ Livré |
| **Feedback** | Notifications SMTP direct (Infomaniak) | ✅ Livré |
| **Adaptation** | Few-shot adaptation au style prof | ✅ Livré 30/04/2026 |
| **Déploiement** | VPS school.afia.fr | ✅ Livré |
| **Futur** | Compteur "X activités créées" (Mes activités) | 📋 Prévu |
| **Futur** | Export PDF | 📋 Prévu |
| **Compte** | Mot de passe oublié | ✅ Livré 02/05/2026 |
| **Futur** | Google OAuth | 📋 Prévu |
| **Futur** | Application mobile (PWA) | 📋 Prévu |
| **Futur** | Partage d'activités entre collègues | 📋 Prévu |
| **Futur** | Intégration ENT (Pronote) | 📋 Prévu |
| **Futur** | Tableau de bord multi-profs établissement | 📋 Prévu |
| **Futur** | Migration SQLite → PostgreSQL | 📋 Prévu (si montée en charge) |

---

## 2. Fonctionnalités livrées

### Génération d'activités
- **12 matières** : Français, Histoire-Géographie, Mathématiques, Physique-Chimie, SVT, SES, NSI, Philosophie, Langues Vivantes, Technologie, Arts, EPS
- **43 types d'activités** répartis sur la matrice 12 matières — voir [MATRICE_ACTIVITES_ASCHOOL.md](MATRICE_ACTIVITES_ASCHOOL.md)
- Sous-types par activité (3 à 9 selon le type)
- Correction incluse en option
- Niveaux : 6e, 5e, 4e, 3e, 2nde, 1re, Terminale, Supérieur *(bandeau "en développement")*
- Résultat en 5 à 10 secondes

### Saisie du texte source
- Saisie directe (copier-coller)
- Import fichier `.txt`
- **Dictée vocale** (Groq Whisper API) — opérationnel
- **OCR image JPG/PNG** (lecture de scans, manuels, photocopies) — opérationnel

### Export et usage immédiat
- Téléchargement Word `.docx` — prêt à modifier
- Téléchargement texte brut `.txt`
- Impression directe depuis le navigateur
- Envoi par email via `mailto:` (corps du mail pré-rempli)

### Compte & Authentification
Flow : `Signup → Email vérification → Login → JWT cookies`
- Inscription par email avec vérification obligatoire
- Connexion sécurisée JWT httpOnly
- Profil prof en BDD : prénom, nom, matière, niveau
- Anti brute-force : 5 tentatives → blocage 30 min

### Historique personnel
- Toutes les activités générées sauvegardées automatiquement en BDD
- Accessible depuis "Mes activités"
- Rechargeable en un clic pour régénérer ou modifier les paramètres

### Admin panel
- **AdminLogs** : historique des connexions avec matière
- **AdminActivités** : toutes les activités générées
- **AdminFeedbacks** : feedbacks + notations CSAT (moyenne, distribution, % satisfaits)
- **AdminProfils** : liste des profs vérifiés + filtre + édition inline

### Feedback & Notation
- **Feedback** : catégorie (Problème / Suggestion / Question) + message
- **Notation** : 1 à 5 étoiles + commentaire optionnel
- SMTP direct Infomaniak — notification à `FEEDBACK_NOTIFY_EMAIL`
- **A-FEEDBACK retiré définitivement le 28/04/2026 — ne jamais réintroduire**

---

## 3. Prochaines étapes (par priorité)

1. **Déploiement VPS** — push en cours → school.afia.fr — PRIORITÉ #1
2. **Validation few-shot avec les pilotes** — tester l'adaptation avec de vrais profs, ajuster
3. **Support niveau Supérieur** — activités dédiées BTS/prépa/licence

---

## 4. Architecture technique

### Endpoints auth
| Méthode | Route | Description |
|---|---|---|
| POST | `/api/auth/signup` | Inscription (email + matière + mot de passe) |
| POST | `/api/auth/login` | Connexion → cookies JWT httpOnly |
| GET | `/api/auth/verify-email?token=` | Activation compte depuis email |
| POST | `/api/auth/refresh` | Renouvellement access token |
| GET | `/api/auth/me` | Profil courant (email, subject, prenom, nom, niveau) |
| POST | `/api/auth/logout` | Révocation + suppression cookies |

### Endpoints profil
| Méthode | Route | Description |
|---|---|---|
| GET | `/api/user/profile` | Profil complet du prof connecté |
| PATCH | `/api/user/profile` | Mise à jour profil (prenom, nom, subject, niveau) |

### Endpoints admin
| Méthode | Route | Description |
|---|---|---|
| GET | `/api/admin/users` | Liste tous les profs vérifiés |
| PATCH | `/api/admin/user/{email}` | Édite le profil d'un prof |
| GET | `/api/admin/logs` | Historique connexions avec matière |
| GET | `/api/admin/feedbacks` | Feedbacks + notations |

### Sécurité
- Mots de passe : **bcrypt**
- JWT : **HS256** — secret via `JWT_SECRET` dans `.env`
- Access token : **15 min** — cookie httpOnly `aschool_access`
- Refresh token : **30 jours** — hash SHA-256 en base, révocable
- Brute force : **5 tentatives → blocage 30 min**
- CORS : GET, POST, PATCH autorisés

### Tables SQLite (`data/aschool.db`)
- `users` — id, email, password_hash, is_verified, created_at, last_login, failed_attempts, locked_until, **subject, prenom, nom, niveau**
- `email_tokens` — token, email, purpose, expires_at, used
- `refresh_tokens` — user_email, token_hash, expires_at, revoked
- `connexion_logs` — email, action, ip, created_at
- `feedbacks` — user_email, **type** (feedback|notation), message, rating, category, created_at
- `activites_sauvegardees` — user_email, activite_key, activite_label, niveau, sous_type, nb, avec_correction, texte_source, resultat

---

## 5. Variables d'environnement

```env
GROQ_API_KEY=...
JWT_SECRET=...
SMTP_HOST=mail.infomaniak.com
SMTP_PORT=587
SMTP_USERNAME=harketti@afia.fr
SMTP_PASSWORD=...
SMTP_FROM=A-SCHOOL <contact@afia.fr>
APP_URL=https://school.afia.fr
ADMIN_USERNAME=...
ADMIN_PASSWORD=...
FEEDBACK_NOTIFY_EMAIL=contact@afia.fr
```

---

## 6. Corrections à planifier

- ~~**Fiche de révision manquante en Français**~~ — ✅ Livré le 08/05/2026 : `fr_fiche_revision` dans `src/prompts.py` + `activities.py`
- **Fiche pédagogique manquante en HG** — ajouter dans `activities.py` + prompt dans `prompts.py` (modèle : `fiche_pedagogique` Français)
- **Français : 15 types dans le code** — certains docs mentionnent 16, corriger au passage lors de la session dev

---

## 7. Améliorations futures

- **Compteur "X activités créées"** dans Mes activités — rétention + fierté utilisateur
- **Analyse IA des notations** (Groq) — pertinent à partir de 20-30 notations avec commentaire
- **Support niveau Supérieur** — activités dédiées BTS/prépa/licence
- **Aide spécifique par matière** — subject en BDD, infrastructure prête
- **Mot de passe oublié** — réutilise `email_tokens` avec `purpose=reset_password`
- **Export PDF**
- **Application mobile (PWA)**
- **Partage d'activités entre collègues**
- **Google OAuth**
- **Intégration ENT (Pronote)**
- **Tableau de bord multi-profs établissement**
- **Migration SQLite → PostgreSQL** — si montée en charge

---

*A-SCHOOL — school.afia.fr — Référence projet — 30/04/2026*
