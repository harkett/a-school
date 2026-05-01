# A-SCHOOL Platform — Roadmap & Suivi de projet

> **À propos de ce document**
> Référence technique du projet : stack, architecture des fichiers, script de déploiement VPS, journal des décisions techniques et état d'avancement. À consulter pour comprendre comment le projet est construit, où il en est, et quelles décisions ont été prises et pourquoi.

> **Vérifié le : 30/04/2026** — Few-shot livré, déploiement VPS imminent

---

## État actuel — 30/04/2026

Toutes les fonctionnalités core sont livrées en local. Le déploiement VPS est la seule étape bloquante avant ouverture aux pilotes.

| Composant | État |
|---|---|
| Backend FastAPI | ✅ Opérationnel |
| Frontend React + Tailwind | ✅ Opérationnel |
| Auth JWT (signup/login/verify) | ✅ Opérationnel |
| 12 matières | ✅ Opérationnel |
| Profil prof (BDD) | ✅ Livré 28/04/2026 |
| Admin panel complet | ✅ Opérationnel |
| Feedback + Notation séparés | ✅ Livré 28/04/2026 |
| SMTP direct (A-FEEDBACK retiré) | ✅ Livré 28/04/2026 |
| Few-shot adaptation style prof | ✅ Livré 30/04/2026 |
| Déploiement VPS school.afia.fr | ✅ Livré |
| PostgreSQL | ⏳ Phase 4 |

---

## Livré le 30/04/2026 — Few-shot adaptation au style prof

**Ce que ça fait** : à partir de 3 activités du même type, A-SCHOOL injecte les 2 derniers exemples du prof dans le prompt. Le modèle imite son style sans être ré-entraîné.

**Ce qui a été implémenté** :
- Auth JWT sur `/api/generate` (bug sécurité corrigé au passage)
- Requête des 3 dernières activités du même type en base
- Injection via `_build_few_shot_prefix()` dans `src/prompts.py`
- Seuil cold start : `< 3` activités du type → génération normale, invisible pour le prof
- Bannière bleue accueil + toast à la 3e sauvegarde + section "apprentissage" dans l'Aide

---

## Priorité actuelle — Déploiement VPS

```bash
# Depuis /var/www/a-school sur le VPS
git pull && bash deploy/deploy.sh
```

Toutes les sessions depuis le 27/04 doivent être poussées : profil prof, admin complet, 12 matières + prompts, few-shot, LV, statuts feedbacks, carrousel, modale Ajuster.

---

## Planning

| Quand | Action |
|---|---|
| **Maintenant** | Push prod — toutes les fonctionnalités depuis 27/04 |
| **Semaine 1 (mai)** | Tester few-shot avec les profs pilotes, ajuster |
| **Semaine 2** | Assets comm (captures d'écran, exemples Word) |
| **Semaine 3** | Premier post Facebook dans un groupe de profs |
| **Mai → Août** | LinkedIn → associations → campagne rentrée |
| **Phase 2** | Bouton "Partagez avec vos collègues" dans l'interface (voir ci-dessous) |

---

## Amélioration future — Gestion des e-mails sortants dans l'admin

**Contexte :** A-SCHOOL va envoyer de nombreux e-mails à des enseignants (invitations collègues, onboarding, campagnes). Il faut une interface admin pour tout suivre.

**Ce qu'il faut construire :**

| Fonctionnalité | Description |
|---|---|
| **Journal des e-mails envoyés** | Chaque e-mail part → une ligne en base : destinataire, objet, type (invitation / onboarding / campagne), date, statut |
| **Statistiques** | Nombre d'envois par jour/semaine/mois, types les plus fréquents |
| **Taux d'ouverture** | Nécessite un pixel de tracking ou un service SMTP avec webhook (Mailgun, Brevo...) |
| **Retours positifs** | Clic sur le lien d'inscription depuis un e-mail d'invitation → attribuer l'inscription à la source |
| **Gestion des bounces** | E-mails invalides ou boîtes pleines → liste noire automatique |
| **Désinscription** | Lien "Ne plus recevoir ces e-mails" dans chaque mail → marquer en base |

**Dépendance :** le suivi d'ouverture et de clics nécessite un fournisseur SMTP transactionnel avec webhooks (Brevo, Mailgun, Resend...) plutôt qu'un SMTP simple. À planifier avant la phase de campagnes à grande échelle (Phase 3).

**Priorité :** à faire avant les campagnes de masse (Phase 3 — avant rentrée 2026).

---

## Fonctionnalité à venir — Bouton "Partagez avec vos collègues" (Option B)

**Contexte :** Une version simplifiée de ce levier existe déjà sur afia.fr/school (Option A) — n'importe quel visiteur peut envoyer une invitation en saisissant son e-mail. L'Option B est la version authentifiée, à implémenter directement dans school.afia.fr.

**Principe :** Un prof connecté peut envoyer une invitation à ses collègues depuis l'interface de A-SCHOOL. Son identité est garantie par la session JWT — pas de champ à saisir, pas de vérification à faire.

**Où le placer :** dans la `Sidebar` (composant `Sidebar.jsx`), dans la section "À propos" ou juste en dessous du bouton feedback — endroit naturel pour des actions secondaires.

**Ce que ça envoie :**
```
Objet : Marie Dupont (marie.dupont@ac-paris.fr) vous recommande A-SCHOOL

Bonjour,

Marie Dupont vous recommande A-SCHOOL, l'outil gratuit pour les enseignants.
Collez un texte, choisissez le type d'activité et le niveau —
vous obtenez un exercice complet en 10 secondes.

→ Créez votre compte gratuit sur school.afia.fr

— A-SCHOOL — school.afia.fr
```

**Ce qu'il faut coder :**
1. Nouveau router FastAPI : `POST /api/partager/` — accepte `{"emails": "..."}`, lit `prenom + nom` depuis le token JWT, envoie les e-mails via SMTP, limite 5 adresses / 5 appels par jour par user
2. Composant React `PartagerCollègues.jsx` — modale légère avec un seul champ (les e-mails des collègues), le nom de l'expéditeur est pré-rempli automatiquement depuis le profil

**Avantage sur l'Option A :** l'expéditeur est authentifié, son nom complet est connu, l'e-mail d'invitation est plus crédible et plus personnalisé.

---

## Règle de communication — few-shot

| Moment | Message autorisé |
|---|---|
| Avant validation avec les pilotes | Ne pas promettre l'adaptation, mais peut être mentionnée |
| Validé avec les pilotes | *"A-SCHOOL s'adapte à votre façon de travailler"* |
| Communication externe | *"Plus vous l'utilisez, moins vous corrigez"* |

---

## Vision

Plateforme web permettant à **tous les enseignants** (collège → université) de générer des activités pédagogiques, accessible depuis un navigateur, sans aucune compétence technique.

**Cas pilote :** Professeur de français, classe de 4e.

---

## Stack technique (définitif depuis 24/04/2026)

| Composant | Technologie |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | React + Vite + Tailwind CSS |
| Base de données | SQLite → PostgreSQL (Phase 4) |
| IA texte | Groq (llama-3.3-70b-versatile) |
| Auth | JWT httpOnly cookies (bcrypt + python-jose) |
| Email | SMTP Infomaniak (mail.infomaniak.com:587) |
| VPS | AfiaCloud — Ubuntu 24.04 LTS, 4 CPU, 12 Go RAM |
| URL | https://school.afia.fr |
| IPv4 | 83.228.245.163 |
| IPv6 | 2001:1600:18:202::8a |
| SSL | Let's Encrypt — expire 2026-07-15 (renouvellement auto) |
| Déploiement | Nginx + HTTPS Let's Encrypt + systemd |

---

## Architecture fichiers (état 30/04/2026)

```
d:\A-SCHOOL\
├── backend/
│   ├── main.py              # FastAPI app + migrations BDD auto
│   ├── auth.py              # bcrypt, JWT, SMTP (vérification + feedback)
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models_db.py         # User, Feedback, ActiviteSauvegardee...
│   └── routers/
│       ├── auth.py          # /api/auth/*
│       ├── generate.py      # /api/generate (auth JWT + few-shot)
│       ├── activites.py     # /api/activites/{matiere}
│       ├── profil.py        # /api/user/profile (GET + PATCH)
│       ├── mes_activites.py # /api/mes-activites
│       ├── feedback.py      # /api/feedback (feedback + notation)
│       ├── ocr.py           # /api/ocr (lecture image JPG/PNG)
│       └── admin.py         # /api/admin/*
├── frontend/src/
│   ├── App.jsx              # Router principal
│   ├── context/AuthContext.jsx
│   ├── components/
│   │   ├── Header.jsx
│   │   ├── Sidebar.jsx      # Nav + Feedback + Notation + Mon profil
│   │   ├── Parametres.jsx   # Sélecteurs + encart feedback + bandeau Supérieur
│   │   ├── MonProfil.jsx    # Formulaire profil prof
│   │   ├── Feedback.jsx     # Modale feedback (catégorie + message)
│   │   ├── Notation.jsx     # Modale notation (étoiles + commentaire optionnel)
│   │   ├── APropos.jsx      # Notez A-SCHOOL + Envoyer un feedback
│   │   └── ...
│   └── pages/
│       ├── Login.jsx / Signup.jsx / VerifyEmail.jsx
│       ├── AdminLogs.jsx    # Connexions + filtre Tous/Inscriptions/Connexions
│       ├── AdminActivites.jsx
│       ├── AdminFeedbacks.jsx  # Onglets CSAT / Feedbacks + statuts
│       └── AdminProfils.jsx    # Liste profs + filtre + édition inline
├── src/
│   ├── activities.py        # Point d'entrée activités — fusionne FR+HG+10 matières
│   ├── generated_activities.py  # 10 matières générées depuis la matrice markdown
│   └── prompts.py           # Templates prompts + _build_few_shot_prefix()
├── deploy/
│   ├── deploy.sh            # Script déploiement VPS
│   ├── aschool.service      # Systemd unit
│   └── nginx-aschool.conf   # Config Nginx
├── data/aschool.db          # SQLite (non versionné)
├── run.ps1                  # Lancement dev local
└── requirements.txt
```

---

## Décisions techniques clés

| Date | Décision |
|---|---|
| 16/04/2026 | Groq comme fournisseur IA (Gemini banni — compte Workspace incompatible) |
| 24/04/2026 | Streamlit abandonné — migration FastAPI + React |
| 25/04/2026 | Auth JWT opérationnelle en local |
| 27/04/2026 | 12 matières + admin panel complet livré |
| 27/04/2026 | A-FEEDBACK comme notification secondaire |
| 28/04/2026 | A-FEEDBACK retiré — SMTP direct uniquement |
| 28/04/2026 | Profil prof en BDD (prenom, nom, subject, niveau) |
| 28/04/2026 | Feedback ≠ Notation — deux flux séparés, CSAT admin |
| 30/04/2026 | Few-shot livré — JWT auth sur /api/generate + injection _build_few_shot_prefix |
| 30/04/2026 | Nettoyage documentation — AF.md → ETAT_PROJET.md, docs obsolètes retirés |
