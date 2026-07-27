import json
import re

from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.core.database import get_db
from backend.core.models_db import ToolUsageLog, User
from backend.systeme.admin import get_ai_model, get_ai_provider, get_cle_texte, get_max_tokens, get_temperature, get_prompt
from backend.llm.generator import generate, LLMRateLimitError

router = APIRouter()


class VerifRequest(BaseModel):
    texte: str            # l'activité générée à vérifier
    matiere: str
    niveau: str
    type_activite: str = ""   # libellé du type choisi (demande initiale)
    precision: str = ""       # sous-type choisi, s'il y en a un
    correction: bool = False  # un corrigé a-t-il été demandé ? (axe Correction ↔ questions)


class AxeVerif(BaseModel):
    axe: str
    statut: str           # ok | info | probleme | non_applicable
    constat: str
    extrait: str = ""


class VerifResponse(BaseModel):
    verdict: str
    axes: list[AxeVerif]


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


@router.post("/verifier-resultat", response_model=VerifResponse)
def api_verifier_resultat(
    req: VerifRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    if not req.texte.strip():
        raise HTTPException(400, "Le résultat à vérifier ne peut pas être vide.")

    prompt = get_prompt(db, "verifier_resultat").format(
        matiere=req.matiere,
        niveau=req.niveau,
        texte=req.texte.strip(),
        type_activite=req.type_activite or "non précisé",
        precision=req.precision or "aucune",
        correction="oui" if req.correction else "non",
    )

    try:
        raw = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), model=get_ai_model(db), max_tokens=get_max_tokens(db, "verifier_resultat"), temperature=get_temperature(db))
        data = _parse_json(raw)
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    except ValueError:
        raise HTTPException(500, "Le modèle n'a pas retourné un résultat exploitable. Réessayez.")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    # Construction défensive : on ne fait pas confiance aux clés du modèle (champs manquants tolérés).
    axes = [
        AxeVerif(
            axe=str(a.get("axe", "")),
            statut=str(a.get("statut", "")),
            constat=str(a.get("constat", "")),
            extrait=str(a.get("extrait", "")),
        )
        for a in data.get("axes", [])
    ]
    nb_probl = sum(1 for a in axes if a.statut == "probleme")

    try:
        db.add(ToolUsageLog(user_id=db.query(User.id).filter(User.email == email).scalar(), tool="verifier_resultat", score_label=str(nb_probl)))
        db.commit()
    except Exception:
        pass

    return VerifResponse(verdict=data.get("verdict", ""), axes=axes)
