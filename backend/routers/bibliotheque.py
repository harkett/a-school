from typing import Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models_db import ActiviteSauvegardee, User
from backend import auth as auth_lib

router = APIRouter()


@router.get("/bibliotheque")
def lister(
    matiere: Optional[str] = Query(default=None),
    niveau: Optional[str] = Query(default=None),
    aschool_access: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")

    query = (
        db.query(ActiviteSauvegardee, User)
        .join(User, User.email == ActiviteSauvegardee.user_email)
        .filter(ActiviteSauvegardee.partagee == True)
        .filter(ActiviteSauvegardee.user_email != email)
        .filter(User.is_active == True)
    )

    if matiere:
        query = query.filter(ActiviteSauvegardee.matiere == matiere)
    if niveau:
        query = query.filter(ActiviteSauvegardee.niveau == niveau)

    rows = query.order_by(ActiviteSauvegardee.id.desc()).all()

    return [
        {
            "id": a.id,
            "activite_key": a.activite_key,
            "activite_label": a.activite_label,
            "niveau": a.niveau,
            "sous_type": a.sous_type,
            "nb": a.nb,
            "avec_correction": a.avec_correction,
            "objet": a.objet,
            "texte_source": a.texte_source,
            "resultat": a.resultat,
            "apercu": a.texte_source[:60] + ("…" if len(a.texte_source) > 60 else ""),
            "partagee_par": u.prenom or "Collègue",
            "matiere": a.matiere or u.subject or "",
        }
        for a, u in rows
    ]
