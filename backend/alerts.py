import os
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import psutil

from backend.database import SessionLocal
from backend.models_db import AdminAlert, FailedLoginAttempt

_COOLDOWN_HOURS = 2


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
        {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC · school.afia.fr
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
    cpu = psutil.cpu_percent(interval=1)
    if cpu > 90:
        create_alert("critical", f"CPU critique : {cpu}%", "Le CPU dépasse 90%. Vérifier les processus actifs sur le VPS.")


def check_disk_alert():
    disk = psutil.disk_usage('/')
    if disk.percent > 85:
        libre = round((disk.total - disk.used) / 1024**3, 1)
        create_alert("warning", f"Disque faible : {disk.percent}% utilisé", f"Il reste {libre} Go libres sur le VPS.")


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
