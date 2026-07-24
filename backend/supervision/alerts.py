import os
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import psutil

from backend.core.database import SessionLocal
from backend.core.models_db import AdminAlert, FailedLoginAttempt

_COOLDOWN_HOURS = 2


def _ou_mesure() -> str:
    """Où la mesure est prise — l'alerte dit la VÉRITÉ selon l'environnement : en production le
    serveur (VPS), en développement la machine de travail (le PC qui fait tourner Docker). Avant,
    le texte disait toujours « sur le VPS » et envoyait l'admin chercher au mauvais endroit quand
    c'était sa machine de dev qui chauffait (cas réel du 24/07 : démarrage de la pile locale)."""
    return "sur le serveur (VPS)" if os.getenv("ENV") == "production" else "sur cette machine de développement"


def _already_alerted(db, title: str) -> bool:
    """Évite le flood : une seule alerte du même titre toutes les 2h."""
    since = datetime.utcnow() - timedelta(hours=_COOLDOWN_HOURS)
    return db.query(AdminAlert).filter(
        AdminAlert.title == title,
        AdminAlert.created_at >= since,
    ).first() is not None


def _send_alert_email(level: str, title: str, message: str):
    admin_email = os.getenv("ADMIN_EMAIL", "")
    if not admin_email:
        return
    from_addr = os.getenv("FEEDBACK_FROM", "aSchool Feedback <feedback@aschool.fr>")
    icon = {"critical": "🔴", "warning": "🟠", "info": "🔵"}.get(level, "⚪")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[aSchool Admin] {icon} {level.upper()} — {title}"
    msg["From"]    = from_addr
    msg["To"]      = admin_email

    plain = f"{title}\n\n{message}\n\nDate : {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC"
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
        {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC · aschool.fr
      </p>
    </div>
    """
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        from backend.auth import _smtp_send
        _smtp_send(msg)
    except Exception:
        pass  # L'alerte est en BDD même si l'email échoue


def create_alert(level: str, title: str, message: str):
    db = SessionLocal()
    try:
        if _already_alerted(db, title):
            return
        db.add(AdminAlert(level=level, title=title, message=message))
        db.commit()
        _send_alert_email(level, title, message)
    except Exception:
        db.rollback()
    finally:
        db.close()


def check_cpu_alert():
    # Charge SOUTENUE sur 5 min, pas un flash d'1 s : psutil.cpu_percent(interval=1)
    # lisait une seule seconde, donc un pic ponctuel déclenchait une fausse alerte
    # alors que la machine était au repos (cas réel du 23/06 : 100% affiché, ~0,3% réel).
    # getloadavg()[1] = nb moyen de processus en attente CPU sur 5 min ; normalisé par
    # le nombre de cœurs, 100 % = tous les cœurs pleinement occupés en continu sur 5 min.
    cores = psutil.cpu_count() or 1
    charge_pct = round(psutil.getloadavg()[1] / cores * 100, 1)
    if charge_pct > 90:
        create_alert(
            "critical",
            f"CPU critique : {charge_pct}%",
            f"Le processeur dépasse 90 % en moyenne sur 5 minutes {_ou_mesure()}. "
            f"Vérifier les processus actifs.",
        )


def check_disk_alert():
    disk = psutil.disk_usage('/')
    if disk.percent > 85:
        libre = round((disk.total - disk.used) / 1024**3, 1)
        create_alert("warning", f"Disque faible : {disk.percent}% utilisé",
                     f"Il reste {libre} Go libres {_ou_mesure()}.")


def check_brute_force_alert():
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(hours=1)
        count = db.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.attempt_at >= since,
        ).count()
        if count >= 10:
            create_alert(
                "critical",
                f"Tentatives d'intrusion : {count} en 1h",
                f"{count} tentatives de connexion admin échouées détectées dans la dernière heure. Vérifier les IPs dans le panel admin.",
            )
    except Exception:
        pass
    finally:
        db.close()


def run_all_checks():
    check_cpu_alert()
    check_disk_alert()
    check_brute_force_alert()
