# A-SCHOOL — À Faire

> **Vérifié le : 28/04/2026 — État : à jour**

---

## Phase 3 — Ce qui a été livré (28/04/2026)

- [x] Stack FastAPI + React + Tailwind + SQLite en production
- [x] Auth email + mot de passe + JWT (access 15 min / refresh 30 jours)
- [x] 12 matières (Français, HG, Maths, Phys-Chimie, SVT, SES, NSI, Philo, LV, Technologie, Arts, EPS)
- [x] Admin panel complet (Connexions, Activités, Feedbacks, Profs)
- [x] **Profil prof** : prénom, nom, matière, niveau — côté prof (Mon profil) + côté admin (édition inline)
- [x] **Inscription** : sélecteur 12 matières, sujet persisté en BDD
- [x] **Notifications feedback par SMTP direct** — A-FEEDBACK retiré définitivement
- [x] **Notation A-SCHOOL** séparée du Feedback (étoiles + commentaire optionnel)
- [x] **CSAT** dans AdminFeedbacks — moyenne, distribution, % satisfaits
- [x] **Feedback** = catégorie + message (sans étoiles)
- [x] **Sidebar prof** : Notez A-SCHOOL + Envoyer un feedback comme actions distinctes
- [x] Niveau "Supérieur" avec bandeau "en développement"
- [x] Encart feedback dans Parametres ("activité manquante → Feedback")
- [x] Logs admin avec colonne Matière
- [x] Migrations BDD automatiques au démarrage

---

## Prochaines étapes (par priorité)

1. **Few-shot adaptation au style prof** — PRIORITÉ #1
   - Auth sur `/api/generate` (bug sécurité + prérequis)
   - Requête 2 dernières activités du même type en base
   - Injection dans `build_prompt()` — seuil cold start : 3 activités
2. **Déploiement VPS** — push en cours
3. **Support niveau Supérieur** — activités dédiées BTS/prépa (voir améliorations futures)

---

## Architecture Auth — opérationnelle depuis 25/04/2026

Flow : `Signup → Email vérification → Login → JWT cookies`

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

## Architecture Feedback — SMTP direct (depuis 28/04/2026)

**A-FEEDBACK retiré définitivement.** Ne pas réintroduire `feedback_client`.

- **Feedback** (bug, suggestion, question) → stocké en BDD, email sans étoiles
- **Notation** (1-5 étoiles + commentaire optionnel) → stocké en BDD, email avec CSAT
- Notification envoyée à `FEEDBACK_NOTIFY_EMAIL` (défaut `contact@afia.fr`)
- SMTP : Infomaniak `mail.infomaniak.com:587`

---

## Variables d'environnement requises

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

## Améliorations futures (à ne pas traiter maintenant)

- **Analyse IA des notations** (Groq) — pertinent à partir de 20-30 notations avec commentaire
- **Support niveau Supérieur** — activités dédiées BTS/prépa/licence
- **Few-shot adaptation au style prof** — PRIORITÉ #1 dès que les pilotes ont généré 3+ activités du même type
- **Aide spécifique par matière** — subject maintenant en BDD, peut être implémenté
- **Mot de passe oublié** — réutilise `email_tokens` avec `purpose=reset_password`
- **Migration SQLite → PostgreSQL** — si montée en charge
