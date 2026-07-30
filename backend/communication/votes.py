from fastapi import APIRouter, Cookie, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.core.database import get_db
from backend.core.models_db import FeatureVotable, FeatureVote, User
from backend.systeme.admin import _require_admin

router = APIRouter()


def catalogue_features(db: Session, actives_seulement: bool = True) -> list[FeatureVotable]:
    """Catalogue des fonctionnalités votables, lu EN BASE (table `features_votables`).
    Aucune liste en dur : l'écran prof, la validation du vote et l'admin passent tous ici.
    Table vide = migration non appliquée -> on lève (erreur claire) plutôt que de retomber
    sur du dur caché. `actif=false` retire la carte de l'écran sans perdre les votes."""
    rows = db.query(FeatureVotable).order_by(FeatureVotable.ordre, FeatureVotable.id).all()
    if not rows:
        raise HTTPException(500, "Fonctionnalités votables absentes en base (migration non appliquée ?).")
    return [r for r in rows if r.actif] if actives_seulement else rows


def _email_ou_401(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Connexion requise.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


@router.get("/feature-votes")
def get_votes(
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    email = _email_ou_401(aschool_access)

    rows = db.query(FeatureVote.feature_key, func.count(FeatureVote.id)).group_by(FeatureVote.feature_key).all()
    votes = {row[0]: row[1] for row in rows}

    mes_votes = [v.feature_key for v in db.query(FeatureVote).filter(FeatureVote.user_id == db.query(User.id).filter(User.email == email).scalar()).all()]

    features = [
        {
            "key":         f.code,
            "label":       f.label,
            "description": f.description,
            "categorie":   f.categorie,
            "icone":       f.icone,
            "count":       votes.get(f.code, 0),
        }
        for f in catalogue_features(db)
    ]
    return {"features": features, "mes_votes": mes_votes}


class VoteBody(BaseModel):
    feature_key: str


@router.post("/feature-vote")
def toggle_vote(
    body: VoteBody,
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    email = _email_ou_401(aschool_access)
    if body.feature_key not in {f.code for f in catalogue_features(db)}:
        raise HTTPException(400, "Cette fonctionnalité n'est pas (ou plus) ouverte au vote.")

    existing = db.query(FeatureVote).filter(
        FeatureVote.user_id == db.query(User.id).filter(User.email == email).scalar(),
        FeatureVote.feature_key == body.feature_key,
    ).first()

    if existing:
        db.delete(existing)
        voted = False
    else:
        db.add(FeatureVote(user_id=db.query(User.id).filter(User.email == email).scalar(), feature_key=body.feature_key))
        voted = True

    db.commit()

    count = db.query(func.count(FeatureVote.id)).filter(
        FeatureVote.feature_key == body.feature_key
    ).scalar()

    return {"voted": voted, "count": count}


@router.get("/admin/feature-votes")
def admin_get_votes(
    db: Session = Depends(get_db),
    _=Depends(_require_admin),
):
    rows = db.query(FeatureVote.feature_key, func.count(FeatureVote.id)).group_by(FeatureVote.feature_key).all()
    votes = {row[0]: row[1] for row in rows}

    # Toutes les lignes, y compris inactives : les votes recueillis restent visibles de
    # l'admin même quand la carte a quitté l'écran prof.
    result = [
        {"key": f.code, "label": f.label, "count": votes.get(f.code, 0)}
        for f in catalogue_features(db, actives_seulement=False)
    ]
    result.sort(key=lambda x: -x["count"])
    return result
