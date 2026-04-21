# A-SCHOOL — Guide de Production

> **Vérifié le : 21/04/2026 — État : à jour**

**URL :** https://school.afia.fr  
**Responsable :** harketti@afia.fr

---

## Infra

| Élément | Valeur |
|---------|--------|
| Serveur | AfiaCloud (Infomaniak) |
| OS | Ubuntu 24.04 LTS |
| CPU / RAM | 4 cœurs / 12 Go |
| IPv4 | 83.228.245.163 |
| IPv6 | 2001:1600:18:202::8a |
| DNS | Infomaniak — zone afia.fr |
| HTTPS | Let's Encrypt (expire 2026-07-15, renouvellement auto) |
| Reverse proxy | Nginx |
| App | Streamlit sur port 8501 |
| IA | Groq API — llama-3.3-70b-versatile |

---

## Déploiement initial (déjà fait)

```bash
cd /var/www
git clone https://github.com/harkett/a-school.git a-school
cd a-school
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Créer .env avec clé Groq
nohup streamlit run app.py --server.port 8501 --server.headless true --server.enableCORS false > streamlit.log 2>&1 &
sudo ln -s /etc/nginx/sites-available/school /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d school.afia.fr
```

---

## Mise à jour du site

**Étape 1 — Sur le PC local :**
```powershell
.\push.ps1 "description des modifications"
```

**Étape 2 — Sur le VPS (SSH) :**
```bash
cd /var/www/a-school && git pull && pkill -f streamlit
nohup streamlit run app.py --server.port 8501 --server.headless true > streamlit.log 2>&1 &
```

---

## Commandes utiles sur le VPS

**Vérifier que Streamlit tourne :**
```bash
ps aux | grep streamlit
```

**Voir les logs Streamlit :**
```bash
tail -f /var/www/a-school/streamlit.log
```

**Redémarrer Nginx :**
```bash
sudo systemctl reload nginx
```

**Vérifier le statut Nginx :**
```bash
sudo systemctl status nginx
```

**Renouveler le certificat HTTPS manuellement :**
```bash
sudo certbot renew
```

---

## Config Nginx

Fichier : `/etc/nginx/sites-available/school`

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

---

## Fichier .env sur le VPS

Emplacement : `/var/www/a-school/.env`

```
AI_PROVIDER=groq
AI_API_KEY=<clé Groq>
AI_MODEL=llama-3.3-70b-versatile
```

---

## Prochaine étape — Phase 2b

Ajouter la saisie vocale (Whisper local) :
- `streamlit-mic-recorder` — capture audio navigateur
- `faster-whisper` — transcription sur VPS (modèle medium, français)

Voir [ROADMAP.md](ROADMAP.md) pour le détail.
