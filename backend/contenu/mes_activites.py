from typing import Optional
from fastapi import APIRouter, HTTPException, Cookie, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend.models_db import ActiviteSauvegardee, FewShotMilestone, User
from backend import auth as auth_lib
from backend.activite.generate import _FEW_SHOT_MIN  # source unique du seuil few-shot



router = APIRouter()


def _maybe_mark_few_shot(db: Session, user_id: int, activite_key: str) -> bool:
    """Pose le jalon « aSchool vous reconnaît » UNE fois par couple (prof, type).
    Renvoie True seulement au franchissement réel du seuil — jamais au-delà, jamais
    rejoué après une suppression qui repasse par le seuil (l'unique fait foi)."""
    count = (
        db.query(ActiviteSauvegardee)
        .filter(
            ActiviteSauvegardee.user_id == user_id,
            ActiviteSauvegardee.activite_key == activite_key,
        )
        .count()
    )
    if count < _FEW_SHOT_MIN:
        return False
    db.add(FewShotMilestone(user_id=user_id, activite_key=activite_key))
    try:
        db.commit()
        return True          # jalon réellement créé = premier franchissement
    except IntegrityError:
        db.rollback()
        return False         # jalon déjà présent = déjà fêté


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
    anonyme: Optional[bool] = None


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
    user_id = db.query(User.id).filter(User.email == email).scalar()
    activite = ActiviteSauvegardee(
        user_id=user_id,
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
    few_shot_just_reached = _maybe_mark_few_shot(db, user_id, req.activite_key)
    return {"id": activite.id, "few_shot_just_reached": few_shot_just_reached}


@router.get("/mes-activites")
def lister(
    aschool_access: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    rows = (
        db.query(ActiviteSauvegardee)
        .filter(ActiviteSauvegardee.user_id == db.query(User.id).filter(User.email == email).scalar())
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
            "created_at": a.created_at.isoformat() if a.created_at else None,
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
        .filter(ActiviteSauvegardee.id == activite_id, ActiviteSauvegardee.user_id == db.query(User.id).filter(User.email == email).scalar())
        .first()
    )
    if not activite:
        raise HTTPException(404, "Activité introuvable.")
    activite.partagee = req.partagee
    if req.anonyme is not None:
        activite.anonyme = req.anonyme
    db.commit()
    return {"ok": True}


@router.delete("/mes-activites/{activite_id}")
def supprimer(
    activite_id: int,
    aschool_access: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    activite = (
        db.query(ActiviteSauvegardee)
        .filter(ActiviteSauvegardee.id == activite_id, ActiviteSauvegardee.user_id == db.query(User.id).filter(User.email == email).scalar())
        .first()
    )
    if not activite:
        raise HTTPException(404, "Activité introuvable.")
    db.delete(activite)
    db.commit()
    return {"ok": True}
