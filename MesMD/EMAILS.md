# EMAILS — Gestion des envois dans aSchool

> **Rôle : référence obligatoire pour tout ce qui concerne les emails — à lire AVANT toute modification email.**
>
> Ce document contient :
> - La configuration SMTP officielle (Infomaniak, `mail.infomaniak.com:587`)
> - Les deux adresses email du projet (`contact@aschool.fr` boîte réelle, `feedback@aschool.fr` alias) et leurs usages respectifs
> - Les variables `.env` complètes pour local et VPS (avec les valeurs réelles masquées)
> - La liste des 4 fonctions d'envoi dans `backend/auth.py` : qui les appelle, quel `From`, quel destinataire
> - Les routes API qui déclenchent un envoi email
> - Les envois prévus non encore codés (séquence onboarding J+2/J+7/J+14, invitation collègues, signature mailto)
> - Les principes absolus (jamais de SMTP hors `_smtp_send()`, jamais de mot de passe dans le code)
>
> **Règles critiques :**
> - Ne jamais changer de fournisseur SMTP sans demande explicite
> - Tout le code SMTP passe par `_smtp_send()` dans `backend/auth.py` — une seule connexion SMTP dans tout le projet
> - `feedback_client.py` est deprecated — ne jamais réutiliser
>
> **À mettre à jour à chaque nouvel envoi email ajouté au projet**

---

## SMTP — Configuration officielle

| Paramètre | Valeur |
|-----------|--------|
| Hébergeur | Infomaniak |
| HOST | `mail.infomaniak.com` |
| PORT | `587` (TLS) |
| Boîte principale | `contact@aschool.fr` (boîte réelle) |

**Règle absolue : ne jamais mettre un autre SMTP sans demander.**

---

## Adresses email (Infomaniak — domaine aschool.fr)

| Adresse | Type | Redirige vers | Usage dans aSchool |
|---------|------|---------------|----------------------|
| `contact@aschool.fr` | Boîte réelle | — | Toutes les réponses arrivent ici — activation, welcome, test admin |
| `feedback@aschool.fr` | Alias | → `contact@aschool.fr` | Notifications feedback / notation uniquement |

**Règle `From` :**
- Emails vers les profs (activation, welcome, invitation) : `aSchool <contact@aschool.fr>`
- Notifications feedback vers l'admin : `aSchool Feedback <feedback@aschool.fr>`

`noreply` supprimé — les profs peuvent répondre à tout email aSchool, c'est souhaitable.

---

## Configuration `.env`

### Variables `.env` local
```
SMTP_HOST=mail.infomaniak.com
SMTP_PORT=587
SMTP_USERNAME=contact@aschool.fr
SMTP_PASSWORD=***
SMTP_FROM=aSchool <contact@aschool.fr>
FEEDBACK_FROM=aSchool Feedback <feedback@aschool.fr>
FEEDBACK_NOTIFY_EMAIL=contact@aschool.fr
APP_URL=http://localhost:5173
```

### Variables `.env` VPS (`/var/www/aSchool/.env`)
```
SMTP_HOST=mail.infomaniak.com
SMTP_PORT=587
SMTP_USERNAME=contact@aschool.fr
SMTP_PASSWORD=***
SMTP_FROM=aSchool <contact@aschool.fr>
FEEDBACK_FROM=aSchool Feedback <feedback@aschool.fr>
FEEDBACK_NOTIFY_EMAIL=contact@aschool.fr
APP_URL=https://school.afia.fr
```

> **Note dev :** contrairement à Django, il n'y a pas de `EMAIL_BACKEND=console`.
> En local, les emails partent en vrai via SMTP. Si on ne veut pas envoyer en vrai pendant les tests, commenter temporairement l'appel `_smtp_send()` dans `backend/auth.py`.

---

## Envois dans le code

Tout le code d'envoi est centralisé dans **`backend/auth.py`**.
La fonction bas niveau `_smtp_send(msg)` (ligne 220) est la seule à ouvrir la connexion SMTP — toutes les autres l'appellent.

### `backend/auth.py` — 4 fonctions ✅

| Fonction | Destinataire | From | Déclencheur |
|----------|-------------|------|-------------|
| `send_verification_email()` | Prof (nouveau compte) | `SMTP_FROM` → `contact@aschool.fr` | Signup → lien d'activation (valable 60 min) |
| `send_custom_email()` | Prof | `SMTP_FROM` → `contact@aschool.fr` | Email vérifié → welcome email (contenu configurable admin) |
| `send_feedback_notification()` | `FEEDBACK_NOTIFY_EMAIL` | `FEEDBACK_FROM` → `feedback@aschool.fr` | Prof soumet un feedback ou une notation |
| `send_custom_email()` | `SMTP_USERNAME` | `SMTP_FROM` → `contact@aschool.fr` | Clic "Tester l'envoi" dans AdminParametres |

> `send_custom_email()` sert à la fois pour le welcome email et les envois admin manuels.
> Le sujet et le corps du welcome email sont configurables depuis AdminParametres — variables acceptées : `{prenom}`, `{email}`.

### Routes API qui déclenchent un envoi

| Route | Méthode | Email déclenché |
|-------|---------|-----------------|
| `/api/auth/signup` | POST | `send_verification_email()` |
| `/api/auth/verify-email` | GET | `send_custom_email()` (welcome) |
| `/api/feedback` | POST | `send_feedback_notification()` |
| `/api/admin/settings/test-email` | POST | `send_custom_email()` (test) |

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

→ Créez votre compte gratuit sur school.afia.fr

— aSchool — school.afia.fr
```

### Signature dans le `mailto:` — Phase 1 S1

Le bouton "Envoyer par e-mail" ouvre le client mail du prof avec l'activité en corps.
À ajouter en fin de corps :

```
--
Généré avec aSchool — school.afia.fr — Créez votre compte gratuit
```

---

## À faire

- [x] Mettre à jour `.env` local — `contact@aschool.fr` + ajouter `FEEDBACK_FROM` *(01/05/2026)*
- [x] Mettre à jour `.env` VPS — idem + vérifier `SMTP_FROM` et `FEEDBACK_FROM` *(01/05/2026)*
- [x] Mettre à jour `backend/auth.py` — fallback `contact@afia.fr` → `contact@aschool.fr`, lire `FEEDBACK_FROM` dans `send_feedback_notification()` *(01/05/2026)*
- [x] Mettre à jour `.env.example` *(01/05/2026)*
- [x] `FEEDBACK_NOTIFY_EMAIL` défini dans `.env` VPS *(01/05/2026)*
- [ ] Ajouter signature dans le corps du `mailto:` (Phase 1 S1)
- [ ] Coder séquence onboarding J+2, J+7, J+14 (Phase 2)
- [ ] Coder `POST /api/partager/` + composant sidebar (Phase 2)
- [ ] Mettre à jour ce fichier à chaque nouvel envoi ajouté

---

## Principes de travail

- **Jamais** de mot de passe dans le code — uniquement dans les `.env`
- **Jamais** de SMTP différent sans demander
- **`SMTP_FROM`** doit toujours être défini dans `.env` — ne pas compter sur le fallback du code
- **Tout le code SMTP** passe par `_smtp_send()` dans `backend/auth.py` — ne pas créer de connexion SMTP ailleurs
- **`feedback_client.py`** est deprecated — ne jamais réutiliser ce fichier
- **`src/auth.py`** (legacy Streamlit) — supprimé le 01/05/2026
