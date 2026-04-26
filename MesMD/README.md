# A-SCHOOL — Générateur d'activités pédagogiques

> **Vérifié le : 24/04/2026 — État : migration en cours** — Streamlit abandonné, nouvelle stack PRO en développement

Plateforme web de génération d'activités pédagogiques pour enseignants (collège → supérieur).  
**En production** sur VPS AfiaCloud (Streamlit, 2 profs pilotes) — **migration vers stack PRO en cours**.

**URL de production :** https://school.afia.fr  
**Dernière mise à jour :** 24/04/2026

---

## Stack cible (validée 24/04/2026)

| Composant | Technologie |
|---|---|
| Backend | FastAPI (Python) — réutilise `src/generator.py` et `src/prompts.py` |
| Frontend | React + Vite + Tailwind CSS |
| Génération texte | Groq API — `llama-3.3-70b-versatile` |
| Génération voix | Groq Whisper API (dictée) |
| Export | Word (.docx) + texte (.txt) |
| Auth | JWT + Google OAuth + Magic link (à reconstruire) |
| BDD | PostgreSQL (historique, comptes) |
| Hébergement | VPS AfiaCloud — Ubuntu 24.04 LTS |
| Accès | Nginx + HTTPS Let's Encrypt |

## Stack en production (Streamlit — NE PAS TOUCHER)

| Composant | Technologie |
|---|---|
| Interface | Streamlit (`app.py`) — **2 profs en production** |
| Génération texte | Groq API — `llama-3.3-70b-versatile` |
| Auth | Google OAuth + Magic link email (`src/auth.py`) |

---

## Installation (première fois uniquement)

```powershell
cd d:\A-SCHOOL
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Lancer en mode DEV (usage quotidien)

```powershell
.\run.ps1
```

L'app s'ouvre automatiquement sur http://localhost:8501  
Streamlit recharge l'app à chaque sauvegarde de fichier — pas besoin de redémarrer.

---

## Configuration

Copier `.env.example` en `.env` :

```bash
copy .env.example .env
```

Éditer `.env` :

```
AI_PROVIDER=groq
AI_API_KEY=ta_cle_groq
AI_MODEL=llama-3.3-70b-versatile
```

---

## Déployer une mise à jour sur le VPS

```powershell
.\push.ps1 "description de la modif"
```

C'est tout. Le script pousse sur GitHub **et** redémarre l'app sur le VPS automatiquement.

---

## Structure du projet

```
d:\A-SCHOOL\
├── app.py               # Interface Streamlit (PRODUCTION — ne pas modifier)
├── frontend/
│   └── index.html       # Prototype UI validé (HTML + Tailwind) — base React à venir
├── src/
│   ├── config.py        # Configuration (Groq API key, modèle)
│   ├── prompts.py       # 27 activités (Français + Histoire-Géo) + prompts
│   ├── generator.py     # Appel API Groq (texte, voix, OCR image)
│   ├── auth.py          # Google OAuth + Magic link
│   └── formats.py       # Mise en forme Markdown
├── outputs/             # Activités générées (non versionné)
├── MesMD/               # Documentation projet
├── .env                 # Clé API (non versionné)
├── .env.example         # Template .env
├── requirements.txt
├── run.ps1              # Lancer en mode DEV (Streamlit)
└── push.ps1             # Push GitHub + redémarrage VPS
```

---

## Règles de développement

- **Pas de "IA"** dans l'interface — utiliser "A-SCHOOL"
- **Boutons** : toujours icône SVG + texte + `title=` (bulle d'aide)
- **Couleur accent** : bordeaux `#A63045` + bleu `#1F6EEB`
- **Workflow** : proposer → valider → coder → tester (jamais coder sans validation)
- **Production** : `app.py` Streamlit ne pas toucher — 2 profs pilotes actifs

---

## Ce qui est en cours / à venir

Voir [ROADMAP.md](ROADMAP.md) dans `MesMD/`.
