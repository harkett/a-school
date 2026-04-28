# A-SCHOOL Platform — Roadmap & Suivi de projet

> **Vérifié le : 28/04/2026** — Stack FastAPI + React en production, Phase 3 largement livrée, push vers prod imminent

---

## État actuel — 28/04/2026

Phase 3 est **fonctionnelle et en production**. Les fondations sont solides.

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
| Few-shot adaptation style prof | ⏳ PRIORITÉ #1 |
| PostgreSQL | ⏳ Phase 4 |

---

## Prochaine priorité — Few-shot adaptation au style prof

**Ce que ça fait** : à partir de 3 activités du même type, A-SCHOOL injecte les 2 derniers exemples du prof dans le prompt. Le modèle imite son style sans être ré-entraîné.

**Étapes dans l'ordre** :

**1. Auth sur `/api/generate`** *(bug sécurité + prérequis obligatoire)*
- `backend/routers/generate.py` : lire le cookie `aschool_access`
- Pattern identique à `mes_activites.py` ligne 24

**2. Requête few-shot en base**
```python
exemples = db.query(ActiviteSauvegardee)
    .filter_by(user_email=email, activite_key=req.activite_key)
    .order_by(id.desc()).limit(2).all()
# Si total pour ce type < 3 → génération normale
```

**3. Injection dans le prompt** (`src/prompts.py`)
```
Voici comment ce professeur formule ses exercices :
--- Exemple 1 ---
Texte source : [texte_source]
Activité produite : [resultat]
--- Exemple 2 ---
[...]
---
Génère le nouvel exercice dans le même style.
```

**Seuil cold start** : `< 3` activités du type → génération normale, invisible pour le prof.

---

## Planning

| Quand | Action |
|---|---|
| **Maintenant** | Push prod — nouvelles fonctionnalités (profil, notation, SMTP) |
| **Semaine 1-2** | Coder few-shot (pendant que les pilotes génèrent) |
| **Semaine 2-3** | Tester l'adaptation avec les pilotes, ajuster |
| **Semaine 3** | Assets comm (captures, vidéo 60s) — seulement après validation few-shot |
| **Semaine 4** | Premier post Facebook dans un groupe de profs |
| **Mai → Août** | LinkedIn → associations → campagne rentrée |

---

## Règle de communication

| Moment | Message autorisé |
|---|---|
| Avant livraison few-shot | Ne pas mentionner l'adaptation |
| Livraison validée avec pilotes | *"A-SCHOOL s'adapte à votre façon de travailler"* |
| Communication externe | *"Plus vous l'utilisez, moins vous corrigez"* |

---

## Vision

Plateforme web permettant à **tous les enseignants** (collège → université) de générer des activités pédagogiques via IA, accessible depuis un navigateur, sans aucune compétence technique.

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
| Déploiement | Nginx + HTTPS Let's Encrypt + systemd |

---

## Déploiement VPS

```bash
# Depuis /var/www/a-school sur le VPS
git pull && bash deploy/deploy.sh
```

Le script gère : pip install, npm build, variables .env manquantes, restart systemd, reload nginx, test santé API.

---

## Architecture fichiers (état 28/04/2026)

```
d:\A-SCHOOL\
├── backend/
│   ├── main.py              # FastAPI app + migrations BDD auto
│   ├── auth.py              # bcrypt, JWT, SMTP (vérification + feedback)
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models_db.py         # User, Feedback, ActiviteSauvegardee...
│   └── routers/
│       ├── auth.py          # /api/auth/*
│       ├── generate.py      # /api/generate
│       ├── activites.py     # /api/activites/{matiere}
│       ├── profil.py        # /api/user/profile (GET + PATCH)
│       ├── mes_activites.py # /api/mes-activites
│       ├── feedback.py      # /api/feedback (feedback + notation)
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
│       ├── AdminLogs.jsx    # Connexions + colonne Matière
│       ├── AdminActivites.jsx
│       ├── AdminFeedbacks.jsx  # Onglets Notations (CSAT) / Feedbacks
│       └── AdminProfils.jsx    # Liste profs + filtre + édition inline
├── src/
│   ├── activities.py        # FR + HG (hardcodé)
│   ├── generated_activities.py  # 10 matières générées depuis markdown
│   └── prompts.py           # Templates prompts par activité
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
