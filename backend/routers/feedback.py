from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel, Field

from backend import auth as auth_lib
from feedback_client import send_async

router = APIRouter()


class FeedbackBody(BaseModel):
    message: str = Field(min_length=5, max_length=2000)
    rating: int = Field(ge=1, le=5)
    category: str | None = None


@router.post("/feedback", status_code=200)
async def submit_feedback(
    body: FeedbackBody,
    aschool_access: str | None = Cookie(default=None),
):
    if not aschool_access:
        raise HTTPException(401, "Connexion requise.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")

    await send_async(
        app="a-school",
        user_id=email,
        message=body.message,
        rating=body.rating,
        category=body.category,
        user_email=email,
    )
    return {"status": "ok"}
