import logging
import os
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import psutil

from backend.core.database import SessionLocal
from backend.core.models_db import AdminAlert, FailedLoginAttempt
from backend.core.horloge import maintenant_utc

log = logging.getLogger(__name__)


# Valeurs d'origine des quatre seuils — celles que la migration f1c9a3e7b5d2 a semées. Elles ne
# servent QU'AU repli sur une valeur illisible (voir `nombre` ci-dessous), jamais sur une ligne
# absente : ce n'est pas une source, c'est un filet de saisie.
SEUILS_ORIGINE = {
    "alerte_cpu_pct": "90",
    "alerte_disque_pct": "85",
    "alerte_tentatives_1h": "10",
    "alerte_anti_flood_h": "2",
}


def seuils_alertes(db) -> dict:
    """Seuils de surveillance LUS EN BASE (réglages `alerte_*`), relus à chaque contrôle — donc
    modifiables sans redéploiement. Ils étaient écrits en dur ici alors que ce sont des choix de
    configuration. Une valeur illisible (saisie fautive) retombe sur le défaut du registre plutôt
    que de faire sauter la surveillance : couper les alertes serait pire que garder l'ancien seuil.
    """
    from backend.systeme.admin import get_settings_dict   # import local : pas de cycle
    s = get_settings_dict(db)

    def nombre(cle):
        """Le seuil, lu en base. Une ligne ABSENTE lève : depuis le 10/08/2026 les quatre seuils
        sont semés par migration (f1c9a3e7b5d2), et un repli en dur redonnerait au code le dernier
        mot — c'est exactement ce qu'on vient de retirer.

        Une VALEUR illisible, en revanche, retombe sur la ligne d'origine de la migration : une
        saisie fautive ne doit pas couper la surveillance, ce serait pire que garder l'ancien
        seuil. La distinction compte : ligne manquante = base incomplète, on le dit ; valeur
        fautive = erreur humaine réparable, on tient."""
        try:
            return float(s[cle])
        except KeyError:
            raise RuntimeError(
                f"Seuil d'alerte « {cle} » absent de `settings` — migration f1c9a3e7b5d2 non "
                f"appliquée ? La surveillance ne choisit pas de valeur à votre place."
            )
        except (TypeError, ValueError):
            return float(SEUILS_ORIGINE[cle])

    return {
        "cpu_pct":       nombre("alerte_cpu_pct"),
        "disque_pct":    nombre("alerte_disque_pct"),
        "tentatives_1h": nombre("alerte_tentatives_1h"),
        "anti_flood_h":  nombre("alerte_anti_flood_h"),
    }


def _ou_mesure() -> str:
    """Où la mesure est prise — l'alerte dit la VÉRITÉ selon l'environnement : en production le
    serveur (VPS), en développement la machine de travail (le PC qui fait tourner Docker). Avant,
    le texte disait toujours « sur le VPS » et envoyait l'admin chercher au mauvais endroit quand
    c'était sa machine de dev qui chauffait (cas réel du 24/07 : démarrage de la pile locale)."""
    return "sur le serveur (VPS)" if os.getenv("ENV") == "production" else "sur cette machine de développement"


def _etiquette_origine() -> str:
    """Ce que le SUJET du mail dit de l'origine de la mesure. `_ou_mesure()` ne renseigne que le
    CORPS ; or dans une boîte mail, seul le sujet se lit sans ouvrir. Le 07/08/2026, douze alertes
    parties de la machine de développement portaient le sujet exact d'une alerte de production —
    l'admin a cherché la panne sur le VPS. Un environnement NON RENSEIGNÉ le dit franchement plutôt
    que de se faire passer pour la production : on préfère un sujet qui interroge à un sujet qui
    ment."""
    env = os.getenv("ENV", "").strip().lower()
    if env == "production":
        return "aSchool PROD"
    return "aSchool DEV" if env else "aSchool ORIGINE INCONNUE"


def _already_alerted(db, title: str) -> bool:
    """Évite le flood : une seule alerte du même titre par fenêtre `alerte_anti_flood_h` (base).

    Le titre est la CLÉ de ce dédoublonnage : il doit rester STABLE d'un contrôle à l'autre. Tant
    qu'il embarquait la valeur mesurée (« CPU critique : 94.4% », puis 100.0%, puis 101.1%), chaque
    relevé portait un titre neuf et la fenêtre n'attrapait jamais rien : la cadence des alertes
    retombait sur celle de l'ordonnanceur, soit une toutes les 5 minutes (douze mails le
    07/08/2026). La valeur va dans le MESSAGE, jamais dans le titre.
    """
    since = maintenant_utc() - timedelta(hours=seuils_alertes(db)["anti_flood_h"])
    return db.query(AdminAlert).filter(
        AdminAlert.title == title,
        AdminAlert.created_at >= since,
    ).first() is not None


def _send_alert_email(level: str, title: str, message: str, sujet_detail: str = ""):
    admin_email = os.getenv("ADMIN_EMAIL", "")
    if not admin_email:
        return

    # Hors production, l'alerte reste en BASE et au JOURNAL mais n'écrit PAS dans la boîte de
    # l'admin : une pile de développement qui chauffe n'est pas un incident (cas réel du
    # 07/08/2026 : douze mails « CPU critique » émis par la machine de travail, envoyant chercher
    # une panne sur le VPS). Le corps du mail disait bien « machine de développement », mais le
    # sujet — seul élément visible dans la liste — était celui d'une alerte de production.
    # Une variable ABSENTE ou vide laisse passer le mail : un serveur dont le réglage a été oublié
    # doit rester bavard. Se taire par défaut de configuration serait pire que le flood.
    env = os.getenv("ENV", "").strip().lower()
    if env and env != "production":
        return
    from_addr = os.getenv("FEEDBACK_FROM", "aSchool Feedback <feedback@aschool.fr>")
    icon = {"critical": "🔴", "warning": "🟠", "info": "🔵"}.get(level, "⚪")

    msg = MIMEMultipart("alternative")
    # Le titre est volontairement STABLE en base (clé anti-flood) : la valeur mesurée voyage à
    # part et ne revient QUE dans le sujet, pour rester lisible dans la liste des mails sans
    # rouvrir la porte au flood.
    detail = f" : {sujet_detail}" if sujet_detail else ""
    msg["Subject"] = f"[{_etiquette_origine()}] {icon} {level.upper()} — {title}{detail}"
    msg["From"]    = from_addr
    msg["To"]      = admin_email

    plain = f"{title}\n\n{message}\n\nDate : {maintenant_utc().strftime('%d/%m/%Y %H:%M')} UTC"
    html  = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:2rem;">
      <div style="background:#1e293b;border-radius:10px;padding:1rem 1.5rem;margin-bottom:1.5rem;">
        <span style="color:white;font-weight:700;font-size:1.1rem;">
          <span style="color:#e05a6e;">A</span>-SCHOOL Admin
        </span>
      </div>
      <p style="font-size:1rem;font-weight:600;color:#1e293b;">{icon} {title}</p>
      <p style="color:#475569;line-height:1.6;">{message}</p>
      <p style="color:#94a3b8;font-size:0.75rem;margin-top:1.5rem;">
        {maintenant_utc().strftime('%d/%m/%Y %H:%M')} UTC · aschool.fr
      </p>
    </div>
    """
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        from backend.securite.comptes import _smtp_send
        _smtp_send(msg)
    except Exception:
        pass  # L'alerte est en BDD même si l'email échoue


def _journaliser(level: str, title: str, message: str):
    """Trace l'alerte dans le JOURNAL (journalctl / docker logs), à côté de la base et du mail.

    Avant, une alerte n'existait que dans `admin_alerts` et dans la boîte de l'admin : invisible
    pour tout outil de supervision qui lit les logs, et donc dépendante d'une boîte mail relevée.
    La sévérité de l'alerte devient la sévérité de la ligne — un « critical » ressort d'un
    `journalctl -p crit` sans ouvrir la base. Un niveau inconnu retombe sur WARNING plutôt que
    d'être perdu : mieux vaut une ligne mal classée qu'une alerte muette.

    L'heure UTC est répétée DANS le message pour recouper avec le mail, qui affiche la même ;
    le préfixe `%(asctime)s` du logger, lui, est à l'heure du conteneur. La SÉVÉRITÉ n'est pas
    répétée dans le texte : `%(levelname)s` la porte déjà en tête de ligne.
    Ne lève jamais : la base et le mail passent même si la journalisation échoue (symétrique du
    « l'alerte est en BDD même si l'email échoue » ci-dessus).
    """
    niveaux = {"critical": logging.CRITICAL, "warning": logging.WARNING, "info": logging.INFO}
    try:
        log.log(
            niveaux.get(level, logging.WARNING),
            "ALERTE — %s | %s | %s UTC",
            title, message, maintenant_utc().strftime("%d/%m/%Y %H:%M:%S"),
        )
    except Exception:
        pass


def create_alert(level: str, title: str, message: str, sujet_detail: str = ""):
    db = SessionLocal()
    try:
        if _already_alerted(db, title):
            # Doublon dans la fenêtre anti-flood : ni base, ni mail, NI journal — reflooder le
            # journal à chaque cycle de surveillance le rendrait illisible.
            return
        db.add(AdminAlert(level=level, title=title, message=message))
        db.commit()
        _journaliser(level, title, message)
        _send_alert_email(level, title, message, sujet_detail)
    except Exception:
        db.rollback()
    finally:
        db.close()


_dernier_cpu = None   # (total, occupé) du contrôle précédent — la fenêtre de mesure


def _charge_cpu_pct():
    """Part du temps processeur RÉELLEMENT consommée depuis le contrôle précédent, en %.

    Deux sondes ont échoué ici, pour la même raison — une intention juste, jamais confrontée à
    une mesure :

      1. `psutil.cpu_percent(interval=1)` ne lisait qu'UNE seconde : un pic isolé faisait
         « 100 % » sur une machine au repos (cas du 23/06).
      2. `getloadavg()[1] / cœurs` a remplacé la première, mais le load average n'est PAS un
         pourcentage de processeur : il compte aussi les tâches en attente de DISQUE, et il peut
         dépasser le nombre de cœurs — d'où les « CPU critique : 104.8% » du 07/08/2026. Mesuré
         dans le conteneur ce jour-là : 17,4 % de CPU réellement consommé pendant que la formule
         annonçait 58,1 %. Sous WSL2 l'écart est maximal, le load lu étant celui de la VM entière.

    Ici on compare deux relevés cumulés de `/proc/stat` : c'est une VRAIE part de temps CPU, et la
    fenêtre est l'intervalle entre deux contrôles (5 min via l'ordonnanceur) — donc une charge
    soutenue, ce que les deux tentatives précédentes cherchaient. L'état est gardé dans ce module
    plutôt qu'avec `cpu_percent(interval=None)`, dont le compteur interne est partagé : chaque
    ouverture du panneau admin (`systeme/admin.py`, qui appelle `cpu_percent`) raccourcirait la
    fenêtre à son insu.

    Rend None quand il n'y a rien à comparer — premier passage après démarrage, ou compteur non
    avancé. Pas de mesure, pas d'alerte : mieux vaut un contrôle sauté qu'un chiffre inventé.
    """
    global _dernier_cpu
    temps = psutil.cpu_times()
    total = sum(temps)
    occupe = total - temps.idle - getattr(temps, "iowait", 0.0)
    precedent, _dernier_cpu = _dernier_cpu, (total, occupe)
    if precedent is None:
        return None
    d_total = total - precedent[0]
    if d_total <= 0:
        return None
    return round(max(0.0, min(100.0, (occupe - precedent[1]) / d_total * 100)), 1)


def check_cpu_alert():
    charge_pct = _charge_cpu_pct()
    if charge_pct is None:
        return
    db = SessionLocal()
    try:
        seuil = seuils_alertes(db)["cpu_pct"]
    finally:
        db.close()
    if charge_pct > seuil:
        create_alert(
            "critical",
            "CPU critique",
            f"Charge à {charge_pct} %, au-delà du seuil de {seuil:g} % en moyenne sur 5 minutes "
            f"{_ou_mesure()}. Vérifier les processus actifs.",
            sujet_detail=f"{charge_pct} %",
        )


def check_disk_alert():
    disk = psutil.disk_usage('/')
    db = SessionLocal()
    try:
        seuil = seuils_alertes(db)["disque_pct"]
    finally:
        db.close()
    if disk.percent > seuil:
        libre = round((disk.total - disk.used) / 1024**3, 1)
        create_alert("warning", "Disque faible",
                     f"{disk.percent} % du disque utilisés, il reste {libre} Go libres "
                     f"{_ou_mesure()}.",
                     sujet_detail=f"{disk.percent} % utilisés")


def check_brute_force_alert():
    db = SessionLocal()
    try:
        seuil = seuils_alertes(db)["tentatives_1h"]
        since = maintenant_utc() - timedelta(hours=1)
        count = db.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.attempt_at >= since,
        ).count()
        if count >= seuil:
            create_alert(
                "critical",
                "Tentatives d'intrusion",
                f"{count} tentatives de connexion admin échouées détectées dans la dernière heure. Vérifier les IPs dans le panel admin.",
                sujet_detail=f"{count} en 1h",
            )
    except Exception:
        pass
    finally:
        db.close()


def run_all_checks():
    check_cpu_alert()
    check_disk_alert()
    check_brute_force_alert()
