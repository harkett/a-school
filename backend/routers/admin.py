import os
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models_db import ConnexionLog, Feedback, User

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
            "message":  f.message,
            "rating":   f.rating,
            "category": f.category,
            "date":     f.created_at.strftime("%d/%m/%Y %H:%M"),
        }
        for f in rows
    ]


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
            "date":    l.created_at.strftime("%d/%m/%Y %H:%M"),
        }
        for l, subject in rows
    ]
