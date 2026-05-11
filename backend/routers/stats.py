from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models_db import ActiviteSauvegardee
from backend import auth as auth_lib

router = APIRouter()


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


@router.get("/stats/matiere")
def get_stats_matiere(
    matiere: str = Query(""),
    niveau: str = Query(""),
    aschool_access: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    _get_email(aschool_access)

    def _filter(q):
        if matiere:
            q = q.filter(ActiviteSauvegardee.matiere == matiere)
        if niveau:
            q = q.filter(ActiviteSauvegardee.niveau == niveau)
        return q

    total = _filter(db.query(func.count(ActiviteSauvegardee.id))).scalar() or 0

    nb_profs = (
        _filter(db.query(func.count(func.distinct(ActiviteSauvegardee.user_email))))
        .scalar() or 0
    )

    top_types = (
        _filter(
            db.query(ActiviteSauvegardee.activite_label, func.count().label("nb"))
        )
        .group_by(ActiviteSauvegardee.activite_label)
        .order_by(func.count().desc())
        .limit(3)
        .all()
    )

    return {
        "total_plateforme": total,
        "nb_profs": nb_profs,
        "top_types": [{"label": t[0] or "—", "nb": t[1]} for t in top_types],
    }


@router.get("/dashboard")
def get_dashboard(
    aschool_access: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)

    mes_activites = db.query(func.count(ActiviteSauvegardee.id)).filter(
        ActiviteSauvegardee.user_email == email
    ).scalar() or 0

    mes_partages = db.query(func.count(ActiviteSauvegardee.id)).filter(
        ActiviteSauvegardee.user_email == email,
        ActiviteSauvegardee.partagee == True,
    ).scalar() or 0

    communaute_total = db.query(func.count(ActiviteSauvegardee.id)).scalar() or 0
    communaute_profs = db.query(func.count(func.distinct(ActiviteSauvegardee.user_email))).scalar() or 0

    recentes = (
        db.query(ActiviteSauvegardee)
        .filter(ActiviteSauvegardee.user_email == email)
        .order_by(ActiviteSauvegardee.id.desc())
        .limit(3)
        .all()
    )

    return {
        "mes_activites": mes_activites,
        "mes_partages": mes_partages,
        "communaute_total": communaute_total,
        "communaute_profs": communaute_profs,
        "recentes": [
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
                "texte_source": a.texte_source,
                "resultat": a.resultat,
            }
            for a in recentes
        ],
    }
