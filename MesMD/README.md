# A-SCHOOL — Générateur d'activités pédagogiques

> **Vérifié le : 21/04/2026 — État : à jour**

Outil web de génération d'activités de français (collège → supérieur) par IA.  
Interface Streamlit — déployé sur VPS AfiaCloud.

**URL de production :** https://school.afia.fr  
**Dernière mise à jour :** 21/04/2026

---

## Stack actuelle

| Composant | Technologie |
|---|---|
| Interface | Streamlit (`app.py`) |
| IA texte | Groq API — `llama-3.3-70b-versatile` |
| IA voix | Groq Whisper API (dictée) |
| Export | Word (.docx) + texte (.txt) |
| Hébergement | VPS AfiaCloud — Ubuntu 24.04 LTS |
| Accès | Nginx + HTTPS Let's Encrypt |

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
cd d:\A-SCHOOL
.venv\Scripts\activate
streamlit run app.py
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
├── app.py               # Interface Streamlit (point d'entrée)
├── src/
│   ├── main.py          # CLI (secondaire)
│   ├── config.py        # Configuration
│   ├── prompts.py       # 15 types d'activités + prompts
│   ├── generator.py     # Appel API Groq / Anthropic
│   └── formats.py       # Mise en forme Markdown
├── outputs/             # Activités générées (non versionné)
├── MesMD/               # Documentation projet
├── .env                 # Clé API (non versionné)
├── .env.example         # Template .env
├── requirements.txt
└── push.ps1             # Script push GitHub
```

---

## Ce qui est en cours / à venir

Voir [ROADMAP.md](ROADMAP.md) et [AF.md](AF.md) dans `MesMD/`.
