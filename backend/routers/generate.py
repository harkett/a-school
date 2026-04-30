from fastapi import APIRouter, HTTPException, Cookie, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import GenerateRequest, GenerateResponse
from backend.models_db import ActiviteSauvegardee
from backend import auth as auth_lib
from src.prompts import build_prompt
from src.generator import generate

router = APIRouter()

_FEW_SHOT_MIN = 3  # nombre minimum d'activités sauvegardées pour activer le few-shot


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


def _get_exemples(db: Session, email: str, activite_key: str) -> list[str]:
    rows = (
        db.query(ActiviteSauvegardee.resultat)
        .filter(
            ActiviteSauvegardee.user_email == email,
            ActiviteSauvegardee.activite_key == activite_key,
        )
        .order_by(ActiviteSauvegardee.id.desc())
        .all()
    )
    if len(rows) < _FEW_SHOT_MIN:
        return []
    return [r.resultat for r in rows[:2]]


@router.post("/generate", response_model=GenerateResponse)
def api_generate(
    req: GenerateRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    try:
        exemples = _get_exemples(db, email, req.activite_key)
        kwargs = {"niveau": req.niveau}
        if req.sous_type:
            kwargs["sous_type"] = req.sous_type
        if req.nb:
            kwargs["nb"] = req.nb
        if req.activite_key.startswith("lv_"):
            kwargs["langue"] = req.langue_lv or "langues vivantes"
        prompt = build_prompt(
            req.activite_key,
            req.texte,
            avec_correction=req.avec_correction,
            exemples=exemples,
            **kwargs,
        )
        resultat = generate(prompt)
        return GenerateResponse(resultat=resultat)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
