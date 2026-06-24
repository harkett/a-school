import json
import re

from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import ToolUsageLog, User
from backend.routers.admin import get_ai_model, get_ai_provider, get_max_tokens, get_prompt
from src.generator import generate, LLMRateLimitError

router = APIRouter()


class OptimiseRequest(BaseModel):
    sequence: str
    matiere: str
    niveau: str


class Probleme(BaseModel):
    type: str
    detail: str


class OptimiseResponse(BaseModel):
    sequence_optimisee: str
    problemes: list[Probleme]
    score: str
    avertissement: str | None = None


# Prompt deplace dans backend/llm_prompts.py (administrable en base, lu via get_prompt).


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


def _parse_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    raise ValueError("Réponse non parseable en JSON")


@router.post("/optimize-sequence", response_model=OptimiseResponse)
def api_optimize(
    req: OptimiseRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    if not req.sequence.strip():
        raise HTTPException(400, "La séquence ne peut pas être vide.")

    prompt = get_prompt(db, "optimiseur").format(
        matiere=req.matiere,
        niveau=req.niveau,
        sequence=req.sequence.strip(),
    )

    try:
        raw = generate(prompt, provider=get_ai_provider(db), model=get_ai_model(db), max_tokens=get_max_tokens(db, "optimiseur"), temperature=0, json_mode=True)
        data = _parse_json(raw)
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    except ValueError:
        raise HTTPException(500, "Le modèle n'a pas retourné un résultat exploitable. Réessayez.")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    score_raw = data.get("score", "")
    score_label = score_raw.split(" — ")[0].strip() or None

    try:
        db.add(ToolUsageLog(user_id=db.query(User.id).filter(User.email == email).scalar(), tool="optimiseur", score_label=score_label))
        db.commit()
    except Exception:
        pass

    return OptimiseResponse(
        sequence_optimisee=data.get("sequence_optimisee", ""),
        problemes=[Probleme(**p) for p in data.get("problemes", [])],
        score=score_raw,
        avertissement=data.get("avertissement") or None,
    )
