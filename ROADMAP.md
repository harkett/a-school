# A-SCHOOL Platform — Roadmap & Suivi de projet

**Dernière mise à jour :** 16/04/2026  
**Responsable :** harketti@afia.fr

---

## Vision

Plateforme web permettant à **tous les enseignants** (collège → université) de générer des activités pédagogiques via IA, accessible depuis un navigateur, sans aucune compétence technique.

**Cas pilote :** Professeur de français, classe de 4e, séquence sur la Nouvelle Réaliste (*Les Misérables*).

---

## Architecture cible

```
┌─────────────────────────────────────────┐
│              VPS (Linux)                │
│                                         │
│  ┌──────────────┐  ┌─────────────────┐  │
│  │   Frontend   │  │    Backend      │  │
│  │   React ou   │  │   FastAPI       │  │
│  │   Streamlit  │  │   Python        │  │
│  └──────┬───────┘  └────────┬────────┘  │
│         └─────────┬─────────┘           │
│            ┌──────┴──────┐              │
│            │   Base de   │              │
│            │   données   │              │
│            │  (SQLite →  │              │
│            │  Postgres)  │              │
│            └─────────────┘              │
└─────────────────────────────────────────┘
         │
         ▼
    Groq API / Claude API (Anthropic)
```

**Stack retenu :**
- Backend : FastAPI (Python)
- Frontend : Streamlit (Phase 2) → React/Vue (Phase 4)
- IA : Groq (gratuit) → Claude Anthropic (production)
- VPS : Ubuntu 22.04, 5€/mois (Hetzner / OVH / DigitalOcean)
- Déploiement : Docker + Nginx + HTTPS (Let's Encrypt)

---

## Phases de développement

### Phase 1 — Prototype local ✅ TERMINÉ
**Objectif :** Valider le concept avec un outil fonctionnel en local.

- [x] CLI Python (Typer + Rich)
- [x] 3 types d'activités : compréhension, pistes de lecture, réécriture
- [x] Export Markdown automatique dans `outputs/`
- [x] Interface Streamlit locale (`streamlit run app.py`)
- [x] Intégration Groq API (llama-3.3-70b-versatile)
- [x] Fichier `.env` pour la configuration

**Commande de lancement :**
```bash
streamlit run app.py --server.port 8080
```

---

### Phase 2 — App web hébergée 🔜 EN COURS (16/04/2026)
**Objectif :** Rendre l'outil accessible en ligne depuis n'importe quel navigateur.

- [x] Nginx installé sur VPS ✅
- [x] Accès SSH disponible ✅
- [x] Code sur GitHub ✅
- [ ] Cloner le repo sur le VPS
- [ ] Créer le `.env` sur le VPS
- [ ] Lancer Streamlit en arrière-plan
- [ ] Configurer Nginx + sous-domaine
- [ ] Obtenir certificat HTTPS (Let's Encrypt)
- [ ] Tester avec la prof pilote

---

### 📋 Commandes de déploiement VPS (à conserver)

**URL cible :** `https://school.afia.fr`

**1. Cloner et installer**
```bash
cd /var/www
git clone TON_REPO_GITHUB a-school
cd a-school
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Créer le `.env` sur le VPS**
```bash
cat > .env << 'EOF'
AI_PROVIDER=groq
AI_API_KEY=TA_CLE_GROQ
AI_MODEL=llama-3.3-70b-versatile
EOF
```

**3. Lancer Streamlit en arrière-plan**
```bash
nohup streamlit run app.py \
  --server.port 8501 \
  --server.headless true \
  --server.enableCORS false \
  > streamlit.log 2>&1 &
```

**4. Config Nginx** → fichier `/etc/nginx/sites-available/school`
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
```

**5. HTTPS**
```bash
certbot --nginx -d school.afia.fr
```

**6. Vérifier**
```bash
curl http://localhost:8501
```

**⚠️ DNS** : ajouter entrée `school.afia.fr → IP du VPS` dans le gestionnaire de domaine **avant** le déploiement (propagation 10-30 min).

---

### Phase 3 — Multi-matières & multi-utilisateurs
**Objectif :** Ouvrir l'outil à plusieurs enseignants et matières.

- [ ] Authentification (login / mot de passe)
- [ ] Profils enseignant (matière, niveau, établissement)
- [ ] Historique des activités générées
- [ ] Toutes matières : maths, histoire, sciences, langues...
- [ ] Base de données (SQLite puis PostgreSQL)
- [ ] Backend FastAPI séparé du frontend

---

### Phase 4 — Produit complet
**Objectif :** Produit finalisé, soigné, partageable.

- [ ] Interface React ou Vue.js
- [ ] Export Word (.docx) en plus du Markdown
- [ ] Partage d'activités entre collègues
- [ ] Tableau de bord par établissement
- [ ] Gestion des abonnements (freemium ?)
- [ ] Documentation utilisateur

---

## Stack technique détaillée

| Composant | Phase 1-2 | Phase 3-4 |
|---|---|---|
| Interface | Streamlit | React / Vue |
| Backend | — | FastAPI |
| Base de données | — | SQLite → PostgreSQL |
| IA | Groq (gratuit) | Groq + Claude |
| Hébergement | Local | VPS Linux |
| Déploiement | — | Docker + Nginx |
| HTTPS | — | Let's Encrypt |

---

## Décisions techniques prises

| Date | Décision | Raison |
|---|---|---|
| 16/04/2026 | Groq comme fournisseur IA | Compte Google Workspace (afia.fr) incompatible free tier Gemini |
| 16/04/2026 | Streamlit pour le frontend Phase 1-2 | Simple, Python, rapide à déployer |
| 16/04/2026 | Appel HTTP direct (requests) | SDK Google instable sur Windows |

---

## Fichiers du projet

```
d:\A-SCHOOL\
├── app.py               # Interface Streamlit
├── src/
│   ├── main.py          # CLI
│   ├── config.py        # Configuration
│   ├── prompts.py       # Templates de prompts IA
│   ├── generator.py     # Appel API (Groq / Anthropic)
│   └── formats.py       # Mise en forme Markdown
├── outputs/             # Activités générées
├── .env                 # Clé API (ne pas versionner)
├── .env.example         # Template .env
├── requirements.txt
├── SPEC.md              # Spécification fonctionnelle initiale
└── ROADMAP.md           # Ce fichier
```

---

## Notes & idées futures

- Permettre l'import de fichiers PDF (extraits de manuels)
- Générer des corrigés en option
- Mode "séquence complète" : générer toutes les activités d'une séquence en une fois
- Application mobile (PWA)
- Intégration ENT (Pronote, etc.)
