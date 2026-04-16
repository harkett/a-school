# A-SCHOOL Platform — Roadmap & Suivi de projet

**Dernière mise à jour :** 16/04/2026  
**Responsable :** harketti@afia.fr

---

## Vision

Plateforme web permettant à **tous les enseignants** (collège → université) de générer des activités pédagogiques via IA, accessible depuis un navigateur, sans aucune compétence technique.

**Cas pilote :** Professeur de français, classe de 4e, séquence sur la Nouvelle Réaliste (*Les Misérables*).

---

## Architecture cible (validée 16/04/2026)

```
┌─────────────────────────────────────────────┐
│                VPS (Linux)                  │
│                                             │
│  ┌─────────────┐      ┌──────────────────┐  │
│  │  Frontend   │      │  Backend FastAPI  │  │
│  │  React/Vue  │◄────►│  + Interface Admin│  │
│  └─────────────┘      └────────┬─────────┘  │
│                                │             │
│                      ┌─────────┴────────┐    │
│                      │  Base de données  │    │
│                      │  SQLite → Postgres│    │
│                      │                   │    │
│                      │  activites        │    │
│                      │  utilisateurs     │    │
│                      │  historique       │    │
│                      └──────────────────┘    │
└─────────────────────────────────────────────┘
              │
              ▼
        Groq API → Claude API (production)
```

**Principe clé — Backend Admin :**
Les prompts et types d'activités sont stockés en **base de données**, pas dans le code.
L'admin ajoute/modifie une activité via formulaire web → elle apparaît immédiatement dans l'interface prof. **Zéro code requis.**

```
Table "activites" :
| id | nom           | prompt_template   | sous_types       |
|----|---------------|-------------------|------------------|
| 1  | comprehension | "Tu es un prof..." | simples, QCM...  |
| 2  | reecriture    | "Tu es un prof..." | direct→indirect  |
```

**Stack retenu :**
- Backend : **FastAPI** (Python)
- Frontend : Streamlit (Phase 2) → React/Vue (Phase 4)
- Admin : Interface FastAPI intégrée
- IA texte : Groq (gratuit) → Claude Anthropic (production)
- IA voix : **Whisper local** (faster-whisper, gratuit pour toujours)
- BDD : SQLite → PostgreSQL
- VPS : **AfiaCloud** — Ubuntu 24.04 LTS, 4 CPU, 12 Go RAM, 250 Go stockage
- URL : **https://school.afia.fr**
- Déploiement : Docker + Nginx + HTTPS (Let's Encrypt)

---

## Phases de développement

### Phase 1 — Prototype local ✅ TERMINÉ (16/04/2026)
**Objectif :** Valider le concept avec un outil fonctionnel en local.

- [x] CLI Python (Typer + Rich)
- [x] 15 types d'activités avec sous-types
- [x] Option correction intégrée
- [x] Export Markdown automatique dans `outputs/`
- [x] Interface Streamlit locale
- [x] Intégration Groq API (llama-3.3-70b-versatile)
- [x] Push GitHub — https://github.com/harkett/a-school

**15 activités disponibles :**
1. Questions de compréhension (6 sous-types)
2. Pistes de lecture (5 sous-types)
3. Résumés (3 sous-types)
4. Analyse de texte (4 sous-types)
5. Exercices de réécriture (9 transformations)
6. Étude de vocabulaire (4 sous-types)
7. Production d'écrit (5 sous-types dont texte poétique)
8. Questions pour l'oral (3 sous-types)
9. Fiche pédagogique
10. Exercices de grammaire (4 sous-types)
11. Recherche de séquences
12. Séquence détaillée
13. Questionnaire sur un roman
14. Évaluation de grammaire
15. Évaluation d'orthographe

---

### Phase 2 — App web hébergée 🔜 EN COURS (16/04/2026)
**Objectif :** Rendre l'outil accessible depuis n'importe quel navigateur.

- [x] Nginx installé sur VPS ✅
- [x] Accès SSH disponible ✅
- [x] Code pushé sur GitHub ✅
- [ ] Cloner le repo sur le VPS
- [ ] Créer le `.env` sur le VPS
- [ ] Lancer Streamlit en arrière-plan
- [ ] Configurer Nginx → `school.afia.fr`
- [ ] HTTPS (Let's Encrypt)
- [ ] Test avec la prof pilote

---

### 📋 Commandes de déploiement VPS

**URL cible :** `https://school.afia.fr`

**1. Cloner et installer**
```bash
cd /var/www
git clone https://github.com/harkett/a-school.git a-school
cd a-school
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Créer le `.env`**
```bash
cat > .env << 'EOF'
AI_PROVIDER=groq
AI_API_KEY=TA_CLE_GROQ
AI_MODEL=llama-3.3-70b-versatile
EOF
```

**3. Lancer Streamlit**
```bash
nohup streamlit run app.py \
  --server.port 8501 \
  --server.headless true \
  --server.enableCORS false \
  > streamlit.log 2>&1 &
```

**4. Config Nginx** → `/etc/nginx/sites-available/school`
```nginx
server {
    server_name school.afia.fr;
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```
```bash
ln -s /etc/nginx/sites-available/school /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
certbot --nginx -d school.afia.fr
```

**Mise à jour après push GitHub :**
```bash
cd /var/www/a-school && git pull && pkill -f streamlit
nohup streamlit run app.py --server.port 8501 --server.headless true > streamlit.log 2>&1 &
```

---

### Phase 2b — Saisie vocale 🎤 PLANIFIÉE (après déploiement VPS)
**Objectif :** Permettre au prof de dicter son texte à la volée via le micro du navigateur.

**Principe :**
```
Micro navigateur → streamlit-mic-recorder (capture audio)
                        ↓
              faster-whisper sur VPS (transcription locale)
                        ↓
              Texte affiché dans la zone de saisie
```

**Pourquoi Whisper local (pas API externe) :**
- Gratuit pour toujours — aucun fournisseur, aucun piège tarifaire
- Données audio restent sur le serveur (confidentialité)
- AfiaCloud 12 Go RAM largement suffisant (modèle medium = 1.5 Go)

**Librairies à ajouter :**
- `streamlit-mic-recorder` — capture audio navigateur
- `faster-whisper` — transcription sur VPS (modèle `medium`, meilleur en français)

**Interface :**
```
[📁 Importer .txt]  [🎤 Dicter]
┌─────────────────────────────┐
│ Ou collez votre texte...    │
└─────────────────────────────┘
```

- [ ] Installer faster-whisper sur VPS
- [ ] Télécharger modèle Whisper medium (français)
- [ ] Ajouter bouton micro dans app.py
- [ ] Ajouter **sélecteur de micro** (liste des périphériques via MediaDevices.enumerateDevices())
- [ ] Ajouter fonction transcription dans generator.py
- [ ] Tester avec la prof pilote

---

### Phase 3 — Backend FastAPI + Admin ⏳ PLANIFIÉE
**Objectif :** Architecture indépendante, admin autonome, multi-utilisateurs.

- [ ] Backend FastAPI (Python)
- [ ] Base de données SQLite (migration PostgreSQL prévue)
- [ ] Table `activites` — prompts gérés en BDD, plus dans le code
- [ ] Interface admin web — ajouter/modifier/supprimer des activités sans code
- [ ] Authentification enseignants (login/mot de passe)
- [ ] Profils : matière, niveau, établissement
- [ ] Historique des activités générées par prof
- [ ] API REST documentée (Swagger auto FastAPI)
- [ ] Docker pour isoler backend/frontend/BDD

---

### Phase 4 — Produit complet ⏳ PLANIFIÉE
**Objectif :** Produit finalisé, multi-matières, partageable.

- [ ] Frontend React ou Vue.js
- [ ] Export Word (.docx)
- [ ] Partage d'activités entre collègues
- [ ] Tableau de bord par établissement
- [ ] Toutes matières (maths, histoire, sciences, langues...)
- [ ] Import PDF (extraits de manuels)
- [ ] Mode "séquence complète" (toutes activités en une fois)
- [ ] Application mobile (PWA)
- [ ] Intégration ENT (Pronote, etc.)
- [ ] Gestion abonnements (freemium ?)
- [ ] Documentation utilisateur

---

## Décisions techniques

| Date | Décision | Raison |
|---|---|---|
| 16/04/2026 | Groq comme fournisseur IA | Compte Google Workspace incompatible free tier Gemini |
| 16/04/2026 | Streamlit Phase 1-2 | Simple, Python, rapide à déployer |
| 16/04/2026 | Appel HTTP direct (requests) | SDK Google instable sur Windows |
| 16/04/2026 | Backend FastAPI + BDD Phase 3 | Prompts en base = admin autonome, zéro code pour modifications |

---

## Workflow de modification (validé)

```
Prof identifie un besoin
        ↓
harketti transmet à Claude
        ↓
Claude code (prompts.py ou app.py)
        ↓
harketti : .\push.ps1 "description"
        ↓
VPS : git pull + restart
        ↓
Disponible en ligne (~15 min)
```

**Phase 3 :** Ce workflow devient un simple formulaire admin. Plus de code du tout.

---

## Fichiers du projet

```
d:\A-SCHOOL\
├── app.py               # Interface Streamlit
├── push.ps1             # Script push GitHub
├── src/
│   ├── main.py          # CLI
│   ├── config.py        # Configuration
│   ├── prompts.py       # 15 types d'activités + prompts
│   ├── generator.py     # Appel API (Groq / Anthropic)
│   └── formats.py       # Mise en forme Markdown
├── outputs/             # Activités générées (non versionné)
├── .env                 # Clé API (non versionné)
├── .env.example         # Template .env
├── requirements.txt
├── SPEC.md              # Spécification fonctionnelle initiale
└── ROADMAP.md           # Ce fichier
```
