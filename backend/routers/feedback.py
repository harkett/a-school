import logging
from fastapi import APIRouter, Cookie, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import Feedback, User

# A-FEEDBACK a été retiré le 28/04/2026 — notification par SMTP direct uniquement.
# Ne pas réintroduire feedback_client / send_async : A-SCHOOL gère ses propres emails.

router = APIRouter()
logger = logging.getLogger(__name__)


class FeedbackBody(BaseModel):
    type: str = "feedback"          # feedback | notation
    message: str = Field(min_length=1, max_length=2000)
    rating: int = Field(ge=0, le=5, default=0)
    category: str | None = None


@router.post("/feedback", status_code=200)
def submit_feedback(
    body: FeedbackBody,
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    if not aschool_access:
        raise HTTPException(401, "Connexion requise.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")

    # 1. Sauvegarde locale — source de vérité
    db.add(Feedback(
        type=body.type,
        user_email=email,
        message=body.message,
        rating=body.rating,
        category=body.category,
    ))
    db.commit()

    # 2. Notification email SMTP direct — profil complet du prof inclus
    user = db.query(User).filter(User.email == email).first()
    prof = {
        "email":   email,
        "prenom":  user.prenom  if user else None,
        "nom":     user.nom     if user else None,
        "subject": user.subject if user else None,
        "niveau":  user.niveau  if user else None,
    }
    try:
        auth_lib.send_feedback_notification(prof, body.message, body.rating, body.category, body.type)
    except Exception:
        logger.warning("Notification feedback non envoyée — feedback sauvegardé en BDD.")

    return {"status": "ok"}
