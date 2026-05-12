# AUTH_DIAGNOSTIC.md — Référence du système d'authentification

> **Rôle : référence complète du système d'auth + archive du diagnostic effectué le 02/05/2026.**
>
> **✅ Tous les problèmes identifiés sont résolus** (8/8 — sessions 1 et 2 du 02/05/2026). Ce document n'est plus un plan d'action : c'est une référence de l'architecture en place et un journal de ce qui a été corrigé et pourquoi.
>
> Ce document contient :
> - **Reprise rapide** : résumé des deux sessions du 02/05/2026 avec ce qui a été fait (numéros de version admin, PROB-1 à PROB-8)
> - **Journal des modifications** : détail complet de chaque correction (contexte, fichiers modifiés, comportement implémenté, garanties de déploiement)
> - **Architecture en place** : stack auth (bcrypt, JWT HS256, cookies httpOnly), tables (`users`, `email_tokens`, `refresh_tokens`, `connexion_logs`), fichiers clés, flux complets (inscription, connexion, refresh, déconnexion)
> - **Ce qui fonctionne bien — à ne pas toucher** : bcrypt, JWT, brute force, rotation refresh tokens, whitelist email, logs IP
> - **Problèmes résolus avec leur spécification** : flux "renvoi email de vérification", flux "mot de passe oublié" (deux routes backend + deux pages React), autoComplete, cookie secure conditionnel, footer email, EyeIcon partagé
> - **Plan d'action** : tableau récapitulatif avec statut ✅ FAIT pour chaque item
>
> **À consulter quand** : on veut comprendre un flux auth, retrouver comment un problème a été résolu, ou vérifier les règles à respecter avant de toucher à l'auth.
>
> **Règle absolue** : ne jamais modifier `backend/auth.py` ni `backend/routers/auth.py` sans validation explicite — le système fonctionne parfaitement depuis le 02/05/2026.
>
> Créé le 02/05/2026 — Dernière mise à jour : 02/05/2026 (session 2) — Système auth complet + logs admin opérationnels

---

## Reprise rapide — par où commencer

**Dernière session : 02/05/2026**

Ce qui a été fait (session 1) :
1. ✅ **PROB-2** — Renvoi email de vérification (lien expiré) → implémenté + déployé en prod + validé
2. ✅ **Numéro de version** — Ajouté en bas à gauche de la sidebar admin (`v1.3 · 02/05/2026`) dans `AdminLayout.jsx`

Ce qui a été fait (session 2) :
3. ✅ **PROB-1** — Mot de passe oublié → flux complet validé en local
4. ✅ **PROB-3** — `autoComplete` corrigé sur `Login.jsx` (email + current-password)
5. ✅ **PROB-5** — Login retourne le profil complet (plus de double aller-retour)
6. ✅ **PROB-6** — Cookie `secure=True` conditionnel (`ENV=production` dans `.env` VPS)
7. ✅ **PROB-7** — Footer `harketti@afia.fr` → `contact@aschool.fr` dans `Login.jsx` et `VerifyEmail.jsx`
8. ✅ **PROB-8** — `EyeIcon` extrait en composant partagé `frontend/src/components/EyeIcon.jsx`
9. ✅ **Admin logs** — Connexions admin loguées (badge orange) + filtre "Admin" dans `AdminLogs.jsx`
10. ✅ **Timezone** — Dates affichées en heure locale (UTC→local via `toLocaleString`) dans `AdminLogs.jsx`

**Tous les problèmes identifiés sont résolus. Prêt pour déploiement VPS.**

Rappel déploiement : ajouter `ENV=production` dans `/var/www/aSchool/.env` puis `sudo systemctl restart aSchool-backend`.

---

## Journal des modifications

### 02/05/2026 — PROB-2 résolu : renvoi de l'email de vérification

**Contexte**
Un utilisateur dont le token de vérification avait expiré se retrouvait définitivement bloqué : impossible de se connecter (email non vérifié), impossible de recréer un compte (email déjà utilisé), aucune issue autonome.

**Ce qui a été implémenté**

| Fichier | Modification |
|---|---|
| `backend/routers/auth.py` | Nouveau modèle `ResendVerificationBody` + route `POST /auth/resend-verification` |
| `frontend/src/pages/Login.jsx` | Détection de l'erreur "non vérifié" + lien "Renvoyer l'email de vérification" dans le bandeau rouge, utilise l'email déjà saisi |
| `frontend/src/pages/VerifyEmail.jsx` | Remplacement du bouton "Créer un compte" (inutile car bloquant) par un formulaire email + bouton "Renvoyer" |

**Comportement de la route `/auth/resend-verification`**
- Cherche l'utilisateur en base
- Si inexistant ou déjà vérifié → retourne `{"status": "ok"}` sans rien faire (anti-énumération)
- Sinon → génère un nouveau token (l'ancien est automatiquement invalidé) + renvoie l'email de vérification via `_smtp_send()`
- Toujours silencieux sur les erreurs SMTP côté client

**Garantie déploiement**
Ces modifications sont purement additives. Aucune route existante n'a été modifiée, aucune donnée en base n'est touchée. Les utilisateurs déjà inscrits en production ne sont pas affectés. Un déploiement de ces fichiers ne fait qu'ajouter la nouvelle fonctionnalité.

**Reste à valider**
Test en dev à effectuer par l'utilisateur avant déploiement en prod.

---

## 1. Architecture en place

### Stack
- **Backend** : FastAPI + SQLAlchemy + SQLite (`data/aschool.db`)
- **Frontend** : React (Vite) + React Router
- **Hachage** : bcrypt (salt=12)
- **Tokens** : JWT HS256 — access 15 min / refresh 30 jours
- **Cookies** : httpOnly + SameSite=Lax
- **SMTP** : Infomaniak (`mail.infomaniak.com:587`)

### Tables d'auth
| Table | Rôle |
|---|---|
| `users` | email, password_hash, is_verified, failed_attempts, locked_until, last_login |
| `email_tokens` | tokens one-time use (verify_email, reset_password) — TTL 60 min |
| `refresh_tokens` | hash SHA256 du refresh token, révocable en base |
| `connexion_logs` | horodatage signup/login + IP |

### Fichiers clés
| Fichier | Rôle |
|---|---|
| `backend/auth.py` | Logique core (hash, JWT, email tokens) |
| `backend/routers/auth.py` | Endpoints signup / login / verify / refresh / me / logout |
| `backend/models_db.py` | Schémas SQLAlchemy |
| `frontend/src/context/AuthContext.jsx` | État React + checkAuth proactif |
| `frontend/src/pages/Login.jsx` | UI connexion |
| `frontend/src/pages/Signup.jsx` | UI inscription |
| `frontend/src/pages/VerifyEmail.jsx` | UI vérification email |

### Flux existants (qui fonctionnent)
1. **Inscription** → hash bcrypt → email de vérification (token 60 min) → compte activé → email de bienvenue
2. **Connexion** → bcrypt compare → cookies JWT (access 15 min + refresh 30 j) → `/api/auth/me`
3. **Refresh silencieux** → rotation du refresh token en base toutes les 10 min
4. **Déconnexion** → révocation du refresh token en base + suppression cookies

---

## 2. Ce qui fonctionne bien — à ne pas toucher

- bcrypt salt=12 avec constant-time comparison (protection timing attack) ✓
- JWT HS256, httpOnly cookies, SameSite=Lax ✓
- Blocage automatique après 5 tentatives échouées (30 min) ✓
- Rotation des refresh tokens (révocables en base) ✓
- `generate_email_token()` / `verify_email_token()` réutilisables (support `reset_password` déjà prévu dans le modèle) ✓
- Whitelist email optionnelle via `ALLOWED_EMAILS` ✓
- Logs signup/login avec IP ✓

---

## 3. Problèmes identifiés

### 🔴 BLOQUANTS — des utilisateurs se retrouvent définitivement coincés

---

#### PROB-1 — Pas de "Mot de passe oublié"

**Situation actuelle**

Le modèle `EmailToken` (champ `purpose`) supporte déjà `"reset_password"`, et les fonctions `generate_email_token()` / `verify_email_token()` dans `backend/auth.py` sont réutilisables. Mais il manque :

- Route backend `POST /auth/request-reset` (envoie un email avec lien)
- Route backend `POST /auth/reset-password` (valide le token + change le mot de passe)
- Page frontend `/forgot-password` (formulaire email)
- Page frontend `/reset-password?token=...` (formulaire nouveau mot de passe)
- Lien "Mot de passe oublié ?" sur `Login.jsx`

**Impact**

Un prof qui oublie son mot de passe est définitivement bloqué. La seule issue est de contacter l'admin.

---

#### PROB-2 — Token de vérification expiré → utilisateur bloqué sans issue

**Situation actuelle**

Scénario courant : le prof s'inscrit, l'email arrive en spam ou il l'ouvre le lendemain.

1. Il essaie de se connecter → `"Email non vérifié"`
2. Il clique sur l'ancien lien → `VerifyEmail.jsx` affiche "Lien invalide ou expiré" + bouton **"Créer un nouveau compte"**
3. Il clique → **"Un compte existe déjà avec cet email."**

**Le prof est bloqué** — il ne peut rien faire seul.

**Ce qui manque**

- Route backend `POST /auth/resend-verification` (génère un nouveau token + renvoie l'email)
- Bouton "Renvoyer l'email de vérification" dans `VerifyEmail.jsx` (cas erreur)
- Bouton "Renvoyer l'email de vérification" dans `Login.jsx` (quand erreur = "Email non vérifié")

---

### 🟡 IMPORTANTS — frictions UX significatives

---

#### PROB-3 — `autoComplete` incorrect bloque les gestionnaires de mots de passe

**Fichiers concernés**
- `frontend/src/pages/Login.jsx` ligne 77 : `autoComplete="off"` sur le `<form>`
- `frontend/src/pages/Login.jsx` ligne 104 : `autoComplete="new-password"` sur le champ password

**Problème**

`autoComplete="off"` empêche Chrome/Safari/Firefox/Bitwarden de proposer automatiquement les identifiants. `"new-password"` est l'attribut correct pour les formulaires de *création*, pas de *connexion* — les gestionnaires de mots de passe ne reconnaissent pas ce champ en mode login.

**Correction**
- Retirer `autoComplete="off"` du `<form>`
- Champ email : `autoComplete="email"`
- Champ password login : `autoComplete="current-password"`

---

#### PROB-4 — Erreur "Email non vérifié" → aucune action proposée

**Fichier concerné** : `frontend/src/pages/Login.jsx` ligne 41

Quand le backend renvoie `"Email non vérifié. Vérifiez votre boîte mail."`, le frontend affiche juste le bandeau rouge. Aucun bouton, aucune instruction supplémentaire.

**Correction**

Détecter ce message d'erreur spécifique et afficher un bouton "Renvoyer l'email de vérification" qui appellera la route `/auth/resend-verification`.

---

#### PROB-5 — Login retourne `{email}` seul → profil incomplet au premier rendu

**Fichier backend** : `backend/routers/auth.py` ligne 94 — retourne `{"email": user.email}`
**Fichier frontend** : `frontend/src/pages/Login.jsx` ligne 42 — `setUser(data)`

Juste après la connexion, `user.subject`, `user.prenom`, `user.niveau`, `user.langue_lv` sont tous `undefined` dans le contexte React, jusqu'à ce que `AuthContext` appelle `/api/auth/me` en arrière-plan.

Si `MainApp` utilise ces champs au premier rendu, ils sont temporairement absents.

**Correction**

Faire retourner le profil complet par `POST /auth/login` (même payload que `/auth/me`), pour éviter le double aller-retour et avoir un état cohérent dès la connexion.

---

### 🟢 MINEURS

---

#### PROB-6 — Cookie sans `secure=True` en production HTTPS

**Fichier** : `backend/routers/auth.py` ligne 20-22

```python
kw = dict(httponly=True, samesite="lax")
```

Sans `secure=True`, les cookies peuvent être transmis sur HTTP. En production HTTPS (school.afia.fr), ajouter `secure=True` conditionnel à l'environnement.

**Correction**

```python
is_prod = os.getenv("ENV") == "production"
kw = dict(httponly=True, samesite="lax", secure=is_prod)
```

---

#### PROB-7 — Footer affiche l'email personnel de l'admin

**Fichiers**
- `frontend/src/pages/Login.jsx` ligne 134
- `frontend/src/pages/Signup.jsx` ligne 234

Les deux pages affichent `harketti@afia.fr`, visible par tous les professeurs inscrits.

**Correction** : remplacer par `contact@aschool.fr`.

---

#### PROB-8 — `EyeIcon` SVG dupliqué dans deux composants

**Fichiers** : `Login.jsx` lignes 3-13 et `Signup.jsx` lignes 3-13

Le même composant SVG est défini deux fois. À extraire dans `frontend/src/components/EyeIcon.jsx`.

---

## 4. Plan d'action — ordre de traitement recommandé

| # | Priorité | Tâche | Fichiers touchés |
|---|---|---|---|
| 1 | ✅ FAIT + PROD | Implémenter `/auth/resend-verification` + boutons frontend | `backend/routers/auth.py`, `Login.jsx`, `VerifyEmail.jsx` |
| 2 | ✅ FAIT | Implémenter flux "Mot de passe oublié" complet | `backend/routers/auth.py`, `backend/auth.py`, 2 nouvelles pages React |
| 3 | ✅ FAIT | Corriger `autoComplete` sur formulaire login | `Login.jsx` |
| 4 | ✅ FAIT | Login retourne profil complet | `backend/routers/auth.py` |
| 5 | ✅ FAIT | Cookie `secure=True` conditionnel | `backend/routers/auth.py` |
| 6 | ✅ FAIT | Footer → `contact@aschool.fr` | `Login.jsx`, `VerifyEmail.jsx` |
| 7 | ✅ FAIT | Extraire `EyeIcon` en composant partagé | `Login.jsx`, `Signup.jsx`, `ResetPassword.jsx`, nouveau `EyeIcon.jsx` |

---

## 5. Spécifications des deux flux manquants

### Flux 1 — Renvoi de l'email de vérification

**Backend** : `POST /auth/resend-verification`

```
Body : { "email": "prof@school.fr" }
Réponse : { "status": "ok" } — toujours (ne pas révéler si l'email existe)
Logique :
  - Cherche l'utilisateur
  - Si inexistant ou déjà vérifié → retourne ok quand même (anti-énumération)
  - Sinon : génère un nouveau token (invalide l'ancien automatiquement) + renvoie l'email
```

**Frontend — VerifyEmail.jsx (cas erreur)**

Ajouter un formulaire "Renvoyer le lien" avec un champ email + bouton.

**Frontend — Login.jsx (erreur "Email non vérifié")**

Détecter le message et afficher un bouton "Renvoyer l'email de vérification" qui ouvre un mini-formulaire (ou appelle directement si l'email est déjà dans le champ).

---

### Flux 2 — Mot de passe oublié

**Backend** : `POST /auth/request-reset`

```
Body : { "email": "prof@school.fr" }
Réponse : { "status": "ok" } — toujours (anti-énumération)
Logique :
  - Si utilisateur existe et est vérifié → génère token "reset_password" + envoie email
  - Sinon → retourne ok sans rien faire
```

**Backend** : `POST /auth/reset-password`

```
Body : { "token": "...", "password": "...", "password_confirm": "..." }
Logique :
  - Valide le token (purpose = "reset_password")
  - Valide le mot de passe (min 8 chars, max 72 bytes)
  - Hash bcrypt + met à jour user.password_hash
  - Révoque tous les refresh tokens de cet utilisateur (déconnexion forcée de toutes les sessions)
  - Retourne { "status": "ok" }
```

**Frontend** : Page `/forgot-password`

Formulaire simple : champ email + bouton "Envoyer le lien". Après soumission : message "Si un compte existe avec cet email, un lien vous a été envoyé."

**Frontend** : Page `/reset-password?token=...`

Formulaire : champ "Nouveau mot de passe" + "Confirmer" + bouton. États : loading / succès (lien vers /login) / erreur (lien expiré → vers /forgot-password).

**Lien** à ajouter sur `Login.jsx` : "Mot de passe oublié ?" entre le bouton submit et le lien "Créer un compte".

---

## 6. Règles à respecter lors des modifications

- Ne jamais créer de connexion SMTP hors de `_smtp_send()` dans `backend/auth.py`
- Ne jamais modifier `backend/auth.py` ni `backend/routers/auth.py` sans validation explicite
- Toujours retourner `{"status": "ok"}` pour les routes sensibles (request-reset, resend-verification), qu'il y ait un utilisateur ou non — anti-énumération d'adresses email
- Révocation de toutes les sessions actives lors d'un reset de mot de passe

---

*Dernière mise à jour : 02/05/2026 — système auth complet + logs admin opérationnels*
