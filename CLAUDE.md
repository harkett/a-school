# CLAUDE.md — Référence permanente aSchool

> Chargé automatiquement à chaque session. Règles + contexte technique — source unique de vérité.

---

## Vision

Plateforme web de génération d'activités pédagogiques pour les enseignants (collège → supérieur), sans compétences techniques requises. Construit étape par étape, validé avec des profs pilotes réels.

**Tagline few-shot :** "À partir de quelques utilisations, aSchool s'adapte à votre façon de formuler les exercices."

---

## Stack technique

| Composant | Détail |
|---|---|
| Backend | FastAPI — `backend/main.py` — port 8000 (local) / 8001 (VPS) |
| Frontend | React + Vite — `frontend/` — port 5173 |
| BDD | SQLite (local + VPS) |
| IA | Groq API — `llama-3.3-70b-versatile` |
| Dictée | Groq Whisper API |
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
.\run.ps1              # Lance backend (:8000) + frontend (:5173) — régénère activities auto
.\push.ps1 "message"   # Bump PATCH auto → commit → push GitHub → déploiement VPS
```

Version courante : **3.2.3** — PATCH incrémenté automatiquement par `push.ps1` (`npm version patch`). MINOR et MAJOR = manuels.

---

## Catalogue d'activités

- **Source de vérité :** `MesMD/MATRICE_ACTIVITES_ASCHOOL.md`
- **Générateur :** `parse_markdown.py` → `src/generated_activities.py` — **NE PAS ÉDITER MANUELLEMENT**
- **Runtime :** `src/activities.py` construit l'index au démarrage
- 12 matières × 43 activités uniques = 140 entrées

**Matières :** Français, Histoire-Géo, Philosophie, Mathématiques, NSI, Physique-Chimie, SVT, Technologie, SES, Langues Vivantes, Arts, EPS

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

Dès qu'un nom UI change (page, section, composant, route), produire dans la même réponse la liste complète des impacts : fichiers frontend, page IDs dans App.jsx, composants, routes backend, noms de fichiers. Demander si on traite maintenant ou si on note dans TRACKER sous "En attente de cascade". Ne jamais clore la session sans que chaque impact soit traité ou noté.

---

## Workflow obligatoire

Proposer → valider → coder → tester. Ne jamais coder sans validation explicite de l'utilisateur.

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

## TRACKER.md — Source unique de vérité

`MesMD/TRACKER.md` est le seul endroit où sont tracés statut, idées et avancement. Règles :
- Toute idée mentionnée en session → notée dans TRACKER.md **immédiatement**, dans la même réponse. Pas en fin de session.
- Jamais de cases ☐/☑ dans un autre document (specs, dashboard, mémoire).
- En fin de session : synchroniser TRACKER.md (cocher les livrés, ajouter les nouvelles idées).

---

## Règles UI permanentes

- **Profil = source unique** pour matière et niveau. Jamais de `<select>` matière/niveau dans les features — toujours lire depuis le profil.
- **Bouton d'action principale** = classe `btn-primary` + icône SVG + `title=` tooltip + positionné en bas à droite. Référence : bouton "Générer l'activité" dans `Parametres.jsx`.
- **Header** : `height: 65px`, `overflow: hidden`. **Logo** : `height: 140px`. INTOUCHABLES.
- **Tagline** "Générateur d'activités pédagogiques" = `<span>` HTML blanc dans le header, toujours présent, jamais dans le PNG seul.
- Pas d'emojis dans l'interface.
- Navigateur de référence : **Edge** (jamais Chrome dans les instructions).

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

Groq (`llama-3.3-70b-versatile`) par défaut. Google Gemini banni — compte Workspace afia.fr incompatible avec le free tier.

---

## Aide — Règle absolue

Dès qu'une fonctionnalité est livrée, sa section Aide est rédigée dans la **même session** — à chaud, pendant que c'est frais. Jamais en retard. Jamais reporté à "plus tard".

---

## Secrets — Règle absolue

Ne jamais afficher mots de passe, clés API ou tokens en clair dans la discussion, même si l'utilisateur le demande.

---

## Sync docs — Règle de fin de session

En fin de chaque session de dev importante : mettre à jour ce fichier (version, règles nouvelles) + synchroniser TRACKER.md.
