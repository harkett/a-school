import json
import re

from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import ToolUsageLog, User
from backend.routers.admin import get_ai_model
from src.generator import generate

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


_PROMPT = """Tu es un expert en didactique et en ingénierie pédagogique pour l'enseignement secondaire français (collège et lycée, 6e à Terminale).

Un enseignant de {matiere}, niveau {niveau}, te soumet une consigne isolée à analyser.

Consigne soumise :
{consigne}

Ta mission : analyser la qualité didactique de cette consigne sur 5 axes, puis proposer une version optimisée.

Axes d'analyse :
1. Clarté linguistique — formulations floues, vagues, trop longues ou mal construites
2. Précision didactique — la consigne dit-elle exactement ce que l'enseignant veut évaluer ?
3. Ambiguïté conceptuelle — mots à double sens, termes polysémiques ("analyser", "expliquer", "décrire", "produit", "simplifier"…)
4. Structure logique — étapes implicites, tâches multiples non séparées, sauts logiques
5. Risque d'erreurs typiques — formulations qui provoquent des erreurs récurrentes chez les élèves de ce niveau

Format de réponse — JSON strict, rien d'autre autour :
{{
  "analyses": [
    {{
      "axe": "Clarté linguistique",
      "severite": "Élevée",
      "extrait": "fragment exact de la consigne posant problème",
      "probleme": "Description précise du problème identifié",
      "conseil": "Suggestion concrète pour corriger ce point"
    }}
  ],
  "verdict": "Phrase de synthèse courte sur la qualité globale de la consigne.",
  "version_optimisee": "La consigne entièrement réécrite avec tous les problèmes corrigés, directement utilisable."
}}

Règles :
- Si la consigne est déjà claire et sans problème, retourner "analyses": [] et un verdict positif. La version_optimisee peut reprendre la consigne telle quelle.
- Citer des extraits textuels exacts dans le champ "extrait" (mot pour mot).
- La version_optimisee doit être adaptée au niveau {niveau} et directement utilisable en classe.
- La sévérité vaut "Modérée" ou "Élevée" uniquement.
- Ne signaler que les vrais problèmes. Ne pas inventer de défauts.
- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON."""


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

    prompt = _PROMPT.format(
        matiere=req.matiere,
        niveau=req.niveau,
        consigne=req.consigne.strip(),
    )

    try:
        raw = generate(prompt, model=get_ai_model(db), max_tokens=2000)
        data = _parse_json(raw)
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
