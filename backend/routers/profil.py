from fastapi import APIRouter, Cookie, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import User

router = APIRouter()


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


class ProfileBody(BaseModel):
    prenom: str = ""
    nom: str = ""
    subject: str = ""
    niveau: str = ""
    langue_lv: str = ""
    mobile: str = ""


@router.get("/user/profile")
def get_profile(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    return {
        "email":     user.email,
        "prenom":    user.prenom    or "",
        "nom":       user.nom       or "",
        "subject":   user.subject   or "",
        "niveau":    user.niveau    or "",
        "langue_lv": user.langue_lv or "",
        "mobile":    user.mobile    or "",
    }


@router.patch("/user/profile")
def update_profile(body: ProfileBody, aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    user.prenom    = body.prenom    or None
    user.nom       = body.nom       or None
    user.subject   = body.subject   or None
    user.niveau    = body.niveau    or None
    user.langue_lv = body.langue_lv or None
    user.mobile    = body.mobile    or None
    db.commit()
    return {"status": "ok"}
