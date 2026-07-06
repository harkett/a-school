import json
import re

from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.core.database import get_db
from backend.core.models_db import ToolUsageLog, User
from backend.systeme.admin import get_ai_model, get_ai_provider, get_max_tokens, get_temperature, get_prompt
from src.generator import generate, LLMRateLimitError

router = APIRouter()


class AmbigsRequest(BaseModel):
    texte: str
    matiere: str
    niveau: str


class Ambiguite(BaseModel):
    extrait: str
    type: str
    risque: str
    reformulation: str


class AmbigsResponse(BaseModel):
    ambiguites: list[Ambiguite]
    verdict: str


# Prompt déplacé dans backend/llm_prompts.py (administrable en base, lu via get_prompt).


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


@router.post("/detect-ambiguites", response_model=AmbigsResponse)
def api_detect_ambiguites(
    req: AmbigsRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    if not req.texte.strip():
        raise HTTPException(400, "L'énoncé ne peut pas être vide.")

    prompt = get_prompt(db, "ambiguites").format(
        matiere=req.matiere,
        niveau=req.niveau,
        texte=req.texte.strip(),
    )

    try:
        raw = generate(prompt, provider=get_ai_provider(db), model=get_ai_model(db), max_tokens=get_max_tokens(db, "ambiguites"), temperature=get_temperature(db))
        data = _parse_json(raw)
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    except ValueError:
        raise HTTPException(500, "Le modèle n'a pas retourné un résultat exploitable. Réessayez.")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    nb = len(data.get("ambiguites", []))

    try:
        db.add(ToolUsageLog(user_id=db.query(User.id).filter(User.email == email).scalar(), tool="ambiguites", score_label=str(nb)))
        db.commit()
    except Exception:
        pass

    return AmbigsResponse(
        ambiguites=[Ambiguite(**a) for a in data.get("ambiguites", [])],
        verdict=data.get("verdict", ""),
    )
