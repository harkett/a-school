# Backoffice Django — Plan d'administration professionnel

> Document de référence — Groupe AFIA / VPS Afiacloud (Infomaniak)
> Applicable à toutes les applications : AFIALOC, A-SCHOOL, etc.
> Rédigé le : 2026-05-02

---

## Contexte et objectif

Le VPS Afiacloud héberge plusieurs applications Django (AFIALOC, A-SCHOOL, etc.). Chaque application dispose d'un backoffice Django Admin. L'objectif est de transformer cet admin standard en un tableau de bord de niveau professionnel SaaS, en conservant tout ce que Django offre nativement et en comblant précisément ce qu'il ne fait pas.

---

## Ce que Django Admin fait nativement (à conserver tel quel)

Django Admin couvre déjà un large spectre sans aucun développement :

- Création, modification, suppression de comptes utilisateurs
- Activation et désactivation de comptes
- Réinitialisation et changement de mot de passe
- Gestion des groupes et des permissions fines par utilisateur
- Voir la date de dernier login et la date de création de compte
- Recherche, tri et filtrage avancés sur les utilisateurs
- Historique des actions administrateur (qui a modifié quoi et quand)
- Gestion complète du contenu de la base de données
- Interface sécurisée avec authentification admin dédiée
- Support multi-administrateurs avec rôles différents
- Gestion rapide sans développer d'interface spécifique

Ces fonctionnalités sont robustes, testées et maintenues par la communauté Django. On ne les réécrit pas — on les complète.

---

## Ce que Django Admin ne fait pas nativement (à développer)

- Voir en temps réel qui est connecté maintenant
- Durée exacte de connexion en live
- Bouton direct "déconnecter cet utilisateur"
- Statistiques graphiques avancées (fréquentation, tendances)
- Tableau de fréquentation détaillé (logins/jour, heures de pointe)
- IP et navigateur automatiquement affichés par session
- Alertes de sécurité avancées (brute force, anomalies)
- Monitoring live du serveur (CPU, RAM, disque)
- Notifications temps réel ou par email
- Dashboard moderne de type SaaS

---

## Packages à installer (vue d'ensemble)

```bash
pip install django-unfold        # Thème UI moderne
pip install django-axes          # Sécurité et détection brute force
pip install user-agents          # Parsing User-Agent (navigateur/OS)
pip install psutil               # Métriques système (CPU, RAM, disque)
pip install django-filter        # Filtres avancés dans les listes admin
```

Ajouter dans `requirements.txt` après installation.

---

## Plan d'implémentation — Ordre optimal

L'ordre a été pensé pour que chaque étape s'appuie sur la précédente. On ne construit pas les alertes avant d'avoir les données qui les alimentent.

```
1. Unfold             → UI moderne en premier (motivation visuelle immédiate)
2. django-axes        → Sécurité dès le départ (alimente les alertes futures)
3. UserSession        → Tracking sessions (base de tout le monitoring)
4. Heartbeat Ajax     → Nécessite UserSession (last_seen, session_key)
5. Déconnexion forcée → S'appuie directement sur UserSession
6. Statistiques       → Valeur ajoutée visible, s'appuie sur les données accumulées
7. Logs sensibles     → Audit trail (les actions à logger existent maintenant)
8. Monitoring psutil  → Infrastructure, données serveur
9. Alertes            → Branche sur axes + psutil déjà en place
```

---

## Étape 1 — Thème UI moderne avec Unfold

### Pourquoi Unfold plutôt que le thème par défaut

Le thème Django Admin par défaut date visuellement et souffre d'ergonomie limitée : navigation peu intuitive, pas de dark mode, pas de cartes de statistiques, mise en page rigide. Unfold repose sur Tailwind CSS et apporte une interface digne d'un SaaS moderne sans toucher à la logique admin.

### Ce qu'Unfold apporte concrètement

- Sidebar de navigation claire et collapsible
- Dark mode intégré
- Cartes de statistiques configurables en haut du dashboard
- Support des widgets personnalisés (graphiques, compteurs)
- Typographie et espacement professionnels
- Compatible 100% avec toutes les customisations Django Admin existantes

### Installation

```bash
pip install django-unfold
```

```python
# settings.py
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    # ... reste des apps
]
```

```python
# settings.py — configuration de base
UNFOLD = {
    "SITE_TITLE": "NOM_APPLICATION Admin",  # ex: "AFIALOC Admin", "A-SCHOOL Admin"
    "SITE_HEADER": "Groupe AFIA — Backoffice",
    "SHOW_HISTORY_DASHBOARD": True,
    "SHOW_VIEW_ON_SITE": True,
}
```

### Résultat visuel

Un backoffice immédiatement reconnaissable comme professionnel. Premier gain de crédibilité visible par tous les administrateurs.

---

## Étape 2 — Sécurité avec django-axes

### Pourquoi commencer par la sécurité

Les données de tentatives de connexion échouées collectées par django-axes alimenteront directement les alertes de l'étape 6.5. Installer axes tôt signifie avoir un historique complet quand on branche les notifications.

### Ce que django-axes fait

- Détecte et bloque les tentatives de connexion répétées (brute force)
- Bloque par IP, par nom d'utilisateur, ou les deux
- Enregistre chaque tentative avec timestamp, IP, user-agent
- S'intègre dans Django Admin pour visualiser les accès bloqués
- Déverrouillage manuel possible depuis l'admin

### Installation et configuration

```bash
pip install django-axes
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'axes',
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    # axes doit être en premier
    'axes.middleware.AxesMiddleware',
    # ... reste du middleware
]

# Seuils de blocage
AXES_FAILURE_LIMIT = 10          # Blocage après 10 tentatives
AXES_COOLOFF_TIME = 1            # Déblocage auto après 1 heure
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True  # Bloquer user+IP ensemble
AXES_RESET_ON_SUCCESS = True     # Remet le compteur à zéro après succès
```

### Ce qui est visible dans l'admin

Une section "Access Attempts" avec la liste de toutes les tentatives échouées : IP, username, user-agent, timestamp, nombre de tentatives, statut bloqué/libre.

---

## Étape 3 — Tracking de sessions avec UserSession

### Problème que ça résout

Django maintient des sessions dans la table `django_session`, mais sans métadonnées utiles : pas d'IP, pas de navigateur, pas de timestamp de dernière activité. Il est impossible de savoir qui est connecté maintenant, depuis quelle machine, depuis combien de temps.

### Modèle UserSession

```python
# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    browser = models.CharField(max_length=100, blank=True)    # ex: Chrome 124
    os = models.CharField(max_length=100, blank=True)         # ex: Windows 11
    device_type = models.CharField(max_length=50, blank=True) # desktop/mobile/tablet
    login_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)           # mis à jour par heartbeat
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Session utilisateur"
        verbose_name_plural = "Sessions utilisateurs"

    @property
    def is_online(self):
        from django.utils import timezone
        from datetime import timedelta
        # Considéré connecté si heartbeat reçu il y a moins de 90 secondes
        return (timezone.now() - self.last_seen).total_seconds() < 90
```

### Middleware de création de session

```python
# middleware.py
from user_agents import parse as parse_ua
from .models import UserSession

class UserSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and hasattr(request, 'session'):
            ua = parse_ua(request.META.get('HTTP_USER_AGENT', ''))
            UserSession.objects.update_or_create(
                session_key=request.session.session_key,
                defaults={
                    'user': request.user,
                    'ip_address': self.get_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'browser': f"{ua.browser.family} {ua.browser.version_string}",
                    'os': f"{ua.os.family} {ua.os.version_string}",
                    'device_type': 'mobile' if ua.is_mobile else 'tablet' if ua.is_tablet else 'desktop',
                }
            )
        return response

    def get_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
```

---

## Étape 4 — Heartbeat Ajax (connecté "maintenant" en temps réel)

### Pourquoi c'est indispensable

Sans heartbeat, `last_seen` n'est mis à jour que lors des requêtes HTTP réelles (navigation entre pages). Un utilisateur qui laisse une page ouverte sans cliquer apparaît comme "inactif" alors qu'il est présent. Le heartbeat envoie un signal silencieux toutes les 60 secondes depuis le navigateur.

### Fonctionnement

```
Navigateur → POST /admin/heartbeat/ toutes les 60s → mise à jour last_seen
Seuil : last_seen > 90s → is_online = False
```

### Vue Django

```python
# views.py
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from .models import UserSession

@staff_member_required
def heartbeat(request):
    if request.method == 'POST' and request.user.is_authenticated:
        UserSession.objects.filter(
            session_key=request.session.session_key
        ).update(last_seen=timezone.now())
    return JsonResponse({'status': 'ok'})
```

### JavaScript côté admin (injecté via template Unfold)

```javascript
// heartbeat.js — inclus dans le template admin de base
setInterval(function() {
    fetch('/admin/heartbeat/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)[1],
            'Content-Type': 'application/json'
        }
    });
}, 60000); // toutes les 60 secondes
```

### Résultat

Un indicateur "● En ligne" ou "○ Hors ligne" fiable par session dans l'admin, mis à jour automatiquement.

---

## Étape 5 — Déconnexion forcée d'un utilisateur

### Cas d'usage

Un compte compromis, une session ouverte sur un poste public, un employé qui quitte l'entreprise. L'admin doit pouvoir déconnecter immédiatement n'importe quel utilisateur sans attendre l'expiration naturelle de sa session.

### Mécanisme

Django stocke les sessions dans la table `django_session`. Supprimer l'enregistrement de session invalide immédiatement le token côté serveur. La prochaine requête du navigateur recevra une réponse "session expirée".

```python
# admin.py
from django.contrib.sessions.models import Session
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import UserSession
from .audit import log_admin_action  # étape 7

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'browser', 'os', 'device_type',
                    'login_at', 'last_seen', 'status_badge', 'force_logout_button']
    list_filter = ['is_active', 'device_type']
    readonly_fields = ['user', 'session_key', 'ip_address', 'browser', 'os',
                       'login_at', 'last_seen']

    def status_badge(self, obj):
        if obj.is_online:
            return format_html('<span style="color:green;">● En ligne</span>')
        return format_html('<span style="color:gray;">○ Hors ligne</span>')
    status_badge.short_description = "Statut"

    def force_logout_button(self, obj):
        if obj.is_active:
            return format_html(
                '<a class="button" href="/admin/force-logout/{}/">Déconnecter</a>',
                obj.pk
            )
        return "—"
    force_logout_button.short_description = "Action"

@staff_member_required
def force_logout_view(request, session_id):
    session_obj = UserSession.objects.get(pk=session_id)
    try:
        Session.objects.get(session_key=session_obj.session_key).delete()
    except Session.DoesNotExist:
        pass
    session_obj.is_active = False
    session_obj.save()
    # Log de l'action sensible (étape 7)
    log_admin_action(
        admin_user=request.user,
        action='FORCE_LOGOUT',
        target_user=session_obj.user,
        ip=request.META.get('REMOTE_ADDR'),
        details=f"Session {session_obj.session_key[:8]}... déconnectée"
    )
    messages.success(request, f"{session_obj.user} a été déconnecté.")
    return redirect('/admin/sessions/usersession/')
```

---

## Étape 6 — Statistiques et graphiques

### Ce qu'on affiche

- Nombre de connexions par jour (30 derniers jours)
- Heures de pointe (répartition horaire des connexions)
- Utilisateurs actifs uniques par semaine
- Pages les plus visitées
- Taux d'échec de connexion (ratio axes)
- Évolution du nombre d'utilisateurs inscrits

### Approche technique

Pas de librairie externe lourde. On utilise :
- Django ORM avec `annotate()` et `TruncDay/TruncHour` pour les agrégations
- Chart.js (CDN, léger) pour les graphiques dans les templates admin
- Des vues admin personnalisées (`TemplateView` intégrées dans l'admin Unfold)

```python
# views.py — exemple stats connexions
from django.db.models.functions import TruncDay
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

def get_login_stats():
    last_30_days = timezone.now() - timedelta(days=30)
    return (
        UserSession.objects
        .filter(login_at__gte=last_30_days)
        .annotate(day=TruncDay('login_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
```

### Intégration dans Unfold

Unfold supporte des "dashboard callbacks" : des fonctions qui retournent des données affichées sous forme de cartes en haut du dashboard. On branche les stats directement là.

---

## Étape 7 — Logs des actions sensibles (Audit Trail)

### Pourquoi c'est critique

Django LogEntry enregistre les modifications CRUD standard (ajout, modification, suppression d'objets via l'admin). Mais il ne trace pas les actions métier sensibles : déconnexion forcée d'un utilisateur, changement de rôle, reset de mot de passe depuis l'admin, modification de permissions.

Dès qu'il y a plusieurs administrateurs, l'audit trail est indispensable. En cas d'incident, on doit pouvoir répondre à "qui a fait quoi, depuis quelle IP, à quelle heure".

### Modèle AdminAuditLog

```python
# models.py
class AdminAuditLog(models.Model):
    ACTION_CHOICES = [
        ('FORCE_LOGOUT', 'Déconnexion forcée'),
        ('ROLE_CHANGE', 'Changement de rôle'),
        ('PASSWORD_RESET', 'Reset mot de passe'),
        ('USER_DELETE', 'Suppression utilisateur'),
        ('PERMISSION_CHANGE', 'Modification permissions'),
        ('ACCOUNT_DISABLE', 'Désactivation compte'),
    ]

    admin_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='audit_actions', verbose_name="Administrateur"
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_targets', verbose_name="Utilisateur ciblé"
    )
    ip_address = models.GenericIPAddressField(null=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log d'audit"
        verbose_name_plural = "Logs d'audit"
        ordering = ['-timestamp']
```

### Fonction de log (appelée à chaque action sensible)

```python
# audit.py
from .models import AdminAuditLog

def log_admin_action(admin_user, action, target_user=None, ip=None, details=''):
    AdminAuditLog.objects.create(
        admin_user=admin_user,
        action=action,
        target_user=target_user,
        ip_address=ip,
        details=details,
    )
```

### Dans l'admin

Section "Logs d'audit" en lecture seule (pas de modification possible). Filtrable par action, par admin, par période. Export CSV disponible.

---

## Étape 8 — Monitoring serveur avec psutil

### Ce qu'on monitore

Un bon monitoring admin ne se limite pas aux utilisateurs. L'état du serveur est visible directement dans le dashboard sans ouvrir de terminal.

**Métriques système :**
- CPU : pourcentage d'utilisation actuel et moyenne 5 minutes
- RAM : utilisée / totale / pourcentage libre
- Disque : espace utilisé / total / pourcentage libre par partition
- Uptime serveur : depuis quand le serveur tourne sans redémarrage

**Métriques applicatives :**
- Nombre d'utilisateurs connectés en ce moment (via UserSession.is_online)
- Nombre de sessions actives totales
- Temps de réponse moyen du serveur (mesuré par middleware)
- Taille de la base de données PostgreSQL

**Métriques sécurité :**
- Nombre de tentatives de login échouées aujourd'hui (axes)
- Nombre d'IPs actuellement bloquées (axes)
- Dernière tentative d'intrusion détectée

### Vue de monitoring

```python
# views.py
import psutil
from datetime import timedelta
from django.utils import timezone

def get_server_metrics():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    boot_time = psutil.boot_time()

    return {
        'cpu_percent': cpu,
        'ram_used_gb': round(ram.used / 1024**3, 1),
        'ram_total_gb': round(ram.total / 1024**3, 1),
        'ram_percent': ram.percent,
        'disk_used_gb': round(disk.used / 1024**3, 1),
        'disk_total_gb': round(disk.total / 1024**3, 1),
        'disk_percent': disk.percent,
        'uptime_hours': round((timezone.now().timestamp() - boot_time) / 3600, 1),
        'users_online': UserSession.objects.filter(
            is_active=True,
            last_seen__gte=timezone.now() - timedelta(seconds=90)
        ).count(),
    }
```

### Taille base de données PostgreSQL

```python
from django.db import connection

def get_db_size():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """)
        return cursor.fetchone()[0]  # ex: "142 MB"
```

---

## Étape 9 — Alertes automatiques

### Architecture de l'alerte

L'alerte suit un principe simple : **détection → log → notification double**.

```
Événement détecté (seuil dépassé)
    → Créer AdminAlert en base (visible dans le dashboard)
    → Envoyer email à tous les admins actifs
```

### Modèle AdminAlert

```python
# models.py
class AdminAlert(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('critical', 'Critique'),
    ]

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
```

### Cas d'alerte configurés

**CPU > 90%**
```python
def check_cpu_alert():
    cpu = psutil.cpu_percent(interval=1)
    if cpu > 90:
        create_alert(
            level='critical',
            title=f"CPU critique : {cpu}%",
            message=f"Le CPU dépasse 90% depuis {timezone.now().strftime('%H:%M')}. Vérifier les processus actifs."
        )
```

**Disque > 85% utilisé**
```python
def check_disk_alert():
    disk = psutil.disk_usage('/')
    if disk.percent > 85:
        create_alert(
            level='warning',
            title=f"Espace disque faible : {disk.percent}% utilisé",
            message=f"Il reste {round((disk.total - disk.used) / 1024**3, 1)} Go libres sur {round(disk.total / 1024**3, 1)} Go."
        )
```

**10 tentatives de connexion échouées**
```python
from axes.models import AccessAttempt
from django.utils import timezone
from datetime import timedelta

def check_brute_force_alert():
    recent = AccessAttempt.objects.filter(
        attempt_time__gte=timezone.now() - timedelta(hours=1)
    ).count()
    if recent >= 10:
        create_alert(
            level='critical',
            title=f"Tentatives d'intrusion : {recent} en 1 heure",
            message="Activité suspecte détectée. Vérifier les IPs bloquées dans django-axes."
        )
```

### Double notification (Email + Admin)

```python
# alerts.py
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

def create_alert(level, title, message):
    # 1. Créer l'alerte dans la base (visible dans l'admin)
    alert = AdminAlert.objects.create(level=level, title=title, message=message)

    # 2. Envoyer email à tous les superusers actifs
    User = get_user_model()
    admin_emails = list(
        User.objects.filter(is_superuser=True, is_active=True)
        .values_list('email', flat=True)
    )
    if admin_emails:
        send_mail(
            subject=f"[AFIA Admin] {level.upper()} — {title}",
            message=f"{message}\n\nDate : {timezone.now().strftime('%d/%m/%Y %H:%M')}\nAccéder au dashboard : https://DOMAINE_APPLICATION/admin/",
            from_email='admin@afia.fr',
            recipient_list=admin_emails,
            fail_silently=True,
        )

    return alert
```

### Affichage dans l'admin

- Bandeau rouge/orange en haut de chaque page admin si alertes non lues
- Section "Alertes" avec liste, niveau de criticité, bouton "Marquer comme lu"
- Compteur d'alertes non lues dans la sidebar Unfold

### Déclenchement des vérifications

Les checks sont appelés via un **management command Django** déclenché par un cron Infomaniak (ou cron Linux sur le VPS) toutes les 5 minutes :

```python
# management/commands/check_alerts.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        check_cpu_alert()
        check_disk_alert()
        check_brute_force_alert()
```

```bash
# crontab — toutes les 5 minutes
*/5 * * * * /path/to/venv/bin/python /path/to/manage.py check_alerts
```

---

## Récapitulatif des choix de conception

| Décision | Choix retenu | Raison |
|---|---|---|
| Thème admin | Unfold | Plus moderne, mieux maintenu, compatible Tailwind |
| Sécurité brute force | django-axes | Standard Django, intégration admin native |
| Tracking sessions | Middleware custom + UserSession | Contrôle total, pas de dépendance externe |
| "Connecté maintenant" | Heartbeat Ajax 60s + seuil 90s | Fiable sans WebSocket, léger |
| Déconnexion forcée | Suppression Session Django | Invalidation immédiate et sûre |
| Statistiques | ORM Django + Chart.js | Pas de librairie lourde, performances optimales |
| Audit trail | Modèle AdminAuditLog custom | Django LogEntry ne couvre pas les actions métier |
| Monitoring système | psutil | Léger, cross-platform, bien maintenu |
| Notifications | Email SMTP + AdminAlert | Email = fiabilité hors connexion / Admin = confort quotidien |
| Déclenchement alertes | Management command + cron | Simple, robuste, sans infrastructure supplémentaire |

---

## Application à un projet concret

Ce plan est générique et s'applique à toutes les applications Django du VPS. Pour chaque application :

1. Installer les packages dans le virtualenv de l'application
2. Ajouter les modèles dans `models.py` et migrer
3. Ajouter les middlewares dans `settings.py` (ordre important : axes en premier)
4. Enregistrer les `ModelAdmin` dans `admin.py`
5. Ajouter les URLs pour le heartbeat et la déconnexion forcée
6. Configurer le cron pour `check_alerts`
7. Tester avec un compte admin de test avant de mettre en production

---

*Document maintenu dans d:\A-VPS\MesMD\ — À mettre à jour lors de chaque évolution du plan.*
