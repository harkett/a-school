# Backoffice FastAPI+React — Plan d'administration professionnel

> Document de référence — A-SCHOOL / VPS Afiacloud (Infomaniak)
> Adapté depuis le plan Django original (PLAN_BACKOFFICE_DJANGO.md)
> Rédigé le : 2026-05-02

---

## Suivi d'avancement

> Dernière mise à jour : 02/05/2026 — Backoffice 100 % déployé en production sur school.afia.fr

---

### Phase 0 — Prérequis techniques ✅
*Étapes couvertes : tables, limiter, jti, audit*

| Fichier | Ce qui a été fait |
|---|---|
| `backend/limiter.py` | Créé — instance slowapi partagée |
| `backend/auth.py` | `jti` ajouté dans `create_refresh_token()` |
| `backend/models_db.py` | 4 tables créées : `UserSession`, `FailedLoginAttempt`, `AdminAuditLog`, `AdminAlert` |
| `backend/audit.py` | Créé — fonction `log_admin_action(db, admin_email, action, target_email, ip, details)` |
| `requirements.txt` | `slowapi`, `user-agents`, `psutil`, `apscheduler` ajoutés |

---

### Phase 1 — Sécurité brute force ✅
*Étape 2 du plan*

| Fichier | Ce qui a été fait |
|---|---|
| `backend/main.py` | `app.state.limiter` + gestionnaire `RateLimitExceeded` |
| `backend/routers/admin.py` | `@limiter.limit("10/hour")` sur `POST /admin/login` |
| `backend/routers/admin.py` | Enregistrement `FailedLoginAttempt` à chaque échec + `blocked=True` dès 10 tentatives/IP/h |
| `backend/routers/admin.py` | Fonction `_get_admin_email(request)` ajoutée |

---

### Phase 2 — Sessions live + déconnexion forcée ✅
*Étapes 3, 4, 5 du plan*

| Fichier | Ce qui a été fait |
|---|---|
| `backend/middleware.py` | Créé — `UserSessionMiddleware` : lit cookie `aschool_refresh`, extrait `jti`+`email`, vérifie `is_active` avant `call_next`, upsert `UserSession` après |
| `backend/main.py` | `UserSessionMiddleware` enregistré (CORS reste en dernier = le plus externe) |
| `backend/routers/auth.py` | Route `POST /api/heartbeat` — met à jour `last_seen` toutes les 60s |
| `backend/routers/admin.py` | `GET /api/admin/sessions` — sessions actives avec `is_online` (seuil 90s) |
| `backend/routers/admin.py` | `POST /api/admin/force-logout/{id}` — `is_active=False` + `log_admin_action("FORCE_LOGOUT")` |
| `frontend/src/App.jsx` | `useEffect` heartbeat 60s dans `MainApp` (déclenché à la connexion du prof) |

---

### Phase 3 — Dashboard statistiques + monitoring ✅
*Étapes 6, 7, 8 du plan*

| Route | Ce qui a été fait |
|---|---|
| `GET /admin/stats/overview` | Total profs, connexions aujourd'hui, feedbacks nouveaux, sessions en ligne |
| `GET /admin/stats/logins` | Connexions par jour — 30 derniers jours |
| `GET /admin/stats/hours` | ✨ **Extra** — Connexions par heure (0h–23h), heures de pointe |
| `GET /admin/server-metrics` | CPU %, RAM %, disque %, uptime (psutil) |
| `GET /admin/db-size` | Taille SQLite en Mo (`os.path.getsize`) — adapté pour SQLite, pas PostgreSQL |
| `GET /admin/audit-log` | 100 dernières entrées `AdminAuditLog` |
| `GET /admin/failed-attempts` | ✨ **Extra** — 200 dernières tentatives `FailedLoginAttempt` avec statut bloqué |

*Note : db-size utilise `os.path.getsize()` (SQLite) — le plan initial prévoyait `pg_size_pretty` (PostgreSQL, non applicable ici).*

---

### Phase 4 — Alertes automatiques ✅
*Étape 9 du plan*

| Fichier | Ce qui a été fait |
|---|---|
| `backend/alerts.py` | Créé — `_already_alerted()` (anti-flood 2h), `_send_alert_email()` (MIMEMultipart), `create_alert()` |
| `backend/alerts.py` | `check_cpu_alert()` — seuil 90 % → alerte `critical` |
| `backend/alerts.py` | `check_disk_alert()` — seuil 85 % → alerte `warning` |
| `backend/alerts.py` | `check_brute_force_alert()` — ≥ 10 tentatives/h → alerte `critical` |
| `backend/alerts.py` | `run_all_checks()` — orchestre les 3 checks |
| `backend/main.py` | APScheduler `AsyncIOScheduler` via lifespan — `run_all_checks` toutes les 5 min |
| `backend/routers/admin.py` | `GET /admin/alerts` — 50 dernières alertes, non lues en premier |
| `backend/routers/admin.py` | `POST /admin/alerts/{id}/read` — marque lu + enregistre `read_by` + `read_at` |

---

### Phase 5 — UI React complète ✅
*Étape 1 du plan — réalisée en CSS inline personnalisé plutôt que shadcn/Tremor*

| Composant / Page | Ce qui a été fait |
|---|---|
| `AdminLayout.jsx` | Sidebar fixe (220px), nav avec icônes + tooltip `?`, bouton retour A-SCHOOL, déconnexion |
| `AdminServeur.jsx` | Cards CPU/RAM/disque/uptime/DB, graphe barres 30j (bleu), graphe heures de pointe (violet) |
| `AdminSessions.jsx` | Tableau sessions actives, badge "En ligne" vert, bouton déconnexion forcée, auto-refresh 30s |
| `AdminLogs.jsx` | Journal connexions utilisateurs (existait déjà — intégré au layout) |
| `AdminAudit.jsx` | Audit trail avec badges colorés par type d'action |
| `AdminAlertes.jsx` | Cartes par niveau (critical/warning/info), badge non lues, bouton "Lu" |
| `AdminTentatives.jsx` | ✨ **Extra** — Tableau IP / identifiant tenté / statut bloqué / user-agent |
| `AdminActivites.jsx` | Catalogue activités pédagogiques (existait) |
| `AdminFeedbacks.jsx` | Feedbacks avec changement de statut (existait) |
| `AdminProfils.jsx` | Profils profs — lecture + modification (existait) |
| `AdminParametres.jsx` | Email de bienvenue — édition + test (existait) |

---

### Audit trail — couverture des actions sensibles ✅

| Action | `log_admin_action` appelé ? |
|---|---|
| `FORCE_LOGOUT` — déconnexion forcée d'un prof | ✅ |
| `DELETE_USER` — suppression d'un compte prof | ✅ (ajouté 02/05/2026) |
| `UPDATE_SETTINGS` — sauvegarde paramètres email | ✅ (ajouté 02/05/2026) |

---

### Ce qui reste à faire (optionnel / future itération)

| Item | Priorité | Note |
|---|---|---|
| Activation / désactivation de compte prof | Basse | Nécessite champ `is_active` sur `User` |
| Réinitialisation de mot de passe par l'admin | Basse | Flow email déjà en place, à adapter |
| shadcn/ui + Tremor (librairies UI) | Très basse | UI actuelle fonctionnelle et pro — investissement non justifié pour l'instant |
| Filtres avancés sur les logs | Basse | Par date, par IP, par action |


---

## Contexte et objectif

A-SCHOOL tourne sur FastAPI + React. L'admin existant (`backend/routers/admin.py`) est fonctionnel mais minimal. L'objectif est de le transformer en tableau de bord de niveau professionnel SaaS, sans changer de stack.

---

## Ce que l'admin existant fait déjà

- Login/logout admin avec JWT httpOnly cookie
- Liste des utilisateurs vérifiés
- Modification et suppression d'utilisateurs
- Liste des feedbacks avec changement de statut
- Logs de connexion
- Paramètres (email de bienvenue)
- Envoi d'email custom à un utilisateur

---

## Ce qui manque (à développer)

- UI moderne de type SaaS (actuellement fonctionnelle mais non stylée)
- Protection brute force sur le login admin
- Qui est connecté maintenant, depuis quelle machine
- Bouton "déconnecter cet utilisateur"
- Statistiques graphiques (fréquentation, tendances)
- Audit trail des actions admin sensibles
- Monitoring serveur (CPU, RAM, disque)
- Alertes automatiques (CPU critique, brute force, disque plein)

---

## Correspondance Django → FastAPI+React

| Django | FastAPI + React |
|---|---|
| django-unfold | shadcn/ui + Tailwind (React) |
| django-axes | slowapi + table `FailedLoginAttempt` |
| UserSession + Django Middleware | Table `UserSession` + FastAPI Middleware |
| Heartbeat Ajax | Route POST `/heartbeat` (logique identique) |
| Déconnexion forcée | Invalider `UserSession.is_active` en base |
| ORM Django + Chart.js | SQLAlchemy + Chart.js (React, identique) |
| AdminAuditLog | Table `AdminAuditLog` (structure identique) |
| psutil | psutil (Python pur, indépendant du framework) |
| Management command + cron | APScheduler intégré FastAPI (lifespan) |

---

## Packages à installer

```bash
# Backend
pip install slowapi          # Rate limiting
pip install user-agents      # Parsing User-Agent (navigateur/OS)
pip install psutil           # Métriques système (CPU, RAM, disque)
pip install apscheduler      # Scheduler pour les checks d'alertes

# Frontend
npm install @tremor/react    # Composants dashboard (cards, graphiques, badges)
```

Ajouter dans `requirements.txt` après installation.

---

## Plan d'implémentation — Ordre optimal

```
1. UI moderne           → Refonte admin React avec shadcn/ui + Tremor
2. Brute force          → slowapi sur /admin/login + table FailedLoginAttempt
3. UserSession          → Table + Middleware FastAPI (base de tout le monitoring)
4. Heartbeat            → Route POST /heartbeat + JS côté React
5. Déconnexion forcée   → S'appuie sur UserSession
6. Statistiques         → SQLAlchemy queries + Chart.js React
7. Audit trail          → Table AdminAuditLog + fonction log_admin_action()
8. Monitoring psutil    → Route /admin/server-metrics
9. Alertes              → APScheduler (lifespan) + email SMTP existant
```

---

## Étape 1 — UI moderne avec shadcn/ui + Tremor

### Pourquoi c'est la première étape

L'admin React actuel est fonctionnel mais sans identité visuelle. Installer un design system en premier donne un résultat visible immédiat et toutes les étapes suivantes profitent directement de ces composants.

### Choix retenus

- **Tailwind CSS** — déjà présent dans le projet ou à ajouter, base de tout
- **shadcn/ui** — composants React modernes (tables, boutons, badges, formulaires)
- **Tremor** — composants spécialisés dashboard (cartes de stats, graphiques, indicateurs)

### Ce qu'on obtient

- Sidebar collapsible avec navigation claire
- Cards de statistiques en haut du dashboard
- Tables avec tri, filtres, badges colorés
- Indicateurs "● En ligne / ○ Hors ligne"
- Layout responsive professionnel

### Installation

```bash
npm install @tremor/react
npx shadcn-ui@latest init
```

### Résultat

Un admin visuellement professionnel, immédiatement crédible. Base pour toutes les étapes suivantes.

---

## Étape 2 — Protection brute force

### Problème que ça résout

La route `/admin/login` actuelle n'a aucune protection contre les tentatives répétées. Un attaquant peut tenter des milliers de combinaisons sans être bloqué.

### Limiter partagé — fichier dédié

slowapi s'appuie sur `app.state.limiter` pour intercepter les erreurs 429. Il ne doit exister qu'une seule instance dans tout le projet.

```python
# backend/limiter.py  — instance unique, importée partout
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

### Configuration dans main.py

```python
# main.py
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.limiter import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### Route protégée avec enregistrement des tentatives

```python
# routers/admin.py
from backend.limiter import limiter  # instance partagée, pas de nouvelle création

@router.post("/admin/login")
@limiter.limit("10/hour")
def admin_login(request: Request, body: AdminLoginBody, response: Response, db: Session = Depends(get_db)):
    expected_user = os.getenv("ADMIN_USERNAME", "")
    expected_pass = os.getenv("ADMIN_PASSWORD", "")
    ok = (
        bool(expected_user) and bool(expected_pass) and
        secrets.compare_digest(body.username, expected_user) and
        secrets.compare_digest(body.password, expected_pass)
    )
    if not ok:
        ip = request.client.host if request.client else None
        attempt = FailedLoginAttempt(
            ip_address=ip,
            username=body.username,
            user_agent=request.headers.get("user-agent", ""),
        )
        db.add(attempt)
        db.commit()
        # Marquer blocked=True si seuil atteint sur cette IP dans la dernière heure
        since = datetime.utcnow() - timedelta(hours=1)
        count = db.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.ip_address == ip,
            FailedLoginAttempt.attempt_at >= since
        ).count()
        if count >= 10:
            db.query(FailedLoginAttempt).filter(
                FailedLoginAttempt.ip_address == ip,
                FailedLoginAttempt.attempt_at >= since
            ).update({"blocked": True})
            db.commit()
        raise HTTPException(401, "Identifiants incorrects.")
    # ... suite de la logique de login existante
```

### Table FailedLoginAttempt

```python
# models_db.py
class FailedLoginAttempt(Base):
    __tablename__ = "failed_login_attempts"

    id         = Column(Integer, primary_key=True)
    ip_address = Column(String, nullable=True)
    username   = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    attempt_at = Column(DateTime, default=datetime.utcnow)
    blocked    = Column(Boolean, default=False)  # mis à True dès que count >= 10 sur cette IP
```

### Ce qui est visible dans l'admin

Section "Tentatives de connexion" : IP, username, user-agent, timestamp, statut bloqué/libre.

---

## Étape 3 — Tracking de sessions avec UserSession

### Problème que ça résout

Le système JWT actuel ne permet pas de savoir qui est connecté maintenant, depuis quelle machine, depuis combien de temps.

### Prérequis — Ajout du champ jti au token utilisateur

Le middleware s'appuie sur `jti` (JWT ID) pour identifier chaque session de manière unique. Ce champ doit être ajouté à la génération du token dans `backend/auth.py`.

```python
# backend/auth.py — génération du token utilisateur
import uuid

def create_user_token(email: str) -> str:
    jti = str(uuid.uuid4())  # identifiant unique par session
    exp = datetime.utcnow() + timedelta(hours=24)
    payload = {"sub": email, "jti": jti, "exp": exp}
    return jwt.encode(payload, os.getenv("JWT_SECRET", ""), algorithm="HS256")
```

### Table UserSession

```python
# models_db.py
class UserSession(Base):
    __tablename__ = "user_sessions"

    id          = Column(Integer, primary_key=True)
    user_email  = Column(String, ForeignKey("users.email"), nullable=False)
    session_key = Column(String(64), unique=True, nullable=False)
    ip_address  = Column(String, nullable=True)
    user_agent  = Column(String, nullable=True)
    browser     = Column(String(100), nullable=True)   # ex: Chrome 124
    os          = Column(String(100), nullable=True)   # ex: Windows 11
    device_type = Column(String(50), nullable=True)    # desktop/mobile/tablet
    login_at    = Column(DateTime, default=datetime.utcnow)
    last_seen   = Column(DateTime, default=datetime.utcnow)
    is_active   = Column(Boolean, default=True)

    @property
    def is_online(self):
        from datetime import timezone
        delta = datetime.now(timezone.utc) - self.last_seen.replace(tzinfo=timezone.utc)
        return delta.total_seconds() < 90
```

### Middleware FastAPI — trois phases obligatoires

Le middleware doit vérifier `is_active` **avant** de traiter la requête. Si la vérification est faite après `call_next`, la requête est déjà traitée et la déconnexion forcée n'a aucun effet.

```python
# middleware.py
import os
from jose import jwt, JWTError
from user_agents import parse as parse_ua
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from backend.models_db import UserSession
from backend.database import SessionLocal

COOKIE_NAME = "aschool_token"  # cookie des utilisateurs connectés (profs)

class UserSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get(COOKIE_NAME)
        email = None
        session_key = None

        # Phase 1 — vérification AVANT de traiter la requête
        if token:
            try:
                payload = jwt.decode(token, os.getenv("JWT_SECRET", ""), algorithms=["HS256"])
                email = payload.get("sub")
                session_key = payload.get("jti")
                if session_key:
                    db = SessionLocal()
                    try:
                        session = db.query(UserSession).filter_by(session_key=session_key).first()
                        if session and not session.is_active:
                            return Response("Session expirée.", status_code=401)
                    finally:
                        db.close()
            except JWTError:
                pass

        # Phase 2 — traitement de la requête
        response = await call_next(request)

        # Phase 3 — mise à jour last_seen (ou création si nouvelle session)
        if email and session_key:
            ua_string = request.headers.get("user-agent", "")
            ua = parse_ua(ua_string)
            db = SessionLocal()
            try:
                session = db.query(UserSession).filter_by(session_key=session_key).first()
                if session:
                    session.last_seen = datetime.utcnow()
                else:
                    db.add(UserSession(
                        user_email=email,
                        session_key=session_key,
                        ip_address=request.client.host if request.client else None,
                        user_agent=ua_string,
                        browser=f"{ua.browser.family} {ua.browser.version_string}",
                        os=f"{ua.os.family} {ua.os.version_string}",
                        device_type="mobile" if ua.is_mobile else "tablet" if ua.is_tablet else "desktop",
                    ))
                db.commit()
            finally:
                db.close()

        return response
```

---

## Étape 4 — Heartbeat Ajax

### Pourquoi c'est indispensable

Sans heartbeat, `last_seen` n'est mis à jour que lors des requêtes HTTP réelles. Un utilisateur qui laisse une page ouverte sans cliquer apparaît "inactif" alors qu'il est présent.

### Fonctionnement

```
Navigateur utilisateur → POST /heartbeat toutes les 60s → mise à jour last_seen
Seuil : last_seen > 90s → is_online = False
```

### Route FastAPI

Le heartbeat est appelé par le **frontend utilisateur** (les profs), pas par l'admin. Il utilise le même cookie `aschool_token` que le middleware.

```python
# routers/auth.py ou routers/profil.py
@router.post("/heartbeat")
def heartbeat(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("aschool_token")
    if token:
        try:
            payload = jwt.decode(token, os.getenv("JWT_SECRET", ""), algorithms=["HS256"])
            jti = payload.get("jti")
            if jti:
                db.query(UserSession).filter_by(session_key=jti).update(
                    {"last_seen": datetime.utcnow()}
                )
                db.commit()
        except JWTError:
            pass
    return {"status": "ok"}
```

### JavaScript côté React (app utilisateur)

```javascript
// App.jsx ou layout principal de l'application
useEffect(() => {
    const interval = setInterval(() => {
        fetch('/heartbeat', { method: 'POST', credentials: 'include' });
    }, 60000);
    return () => clearInterval(interval);
}, []);
```

### Résultat

Indicateur "● En ligne / ○ Hors ligne" fiable dans le tableau des sessions de l'admin.

---

## Étape 5 — Déconnexion forcée

### Mécanisme

L'admin marque `UserSession.is_active = False` en base. Le middleware (étape 3, phase 1) vérifie ce flag avant chaque requête — la prochaine requête du navigateur de l'utilisateur reçoit un 401 immédiat.

### Fonction utilitaire _get_admin_email

```python
# routers/admin.py
def _get_admin_email(request: Request) -> str:
    token = request.cookies.get("aschool_admin")
    if not token:
        return "admin"
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET", ""), algorithms=["HS256"])
        return payload.get("sub", "admin")
    except JWTError:
        return "admin"
```

### Route de déconnexion forcée

```python
# routers/admin.py
@router.post("/admin/force-logout/{session_id}")
def force_logout(session_id: int, request: Request, db: Session = Depends(get_db), _=Depends(_require_admin)):
    session_obj = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session_obj:
        raise HTTPException(404, "Session introuvable.")
    session_obj.is_active = False
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="FORCE_LOGOUT",
        target_email=session_obj.user_email,
        ip=request.client.host if request.client else None,
        details=f"Session {session_obj.session_key[:8]}... déconnectée"
    )
    return {"status": "ok"}
```

---

## Étape 6 — Statistiques et graphiques

### Ce qu'on affiche

- Connexions par jour (30 derniers jours)
- Heures de pointe (répartition horaire)
- Utilisateurs actifs uniques par semaine
- Taux d'échec de connexion
- Évolution des inscriptions

### Requêtes SQLAlchemy

```python
# routers/admin.py
from sqlalchemy import func
from datetime import timedelta

@router.get("/admin/stats/logins")
def stats_logins(db: Session = Depends(get_db), _=Depends(_require_admin)):
    since = datetime.utcnow() - timedelta(days=30)
    rows = (
        db.query(
            func.date(UserSession.login_at).label("day"),
            func.count(UserSession.id).label("count")
        )
        .filter(UserSession.login_at >= since)
        .group_by(func.date(UserSession.login_at))
        .order_by(func.date(UserSession.login_at))
        .all()
    )
    return [{"day": str(r.day), "count": r.count} for r in rows]
```

### Côté React

```jsx
// Tremor AreaChart — aucune librairie externe supplémentaire
import { AreaChart } from "@tremor/react";

<AreaChart
    data={loginStats}
    index="day"
    categories={["count"]}
    colors={["blue"]}
    yAxisWidth={40}
/>
```

---

## Étape 7 — Audit trail des actions sensibles

### Pourquoi c'est critique

Le système actuel ne trace pas les actions admin sensibles : déconnexion forcée, suppression d'utilisateur, modification de settings.

### Table AdminAuditLog

```python
# models_db.py
class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id           = Column(Integer, primary_key=True)
    admin_email  = Column(String, nullable=True)
    action       = Column(String(50))   # FORCE_LOGOUT, USER_DELETE, SETTINGS_CHANGE, etc.
    target_email = Column(String, nullable=True)
    ip_address   = Column(String, nullable=True)
    details      = Column(Text, nullable=True)
    timestamp    = Column(DateTime, default=datetime.utcnow)
```

### Fonction de log

```python
# backend/audit.py
from backend.models_db import AdminAuditLog

def log_admin_action(db, admin_email, action, target_email=None, ip=None, details=""):
    db.add(AdminAuditLog(
        admin_email=admin_email,
        action=action,
        target_email=target_email,
        ip_address=ip,
        details=details,
    ))
    db.commit()
```

Appelée à chaque action sensible : déconnexion forcée (étape 5), suppression d'utilisateur, modification de settings.

---

## Étape 8 — Monitoring serveur avec psutil

### Route de monitoring

```python
# routers/admin.py
import psutil
from datetime import timezone, timedelta

@router.get("/admin/server-metrics")
def server_metrics(db: Session = Depends(get_db), _=Depends(_require_admin)):
    cpu    = psutil.cpu_percent(interval=1)
    ram    = psutil.virtual_memory()
    disk   = psutil.disk_usage('/')
    uptime = (datetime.now(timezone.utc).timestamp() - psutil.boot_time()) / 3600

    threshold = datetime.utcnow() - timedelta(seconds=90)
    users_online = db.query(UserSession).filter(
        UserSession.is_active == True,
        UserSession.last_seen >= threshold
    ).count()

    return {
        "cpu_percent":   cpu,
        "ram_used_gb":   round(ram.used / 1024**3, 1),
        "ram_total_gb":  round(ram.total / 1024**3, 1),
        "ram_percent":   ram.percent,
        "disk_used_gb":  round(disk.used / 1024**3, 1),
        "disk_total_gb": round(disk.total / 1024**3, 1),
        "disk_percent":  disk.percent,
        "uptime_hours":  round(uptime, 1),
        "users_online":  users_online,
    }
```

### Taille base PostgreSQL

```python
from sqlalchemy import text

@router.get("/admin/db-size")
def db_size(db: Session = Depends(get_db), _=Depends(_require_admin)):
    result = db.execute(text(
        "SELECT pg_size_pretty(pg_database_size(current_database()))"
    )).fetchone()
    return {"size": result[0]}
```

---

## Étape 9 — Alertes automatiques

### Architecture

```
APScheduler (toutes les 5 min, démarré via lifespan FastAPI)
    → check_cpu_alert()
    → check_disk_alert()
    → check_brute_force_alert()
    → si seuil dépassé : créer AdminAlert en base + email SMTP
```

> **⚠ À implémenter — Déduplication des alertes**
> `check_brute_force_alert()` (et les autres checks) créent une nouvelle alerte **à chaque exécution** tant que la condition est vraie, soit toutes les 5 minutes. Cela provoque un flood d'alertes et d'emails.
> Mécanisme à prévoir lors de l'implémentation : avant de créer une alerte, vérifier si une alerte du même type existe déjà dans la base depuis moins de X heures (ex. 2h). Si oui, ne pas créer de doublon.
> ```python
> # Vérification anti-flood à ajouter dans create_alert()
> cooldown_hours = 2
> existing = db.query(AdminAlert).filter(
>     AdminAlert.title == title,
>     AdminAlert.created_at >= datetime.utcnow() - timedelta(hours=cooldown_hours)
> ).first()
> if existing:
>     return  # alerte déjà envoyée récemment, on ne recrée pas
> ```

### Table AdminAlert

```python
# models_db.py
class AdminAlert(Base):
    __tablename__ = "admin_alerts"

    id         = Column(Integer, primary_key=True)
    level      = Column(String(20))   # info / warning / critical
    title      = Column(String(200))
    message    = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read    = Column(Boolean, default=False)
    read_by    = Column(String, nullable=True)
    read_at    = Column(DateTime, nullable=True)
```

### Scheduler via lifespan (syntaxe FastAPI >= 0.93)

`@app.on_event` est déprécié depuis FastAPI 0.93. Le remplacement est le lifespan context manager.

```python
# main.py
import os
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.alerts import run_all_checks

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(run_all_checks, "interval", minutes=5)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

### Checks d'alertes

```python
# backend/alerts.py
import os
import psutil
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend.models_db import AdminAlert, FailedLoginAttempt
from backend import auth as auth_lib


def create_alert(level, title, message):
    db = SessionLocal()
    try:
        db.add(AdminAlert(level=level, title=title, message=message))
        db.commit()
        admin_email = os.getenv("ADMIN_EMAIL", "")
        if admin_email:
            auth_lib._smtp_send(
                to=admin_email,
                subject=f"[A-SCHOOL Admin] {level.upper()} — {title}",
                body=f"{message}\n\nDate : {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}"
            )
    finally:
        db.close()


def check_cpu_alert():
    cpu = psutil.cpu_percent(interval=1)
    if cpu > 90:
        create_alert("critical", f"CPU critique : {cpu}%", "Le CPU dépasse 90%. Vérifier les processus actifs.")


def check_disk_alert():
    disk = psutil.disk_usage('/')
    if disk.percent > 85:
        libre = round((disk.total - disk.used) / 1024**3, 1)
        create_alert("warning", f"Disque faible : {disk.percent}% utilisé", f"Il reste {libre} Go libres.")


def check_brute_force_alert():
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(hours=1)
        count = db.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.attempt_at >= since
        ).count()
        if count >= 10:
            create_alert("critical", f"Tentatives d'intrusion : {count} en 1h", "Activité suspecte. Vérifier les IPs.")
    finally:
        db.close()


def run_all_checks():
    check_cpu_alert()
    check_disk_alert()
    check_brute_force_alert()
```

---

## Récapitulatif des choix de conception

| Décision | Choix retenu | Raison |
|---|---|---|
| UI admin | shadcn/ui + Tremor (React) | Moderne, léger, Tailwind-compatible |
| Protection brute force | slowapi + table custom | Standard FastAPI, simple à intégrer |
| Instance Limiter | `backend/limiter.py` partagé | Une seule instance pour que app.state.limiter soit cohérent |
| Tracking sessions | Middleware FastAPI + UserSession | Contrôle total, même logique que le plan Django |
| Ordre middleware | Check is_active → call_next → update last_seen | Le check doit précéder le traitement pour que force logout soit effectif |
| Cookie session | `aschool_token` (uniforme middleware + heartbeat) | Un seul nom de cookie pour les sessions utilisateur |
| "Connecté maintenant" | Heartbeat 60s + seuil 90s | Identique au plan Django, logique éprouvée |
| Déconnexion forcée | Flag is_active + vérif middleware phase 1 | Invalidation immédiate sans blacklist JWT |
| Statistiques | SQLAlchemy + Tremor charts | Pas de librairie lourde, cohérent avec le stack |
| Audit trail | Table AdminAuditLog | Identique au plan Django |
| Monitoring système | psutil | Python pur, indépendant du framework |
| Notifications | SMTP existant (_smtp_send) + AdminAlert | Réutilise l'infra email déjà en place |
| Scheduler alertes | APScheduler via lifespan | Syntaxe FastAPI >= 0.93, pas de cron externe |

---

## Ordre de migration depuis l'existant

Chaque étape est indépendante et non-destructive. L'admin actuel continue de fonctionner pendant tout le développement.

1. Installer les packages backend + frontend
2. Créer `backend/limiter.py`
3. Ajouter `jti` à la génération du token dans `backend/auth.py`
4. Créer les nouvelles tables (`UserSession`, `FailedLoginAttempt`, `AdminAuditLog`, `AdminAlert`) et migrer
5. Ajouter `UserSessionMiddleware` dans `main.py`
6. Implémenter les étapes 1 à 9 dans l'ordre
7. Tester chaque étape avant de passer à la suivante
8. Déployer sur le VPS uniquement après validation locale complète

---

*Document maintenu dans d:\A-VPS\MesMD\PLAN_BACKOFFICE_FASTAPI.md — À mettre à jour lors de chaque évolution du plan.*
