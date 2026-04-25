import os
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models_db import ConnexionLog

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


class AdminLoginBody(BaseModel):
    username: str
    password: str


@router.post("/admin/login")
def admin_login(body: AdminLoginBody, response: Response):
    expected_user = os.getenv("ADMIN_USERNAME", "")
    expected_pass = os.getenv("ADMIN_PASSWORD", "")
    ok = (
        bool(expected_user) and bool(expected_pass) and
        secrets.compare_digest(body.username, expected_user) and
        secrets.compare_digest(body.password, expected_pass)
    )
    if not ok:
        raise HTTPException(401, "Identifiants incorrects.")
    response.set_cookie(_COOKIE, _make_admin_token(), max_age=_MAX_AGE, httponly=True, samesite="lax")
    return {"status": "ok"}


@router.post("/admin/logout")
def admin_logout(response: Response):
    response.delete_cookie(_COOKIE)
    return {"status": "ok"}


@router.get("/admin/check")
def admin_check(_: None = Depends(_require_admin)):
    return {"status": "ok"}


@router.get("/admin/logs")
def get_logs(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    logs = (
        db.query(ConnexionLog)
        .order_by(ConnexionLog.created_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id":     l.id,
            "email":  l.email,
            "action": l.action,
            "ip":     l.ip,
            "date":   l.created_at.strftime("%d/%m/%Y %H:%M"),
        }
        for l in logs
    ]
