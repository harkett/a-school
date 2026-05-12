import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Cookie, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import Feedback, User

# A-FEEDBACK a été retiré le 28/04/2026 — notification par SMTP direct uniquement.
router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("data/uploads/feedbacks")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {
    "image/png":        ".png",
    "image/jpeg":       ".jpg",
    "application/pdf":  ".pdf",
    "text/plain":       ".txt",
}
MAX_SIZE = 5 * 1024 * 1024  # 5 Mo

STATUTS_MODIFIABLES = {"nouveau", "en_cours"}


class FeedbackBody(BaseModel):
    type: str = "feedback"
    message: str = Field(min_length=1, max_length=2000)
    rating: int = Field(ge=0, le=5, default=0)
    category: str | None = None
    attachment_path: str | None = None


class FeedbackUpdateBody(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    category: str | None = None
    attachment_path: str | None = None


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Connexion requise.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


# ── Upload fichier joint ──────────────────────────────────────────────────────

@router.post("/feedback/upload", status_code=200)
async def upload_attachment(
    file: UploadFile = File(...),
    aschool_access: str | None = Cookie(default=None),
):
    _get_email(aschool_access)  # auth uniquement

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Format non accepté. Seuls PNG, JPEG, PDF et TXT sont autorisés.")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, "Fichier trop volumineux. Maximum 5 Mo.")

    ext = ALLOWED_TYPES[file.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename
    dest.write_bytes(content)

    return {"path": filename}


# ── Télécharger un fichier joint (prof propriétaire ou admin) ─────────────────

@router.get("/feedback/attachment/{filename}", status_code=200)
def get_attachment(
    filename: str,
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
    aschool_admin: str | None = Cookie(default=None),
):
    # Sécurité : nom de fichier sans chemin
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Nom de fichier invalide.")

    # Auth : prof ou admin
    is_admin = False
    if aschool_admin:
        payload = auth_lib.verify_access_token(aschool_admin)
        is_admin = bool(payload)

    if not is_admin:
        email = _get_email(aschool_access)
        fb = (
            db.query(Feedback)
            .filter(
                Feedback.user_email == email,
                Feedback.attachment_path.like(f"%{filename}%"),
            )
            .first()
        )
        if not fb:
            raise HTTPException(403, "Accès refusé.")

    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Fichier introuvable.")

    return FileResponse(str(path))


# ── Soumettre un feedback ──────────────────────────────────────────────────────

@router.post("/feedback", status_code=200)
def submit_feedback(
    body: FeedbackBody,
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    email = _get_email(aschool_access)

    db.add(Feedback(
        type=body.type,
        user_email=email,
        message=body.message,
        rating=body.rating,
        category=body.category,
        attachment_path=body.attachment_path,
    ))
    db.commit()

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
    except Exception as e:
        logger.error(f"Notification feedback non envoyée : {type(e).__name__}: {e}")

    return {"status": "ok"}


# ── Mes feedbacks ──────────────────────────────────────────────────────────────

@router.get("/feedback/mes-feedbacks", status_code=200)
def mes_feedbacks(
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    email = _get_email(aschool_access)
    rows = (
        db.query(Feedback)
        .filter(Feedback.user_email == email, Feedback.type != "notation")
        .order_by(Feedback.created_at.desc())
        .all()
    )
    return [
        {
            "id":              f.id,
            "category":        f.category,
            "message":         f.message,
            "statut":          f.statut or "nouveau",
            "created_at":      f.created_at.strftime("%d/%m/%Y") if f.created_at else "—",
            "updated_at":      f.updated_at.strftime("%d/%m/%Y") if f.updated_at else None,
            "attachment_path": f.attachment_path,
            "modifiable":      (f.statut or "nouveau") in STATUTS_MODIFIABLES,
        }
        for f in rows
    ]


# ── Modifier un feedback ───────────────────────────────────────────────────────

@router.patch("/feedback/{feedback_id}", status_code=200)
def update_feedback(
    feedback_id: int,
    body: FeedbackUpdateBody,
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    email = _get_email(aschool_access)

    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(404, "Feedback introuvable.")
    if fb.user_email != email:
        raise HTTPException(403, "Ce feedback ne vous appartient pas.")
    if (fb.statut or "nouveau") not in STATUTS_MODIFIABLES:
        raise HTTPException(400, "Ce feedback ne peut plus être modifié.")

    fb.message         = body.message
    fb.category        = body.category
    fb.attachment_path = body.attachment_path
    fb.updated_at      = datetime.now(timezone.utc)
    db.commit()

    user = db.query(User).filter(User.email == email).first()
    prof = {
        "email":   email,
        "prenom":  user.prenom  if user else None,
        "nom":     user.nom     if user else None,
        "subject": user.subject if user else None,
        "niveau":  user.niveau  if user else None,
    }
    try:
        auth_lib.send_feedback_update_notification(prof, body.message, body.category)
    except Exception as e:
        logger.error(f"Notification modification feedback non envoyée : {type(e).__name__}: {e}")

    return {"status": "ok"}
