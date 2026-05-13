import json
import re

from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import ToolUsageLog
from src.config import AI_API_KEY, AI_MODEL, AI_PROVIDER

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


_PROMPT = """Tu es un expert en didactique et en conception de consignes pédagogiques pour l'enseignement secondaire français (collège et lycée, 6e à Terminale).

Un enseignant de {matiere}, niveau {niveau}, te soumet un exercice ou un énoncé.

Ta mission : détecter toutes les ambiguïtés cognitives — les formulations qui peuvent être mal comprises ou mal interprétées par les élèves — et proposer une reformulation corrigée pour chacune.

Énoncé soumis :
{texte}

Types d'ambiguïtés à détecter :
1. Consigne vague — verbe trop général ("analysez", "commentez", "étudiez") sans critères précis
2. Vocabulaire technique non défini — terme spécialisé supposé connu sans garantie
3. Double sens — formulation pouvant être interprétée de deux façons différentes
4. Critères de réussite absents — l'élève ne sait pas ce qu'on attend (longueur, forme, nombre de points…)
5. Référence implicite — "le texte", "l'auteur", "le document" sans préciser lequel
6. Consigne trop longue — plusieurs tâches combinées sans séparation claire

Format de réponse — JSON strict, rien d'autre autour :
{{
  "ambiguites": [
    {{
      "extrait": "fragment exact de l'énoncé problématique",
      "type": "Consigne vague",
      "risque": "Ce que l'élève risque de comprendre ou de faire à tort",
      "reformulation": "Version corrigée de cet extrait, directement réutilisable"
    }}
  ],
  "verdict": "Phrase de synthèse courte sur la qualité globale de l'énoncé."
}}

Règles :
- Si l'énoncé est clair et sans ambiguïté, retourner "ambiguites": [] et un verdict positif.
- Citer des extraits textuels exacts dans le champ "extrait" (reprendre mot pour mot).
- Les reformulations doivent être concrètes, adaptées au niveau {niveau} et directement utilisables.
- Ne pas inventer de problèmes — ne signaler que les vraies zones à risque.
- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON."""


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


def _call_groq(prompt: str) -> str:
    import requests
    headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000,
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers, json=body, timeout=90,
    )
    if not r.ok:
        raise RuntimeError(f"Erreur Groq {r.status_code}: {r.text}")
    return r.json()["choices"][0]["message"]["content"]


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

    prompt = _PROMPT.format(
        matiere=req.matiere,
        niveau=req.niveau,
        texte=req.texte.strip(),
    )

    try:
        if AI_PROVIDER == "groq":
            raw = _call_groq(prompt)
        else:
            from src.generator import generate
            raw = generate(prompt)
        data = _parse_json(raw)
    except ValueError:
        raise HTTPException(500, "Le modèle n'a pas retourné un résultat exploitable. Réessayez.")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    nb = len(data.get("ambiguites", []))

    try:
        db.add(ToolUsageLog(user_email=email, tool="ambiguites", score_label=str(nb)))
        db.commit()
    except Exception:
        pass

    return AmbigsResponse(
        ambiguites=[Ambiguite(**a) for a in data.get("ambiguites", [])],
        verdict=data.get("verdict", ""),
    )
