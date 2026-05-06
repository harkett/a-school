import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.audit import log_admin_action
from backend.database import get_db
from backend.limiter import limiter
from backend.models_db import ActiviteSauvegardee, AdminAlert, AdminAuditLog, ConnexionLog, EmailToken, FailedLoginAttempt, Feedback, RefreshToken, Setting, User, UserSession

router = APIRouter()

_COOKIE  = "aschool_admin"
_MAX_AGE = 4 * 3600
_ALGO    = "HS256"


def _make_admin_token() -> str:
    secret = os.getenv("JWT_SECRET", "")
    exp = datetime.utcnow() + timedelta(hours=4)
    return jwt.encode({"sub": "admin", "role": "admin", "exp": exp}, secret, algorithm=_ALGO)


def _verify_admin_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET", ""), algorithms=[_ALGO])
        return payload.get("role") == "admin"
    except JWTError:
        return False


def _require_admin(aschool_admin: str = Cookie(default=None)):
    if not aschool_admin or not _verify_admin_token(aschool_admin):
        raise HTTPException(401, "Accès réservé à l'administrateur.")


SETTING_DEFAULTS = {
    "welcome_email_subject": "Bienvenue sur A-SCHOOL !",
    "welcome_email_body": (
        "Bonjour {prenom},\n\n"
        "Votre compte A-SCHOOL est maintenant actif !\n\n"
        "A-SCHOOL est votre assistant pédagogique : générez des activités adaptées à votre matière "
        "et à vos élèves en quelques secondes.\n\n"
        "Connectez-vous dès maintenant sur school.afia.fr\n\n"
        "Parlez-en à vos collègues — plus on est nombreux, plus A-SCHOOL s'améliore !\n\n"
        "Bonne utilisation,\nL'équipe A-SCHOOL"
    ),
}


def get_settings_dict(db: Session) -> dict:
    rows = db.query(Setting).all()
    result = dict(SETTING_DEFAULTS)
    for row in rows:
        result[row.key] = row.value
    return result


class AdminLoginBody(BaseModel):
    username: str
    password: str


def _get_admin_email(request: Request) -> str:
    token = request.cookies.get(_COOKIE)
    if not token:
        return "admin"
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET", ""), algorithms=[_ALGO])
        return payload.get("sub", "admin")
    except JWTError:
        return "admin"


@router.post("/admin/login")
@limiter.limit("10/hour")
def admin_login(request: Request, body: AdminLoginBody, response: Response, db: Session = Depends(get_db)):
    import bcrypt as _bcrypt
    expected_user = os.getenv("ADMIN_USERNAME", "")
    expected_pass = os.getenv("ADMIN_PASSWORD", "")
    ip = request.client.host if request.client else None
    pwd_setting = db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    username_ok = bool(expected_user) and secrets.compare_digest(body.username, expected_user)
    env_ok = bool(expected_pass) and secrets.compare_digest(body.password, expected_pass)
    db_ok = False
    if pwd_setting:
        try:
            db_ok = _bcrypt.checkpw(body.password.encode("utf-8"), pwd_setting.value.encode("utf-8"))
        except Exception:
            pass
    password_ok = env_ok or db_ok
    ok = username_ok and password_ok
    if not ok:
        attempt = FailedLoginAttempt(
            ip_address=ip,
            username=body.username,
            user_agent=request.headers.get("user-agent", ""),
        )
        db.add(attempt)
        db.commit()
        since = datetime.utcnow() - timedelta(hours=1)
        count = db.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.ip_address == ip,
            FailedLoginAttempt.attempt_at >= since,
        ).count()
        if count >= 10:
            db.query(FailedLoginAttempt).filter(
                FailedLoginAttempt.ip_address == ip,
                FailedLoginAttempt.attempt_at >= since,
            ).update({"blocked": True})
            db.commit()
        raise HTTPException(401, "Identifiants incorrects.")
    response.set_cookie(_COOKIE, _make_admin_token(), max_age=_MAX_AGE, httponly=True, samesite="lax")
    admin_email = os.getenv("ADMIN_EMAIL", expected_user)
    db.add(ConnexionLog(email=admin_email, action="admin_login", ip=ip))
    db.commit()
    return {"status": "ok"}


@router.post("/admin/logout")
def admin_logout(response: Response):
    response.delete_cookie(_COOKIE)
    return {"status": "ok"}


@router.get("/admin/check")
def admin_check(_: None = Depends(_require_admin)):
    return {"status": "ok"}


@router.get("/admin/feedbacks")
def get_feedbacks(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(Feedback)
        .order_by(Feedback.created_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id":       f.id,
            "email":    f.user_email,
            "type":     f.type,
            "message":  f.message,
            "rating":   f.rating,
            "category": f.category,
            "statut":   f.statut,
            "date":     f.created_at.strftime("%d/%m/%Y %H:%M"),
        }
        for f in rows
    ]


class StatutBody(BaseModel):
    statut: str

_STATUTS_VALIDES = {"nouveau", "en_cours", "traite", "archive"}

@router.patch("/admin/feedbacks/{feedback_id}/statut")
def update_feedback_statut(
    feedback_id: int,
    body: StatutBody,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    if body.statut not in _STATUTS_VALIDES:
        raise HTTPException(400, "Statut invalide.")
    fb = db.get(Feedback, feedback_id)
    if not fb:
        raise HTTPException(404, "Feedback introuvable.")
    fb.statut = body.statut
    db.commit()
    return {"status": "ok"}


@router.get("/admin/activites")
def get_activites_admin(_: None = Depends(_require_admin)):
    from src.activities import ACTIVITES_PAR_MATIERE, ACTIVITES_PAR_ACTIVITE

    matieres = list(ACTIVITES_PAR_MATIERE.keys())
    total_entrees = sum(len(a) for a in ACTIVITES_PAR_MATIERE.values())

    par_matiere = {
        matiere: [
            {
                "nom": nom,
                "key": data["key"],
                "sous_types": data["sous_types"],
                "nb_sous_types": len(data["sous_types"]),
            }
            for nom, data in activites.items()
        ]
        for matiere, activites in ACTIVITES_PAR_MATIERE.items()
    }

    matrice = [
        {
            "activite": activite,
            "matieres": list(matieres_data.keys()),
        }
        for activite, matieres_data in ACTIVITES_PAR_ACTIVITE.items()
    ]

    return {
        "stats": {
            "nb_matieres": len(matieres),
            "nb_activites_uniques": len(ACTIVITES_PAR_ACTIVITE),
            "nb_entrees": total_entrees,
        },
        "matieres": matieres,
        "par_matiere": par_matiere,
        "matrice": matrice,
    }


class UpdateUserBody(BaseModel):
    prenom: str = ""
    nom: str = ""
    subject: str = ""
    niveau: str = ""


@router.get("/admin/users")
def get_users(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    users = db.query(User).filter(User.is_verified == True).order_by(User.created_at.desc()).all()
    return [
        {
            "email":       u.email,
            "prenom":      u.prenom or "",
            "nom":         u.nom or "",
            "subject":     u.subject or "",
            "niveau":      u.niveau or "",
            "created_at":  u.created_at.strftime("%d/%m/%Y"),
            "last_login":  u.last_login.strftime("%d/%m/%Y %H:%M") if u.last_login else "—",
            "is_active":   u.is_active,
        }
        for u in users
    ]


@router.patch("/admin/user/{email}")
def update_user_profile(email: str, body: UpdateUserBody, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    user.prenom  = body.prenom or None
    user.nom     = body.nom or None
    user.subject = body.subject or None
    user.niveau  = body.niveau or None
    db.commit()
    return {"status": "ok"}


@router.delete("/admin/user/{email}")
def delete_user(email: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    db.query(EmailToken).filter(EmailToken.email == email).delete()
    db.query(RefreshToken).filter(RefreshToken.user_email == email).delete()
    db.query(ActiviteSauvegardee).filter(ActiviteSauvegardee.user_email == email).delete()
    db.query(ConnexionLog).filter(ConnexionLog.email == email).delete()
    db.query(Feedback).filter(Feedback.user_email == email).delete()
    db.delete(user)
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="DELETE_USER",
        target_email=email,
        ip=request.client.host if request.client else None,
        details="Compte supprimé avec toutes ses données",
    )
    return {"status": "ok"}


class ChangePasswordBody(BaseModel):
    old_password: str
    new_password: str
    new_password_confirm: str


@router.post("/admin/change-password")
def change_admin_password(body: ChangePasswordBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    import bcrypt as _bcrypt
    if body.new_password != body.new_password_confirm:
        raise HTTPException(400, "Les mots de passe ne correspondent pas.")
    if len(body.new_password) < 8:
        raise HTTPException(400, "Minimum 8 caractères.")
    expected_pass = os.getenv("ADMIN_PASSWORD", "")
    pwd_setting = db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    if pwd_setting:
        try:
            old_ok = _bcrypt.checkpw(body.old_password.encode("utf-8"), pwd_setting.value.encode("utf-8"))
        except Exception:
            old_ok = False
    else:
        old_ok = bool(expected_pass) and secrets.compare_digest(body.old_password, expected_pass)
    if not old_ok:
        raise HTTPException(400, "Mot de passe actuel incorrect.")
    new_hash = _bcrypt.hashpw(body.new_password.encode("utf-8"), _bcrypt.gensalt(12)).decode("utf-8")
    if pwd_setting:
        pwd_setting.value = new_hash
    else:
        db.add(Setting(key="admin_password_hash", value=new_hash))
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="CHANGE_PASSWORD",
        target_email=None,
        ip=request.client.host if request.client else None,
        details="Mot de passe admin modifié via l'interface",
    )
    return {"status": "ok"}


class SettingsBody(BaseModel):
    welcome_email_subject: str = ""
    welcome_email_body: str = ""


@router.get("/admin/settings")
def get_settings(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    return get_settings_dict(db)


@router.put("/admin/settings")
def save_settings(body: SettingsBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    for key, value in body.dict().items():
        row = db.query(Setting).filter(Setting.key == key).first()
        if row:
            row.value = value
        else:
            db.add(Setting(key=key, value=value))
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="UPDATE_SETTINGS",
        target_email=None,
        ip=request.client.host if request.client else None,
        details="Paramètres email mis à jour",
    )
    return {"status": "ok"}


class SendEmailBody(BaseModel):
    subject: str
    body: str


@router.post("/admin/user/{email}/reset-password")
def admin_reset_password(email: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    from backend import auth as auth_lib
    token = auth_lib.generate_email_token(db, email, "reset_password")
    try:
        auth_lib.send_reset_email(email, token)
    except Exception as e:
        raise HTTPException(500, f"Erreur envoi email : {e}")
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="RESET_PASSWORD",
        target_email=email,
        ip=request.client.host if request.client else None,
        details="Lien de réinitialisation envoyé par l'admin",
    )
    return {"status": "ok"}


@router.patch("/admin/user/{email}/toggle-active")
def toggle_user_active(email: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    user.is_active = not user.is_active
    if not user.is_active:
        db.query(UserSession).filter(
            UserSession.user_email == email,
            UserSession.is_active == True,
        ).update({"is_active": False})
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="ACTIVATE_USER" if user.is_active else "DEACTIVATE_USER",
        target_email=email,
        ip=request.client.host if request.client else None,
        details=f"Compte {'activé' if user.is_active else 'désactivé'}",
    )
    return {"status": "ok", "is_active": user.is_active}


@router.post("/admin/user/{email}/send-email")
def send_email_to_user(email: str, body: SendEmailBody, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    from backend import auth as auth_lib
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    try:
        auth_lib.send_custom_email(email, user.prenom, body.subject, body.body)
    except Exception as e:
        raise HTTPException(500, f"Erreur envoi email : {e}")
    return {"status": "ok"}


@router.post("/admin/settings/test-email")
def test_welcome_email(body: SettingsBody, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    from backend import auth as auth_lib
    admin_email = os.getenv("SMTP_USERNAME", "")
    if not admin_email:
        raise HTTPException(500, "SMTP_USERNAME non configuré.")
    settings = get_settings_dict(db)
    subject = body.welcome_email_subject or settings["welcome_email_subject"]
    content = body.welcome_email_body    or settings["welcome_email_body"]
    try:
        auth_lib.send_custom_email(admin_email, "Admin", subject, content)
    except Exception as e:
        raise HTTPException(500, f"Erreur envoi email : {e}")
    return {"status": "ok"}


@router.get("/admin/sessions")
def get_sessions(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    sessions = (
        db.query(UserSession)
        .filter(UserSession.is_active == True)
        .order_by(UserSession.last_seen.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id":        s.id,
            "email":     s.user_email,
            "browser":   s.browser or "—",
            "os":        s.os or "—",
            "device":    s.device_type or "—",
            "ip":        s.ip_address or "—",
            "login_at":  s.login_at.strftime("%d/%m/%Y %H:%M"),
            "last_seen": s.last_seen.strftime("%d/%m/%Y %H:%M"),
            "is_online": s.is_online,
        }
        for s in sessions
    ]


@router.post("/admin/force-logout/{session_id}")
def force_logout(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    session_obj = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session_obj:
        raise HTTPException(404, "Session introuvable.")
    admin_email = os.getenv("ADMIN_EMAIL", "")
    if admin_email and session_obj.user_email == admin_email:
        raise HTTPException(403, "Impossible de déconnecter la session administrateur.")
    session_obj.is_active = False
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="FORCE_LOGOUT",
        target_email=session_obj.user_email,
        ip=request.client.host if request.client else None,
        details=f"Session {session_obj.session_key[:8]}... déconnectée",
    )
    return {"status": "ok"}


@router.get("/admin/stats/overview")
def stats_overview(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    today = datetime.utcnow().date()
    threshold_online = datetime.utcnow() - timedelta(seconds=90)
    return {
        "total_profs":        db.query(User).filter(User.is_verified == True).count(),
        "connexions_today":   db.query(ConnexionLog).filter(
                                  ConnexionLog.action == "login",
                                  func.date(ConnexionLog.created_at) == today
                              ).count(),
        "feedbacks_nouveaux": db.query(Feedback).filter(Feedback.statut == "nouveau").count(),
        "alertes_nonlues":    db.query(AdminAlert).filter(AdminAlert.is_read == False).count(),
        "sessions_online":    db.query(UserSession).filter(
                                  UserSession.is_active == True,
                                  UserSession.last_seen >= threshold_online
                              ).count(),
    }


@router.get("/admin/stats/logins")
def stats_logins(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    since = datetime.utcnow() - timedelta(days=30)
    rows = (
        db.query(
            func.date(ConnexionLog.created_at).label("day"),
            func.count(ConnexionLog.id).label("count"),
        )
        .filter(ConnexionLog.action == "login", ConnexionLog.created_at >= since)
        .group_by(func.date(ConnexionLog.created_at))
        .order_by(func.date(ConnexionLog.created_at))
        .all()
    )
    return [{"day": str(r.day), "count": r.count} for r in rows]


@router.get("/admin/server-metrics")
def server_metrics(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    import psutil
    cpu   = psutil.cpu_percent(interval=1)
    ram   = psutil.virtual_memory()
    disk  = psutil.disk_usage('/')
    up_h  = round((datetime.now(timezone.utc).timestamp() - psutil.boot_time()) / 3600, 1)
    return {
        "cpu_percent":  cpu,
        "ram_used_gb":  round(ram.used / 1024**3, 1),
        "ram_total_gb": round(ram.total / 1024**3, 1),
        "ram_percent":  ram.percent,
        "disk_used_gb": round(disk.used / 1024**3, 1),
        "disk_total_gb":round(disk.total / 1024**3, 1),
        "disk_percent": disk.percent,
        "uptime_hours": up_h,
    }


@router.get("/admin/db-size")
def db_size(_: None = Depends(_require_admin)):
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "aschool.db")
    try:
        size_mb = round(os.path.getsize(os.path.normpath(path)) / 1024**2, 2)
    except FileNotFoundError:
        size_mb = 0
    return {"size_mb": size_mb}


@router.get("/admin/alerts")
def get_alerts(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(AdminAlert)
        .order_by(AdminAlert.is_read.asc(), AdminAlert.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id":         r.id,
            "level":      r.level,
            "title":      r.title,
            "message":    r.message,
            "is_read":    r.is_read,
            "read_by":    r.read_by or "",
            "date":       r.created_at.strftime("%d/%m/%Y %H:%M"),
        }
        for r in rows
    ]


@router.post("/admin/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    alert = db.query(AdminAlert).filter(AdminAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alerte introuvable.")
    alert.is_read  = True
    alert.read_by  = _get_admin_email(request)
    alert.read_at  = datetime.utcnow()
    db.commit()
    return {"status": "ok"}


@router.get("/admin/audit-log")
def get_audit_log(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(AdminAuditLog)
        .order_by(AdminAuditLog.timestamp.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id":           r.id,
            "admin_email":  r.admin_email or "admin",
            "action":       r.action,
            "target_email": r.target_email or "—",
            "ip":           r.ip_address or "—",
            "details":      r.details or "",
            "date":         r.timestamp.strftime("%d/%m/%Y %H:%M"),
        }
        for r in rows
    ]


@router.get("/admin/stats/hours")
def stats_hours(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(
            func.strftime('%H', ConnexionLog.created_at).label("hour"),
            func.count(ConnexionLog.id).label("count"),
        )
        .filter(ConnexionLog.action == "login")
        .group_by(func.strftime('%H', ConnexionLog.created_at))
        .order_by(func.strftime('%H', ConnexionLog.created_at))
        .all()
    )
    hours_map = {r.hour: r.count for r in rows}
    return [{"hour": f"{h:02d}h", "count": hours_map.get(f"{h:02d}", 0)} for h in range(24)]


@router.get("/admin/failed-attempts")
def get_failed_attempts(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(FailedLoginAttempt)
        .order_by(FailedLoginAttempt.attempt_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id":         r.id,
            "ip":         r.ip_address or "—",
            "username":   r.username or "—",
            "user_agent": r.user_agent or "—",
            "blocked":    r.blocked,
            "date":       r.attempt_at.strftime("%d/%m/%Y %H:%M"),
        }
        for r in rows
    ]


@router.get("/admin/logs")
def get_logs(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(ConnexionLog, User.subject)
        .outerjoin(User, User.email == ConnexionLog.email)
        .order_by(ConnexionLog.created_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id":      l.id,
            "email":   l.email,
            "subject": subject or "—",
            "action":  l.action,
            "ip":      l.ip,
            "date":    l.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for l, subject in rows
    ]
