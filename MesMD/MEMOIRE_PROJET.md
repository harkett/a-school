# MÉMOIRE PROJET A-SCHOOL
> Vérifié le 12/05/2026 — À mettre à jour en fin de chaque session de dev importante.
> Ce fichier est la référence rapide pour reprendre une session sans repartir de zéro.

---

## Vision

Plateforme web de génération d'activités pédagogiques pour les enseignants (collège → supérieur), sans compétences techniques requises. Construit étape par étape, validé avec des profs pilotes réels.

**Tagline few-shot :** "À partir de quelques utilisations, aSchool s'adapte à votre façon de formuler les exercices."

---

## Stack technique

| Composant | Détail |
|---|---|
| Backend | FastAPI — `backend/main.py` — port 8000 (local) / 8001 (VPS) |
| Frontend | React + Vite + Tailwind — `frontend/` — port 5173 |
| BDD | SQLite (local + VPS) — migration PostgreSQL prévue Phase 3 |
| IA | Groq API — `llama-3.3-70b-versatile` — **toujours Groq par défaut** |
| Dictée | Groq Whisper API (court terme) → faster-whisper local (long terme) |
| Auth profs | email + mot de passe + bcrypt + JWT (python-jose) + httpOnly cookies |
| Auth admin | Cookie `aschool_admin` — JWT séparé `{"role": "admin"}` — jamais dans `user_sessions` |
| SMTP | mail.infomaniak.com:587 — `SMTP_USERNAME=harketti@afia.fr` |

---

## VPS production

| Info | Valeur |
|---|---|
| URL | https://aschool.fr |
| IP | 83.228.245.163 (IPv6 : 2001:1600:18:202::8a) |
| Accès SSH | ubuntu@83.228.245.163 |
| Chemin | /var/www/a-school/ |
| Service | `aschool.service` (systemd) |
| Port | 8001 (8000 occupé par Django AFIA-FR) |
| OS | Ubuntu 24.04 LTS |
| DNS | Infomaniak |
| SSL expiry | 2026-07-15 |

**Statut : opérationnel en production — des profs réels l'utilisent. Ne jamais remettre en doute.**

---

## Scripts clés

```powershell
.\run.ps1            # Lance backend (:8000) + frontend (:5173) — régénère activities auto
.\push.ps1"message"  # Push GitHub + déploiement automatique VPS
```

---

## Catalogue d'activités

- **Source de vérité :** `MesMD/MATRICE_ACTIVITES_ASCHOOL.md`
- **Générateur :** `parse_markdown.py` → `src/generated_activities.py` (NE PAS ÉDITER MANUELLEMENT)
- **Runtime :** `src/activities.py` construit l'index au démarrage
- **Stats :** 12 matières × 43 activités uniques = 140 entrées

**Matières :** Français, Histoire-Géo, Philosophie, Mathématiques, NSI, Physique-Chimie, SVT, Technologie, SES, Langues Vivantes, Arts, EPS

---

## Fonctionnalités opérationnelles

| Feature | Statut | Date |
|---|---|---|
| Auth email+password+JWT | ✅ Production | 25/04/2026 |
| 12 matières + profil prof (subject, prenom, nom, niveau) | ✅ Production | 28/04/2026 |
| Few-shot adaptation style prof (après 3 saves) | ✅ Production | 30/04/2026 |
| Dictée vocale (Groq Whisper) | ✅ Opérationnel | — |
| OCR | ✅ Opérationnel | — |
| Feedback modale + BDD + statuts admin | ✅ Production | 30/04/2026 |
| Backoffice complet (sessions, brute force, audit, alertes) | ✅ Production | 02/05/2026 |
| Email inscription automatique | ✅ Production | 02/05/2026 |
| Admin — Mon compte + changement mot de passe | ✅ Production | 02/05/2026 |
| Séparation sessions Admin/Prof (garde-fou force-logout) | ✅ Local (à déployer) | 06/05/2026 |
| PWA — Installabilité iOS (IOSInstallBanner, bfcache fix, cross-tab logout) | ✅ Production | 12/05/2026 |
| PWA — Responsive mobile (sidebar collapse, header mobile, Mes Outils liste verticale) | ✅ Production | 12/05/2026 |

---

## Architecture auth (ne pas toucher)

**Profs :**
- Cookie `aschool_refresh` — JWT avec `type: "refresh"`, `sub: email`, `jti: session_key`
- Middleware `UserSessionMiddleware` crée une entrée `UserSession` à chaque requête prof
- `backend/auth.py` + `backend/routers/auth.py` — intouchables sans demande explicite

**Admin :**
- Cookie `aschool_admin` — JWT avec `{"sub": "admin", "role": "admin"}` — sans `type: "refresh"`
- Le middleware NE crée PAS de `UserSession` pour l'admin
- Résultat : la table `user_sessions` ne contient QUE des sessions de profs
- Garde-fou `force-logout` : refus 403 si `user_email == ADMIN_EMAIL` (env var)

---

## Backoffice admin — tables BDD

| Table | Usage |
|---|---|
| `UserSession` | Sessions actives des profs (middleware) |
| `FailedLoginAttempt` | Tentatives échouées sur `/admin/login` |
| `AdminAuditLog` | Toutes les actions admin (FORCE_LOGOUT, DELETE_USER, UPDATE_SETTINGS…) |
| `AdminAlert` | Alertes auto (CPU, disque, brute force) — APScheduler 5 min |

---

## SMTP — règles absolues

- Fournisseur : **Infomaniak uniquement** — ne jamais changer sans demande explicite
- `SMTP_FROM` = `A-SCHOOL <contact@aschool.fr>` (emails vers les profs)
- `FEEDBACK_FROM` = `A-SCHOOL Feedback <feedback@aschool.fr>` (notifications admin)
- Tout le code SMTP passe par `_smtp_send()` dans `backend/auth.py` — jamais ailleurs
- **⚠️ ACTION À FAIRE — Boîtes mail @aschool.fr** : Infomaniak force l'adresse d'expédition à correspondre au compte authentifié. Comme `SMTP_USERNAME=harketti@afia.fr` (compte gratuit), les emails partent avec cette adresse au lieu de `contact@aschool.fr`. **Solution définitive : acheter les boîtes `contact@aschool.fr` et `feedback@aschool.fr` chez Infomaniak (~3€/mois chacune)**. Le code n'a pas besoin de changer — il suffit de mettre à jour `SMTP_USERNAME` et `SMTP_PASSWORD` dans le `.env` avec les nouvelles boîtes.

---

## Règles d'interface

- Jamais le mot "IA" → toujours "A-SCHOOL"
- Pas d'emojis dans l'interface
- Pas de Google Gemini (compte Workspace afia.fr incompatible free tier) — Groq par défaut
- Boutons sur fond foncé : `color: white !important` + attribut `title=` sur tous les boutons d'action
- Navigateur de référence : **Edge** (jamais Chrome dans les instructions)

---

## Fonctionnalités futures (ne pas coder sans demande)

| Feature | Prérequis / condition |
|---|---|
| Aide spécifique par matière | Prêt (subject en BDD) — session courte |
| Détection mise à jour (version notification) | À partir de 20+ profs actifs |
| Feedback page dédiée (bidirectionnel) | Quand volume feedbacks le justifie |
| Analyse IA des retours (Groq) | À partir de 20-30 notations avec commentaire |
| Niveau Supérieur (BTS/prépa) | Catalogue activités à définir avec pilotes |
| Multi-matières dans le profil | Refonte Many-to-Many — après retours pilotes |
| Théâtre (13e matière) | Nécessite prof pilote théâtre |
| Assistant d'utilisation interactif | Phase 3/4 — après validation pilotes |
| Micro Windows (Web Speech API) | Session dédiée |
| Recherche texte par description | Intégration API Gallica/Wikisource requise |
| Migration SQLite → PostgreSQL | Phase 3 |
| **Quiz interactif élèves** | Spec validée 07/05/2026 — voir section dédiée ci-dessous |

---

## Quiz interactif élèves — Spec v1 validée

> Affiché "Bientôt disponible" dans la Sidebar. À coder en session dédiée.

**Concept :** Outil de diagnostic pour le prof, pas une évaluation notée.
- "Est-ce que ma classe a compris le chapitre ?"
- "Sur quelle question est-ce qu'ils bloquent ?"
- "Qui n'a pas encore répondu ?"

La triche est possible (pseudo libre) mais non bloquante — ce n'est pas un outil d'examen.

**Flux :**
1. Prof génère un quiz QCM depuis A-SCHOOL (matière, niveau, thème, nb questions)
2. A-SCHOOL crée un lien unique `school.afia.fr/quiz/{token}`
3. Prof partage le lien (projette, envoie par message)
4. Élève ouvre sur téléphone → entre son prénom → répond → voit son score
5. Prof voit les résultats en direct (polling ~5s) ou différé

**Résultats prof :** liste élèves + score (ex : "Marie — 7/10") + par question : nb bons/faux.

**Périmètre v1 :** QCM uniquement, pseudo libre, pas de limite de temps, pas de classement.

**Technique à implémenter :**
- Modèles BDD : `Quiz` (id, token uuid, prof_email, titre, matiere, niveau, questions_json, created_at) + `ReponseQuiz` (id, quiz_id, eleve_pseudo, reponses_json, score, submitted_at)
- Endpoints : `POST /api/quiz` (auth) · `GET /api/quiz/{token}` (public) · `POST /api/quiz/{token}/repondre` (public) · `GET /api/quiz/{token}/resultats` (auth)
- Pages frontend : "Quiz" dans menu Sidebar (prof) + `/quiz/{token}` mobile-first sans auth (élève) + vue résultats live

---

## Règles de collaboration

- **Workflow :** Proposer → valider → coder → tester. Ne jamais coder sans validation explicite.
- **Solution simple d'abord** — pas de composants inutiles
- **MesRessources interdit** — ne jamais lire/écrire `D:\A-SCHOOL\MesRessources\`, même si l'IDE ouvre un fichier depuis ce dossier (ignorer l'`ide_opened_file`)
- **Auth intouchable** — ne jamais modifier `backend/auth.py` ni `backend/routers/auth.py` sans demande explicite
- **Secrets interdits en chat** — ne jamais afficher mots de passe, clés API ou tokens en clair
- **Sync docs** — mettre à jour ce fichier + `ETAT_PROJET.md` en fin de session de dev importante
