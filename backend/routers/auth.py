import os

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import ConnexionLog

router = APIRouter()

_ACCESS = "aschool_access"
_REFRESH = "aschool_refresh"
_ACCESS_MAX = 15 * 60
_REFRESH_MAX = 30 * 24 * 3600


def _set_cookies(response: Response, access: str, refresh: str):
    kw = dict(httponly=True, samesite="lax")
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
    password: str
    password_confirm: str


class LoginBody(BaseModel):
    email: str
    password: str


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
        user = auth_lib.create_user(db, body.email, body.password)
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
    return {"email": user.email}


@router.get("/auth/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    email = auth_lib.verify_email_token(db, token, "verify_email")
    if not email:
        raise HTTPException(400, "Lien invalide ou expiré.")
    auth_lib.mark_user_verified(db, email)
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
def get_me(aschool_access: str = Cookie(default=None)):
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return {"email": email}


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
