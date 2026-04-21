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

```powershell
.\push.ps1 "description des modifications"
```

Le script fait tout : push GitHub + `git pull` + redémarrage Streamlit sur le VPS via SSH. Une seule commande suffit.

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

## Fonctionnalités en production

- Dictée vocale via `streamlit-mic-recorder` + Groq Whisper API
- Export Word (.docx) et texte (.txt)
- Résultat persistant avec bouton Fermer

## Prochaine étape — Phase 2b

Basculer la dictée de Groq Whisper API vers **faster-whisper local** sur le VPS :
- Gratuit illimité, données audio restent sur le serveur
- Modèle `medium` (~1.5 Go RAM), meilleur en français

Voir [ROADMAP.md](ROADMAP.md) et [AF.md](AF.md) pour le détail.
