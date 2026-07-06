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


class ConsigneRequest(BaseModel):
    consigne: str
    matiere: str
    niveau: str


class AxeAnalyse(BaseModel):
    axe: str
    severite: str
    extrait: str
    probleme: str
    conseil: str


class ConsigneResponse(BaseModel):
    analyses: list[AxeAnalyse]
    verdict: str
    version_optimisee: str


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


@router.post("/analyser-consigne", response_model=ConsigneResponse)
def api_analyser_consigne(
    req: ConsigneRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    if not req.consigne.strip():
        raise HTTPException(400, "La consigne ne peut pas être vide.")

    prompt = get_prompt(db, "consigne").format(
        matiere=req.matiere,
        niveau=req.niveau,
        consigne=req.consigne.strip(),
    )

    try:
        raw = generate(prompt, provider=get_ai_provider(db), model=get_ai_model(db), max_tokens=get_max_tokens(db, "consigne"), temperature=get_temperature(db))
        data = _parse_json(raw)
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    except ValueError:
        raise HTTPException(500, "Le modèle n'a pas retourné un résultat exploitable. Réessayez.")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    nb = len(data.get("analyses", []))

    try:
        db.add(ToolUsageLog(user_id=db.query(User.id).filter(User.email == email).scalar(), tool="consigne", score_label=str(nb)))
        db.commit()
    except Exception:
        pass

    return ConsigneResponse(
        analyses=[AxeAnalyse(**a) for a in data.get("analyses", [])],
        verdict=data.get("verdict", ""),
        version_optimisee=data.get("version_optimisee", req.consigne),
    )
