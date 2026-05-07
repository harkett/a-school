from typing import Optional
from fastapi import APIRouter, HTTPException, Cookie, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.models_db import ActiviteSauvegardee
from backend import auth as auth_lib



router = APIRouter()


class SauvegarderRequest(BaseModel):
    activite_key: str
    activite_label: str
    matiere: Optional[str] = None
    niveau: str
    sous_type: Optional[str] = None
    nb: Optional[int] = None
    avec_correction: bool = False
    objet: Optional[str] = None
    texte_source: str
    resultat: str


class PartagerRequest(BaseModel):
    partagee: bool


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


@router.post("/mes-activites")
def sauvegarder(
    req: SauvegarderRequest,
    aschool_access: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    activite = ActiviteSauvegardee(
        user_email=email,
        activite_key=req.activite_key,
        activite_label=req.activite_label,
        matiere=req.matiere or None,
        niveau=req.niveau,
        sous_type=req.sous_type,
        nb=req.nb,
        avec_correction=req.avec_correction,
        objet=req.objet or None,
        texte_source=req.texte_source,
        resultat=req.resultat,
    )
    db.add(activite)
    db.commit()
    db.refresh(activite)
    return {"id": activite.id}


@router.get("/mes-activites")
def lister(
    aschool_access: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    rows = (
        db.query(ActiviteSauvegardee)
        .filter(ActiviteSauvegardee.user_email == email)
        .order_by(ActiviteSauvegardee.id.desc())
        .all()
    )
    return [
        {
            "id": a.id,
            "activite_key": a.activite_key,
            "activite_label": a.activite_label,
            "matiere": a.matiere,
            "niveau": a.niveau,
            "sous_type": a.sous_type,
            "nb": a.nb,
            "avec_correction": a.avec_correction,
            "objet": a.objet,
            "partagee": a.partagee,
            "texte_source": a.texte_source,
            "resultat": a.resultat,
            "apercu": a.texte_source[:60] + ("…" if len(a.texte_source) > 60 else ""),
        }
        for a in rows
    ]


@router.patch("/mes-activites/{activite_id}")
def basculer_partage(
    activite_id: int,
    req: PartagerRequest,
    aschool_access: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    activite = (
        db.query(ActiviteSauvegardee)
        .filter(ActiviteSauvegardee.id == activite_id, ActiviteSauvegardee.user_email == email)
        .first()
    )
    if not activite:
        raise HTTPException(404, "Activité introuvable.")
    activite.partagee = req.partagee
    db.commit()
    return {"ok": True}
