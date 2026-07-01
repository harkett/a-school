# EMAILS — Gestion des envois dans aSchool

> **Rôle : référence obligatoire pour tout ce qui concerne les emails. À lire AVANT toute modification email.**
>
> Ce document dit la même vérité que le `.env` et que la section « Gestion des emails » de `CLAUDE.md`. Si les trois divergent un jour, le `.env` fait foi sur les valeurs, et on réaligne les documents.
>
> Ce document contient :
> - La configuration SMTP (Infomaniak).
> - L'explication de la connexion par mot de passe dédié.
> - Le rôle de chaque variable email du `.env`, sans recopier les valeurs.
> - Les envois dans le code : 6 fonctions dans `backend/auth.py` plus 1 dans `backend/alerts.py`.
> - Les routes API qui déclenchent un envoi.
> - Les envois prévus mais pas encore codés.
> - Les principes absolus.
>
> **Règles critiques :**
> - Ne jamais changer de fournisseur SMTP sans demande explicite.
> - Tout le code SMTP passe par `_smtp_send()` dans `backend/auth.py`. C'est la seule connexion SMTP du projet.
> - On ne recopie jamais une adresse ni un mot de passe en dur, ni ici ni dans le code. Tout vit dans le `.env`.
>
> **À mettre à jour à chaque nouvel envoi email ajouté au projet.**

---

## Fournisseur SMTP

aSchool envoie ses emails via Infomaniak.
Le serveur est `mail.infomaniak.com`, sur le port `587` (TLS).
On ne change jamais de fournisseur sans demande explicite.

---

## Connexion — le point qui nous a coûté cher

Pour se connecter au serveur d'envoi, Infomaniak refuse le mot de passe du webmail.
Il faut un mot de passe dédié, généré dans Infomaniak (Service Mail, puis l'adresse, puis Appareils, puis Ajouter un appareil).
C'est ce mot de passe qu'on met dans le `.env`.
Sans lui, la connexion est refusée avec l'erreur « 535 Invalid login or password ».

---

## Une seule adresse d'envoi

Tout part de la même adresse d'envoi : celle du compte Infomaniak, définie dans le `.env`.
Infomaniak exige que le compte de connexion et l'adresse d'expéditeur soient la même adresse.
Les notifications de feedback gardent seulement un nom affiché différent (« aSchool Feedback »).
C'est la même adresse derrière ce nom, pas une autre boîte.
L'ancienne adresse `feedback@aschool.fr` n'est plus utilisée comme adresse d'envoi.

---

## Variables `.env`

Toutes les valeurs vivent dans le `.env`, jamais recopiées ici.
Le modèle complet est dans `.env.example`.

| Variable | Rôle |
|---|---|
| `SMTP_HOST` | Serveur Infomaniak |
| `SMTP_PORT` | Port d'envoi (587) |
| `SMTP_USERNAME` | Adresse du compte de connexion |
| `SMTP_PASSWORD` | Mot de passe dédié Infomaniak (voir plus haut) |
| `SMTP_FROM` | Expéditeur des emails aux profs (nom affiché « aSchool ») |
| `FEEDBACK_FROM` | Expéditeur des notifications feedback (même adresse, nom affiché « aSchool Feedback ») |
| `FEEDBACK_NOTIFY_EMAIL` | Adresse qui reçoit les notifications feedback et les nouvelles inscriptions |
| `ADMIN_EMAIL` | Adresse qui reçoit les alertes techniques du serveur |
| `APP_URL` | URL publique de l'app, utilisée dans les liens des emails |

Le `.env` local et le `.env` VPS ont les mêmes variables.
Seule `APP_URL` change : adresse locale en développement, `https://aschool.fr` en production.
Sur le VPS, le fichier est `/var/www/a-school/.env`.

> **Note développement :** il n'y a pas de mode « console » comme dans Django.
> En local, les emails partent en vrai via SMTP.
> Pour ne pas envoyer en vrai pendant un test, on commente temporairement l'appel `_smtp_send()` dans `backend/auth.py`.

---

## Envois dans le code

Tout le code d'envoi passe par `backend/auth.py`.
La fonction `_smtp_send()` est la seule à ouvrir la connexion SMTP.
Toutes les autres fonctions l'appellent.

### 6 fonctions d'envoi dans `backend/auth.py`

| Fonction | Destinataire | From | Déclencheur |
|---|---|---|---|
| `send_verification_email()` | le prof (nouveau compte) | `SMTP_FROM` | Inscription : lien d'activation valable 60 minutes |
| `send_custom_email()` | le prof (ou l'admin pour le test) | `SMTP_FROM` | Email de bienvenue, envoi manuel admin, bouton « Tester l'envoi » |
| `send_reset_email()` | le prof | `SMTP_FROM` | Demande de réinitialisation du mot de passe |
| `send_feedback_notification()` | `FEEDBACK_NOTIFY_EMAIL` | `FEEDBACK_FROM` | Un prof envoie un feedback ou une notation |
| `send_feedback_update_notification()` | `FEEDBACK_NOTIFY_EMAIL` | `FEEDBACK_FROM` | Un prof complète un feedback existant |
| `send_admin_new_user_notification()` | `FEEDBACK_NOTIFY_EMAIL` | `FEEDBACK_FROM` | Une nouvelle inscription vient d'être vérifiée |

> `send_custom_email()` sert à plusieurs usages : email de bienvenue, envoi manuel depuis l'admin, et bouton de test.
> Le sujet et le corps de l'email de bienvenue se règlent depuis l'écran admin. Variables acceptées : `{prenom}`, `{email}`.

### 1 fonction d'envoi dans `backend/alerts.py`

| Fonction | Destinataire | From | Déclencheur |
|---|---|---|---|
| `_send_alert_email()` | `ADMIN_EMAIL` | `FEEDBACK_FROM` | Alerte technique du serveur : CPU élevé, disque presque plein, tentatives d'intrusion |

Cette fonction vit dans un autre fichier que les six précédentes.
Elle passe quand même par `_smtp_send()` de `backend/auth.py`.
On la garde visible à part, justement parce que le fait qu'elle soit ailleurs l'avait fait oublier.

### Routes API qui déclenchent un envoi

| Route | Méthode | Envoi déclenché |
|---|---|---|
| `/api/auth/signup` | POST | `send_verification_email()` |
| `/api/auth/resend-verification` | POST | `send_verification_email()` |
| `/api/auth/request-reset` | POST | `send_reset_email()` |
| `/api/auth/verify-email` | GET | `send_custom_email()` (bienvenue) et `send_admin_new_user_notification()` |
| `/api/feedback` | POST | `send_feedback_notification()` |
| `/api/feedback/{id}` | PATCH | `send_feedback_update_notification()` |
| `/api/admin/user/{email}/reset-password` | POST | `send_reset_email()` |
| `/api/admin/user/{email}/send-email` | POST | `send_custom_email()` |
| `/api/admin/mail-groupe` | POST | `send_custom_email()` (email groupé aux profs) |
| `/api/admin/force-logout/{session_id}` | POST | `send_custom_email()` (avertit le prof que sa session est fermée) |
| `/api/admin/settings/test-email` | POST | `send_custom_email()` (test) |

Les alertes techniques (`_send_alert_email()`) ne partent pas d'une route : elles sont déclenchées par les vérifications automatiques du serveur.

---

## Envois prévus (non encore codés)

### Séquence onboarding — Phase 2 (Juin 2026)

| Email | Timing | Contenu |
|-------|--------|---------|
| Bienvenue enrichi | J+0 | "Votre compte est actif. Voici comment faire votre première activité." |
| Premier usage | J+2 | "Avez-vous essayé les exercices de réécriture ? Voilà un exemple." |
| Rétention | J+7 | "X activités générées cette semaine par vos collègues." |
| Feedback | J+14 | "Qu'est-ce qui manque ? Répondez directement." |

> Le J+0 existe déjà (welcome email). Les J+2, J+7, J+14 nécessitent un scheduler (cron ou Celery).

### Invitation collègues — Phase 2 (Option B)

Route prévue : `POST /api/partager/`
Déclencheur : prof connecté envoie une invitation depuis la sidebar.
Limite : 5 adresses / 5 appels par jour par utilisateur.

```
Objet : [Prénom Nom] vous recommande aSchool

Bonjour,

[Prénom Nom] vous recommande aSchool, l'outil gratuit pour les enseignants.
Collez un texte, choisissez le type d'activité et le niveau —
vous obtenez un exercice complet en 10 secondes.

→ Créez votre compte gratuit sur aschool.fr

— aSchool — aschool.fr
```

### Signature dans le `mailto:` — Phase 1 S1

Le bouton "Envoyer par e-mail" ouvre le client mail du prof avec l'activité en corps.
À ajouter en fin de corps :

```
--
Généré avec aSchool — aschool.fr — Créez votre compte gratuit
```

---

## Principes de travail

- Jamais de mot de passe dans le code. Uniquement dans le `.env`.
- Jamais un autre fournisseur SMTP sans demande explicite.
- `SMTP_FROM` doit toujours être défini dans le `.env`. On ne compte pas sur la valeur de repli du code.
- Tout le code SMTP passe par `_smtp_send()` dans `backend/auth.py`. On ne crée jamais de connexion SMTP ailleurs.
