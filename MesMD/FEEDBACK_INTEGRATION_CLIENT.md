# INTÉGRATION feedback_client.py — Procédure Claude

## Contexte

A-FEEDBACK est un microservice HTTP déployé sur `https://feedback.afia.fr`.
Il reçoit les retours utilisateurs envoyés par les applications clientes.
Le client réutilisable est `feedback_client.py` (à la racine de `D:\A-FEEDBACK\`).

---

## Ce que tu dois faire

### 1. Copier le client dans l'application cible

Copie le fichier `D:\A-FEEDBACK\feedback_client.py` à la racine de l'application cible.

### 2. Ajouter la dépendance

Dans `requirements.txt` de l'app cible, vérifier que `httpx` est présent. Sinon l'ajouter :
```
httpx>=0.27.0
```

### 3. Ajouter la variable d'environnement

Dans le `.env` de l'app cible, ajouter :
```
FEEDBACK_URL=https://feedback.afia.fr
```

### 4. Intégrer l'appel dans le code

Dans la route ou le service approprié de l'app cible, importer et appeler le client :

**App FastAPI (async) :**
```python
from feedback_client import send_async

await send_async(
    app="nom-app",        # identifiant de l'app (ex: "a-school", "a-viewcam")
    user_id=str(user.id), # identifiant de l'utilisateur connecté
    message=message,      # texte du retour (1–2000 car.)
    rating=rating         # note de 1 à 5
)
```

**Script ou app non-async :**
```python
from feedback_client import send

send(app="nom-app", user_id="user_42", message="...", rating=5)
```

### 5. Règles importantes

- Le champ `app` doit correspondre à une clé dans `APP_EMAILS` sur le serveur A-FEEDBACK
  (sinon le feedback est enregistré mais aucun email n'est envoyé)
- Les valeurs actuelles dans `APP_EMAILS` : `{"a-viewcam": "contact@afia.fr"}`
- `send()` et `send_async()` retournent `True` si succès, `False` si erreur — **jamais d'exception**
- Timeout 3 secondes — ne bloque pas l'utilisateur

---

## Test de vérification

Après intégration, vérifier que :
1. `GET https://feedback.afia.fr/health` → `{"status":"ok"}`
2. Un feedback envoyé depuis l'app apparaît dans `GET https://feedback.afia.fr/feedback` (avec token admin)
3. Un email est reçu sur `contact@afia.fr`

---

## Accès pour un développeur externe

**Aucun accès au VPS n'est nécessaire.**

`POST /feedback` est une route **publique** — elle ne nécessite aucun token, aucune clé SSH, aucun accès serveur. Le collègue fait simplement un appel HTTPS standard vers `https://feedback.afia.fr/feedback`, comme n'importe quelle API publique.

Le VPS reste fermé. Seul le port 443 (HTTPS) est exposé publiquement.

Les routes admin (lire, supprimer, répondre aux feedbacks) sont protégées par JWT — seul l'administrateur AFIA y a accès.

---

## Informations serveur A-FEEDBACK

- URL production : `https://feedback.afia.fr`
- Port interne VPS : `8002`
- Service systemd : `a-feedback.service`
- Répertoire VPS : `/home/ubuntu/a-feedback`
