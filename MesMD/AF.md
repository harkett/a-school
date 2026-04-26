# A-SCHOOL — À Faire

> **Vérifié le : 25/04/2026 — État : à jour**

---

## Phase 2 — Ce qui a été fait

- [x] Déploiement VPS complet (Nginx, HTTPS Let's Encrypt, DNS Infomaniak)
- [x] App accessible sur https://school.afia.fr
- [x] Dictée vocale via Groq Whisper API
- [x] Export Word (.docx) et texte (.txt)
- [x] Résultat persistant avec bouton Fermer
- [x] Saisie libre désactivée dans les combos
- [x] Interface nettoyée (emojis supprimés, zones Upload/Micro côte à côte)
- [x] Nouveau design (header bleu dégradé, curseur main sur combos, nombre de questions libre)
- [x] `push.ps1` automatisé — push GitHub + restart VPS en une commande
- [x] `run.ps1` créé — lancer en local en une commande
- [x] Magic link email — fonctionne (lien reçu + connexion OK)
- [x] Notification admin `harketti@afia.fr` à chaque connexion — fonctionne avec `from_email = "contact@afia.fr"` (compte SMTP authentifié)
- [ ] Google OAuth — en attente (config secrets.toml à corriger, provider "google" non reconnu)

---

## Outils provisoires (à remplacer)

| Outil actuel | Remplacé par | Quand | Raison |
|---|---|---|---|
| Groq Whisper API (dictée) | faster-whisper local sur VPS | Phase 2b | Confidentialité données élèves, gratuit illimité |
| Streamlit | React ou Vue.js | Phase 4 | Limites UI, scalabilité |
| SQLite | PostgreSQL | Phase 3 | Multi-utilisateurs, robustesse |
| Fichiers `.env` | Variables d'environnement Docker | Phase 3 | Sécurité, déploiement propre |

---

## À faire — Court terme (Phase 2 / 2b)

- [ ] **Tester massivement avec de vrais profs** — HAUTE / Faible — Minimum 5 profs, 3 matières différentes pour découvrir ce qui manque vraiment
- [ ] **Tester la dictée avec la prof pilote** — HAUTE / Faible — Valider avant de continuer
- [ ] **Zone micro visuellement identique à Upload** — MOYENNE / Haute — Limite Streamlit, nécessite composant React (Phase 4)
- [ ] **Basculer dictée sur faster-whisper local** — MOYENNE / Moyenne — Installer sur VPS, modèle medium français (~1.5 Go)
- [ ] **Sélecteur de microphone dans l'interface** — BASSE / Moyenne — Utile si plusieurs micros disponibles
- [ ] **Export PDF** — BASSE / Moyenne — Ajouter après validation prof pilote

---

## À faire — Moyen terme (Phase 3)

- [ ] **Ajouter d'autres matières (histoire, maths, SVT...)** — HAUTE / Faible — Juste des prompts en BDD, pas de code — c'est là que l'outil devient une plateforme
- [ ] **Compte utilisateur minimal** — HAUTE / Moyenne — Email + mot de passe pour retrouver ses activités passées, créer de la fidélité
- [ ] **Backend FastAPI** — HAUTE / Haute — Remplace Streamlit comme moteur
- [ ] **Base de données SQLite (puis PostgreSQL)** — HAUTE / Moyenne — Stockage prompts, activités, historique
- [ ] **Interface admin web** — HAUTE / Haute — Ajouter/modifier activités sans code
- [ ] **Authentification enseignants** — HAUTE / Moyenne — Login/mot de passe par établissement
- [ ] **Historique des activités par prof** — MOYENNE / Moyenne — Retrouver ses activités passées
- [ ] **Docker (backend + frontend + BDD)** — MOYENNE / Haute — Isolation, déploiement propre
- [x] **Procédure de mise à jour automatisée** — `push.ps1` gère push GitHub + restart VPS en une seule commande

---

## À faire — Long terme (Phase 4)

- [ ] **Frontend React/Vue** — HAUTE / Très haute — Remplace Streamlit, UI pro
- [ ] **Partage d'activités entre collègues** — MOYENNE / Haute
- [ ] **Tableau de bord par établissement** — MOYENNE / Haute
- [ ] **Toutes matières (maths, histoire...)** — MOYENNE / Moyenne — Ajouter prompts en BDD via admin
- [ ] **Import PDF (extraits de manuels)** — BASSE / Haute — OCR + parsing
- [ ] **Application mobile (PWA)** — BASSE / Haute
- [ ] **Intégration ENT (Pronote...)** — BASSE / Très haute
- [ ] **Gestion abonnements (freemium)** — BASSE / Très haute

---

## Limite connue Streamlit (pour info)

Streamlit ne permet pas d'envelopper un composant externe (comme le micro) dans un `<div>` HTML personnalisé. La zone "Dicter" ne peut pas être rendue visuellement identique à la zone "Upload" sans un composant React custom. Ce sera résolu en Phase 4 avec le frontend React.

---

## Prochaine session recommandée

1. **Test prof pilote** — faire tester school.afia.fr à la professeure de français 4e
2. **Recueillir les retours** — noter ce qui manque, ce qui gêne
3. **Décider** : corriger les retours pilote OU démarrer Phase 2b (dictée locale)

---

## Architecture Auth — implémentée le 25/04/2026

Flow : `Signup → Email vérification → Login → JWT cookies`

### Endpoints
| Méthode | Route | Description |
|---|---|---|
| POST | `/api/auth/signup` | Inscription (email + mot de passe) |
| POST | `/api/auth/login` | Connexion → cookies JWT httpOnly |
| GET | `/api/auth/verify-email?token=` | Activation compte depuis email |
| POST | `/api/auth/refresh` | Renouvellement access token |
| GET | `/api/auth/me` | Utilisateur courant |
| POST | `/api/auth/logout` | Révocation + suppression cookies |

### Sécurité intégrée
- Mots de passe : **bcrypt** (passlib)
- JWT : **HS256** (python-jose) — secret via `JWT_SECRET` dans `.env`
- Access token : **15 min** — cookie httpOnly `aschool_access`
- Refresh token : **30 jours** — cookie httpOnly `aschool_refresh`, **hash SHA-256 stocké en base** (révocable)
- Brute force : **5 tentatives → blocage 30 min**
- Email normalisé **lowercase** avant stockage et comparaison
- Token email : **usage unique** (`used=True`), expiration 60 min
- Message d'erreur générique (jamais "email inconnu")

### Tables SQLite (`data/aschool.db`)
- `users` — id, email (UNIQUE), password_hash, is_verified, created_at, **last_login**, **failed_attempts**, **locked_until**
- `email_tokens` — token (UNIQUE), email, purpose, expires_at, **used**
- `refresh_tokens` — user_email, **token_hash** (SHA-256), expires_at, **revoked**

### À ajouter en Phase 3
- Mot de passe oublié (réutilise `email_tokens` avec `purpose=reset_password`)
- Rate limiting Nginx sur `/api/auth/login` et `/api/auth/signup`
- Nettoyage automatique des tokens expirés (cron)
- Migration SQLite → PostgreSQL si montée en charge

### 2FA — décision 25/04/2026 : non nécessaire
La sécurité actuelle (email vérifié + bcrypt + JWT + brute force bloqué) est suffisante pour une plateforme pédagogique.
La 2FA ajouterait une friction inutile pour des enseignants peu habitués aux apps d'authentification.
À reconsidérer uniquement si : données élèves sensibles ou exigence contractuelle d'un établissement.
