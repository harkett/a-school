import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.audit import log_admin_action
from backend.database import get_db
from backend.models_db import (
    ActiviteSauvegardee, AdminAlert, AdminAuditLog, ConnexionLog,
    EmailToken, FailedLoginAttempt, Feedback, RefreshToken,
    Setting, User, UserSession,
)
from backend.routers.admin import _require_admin, _get_admin_email

router = APIRouter()

DB_PATH = os.path.join("data", "aschool.db")

CATEGORIES = {
    "tokens_email_expires": {
        "label": "Tokens email expirés",
        "detail": "Liens de vérification et de réinitialisation de mot de passe périmés.",
        "seuil": None,
    },
    "tokens_refresh_old": {
        "label": "Refresh tokens périmés / révoqués",
        "detail": "Tokens de session expirés ou révoqués manuellement.",
        "seuil": None,
    },
    "sessions_inactives": {
        "label": "Sessions fermées",
        "detail": "Sessions déconnectées (manuellement ou par expiration).",
        "seuil": None,
    },
    "users_non_verifies_30j": {
        "label": "Comptes non vérifiés depuis +30 jours",
        "detail": "Inscriptions abandonnées sans clic sur le lien email.",
        "seuil": 30,
    },
    "connexion_logs_90j": {
        "label": "Logs de connexion de +90 jours",
        "detail": "Historique des connexions antérieur à 3 mois.",
        "seuil": 90,
    },
    "failed_logins_30j": {
        "label": "Tentatives échouées de +30 jours",
        "detail": "Tentatives de connexion échouées antérieures à 1 mois.",
        "seuil": 30,
    },
    "audit_logs_180j": {
        "label": "Audit trail de +180 jours",
        "detail": "Actions admin antérieures à 6 mois.",
        "seuil": 180,
    },
}


def _count_orphans(db: Session, now: datetime) -> dict:
    return {
        "tokens_email_expires": db.query(EmailToken).filter(EmailToken.expires_at < now).count(),
        "tokens_refresh_old": db.query(RefreshToken).filter(
            (RefreshToken.expires_at < now) | (RefreshToken.revoked == True)
        ).count(),
        "sessions_inactives": db.query(UserSession).filter(UserSession.is_active == False).count(),
        "users_non_verifies_30j": db.query(User).filter(
            User.is_verified == False,
            User.created_at < now - timedelta(days=30),
        ).count(),
        "connexion_logs_90j": db.query(ConnexionLog).filter(
            ConnexionLog.created_at < now - timedelta(days=90)
        ).count(),
        "failed_logins_30j": db.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.attempt_at < now - timedelta(days=30)
        ).count(),
        "audit_logs_180j": db.query(AdminAuditLog).filter(
            AdminAuditLog.timestamp < now - timedelta(days=180)
        ).count(),
    }


@router.get("/admin/maintenance/stats")
def get_maintenance_stats(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    now = datetime.utcnow()

    db_size_mb = round(os.path.getsize(DB_PATH) / (1024 * 1024), 2) if os.path.exists(DB_PATH) else 0

    tables = {
        "Utilisateurs":         db.query(User).count(),
        "Activités sauvegardées": db.query(ActiviteSauvegardee).count(),
        "Tokens email":         db.query(EmailToken).count(),
        "Refresh tokens":       db.query(RefreshToken).count(),
        "Sessions":             db.query(UserSession).count(),
        "Logs connexions":      db.query(ConnexionLog).count(),
        "Tentatives échouées":  db.query(FailedLoginAttempt).count(),
        "Feedbacks":            db.query(Feedback).count(),
        "Audit trail":          db.query(AdminAuditLog).count(),
        "Alertes":              db.query(AdminAlert).count(),
    }

    orphans = _count_orphans(db, now)

    return {
        "db_size_mb": db_size_mb,
        "tables": tables,
        "orphans": orphans,
        "categories": CATEGORIES,
    }


@router.post("/admin/maintenance/purge/{category}")
def purge_category(
    category: str,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    if category not in CATEGORIES:
        raise HTTPException(400, f"Catégorie inconnue : {category}")

    now = datetime.utcnow()
    purged = 0

    if category == "tokens_email_expires":
        purged = db.query(EmailToken).filter(EmailToken.expires_at < now).delete()

    elif category == "tokens_refresh_old":
        purged = db.query(RefreshToken).filter(
            (RefreshToken.expires_at < now) | (RefreshToken.revoked == True)
        ).delete()

    elif category == "sessions_inactives":
        purged = db.query(UserSession).filter(UserSession.is_active == False).delete()

    elif category == "users_non_verifies_30j":
        users = db.query(User).filter(
            User.is_verified == False,
            User.created_at < now - timedelta(days=30),
        ).all()
        for u in users:
            db.query(EmailToken).filter(EmailToken.email == u.email).delete()
            db.delete(u)
            purged += 1

    elif category == "connexion_logs_90j":
        purged = db.query(ConnexionLog).filter(
            ConnexionLog.created_at < now - timedelta(days=90)
        ).delete()

    elif category == "failed_logins_30j":
        purged = db.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.attempt_at < now - timedelta(days=30)
        ).delete()

    elif category == "audit_logs_180j":
        purged = db.query(AdminAuditLog).filter(
            AdminAuditLog.timestamp < now - timedelta(days=180)
        ).delete()

    db.commit()

    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="MAINTENANCE_PURGE",
        target_email=None,
        ip=request.client.host if request.client else None,
        details=f"Purge '{CATEGORIES[category]['label']}' — {purged} enregistrement(s) supprimé(s)",
    )

    return {"purged": purged, "category": category}
