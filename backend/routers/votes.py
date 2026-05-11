from fastapi import APIRouter, Cookie, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import FeatureVote
from backend.routers.admin import _require_admin

router = APIRouter()

VALID_KEYS = {
    'analyser-consigne', 'verifier-evaluation',
    'quiz-interactif', 'app-mobile', 'escape-game',
}

FEATURE_LABELS = {
    'analyser-consigne':   'Analyser une consigne',
    'verifier-evaluation': 'Vérifier une évaluation',
    'quiz-interactif':     'Quiz interactif élèves',
    'app-mobile':          'Application mobile',
    'escape-game':         'Escape Game pédagogique',
}


@router.get("/feature-votes")
def get_votes(
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    if not aschool_access:
        raise HTTPException(401, "Connexion requise.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")

    rows = db.query(FeatureVote.feature_key, func.count(FeatureVote.id)).group_by(FeatureVote.feature_key).all()
    votes = {row[0]: row[1] for row in rows}

    mes_votes = [v.feature_key for v in db.query(FeatureVote).filter(FeatureVote.user_email == email).all()]

    return {"votes": votes, "mes_votes": mes_votes}


class VoteBody(BaseModel):
    feature_key: str


@router.post("/feature-vote")
def toggle_vote(
    body: VoteBody,
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    if not aschool_access:
        raise HTTPException(401, "Connexion requise.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    if body.feature_key not in VALID_KEYS:
        raise HTTPException(400, "Feature inconnue.")

    existing = db.query(FeatureVote).filter(
        FeatureVote.user_email == email,
        FeatureVote.feature_key == body.feature_key,
    ).first()

    if existing:
        db.delete(existing)
        voted = False
    else:
        db.add(FeatureVote(user_email=email, feature_key=body.feature_key))
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

    result = []
    for key in VALID_KEYS:
        result.append({
            "key":   key,
            "label": FEATURE_LABELS[key],
            "count": votes.get(key, 0),
        })

    result.sort(key=lambda x: -x["count"])
    return result
