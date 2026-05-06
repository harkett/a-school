import os

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import ConnexionLog, User

router = APIRouter()

_ACCESS = "aschool_access"
_REFRESH = "aschool_refresh"
_ACCESS_MAX = 15 * 60
_REFRESH_MAX = 30 * 24 * 3600


def _set_cookies(response: Response, access: str, refresh: str):
    kw = dict(httponly=True, samesite="lax", secure=os.getenv("ENV") == "production")
    response.set_cookie(_ACCESS, access, max_age=_ACCESS_MAX, **kw)
    response.set_cookie(_REFRESH, refresh, max_age=_REFRESH_MAX, **kw)


def _clear_cookies(response: Response):
    response.delete_cookie(_ACCESS)
    response.delete_cookie(_REFRESH)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SignupBody(BaseModel):
    email: str
    subject: str = ""
    langue_lv: str = ""
    password: str
    password_confirm: str


class LoginBody(BaseModel):
    email: str
    password: str


class ResendVerificationBody(BaseModel):
    email: str


class RequestResetBody(BaseModel):
    email: str


class ResetPasswordBody(BaseModel):
    token: str
    password: str
    password_confirm: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/auth/signup", status_code=201)
def signup(body: SignupBody, request: Request, db: Session = Depends(get_db)):
    if body.password != body.password_confirm:
        raise HTTPException(400, "Les mots de passe ne correspondent pas.")
    if len(body.password) < 8:
        raise HTTPException(400, "Le mot de passe doit contenir au moins 8 caractères.")
    if len(body.password.encode("utf-8")) > 72:
        raise HTTPException(400, "Le mot de passe est trop long (72 caractères maximum).")

    allowed = os.getenv("ALLOWED_EMAILS", "")
    if allowed:
        whitelist = {e.strip().lower() for e in allowed.split(",")}
        if body.email.strip().lower() not in whitelist:
            raise HTTPException(403, "Inscription réservée aux membres autorisés.")

    try:
        user = auth_lib.create_user(db, body.email, body.password, body.subject, body.langue_lv)
    except ValueError as e:
        raise HTTPException(400, str(e))

    token = auth_lib.generate_email_token(db, user.email, "verify_email")
    try:
        auth_lib.send_verification_email(user.email, token)
    except Exception as e:
        raise HTTPException(500, f"Erreur envoi email : {e}")

    db.add(ConnexionLog(email=user.email, action="signup", ip=request.client.host if request.client else None))
    db.commit()
    return {"status": "ok", "message": "Vérifiez votre boîte mail pour activer votre compte."}


@router.post("/auth/login")
def login(body: LoginBody, request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        user = auth_lib.authenticate_user(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(401, str(e))

    access = auth_lib.create_access_token(user.email)
    refresh = auth_lib.create_refresh_token(db, user.email)
    _set_cookies(response, access, refresh)
    db.add(ConnexionLog(email=user.email, action="login", ip=request.client.host if request.client else None))
    db.commit()
    return {
        "email":     user.email,
        "subject":   user.subject,
        "prenom":    user.prenom,
        "nom":       user.nom,
        "niveau":    user.niveau,
        "langue_lv": user.langue_lv,
    }


@router.post("/auth/resend-verification")
def resend_verification(body: ResendVerificationBody, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    # Toujours retourner ok — ne pas révéler si l'email existe
    if user and not user.is_verified:
        token = auth_lib.generate_email_token(db, email, "verify_email")
        try:
            auth_lib.send_verification_email(email, token)
        except Exception:
            pass  # Silencieux — le frontend reçoit ok dans tous les cas
    return {"status": "ok"}


@router.post("/auth/request-reset")
def request_reset(body: RequestResetBody, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user and user.is_verified:
        token = auth_lib.generate_email_token(db, email, "reset_password")
        try:
            auth_lib.send_reset_email(email, token)
        except Exception:
            pass
    return {"status": "ok"}


@router.post("/auth/reset-password")
def reset_password(body: ResetPasswordBody, db: Session = Depends(get_db)):
    if body.password != body.password_confirm:
        raise HTTPException(400, "Les mots de passe ne correspondent pas.")
    if len(body.password) < 8:
        raise HTTPException(400, "Le mot de passe doit contenir au moins 8 caractères.")
    if len(body.password.encode("utf-8")) > 72:
        raise HTTPException(400, "Le mot de passe est trop long (72 caractères maximum).")

    email = auth_lib.verify_email_token(db, body.token, "reset_password")
    if not email:
        raise HTTPException(400, "Lien invalide ou expiré.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(400, "Lien invalide ou expiré.")

    user.password_hash = auth_lib._hash_password(body.password)
    auth_lib.revoke_all_refresh_tokens(db, email)
    db.commit()
    return {"status": "ok"}


@router.get("/auth/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    email = auth_lib.verify_email_token(db, token, "verify_email")
    if not email:
        raise HTTPException(400, "Lien invalide ou expiré.")
    auth_lib.mark_user_verified(db, email)
    user = db.query(User).filter(User.email == email).first()
    try:
        from backend.routers.admin import get_settings_dict
        settings = get_settings_dict(db)
        auth_lib.send_custom_email(
            email,
            user.prenom if user else None,
            settings["welcome_email_subject"],
            settings["welcome_email_body"],
        )
    except Exception:
        pass
    try:
        auth_lib.send_admin_new_user_notification(email, user.subject if user else None)
    except Exception:
        pass
    return {"status": "ok", "email": email}


@router.post("/auth/refresh")
def refresh(
    response: Response,
    aschool_refresh: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not aschool_refresh:
        raise HTTPException(401, "Non connecté.")
    try:
        access, new_refresh = auth_lib.rotate_refresh_token(db, aschool_refresh)
    except ValueError as e:
        _clear_cookies(response)
        raise HTTPException(401, str(e))
    _set_cookies(response, access, new_refresh)
    return {"status": "ok"}


@router.get("/auth/me")
def get_me(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    user = db.query(User).filter(User.email == email).first()
    return {
        "email":     email,
        "subject":   user.subject   if user else None,
        "prenom":    user.prenom    if user else None,
        "nom":       user.nom       if user else None,
        "niveau":    user.niveau    if user else None,
        "langue_lv": user.langue_lv if user else None,
    }


@router.post("/heartbeat")
def heartbeat():
    # Le UserSessionMiddleware met à jour last_seen sur chaque requête authentifiée.
    # Cette route existe uniquement pour que le browser puisse pinger sans payload.
    return {"status": "ok"}


@router.post("/auth/logout-inactivite")
def logout_inactivite(
    aschool_access: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    email = auth_lib.verify_access_token(aschool_access) if aschool_access else None
    if email:
        db.add(ConnexionLog(email=email, action="inactivite_logout"))
        db.commit()
    return {"status": "ok"}


@router.post("/auth/logout")
def logout(
    response: Response,
    aschool_refresh: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if aschool_refresh:
        auth_lib.revoke_refresh_token(db, aschool_refresh)
    _clear_cookies(response)
    return {"status": "ok"}
