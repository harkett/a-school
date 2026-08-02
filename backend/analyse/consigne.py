import json
import re

from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.securite import comptes
from backend.core.database import get_db
from backend.core.models_db import ToolUsageLog, User
from backend.prof.profil import couple_de_travail
from backend.systeme.admin import (get_ai_model, get_ai_provider, get_cle_texte, get_max_tokens,
                                   get_retry_max, get_retry_wait_max, get_temperature, get_prompt)
from backend.llm.generator import generate, LLMRateLimitError

router = APIRouter()


class ConsigneRequest(BaseModel):
    consigne: str


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


# Prompt déplacé dans backend/core/llm_prompts.py (administrable en base, lu via get_prompt).


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = comptes.verify_access_token(aschool_access)
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
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    if not req.consigne.strip():
        raise HTTPException(400, "La consigne ne peut pas être vide.")

    # Couple résolu EN BASE (couple_de_travail, décision 25/07) — l'écran n'envoie plus
    # matière/niveau, le serveur ne fait plus confiance au corps de la requête.
    matiere, niveau, _ajuste = couple_de_travail(db, user)
    if not matiere or not niveau:
        raise HTTPException(400, "Votre profil n'a pas encore de matière et de niveau — complétez Mon profil avant de lancer l'analyse.")

    prompt = get_prompt(db, "consigne").format(
        matiere=matiere,
        niveau=niveau,
        consigne=req.consigne.strip(),
    )

    try:
        # retry_max / retry_wait_max : même politique de rattrapage qu'ailleurs, lue en base.
        # Elle manquait ici : le réglage `ai_retry_max` de l'admin ne s'appliquait pas.
        raw = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), model=get_ai_model(db),
                       max_tokens=get_max_tokens(db, "consigne"), temperature=get_temperature(db),
                       retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db))
        data = _parse_json(raw)
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    except ValueError:
        raise HTTPException(500, "Le modèle n'a pas retourné un résultat exploitable. Réessayez.")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    nb = len(data.get("analyses", []))

    try:
        db.add(ToolUsageLog(user_id=user.id, tool="consigne", score_label=str(nb)))
        db.commit()
    except Exception:
        pass

    return ConsigneResponse(
        analyses=[AxeAnalyse(**a) for a in data.get("analyses", [])],
        verdict=data.get("verdict", ""),
        version_optimisee=data.get("version_optimisee", req.consigne),
    )
