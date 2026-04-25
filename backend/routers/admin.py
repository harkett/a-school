import os

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import ConnexionLog

router = APIRouter()


def _require_admin(aschool_access: str = Cookie(default=None)):
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    admin = os.getenv("ADMIN_EMAIL", "")
    if email.lower() != admin.lower():
        raise HTTPException(403, "Accès réservé à l'administrateur.")
    return email


@router.get("/admin/logs")
def get_logs(db: Session = Depends(get_db), _: str = Depends(_require_admin)):
    logs = db.query(ConnexionLog).order_by(ConnexionLog.created_at.desc()).limit(200).all()
    return [
        {"id": l.id, "email": l.email, "action": l.action, "ip": l.ip, "date": l.created_at.strftime("%d/%m/%Y %H:%M")}
        for l in logs
    ]
